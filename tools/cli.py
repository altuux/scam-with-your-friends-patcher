#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from config import load_config, save_config
from proxy import run_proxy

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_header():
    clear_screen()
    print("=" * 60)
    print("      SWYF AI Toolkit & Multi-Provider Gateway v2.0       ")
    print("             Open Source Edition - by @altuux             ")
    print("=" * 60)
    print()

def setup_keys_wizard():
    cfg = load_config()
    while True:
        print_header()
        print("--- AI Provider & Key Management ---")
        print(f"Current Active Provider: {cfg.get('provider', 'groq').upper()}")
        print(f"Current Model:           {cfg.get('model', 'llama-3.3-70b-versatile')}")
        print()
        
        groq_keys = cfg.get("keys", {}).get("groq", [])
        ds_keys = cfg.get("keys", {}).get("deepseek", [])
        or_keys = cfg.get("keys", {}).get("openrouter", [])
        
        print(f"1. Groq Keys ({len(groq_keys)} configured) [RECOMMENDED: Free & Fastest]")
        print(f"2. DeepSeek Keys ({len(ds_keys)} configured)")
        print(f"3. OpenRouter Keys ({len(or_keys)} configured)")
        print(f"4. Change Active Provider & Model")
        print("0. Back to Main Menu")
        print()
        
        choice = input("Select an option [0-4]: ").strip()
        if choice == "0":
            break
        elif choice == "1":
            manage_provider_keys(cfg, "groq", "https://console.groq.com/keys")
        elif choice == "2":
            manage_provider_keys(cfg, "deepseek", "https://platform.deepseek.com/api_keys")
        elif choice == "3":
            manage_provider_keys(cfg, "openrouter", "https://openrouter.ai/settings/keys")
        elif choice == "4":
            print("\nSelect Active Provider:")
            print("1. Groq (Llama 3.3 70B - Ultra fast, completely free)")
            print("2. DeepSeek (DeepSeek V3 - High quality)")
            print("3. OpenRouter (Custom models)")
            p_choice = input("Choice [1-3]: ").strip()
            if p_choice == "1":
                cfg["provider"] = "groq"
                cfg["model"] = "llama-3.3-70b-versatile"
            elif p_choice == "2":
                cfg["provider"] = "deepseek"
                cfg["model"] = "deepseek-chat"
            elif p_choice == "3":
                cfg["provider"] = "openrouter"
                cfg["model"] = "deepseek/deepseek-v4-flash"
            save_config(cfg)

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
        p = cfg.get("provider", "groq")
        keys_count = len(cfg.get("keys", {}).get(p, []))
        
        print(f"Active Provider: {p.upper()} ({keys_count} keys in pool)")
        print(f"Active Model:    {cfg.get('model')}")
        print("Proxy Port:      8888 (http://127.0.0.1:8888)")
        print()
        print("1. [START] Launch AI Gateway & Live Proxy (Keep running while playing)")
        print("2. [SETUP] Configure AI Providers & Add API Keys")
        print("3. [PATCH] Run KolkataPatcher (Patch game executable & assemblies)")
        print("0. Exit")
        print()
        
        opt = input("Select an option [0-3]: ").strip()
        if opt == "0":
            print("\nGoodbye!")
            break
        elif opt == "1":
            if keys_count == 0:
                print("\n[!] Error: No API keys configured for active provider!")
                print("    Please choose option [2] first and add at least one key.")
                input("Press Enter to continue...")
                continue
            print_header()
            run_proxy(cfg.get("port", 8888))
        elif opt == "2":
            setup_keys_wizard()
        elif opt == "3":
            print("\nLaunching KolkataPatcher...")
            patcher_exe = os.path.join(os.path.dirname(__file__), "..", "release", "KolkataPatcher.exe")
            patcher_linux = os.path.join(os.path.dirname(__file__), "..", "release", "KolkataPatcher-linux")
            
            if os.name == "nt" and os.path.exists(patcher_exe):
                subprocess.run([patcher_exe])
            elif os.path.exists(patcher_linux):
                subprocess.run(["chmod", "+x", patcher_linux])
                subprocess.run([patcher_linux])
            else:
                print("[!] Could not locate precompiled patcher binary.")
            input("\nPress Enter to return to menu...")

if __name__ == "__main__":
    main_menu()
