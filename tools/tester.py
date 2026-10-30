import os
import glob
import json
import platform
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

def find_local_json() -> Optional[str]:
    candidates = []
    
    # 1. Native Windows path (AppData/LocalLow)
    userprofile = os.environ.get("USERPROFILE")
    appdata = os.environ.get("APPDATA")
    localappdata = os.environ.get("LOCALAPPDATA")
    
    potential_bases = []
    if userprofile:
        potential_bases.append(os.path.join(userprofile, "AppData", "LocalLow"))
    if localappdata:
        potential_bases.append(os.path.abspath(os.path.join(localappdata, "..", "LocalLow")))
    if appdata:
        potential_bases.append(os.path.abspath(os.path.join(appdata, "..", "LocalLow")))
        
    for base in potential_bases:
        target = os.path.join(base, "Jatater Worldwide", "Scam With Your Friends", "MetaSave", "local.json")
        if os.path.exists(target):
            candidates.append(target)
            
    # 2. Linux / Proton / Steam Deck paths
    home = os.path.expanduser("~")
    proton_pattern = os.path.join(
        home, ".local/share/Steam/steamapps/compatdata/*/pfx/drive_c/users/*/AppData/LocalLow/Jatater Worldwide/Scam With Your Friends/MetaSave/local.json"
    )
    candidates.extend(glob.glob(proton_pattern))
    
    flatpak_pattern = os.path.join(
        home, ".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/*/pfx/drive_c/users/*/AppData/LocalLow/Jatater Worldwide/Scam With Your Friends/MetaSave/local.json"
    )
    candidates.extend(glob.glob(flatpak_pattern))
    
    # 3. Check current working directory or relative to game exe
    relative_paths = [
        "local.json",
        os.path.join("MetaSave", "local.json"),
        os.path.join("..", "MetaSave", "local.json")
    ]
    for rel in relative_paths:
        if os.path.exists(rel):
            candidates.append(os.path.abspath(rel))

    if not candidates:
        return None
        
    candidates = list(set(candidates))
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]

def test_provider_key(provider: str, api_key: str, model: str) -> bool:
    print(f"\n[*] Testing connection to {provider.upper()} API...")
    
    endpoints = {
        "groq": "https://api.groq.com/openai/v1/chat/completions",
        "deepseek": "https://api.deepseek.com/chat/completions",
        "openrouter": "https://openrouter.ai/api/v1/chat/completions"
    }
    
    endpoint = endpoints.get(provider.lower())
    if not endpoint:
        print(f"[!] Unknown provider: {provider}")
        return False
        
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "user", "content": "Respond with the single word: OK"}
        ],
        "max_tokens": 10
    }).encode("utf-8")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key.strip()}"
    }
    if provider.lower() == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/altuux/swyf-patcher"
        headers["X-Title"] = "SWYF Toolkit"
        
    req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            reply = res_data["choices"][0]["message"]["content"]
            print(f"[+] Provider response: \"{reply.strip()}\"")
            print(f"[+] {provider.upper()} API Key is VALID and ACTIVE!")
            return True
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        print(f"[-] {provider.upper()} rejected request (HTTP {e.code}): {err_msg[:200]}")
        return False
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return False

def inspect_game_save():
    config_path = find_local_json()
    if not config_path:
        print("[!] local.json not found.")
        return
        
    print(f"[*] Found game configuration: {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        values = data.get("values", {})
        print(f"  - Browser Privacy: {values.get('Browser Privacy', 'Default')}")
        print(f"  - Host AI Backend: {values.get('HostAI.Backend', 'Default')}")
    except Exception as e:
        print(f"[!] Failed to parse {config_path}: {e}")

if __name__ == "__main__":
    print("This module is part of SWYF Toolkit and should be run via 'python cli.py'.")
