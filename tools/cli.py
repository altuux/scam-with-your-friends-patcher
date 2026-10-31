#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from config import load_config, save_config, get_app_dir
from proxy import run_proxy, PROVIDER_PRIORITY, DEFAULT_MODELS
from tester import test_provider_key, inspect_game_save

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_header():
    clear_screen()
    print("=" * 60)
    print("      SWYF AI Toolkit & Multi-Provider Gateway v2.0       ")
    print("             Open Source Edition - by @altuux             ")
    print("=" * 60)
    print()

def run_tests():
    print_header()
    print("--- Diagnostics & Connection Tester ---")
    cfg = load_config()
    keys_dict = cfg.get("keys", {})
    
    total_tested = 0
    for p in PROVIDER_PRIORITY:
        keys = keys_dict.get(p, [])
        m = DEFAULT_MODELS.get(p, "")
        if not keys:
            continue
        print(f"Checking Provider: {p.upper()} (Default Model: {m})")
        print(f"Configured Keys:   {len(keys)}")
        for idx, k in enumerate(keys):
            print(f"  Testing Key #{idx + 1} ({k[:8]}...):")
            test_provider_key(p, k, m)
            total_tested += 1
            print("-" * 40)
            
    if total_tested == 0:
        print("[!] No keys found to test! Go to [2] in main menu to add keys.")
            
    print("\nLocal Game Configuration:")
    inspect_game_save()
    input("\nPress Enter to return to menu...")

def setup_keys_wizard():
    cfg = load_config()
    while True:
        print_header()
        print("--- AI Provider Key Pools (Automatic Cascade & Rotation) ---")
        print("All providers with added keys are AUTOMATICALLY ACTIVE.")
        print("Calls cascade by priority: GROQ (Free) -> DEEPSEEK -> OPENROUTER.")
        print()
        
        groq_keys = cfg.get("keys", {}).get("groq", [])
        ds_keys = cfg.get("keys", {}).get("deepseek", [])
        or_keys = cfg.get("keys", {}).get("openrouter", [])
        
        print(f"1. Groq Keys       [{len(groq_keys)} in pool]  (100% Free, Fastest)")
        print(f"2. DeepSeek Keys   [{len(ds_keys)} in pool]  (High Quality)")
        print(f"3. OpenRouter Keys [{len(or_keys)} in pool]  (Fallback network)")
        print("0. Back to Main Menu")
        print()
        
        choice = input("Select an option [0-3]: ").strip()
        if choice == "0":
            break
        elif choice == "1":
            manage_provider_keys(cfg, "groq", "https://console.groq.com/keys")
        elif choice == "2":
            manage_provider_keys(cfg, "deepseek", "https://platform.deepseek.com/api_keys")
        elif choice == "3":
            manage_provider_keys(cfg, "openrouter", "https://openrouter.ai/settings/keys")

def manage_provider_keys(cfg, provider_name: str, get_url: str):
    while True:
        print_header()
        keys = cfg.get("keys", {}).get(provider_name, [])
        print(f"--- Manage {provider_name.upper()} Keys ---")
        print(f"Get a free API key here: {get_url}")
        print(f"Current keys in rotation pool ({len(keys)}):")
        for idx, k in enumerate(keys):
            print(f"  [{idx + 1}] {k[:10]}...{k[-4:] if len(k) > 14 else ''}")
        print()
        print("1. Add new key to pool")
        print("2. Remove a key")
        print("3. Clear all keys")
        print("0. Back")
        print()
        
        sub = input("Select option [0-3]: ").strip()
        if sub == "0":
            break
        elif sub == "1":
            new_key = input("Paste your API key: ").strip()
            if new_key and new_key not in keys:
                keys.append(new_key)
                cfg["keys"][provider_name] = keys
                save_config(cfg)
                print("[+] Key added successfully!")
                time.sleep(1)
        elif sub == "2":
            del_idx = input("Enter number to remove: ").strip()
            if del_idx.isdigit() and 1 <= int(del_idx) <= len(keys):
                removed = keys.pop(int(del_idx) - 1)
                cfg["keys"][provider_name] = keys
                save_config(cfg)
                print(f"[+] Removed key {removed[:8]}...")
                time.sleep(1)
        elif sub == "3":
            cfg["keys"][provider_name] = []
            save_config(cfg)
            print("[+] All keys cleared!")
            time.sleep(1)

def main_menu():
    while True:
        print_header()
        cfg = load_config()
        keys_dict = cfg.get("keys", {})
        
        active_list = [f"{p.upper()} ({len(keys_dict.get(p, []))})" for p in PROVIDER_PRIORITY if keys_dict.get(p)]
        total_keys = sum(len(keys_dict.get(p, [])) for p in PROVIDER_PRIORITY)
        
        print(f"Active Pools:    {' -> '.join(active_list) if active_list else 'NO KEYS (Setup required)'}")
        print(f"Total Key Pool:  {total_keys} keys active in rotation")
        print("Local Gateway:   http://127.0.0.1:8888/v1/chat/completions")
        print()
        print("1. [START] Launch AI Gateway (Keep running in background while playing)")
        print("2. [SETUP] Manage API Keys & Add Friends' Keys to Pool")
        print("3. [TEST]  Test All Active Keys & Verify Connections")
        print("4. [PATCH] Run KolkataPatcher (One-click game & engine patch)")
        print("0. Exit")
        print()
        
        opt = input("Select an option [0-4]: ").strip()
        if opt == "0":
            print("\nGoodbye!")
            break
        elif opt == "1":
            if total_keys == 0:
                print("\n[!] Error: No API keys configured in any pool!")
                print("    Please choose option [2] first and add at least one key.")
                input("Press Enter to continue...")
                continue
            print_header()
            run_proxy(cfg.get("port", 8888))
        elif opt == "2":
            setup_keys_wizard()
        elif opt == "3":
            run_tests()
        elif opt == "4":
            print("\nLaunching KolkataPatcher...")
            app_dir = get_app_dir()
            win_candidates = [
                os.path.join(app_dir, "KolkataPatcher.exe"),
                os.path.join(app_dir, "..", "release", "KolkataPatcher.exe"),
            ]
            linux_candidates = [
                os.path.join(app_dir, "KolkataPatcher-linux"),
                os.path.join(app_dir, "..", "release", "KolkataPatcher-linux"),
            ]
            patcher_exe = next((p for p in win_candidates if os.path.exists(p)), None)
            patcher_linux = next((p for p in linux_candidates if os.path.exists(p)), None)

            if os.name == "nt" and patcher_exe:
                subprocess.run([patcher_exe])
            elif patcher_linux:
                subprocess.run(["chmod", "+x", patcher_linux])
                subprocess.run([patcher_linux])
            else:
                print("[!] Could not locate precompiled patcher binary.")
            input("\nPress Enter to return to menu...")

if __name__ == "__main__":
    main_menu()
