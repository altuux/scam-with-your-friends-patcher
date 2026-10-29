#!/usr/bin/env python3
import os
import glob
import json
import sys
import urllib.request
import urllib.error

def find_local_json():
    pattern = os.path.expanduser(
        "~/.local/share/Steam/steamapps/compatdata/*/pfx/drive_c/users/steamuser/AppData/LocalLow/Jatater Worldwide/Scam With Your Friends/MetaSave/local.json"
    )
    matches = glob.glob(pattern)
    if not matches:
        return None
    matches.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return matches[0]

def test_completion(api_key, model_id):
    print(f"\n[*] Testing AI completion with model '{model_id}'...")
    payload = json.dumps({
        "model": model_id,
        "messages": [
            {"role": "user", "content": "Ahoj, odpověz jednou větou česky, že jsi online."}
        ],
        "max_tokens": 50
    }).encode("utf-8")

    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=payload, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            res_data = json.loads(res.read().decode())
            reply = res_data["choices"][0]["message"]["content"]
            print(f"[+] AI Response: \"{reply.strip()}\"")
            print("[+] Connection test SUCCESSFUL!")
    except Exception as e:
        print(f"[-] AI request failed: {e}")

def inspect_config(fix=False, set_model=None, do_test=False):
    config_path = find_local_json()
    if not config_path:
        print("[!] local.json not found in Steam Proton compatdata!")
        return

    print(f"[*] Found config: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    values = data.get("values", {})
    backend = values.get("HostAI.Backend", 0)
    api_key = values.get("HostAI.OpenRouterKey", "")
    raw_model = values.get("HostAI.OpenRouterModel", None)
    favorites_raw = values.get("HostAI.OpenRouterFavorites", "[]")

    print("\n--- Current Game Host AI Configuration ---")
    print(f"Backend: {backend} ({'OpenRouter Direct' if backend == 1 else 'Official / Jatater Server'})")
    
    key_valid = False
    if api_key:
        masked_key = api_key[:10] + "..." + api_key[-4:]
        print(f"OpenRouter API Key: {masked_key} (Length: {len(api_key)})")
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/auth/key", headers={
                "Authorization": f"Bearer {api_key}"
            })
            with urllib.request.urlopen(req, timeout=5) as res:
                key_info = json.loads(res.read().decode())["data"]
                rem_limit = key_info.get("limit_remaining", 0)
                free_reqs = key_info.get("free_model_daily_requests", {}).get("remaining", 0)
                print(f"  [+] API Key is VALID! Limit: ${rem_limit}, Free daily requests remaining: {free_reqs}")
                key_valid = True
        except Exception as e:
            print(f"  [-] Failed to verify API key with OpenRouter: {e}")
    else:
        print("[-] OpenRouter API Key: NOT SET!")

    selected_model_id = None
    if raw_model:
        try:
            model_obj = json.loads(raw_model)
            selected_model_id = model_obj.get("Id")
            print(f"[+] Assigned Model: {selected_model_id} ({model_obj.get('Name', 'Unknown')})")
        except Exception as e:
            print(f"[!] Assigned Model has invalid JSON: {raw_model} ({e})")
    else:
        print("[-] Assigned Model (HostAI.OpenRouterModel): NOT SET (MISSING)!")
        print("    -> In-game error: 'Choose an OpenRouter model in Host Settings.'")

    favorites = []
    try:
        favorites = json.loads(favorites_raw)
        if favorites:
            print("\nFavorite Models in Game UI:")
            for idx, fav in enumerate(favorites):
                print(f"  [{idx + 1}] {fav.get('Id')} - {fav.get('Name')}")
    except Exception:
        pass

    target_model = set_model
    if not target_model and fix and not selected_model_id:
        if favorites:
            target_model = favorites[0]["Id"]
        else:
            target_model = "deepseek/deepseek-v4.1-flash"

    if target_model:
        print(f"\n[*] Setting model to: {target_model}...")
        matched = None
        for fav in favorites:
            if fav.get("Id") == target_model:
                matched = fav
                break

        if not matched:
            matched = {
                "Id": target_model,
                "Name": target_model,
                "SupportedParameters": ["temperature", "max_tokens"],
                "PriceLabel": "Custom",
                "MaxCompletionTokens": 4096,
                "ReasoningMandatory": False,
                "ReasoningEfforts": [],
                "ReasoningSupportsTokenBudget": None
            }

        values["HostAI.OpenRouterModel"] = json.dumps(matched)
        values["HostAI.Backend"] = 1
        data["values"] = values

        backup_path = config_path + ".bak"
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        selected_model_id = target_model
        print(f"[+] Successfully wrote HostAI.OpenRouterModel to {config_path}!")
        print("[+] Game is now configured to use:", matched["Id"])

    if do_test and key_valid and selected_model_id:
        test_completion(api_key, selected_model_id)

if __name__ == "__main__":
    fix_flag = "--fix" in sys.argv
    test_flag = "--test" in sys.argv
    model_arg = None
    for i, arg in enumerate(sys.argv):
        if arg == "--set-model" and i + 1 < len(sys.argv):
            model_arg = sys.argv[i + 1]

    inspect_config(fix=fix_flag, set_model=model_arg, do_test=test_flag)
