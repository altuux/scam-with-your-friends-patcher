#!/usr/bin/env python3
import http.server
import json
import socketserver
import threading
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from config import load_config, save_config

PROVIDER_ENDPOINTS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions"
}

DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "deepseek": "deepseek-chat",
    "openrouter": "deepseek/deepseek-v4-flash"
}

class KeyRotator:
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
            "last_latency_ms": 0
        }

    def get_next_key(self, provider: str, keys: List[str]) -> Optional[str]:
        if not keys:
            return None
        with self.lock:
            idx = self.indices.get(provider, 0) % len(keys)
            key = keys[idx]
            self.indices[provider] = (idx + 1) % len(keys)
            return key

rotator = KeyRotator()

def forward_request(payload: Dict[str, Any], provider: str, api_key: str, model_override: Optional[str] = None) -> Optional[Dict[str, Any]]:
    endpoint = PROVIDER_ENDPOINTS.get(provider)
    if not endpoint or not api_key:
        return None

    model = model_override or DEFAULT_MODELS.get(provider, "deepseek/deepseek-v4-flash")
    
    # Clone and prepare payload for target provider
    body = dict(payload)
    body["model"] = model
    
    # Strip game-specific non-standard fields that external APIs might reject
    for extra in ["lobby_session_id", "ai_category", "backend_prompt_length", "prompt_revision", "gameplay_route", "gameplay_player", "gameplay_owner_revision", "prompt_sources", "model_settings", "conversation_protocol", "prompt_version", "prompt_appendix", "conversation_diagnostics"]:
        body.pop(extra, None)

    # Clean up provider requirements for non-OpenRouter providers
    if provider != "openrouter":
        body.pop("provider", None)
        body.pop("models", None)
        body.pop("route", None)

    # Ensure JSON object response format is enabled
    if "response_format" not in body or not isinstance(body["response_format"], dict):
        body["response_format"] = {"type": "json_object"}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key.strip()}"
    }

    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/altuux/swyf-patcher"
        headers["X-Title"] = "Scam With Your Friends Community Patch"

    req_data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            elapsed_ms = int((time.time() - start_time) * 1000)
            rotator.stats["last_latency_ms"] = elapsed_ms
            res_json = json.loads(resp.read().decode("utf-8"))
            return res_json
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        print(f"[!] {provider.upper()} returned HTTP {e.code}: {err_msg[:200]}")
        return None
    except Exception as e:
        print(f"[!] {provider.upper()} request failed: {e}")
        return None

class GameProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default server spam
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
        primary_provider = config.get("provider", "groq")
        fallback_provider = config.get("fallback_provider", "openrouter")
        
        primary_keys = config.get("keys", {}).get(primary_provider, [])
        fallback_keys = config.get("keys", {}).get(fallback_provider, [])

        rotator.stats["total_requests"] += 1
        response = None
        used_provider = None

        # 1. Try primary provider with rotating keys
        for attempt in range(len(primary_keys) or 1):
            key = rotator.get_next_key(primary_provider, primary_keys)
            if not key:
                break
            print(f"[*] Dispatching call to {primary_provider.upper()} (Key: {key[:8]}...)...")
            response = forward_request(payload, primary_provider, key, config.get("model"))
            if response:
                used_provider = primary_provider
                break
            print(f"[!] {primary_provider.upper()} attempt {attempt + 1} failed, trying next key or fallback...")

        # 2. Try fallback provider if primary failed
        if not response and fallback_keys:
            print(f"[!] Primary provider failed. Activating FAILOVER to {fallback_provider.upper()}...")
            for attempt in range(len(fallback_keys) or 1):
                fb_key = rotator.get_next_key(fallback_provider, fallback_keys)
                if not fb_key:
                    break
                response = forward_request(payload, fallback_provider, fb_key, config.get("fallback_model"))
                if response:
                    used_provider = fallback_provider
                    break

        if response:
            rotator.stats["successful_requests"] += 1
            latency = rotator.stats["last_latency_ms"]
            print(f"[+] Call completed successfully via {used_provider.upper()} in {latency}ms!")
            
            res_bytes = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(res_bytes)))
            self.end_headers()
            self.wfile.write(res_bytes)
        else:
            rotator.stats["failed_requests"] += 1
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

    httpd = ThreadedHTTPServer(server_address, GameProxyHandler)
    print(f"[+] SWYF AI Proxy Server listening on http://127.0.0.1:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping proxy server...")
        httpd.server_close()

if __name__ == "__main__":
    cfg = load_config()
    run_proxy(cfg.get("port", 8888))
