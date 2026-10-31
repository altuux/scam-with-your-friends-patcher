import os
import sys
import json
from typing import Dict, Any

CONFIG_FILE = "swyf_config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "groq",
    "model": "qwen/qwen3.8-27b",
    "port": 8888,
    "keys": {
        "groq": [],
        "deepseek": [],
        "openrouter": []
    },
    "fallback_provider": "openrouter",
    "fallback_model": "deepseek/deepseek-v4-flash",
    "auto_retry_count": 3
}

def get_app_dir() -> str:
    # In Nuitka --onefile or frozen builds, __file__ points to a temporary extraction directory.
    # Use sys.argv[0] so swyf_config.json is persisted next to the actual executable.
    if "__compiled__" in globals() or getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.dirname(os.path.abspath(__file__))

def get_config_path() -> str:
    return os.path.join(get_app_dir(), CONFIG_FILE)

def load_config() -> Dict[str, Any]:
    path = get_config_path()
    if not os.path.exists(path):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception as e:
        print(f"[!] Warning: Failed to load {CONFIG_FILE} ({e}). Using defaults.")
        return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]) -> bool:
    path = get_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"[!] Error: Could not save config to {path}: {e}")
        return False
