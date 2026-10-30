import os
import json
from typing import List, Dict, Any

CONFIG_FILE = "swyf_config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",
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

def get_config_path() -> str:
    # Look next to the script / executable
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, CONFIG_FILE)

def load_config() -> Dict[str, Any]:
    path = get_config_path()
    if not os.path.exists(path):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge with defaults for any missing keys
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
