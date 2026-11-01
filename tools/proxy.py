#!/usr/bin/env python3
import copy
import http.server
import json
import socketserver
import threading
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from config import load_config

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SWYF-Gateway/2.0"

PROVIDER_ENDPOINTS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions"
}

DEFAULT_MODELS = {
    "groq": "qwen/qwen3.8-27b",
    "deepseek": "deepseek-chat",
    "openrouter": "deepseek/deepseek-v4-flash"
}

GROQ_FALLBACK_MODELS = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]

OPENAI_STANDARD_FIELDS = {
    "model", "messages", "max_tokens", "temperature", "top_p", "stop",
    "stream", "frequency_penalty", "presence_penalty", "response_format",
    "seed", "tools", "tool_choice", "parallel_tool_calls", "user"
}

# Provider priority hierarchy (Fast & Free first -> High quality -> Fallback)
PROVIDER_PRIORITY = ["groq", "deepseek", "openrouter"]

class MultiProviderPool:
    def __init__(self):
        self.lock = threading.Lock()
        self.indices = {
            "groq": 0,
            "deepseek": 0,
            "openrouter": 0
        }
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "last_latency_ms": 0,
            "provider_usage": {
                "groq": 0,
                "deepseek": 0,
                "openrouter": 0
            }
        }

    def get_next_key(self, provider: str, keys: List[str]) -> Optional[str]:
        if not keys:
            return None
        with self.lock:
            idx = self.indices.get(provider, 0) % len(keys)
            key = keys[idx]
            self.indices[provider] = (idx + 1) % len(keys)
            return key

pool = MultiProviderPool()

def _downgrade_json_schema_to_json_object(body: Dict[str, Any]) -> None:
    rf = body.get("response_format")
    if not isinstance(rf, dict) or rf.get("type") != "json_schema":
        return
    schema_obj = (rf.get("json_schema") or {}).get("schema")
    if schema_obj and isinstance(body.get("messages"), list):
        schema_str = json.dumps(schema_obj, separators=(",", ":"))
        instruction = f"Respond ONLY with a valid JSON object strictly conforming to this JSON schema: {schema_str}"
        msgs = body["messages"]
        if msgs and isinstance(msgs[0], dict) and msgs[0].get("role") == "system":
            if isinstance(msgs[0].get("content"), str) and schema_str not in msgs[0]["content"]:
                msgs[0]["content"] = msgs[0]["content"] + "\n\n" + instruction
        else:
            msgs.insert(0, {"role": "system", "content": instruction})
    body["response_format"] = {"type": "json_object"}

def _normalize_response(res_json: Dict[str, Any]) -> Dict[str, Any]:
    choices = res_json.get("choices")
    if isinstance(choices, list):
        for ch in choices:
            msg = ch.get("message") if isinstance(ch, dict) else None
            if isinstance(msg, dict) and not msg.get("content"):
                reasoning = msg.get("reasoning")
                if isinstance(reasoning, str) and reasoning.strip():
                    msg["content"] = reasoning
    return res_json

def _send_single(endpoint: str, body: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    req_data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")
    start_time = time.time()
    with urllib.request.urlopen(req, timeout=25) as resp:
        elapsed_ms = int((time.time() - start_time) * 1000)
        pool.stats["last_latency_ms"] = elapsed_ms
        res_json = json.loads(resp.read().decode("utf-8"))
        return _normalize_response(res_json)

def forward_request(payload: Dict[str, Any], provider: str, api_key: str, model_override: Optional[str] = None) -> Optional[Dict[str, Any]]:
    endpoint = PROVIDER_ENDPOINTS.get(provider)
    if not endpoint or not api_key:
        return None

    model = model_override or DEFAULT_MODELS.get(provider, "deepseek/deepseek-v4-flash")
    body = copy.deepcopy(payload)

    # Strip game-specific custom metadata fields
    for extra in [
        "lobby_session_id", "ai_category", "backend_prompt_length", "prompt_revision",
        "gameplay_route", "gameplay_player", "gameplay_owner_revision", "prompt_sources",
        "model_settings", "conversation_protocol", "prompt_version", "prompt_appendix",
        "conversation_diagnostics"
    ]:
        body.pop(extra, None)

    if provider != "openrouter":
        if "max_completion_tokens" in body and "max_tokens" not in body:
            body["max_tokens"] = body.pop("max_completion_tokens")
        body = {k: v for k, v in body.items() if k in OPENAI_STANDARD_FIELDS}
        if provider == "deepseek":
            _downgrade_json_schema_to_json_object(body)

    if "response_format" not in body or not isinstance(body["response_format"], dict):
        if "json" in json.dumps(body.get("messages", "")).lower():
            body["response_format"] = {"type": "json_object"}
        else:
            body.pop("response_format", None)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key.strip()}",
        "User-Agent": USER_AGENT
    }
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/altuux/swyf-patcher"
        headers["X-Title"] = "SWYF Toolkit"

    models_to_try = [model]
    if provider == "groq":
        for m in GROQ_FALLBACK_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)

    for candidate_model in models_to_try:
        attempt_body = copy.deepcopy(body)
        attempt_body["model"] = candidate_model
        try:
            return _send_single(endpoint, attempt_body, headers)
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            # Automatic fallback if Groq deprecates a model ID or hits 429 rate limit on this specific model
            if provider == "groq" and candidate_model != models_to_try[-1]:
                if e.code == 404 and "model_not_found" in err_msg:
                    print(f"[*] Groq model '{candidate_model}' unavailable, falling back to next active Groq model...")
                    continue
                if e.code == 429:
                    next_model = models_to_try[models_to_try.index(candidate_model) + 1]
                    print(f"[*] Groq model '{candidate_model}' hit 429 rate limit. Switching to independent model quota '{next_model}' on same key...")
                    continue
            # Automatic fallback if strict json_schema grammar is unsupported by the target model
            if e.code == 400 and isinstance(attempt_body.get("response_format"), dict) and attempt_body["response_format"].get("type") == "json_schema":
                _downgrade_json_schema_to_json_object(attempt_body)
                try:
                    return _send_single(endpoint, attempt_body, headers)
                except Exception as retry_err:
                    print(f"[!] {provider.upper()} schema fallback failed: {retry_err}")
                    return None
            print(f"[!] {provider.upper()} returned HTTP {e.code}: {err_msg[:180]}")
            return None
        except Exception as e:
            print(f"[!] {provider.upper()} request failed: {e}")
            return None
    return None

class GameProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_len)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception:
            self.send_error(400, "Invalid JSON payload")
            return

        config = load_config()
        configured_keys = config.get("keys", {})
        active_providers = [p for p in PROVIDER_PRIORITY if configured_keys.get(p)]

        pool.stats["total_requests"] += 1
        response = None
        successful_provider = None

        if not active_providers:
            print("[!] Warning: No API keys configured in any provider!")

        for provider in active_providers:
            keys = configured_keys.get(provider, [])
            model = DEFAULT_MODELS.get(provider)

            for _ in range(len(keys)):
                key = pool.get_next_key(provider, keys)
                if not key:
                    break

                print(f"[*] Dispatching call to {provider.upper()} (Key: {key[:8]}..., Model: {model})...")
                response = forward_request(payload, provider, key, model)
                if response:
                    successful_provider = provider
                    break
                print(f"[!] {provider.upper()} key {key[:8]}... failed or rate-limited, trying next...")

            if response:
                break
            else:
                print(f"[!] All keys for {provider.upper()} failed. Cascading to next provider in priority...")

        if response:
            pool.stats["successful_requests"] += 1
            pool.stats["provider_usage"][successful_provider] = pool.stats["provider_usage"].get(successful_provider, 0) + 1
            latency = pool.stats["last_latency_ms"]
            print(f"[+] Call completed successfully via {successful_provider.upper()} in {latency}ms!")

            res_bytes = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(res_bytes)))
            self.end_headers()
            self.wfile.write(res_bytes)
        else:
            pool.stats["failed_requests"] += 1
            print("[-] All configured providers and keys failed!")
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            err_payload = json.dumps({"error": {"message": "All AI providers in SWYF Proxy failed or have no valid keys."}}).encode("utf-8")
            self.send_header("Content-Length", str(len(err_payload)))
            self.end_headers()
            self.wfile.write(err_payload)

def run_proxy(port: int = 8888):
    server_address = ("127.0.0.1", port)
    class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    httpd = ThreadedHTTPServer(server_address, GameProxyHandler)
    cfg = load_config()
    keys = cfg.get("keys", {})
    active = [p.upper() for p in PROVIDER_PRIORITY if keys.get(p)]

    print(f"[+] SWYF AI Multi-Provider Gateway listening on http://127.0.0.1:{port}/")
    print(f"[*] Priority Hierarchy: {' -> '.join(active) if active else 'NO KEYS CONFIGURED'}")
    print("[*] Ready for game calls. Press Ctrl+C to return to menu.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping proxy server...")
        httpd.server_close()

if __name__ == "__main__":
    cfg = load_config()
    run_proxy(cfg.get("port", 8888))
