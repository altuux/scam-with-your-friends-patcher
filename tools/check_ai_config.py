#!/usr/bin/env python3
import os
import glob
import json
import sys
import platform
import urllib.request
import urllib.error

def find_local_json():
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
        
    # Sort by newest modification time
    candidates = list(set(candidates))
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]

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

def inspect_config(fix=False, set_model=None, set_key=None, do_test=False):
    config_path = find_local_json()
    if not config_path:
        print("[!] Error: local.json could not be located automatically.")
        if platform.system() == "Windows":
            print("    Expected location: %USERPROFILE%\\AppData\\LocalLow\\Jatater Worldwide\\Scam With Your Friends\\MetaSave\\local.json")
            print("    Make sure you have launched the game at least once so it generates the save directory.")
        else:
            print("    Expected location inside Steam Proton compatdata.")
        return

    print(f"[*] Found config: {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Failed to read {config_path}: {e}")
        return

    values = data.get("values", {})
    backend = values.get("HostAI.Backend", 0)
    api_key = values.get("HostAI.OpenRouterKey", "")
    raw_model = values.get("HostAI.OpenRouterModel", None)
    favorites_raw = values.get("HostAI.OpenRouterFavorites", "[]")

    if set_key:
        api_key = set_key.strip()
        values["HostAI.OpenRouterKey"] = api_key
        values["HostAI.Backend"] = 1
        data["values"] = values
        print(f"[+] Setting OpenRouter API key: {api_key[:10]}...{api_key[-4:]}")

    print("\n--- Current Game Host AI Configuration ---")
    print(f"Backend: {backend} ({'OpenRouter Direct' if backend == 1 else 'Official / Jatater Server (requires legit Steam license)'})")
    
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
                print(f"  [+] API Key is VALID! Remaining limit: ${rem_limit}, Free daily requests remaining: {free_reqs}")
                key_valid = True
        except Exception as e:
            print(f"  [-] Failed to verify API key with OpenRouter: {e}")
            print("      Make sure you pasted the key correctly and your internet connection is active.")
    else:
        print("[-] OpenRouter API Key: NOT SET!")
        print("    -> You must enter an API key from https://openrouter.ai/")

    selected_model_id = None
    if raw_model:
        try:
            model_obj = json.loads(raw_model)
            selected_model_id = model_obj.get("Id")
            print(f"[+] Assigned Model: {selected_model_id} ({model_obj.get('Name', 'Custom')})")
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
            target_model = "deepseek/deepseek-v4-flash"

    needs_save = False
    if set_key:
        needs_save = True

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
                "SupportedParameters": [
                    "frequency_penalty", "include_reasoning", "logit_bias", "logprobs",
                    "max_completion_tokens", "max_tokens", "min_p", "presence_penalty",
                    "reasoning", "reasoning_effort", "repetition_penalty", "response_format",
                    "seed", "stop", "structured_outputs", "temperature", "tool_choice",
                    "tools", "top_a", "top_k", "top_logprobs", "top_p"
                ],
                "PriceLabel": "Custom",
                "MaxCompletionTokens": 4096,
                "ReasoningMandatory": False,
                "ReasoningEfforts": ["none"],
                "ReasoningSupportsTokenBudget": None
            }

        values["HostAI.OpenRouterModel"] = json.dumps(matched)
        values["HostAI.Backend"] = 1
        data["values"] = values
        needs_save = True
        selected_model_id = target_model

    # Also automatically ensure Browser Privacy is allowed
    if values.get("Browser Privacy") != "Allow without asking":
        values["Browser Privacy"] = "Allow without asking"
        needs_save = True
        print("[+] Fixed: Enabled Browser Privacy ('Allow without asking')")

    if needs_save:
        backup_path = config_path + ".bak"
        try:
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"[+] Successfully saved updated configuration to:\n    {config_path}")
            print("[!] IMPORTANT: If the game is currently running, RESTART THE GAME so changes take effect!")
        except Exception as e:
            print(f"[!] Failed to write config: {e}")

    if do_test and key_valid and selected_model_id:
        test_completion(api_key, selected_model_id)

if __name__ == "__main__":
    fix_flag = "--fix" in sys.argv
    test_flag = "--test" in sys.argv
    model_arg = None
    key_arg = None
    
    for i, arg in enumerate(sys.argv):
        if arg == "--set-model" and i + 1 < len(sys.argv):
            model_arg = sys.argv[i + 1]
        elif arg == "--set-key" and i + 1 < len(sys.argv):
            key_arg = sys.argv[i + 1]

    # If user ran without args and model is missing, default to fix
    inspect_config(fix=fix_flag, set_model=model_arg, set_key=key_arg, do_test=test_flag)
