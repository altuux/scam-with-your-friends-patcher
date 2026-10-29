# Kolkata OS Patcher & Auth Bypass for *Scam With Your Friends*

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%2F%20Steam%20Deck-success)](https://github.com/)

A standalone, open-source binary patcher for **Scam With Your Friends** running on the Kolkata OS engine (Unity 6 Mono). 

This tool fixes game-breaking engine crashes, bypasses the broken remote auth loop, and restores full desktop/taskbar functionality in offline, LAN, and non-Steam/cracked environments.

---

## 🛠️ What This Fixes

1. **`MissingMethodException: PlayerPrefs.SetInt` (Game / OS Crash)**
   - Unity 6's Managed Code Stripping stripped core `PlayerPrefs` methods (`SetInt`, `SetFloat`, `DeleteKey`, `Save`, `DeleteAll`) from `UnityEngine.CoreModule.dll`.
   - Restores clean binary stubs so `KolkataOsSingleton.Start()` and `KolkataOsController` boot up without crashing.

2. **Kolkata OS Auth Loop (`STEAM_REJECTED` / `http=0` / `401`)**
   - In offline or OnlineFix environments, the game loops infinitely trying to authenticate with `kolkata-auth.jataterworldwide.com`.
   - Bypasses `EnsureEdgeSessionAsync` and `EdgePostAsync` to immediately validate the session locally with the **Unlimited** membership role and Deluxe entitlements.

3. **Broken System Tray, Taskbar & Caller Queue App Crash**
   - In offline builds, `KolkataOsCallerQueueApp` crashes with `NullReferenceException` when binding the missing Steam Workshop button (`workshop-page`).
   - This exception aborted `BuildDesktop()` halfway through, preventing taskbar buttons, desktop icons, and the system tray from rendering properly.
   - Makes the button binding null-safe, allowing the entire desktop and taskbar to initialize cleanly.

4. **`UnityWebRequest.Get(Uri)` Missing Method**
   - Re-injects the missing URI overload into `UnityEngine.UnityWebRequestModule.dll`.

5. **False-Positive Piracy Alarm**
   - Disables the annoying in-game siren alarm triggered by rejected auth tokens.

6. **Web Browser Privacy Blocker Bypass**
   - Bypasses the blocking consent modal in `KolkataOsController` and approval check in `KolkataOsBrowserHost`, allowing the CEF/UWB in-game browser to launch and display directly without freezing or crashing.

---

## 🚀 Quick Start (Tutorial)

### Windows
1. Download **`KolkataPatcher.exe`** from the [Releases](https://github.com/) page.
2. Copy `KolkataPatcher.exe` into your game directory (the folder containing `Scam With Your Friends.exe`).
3. Double-click **`KolkataPatcher.exe`**.
4. That's it! Launch the game as normal.

### Linux / Steam Deck (Proton)
1. Download **`KolkataPatcher-linux`** from the [Releases](https://github.com/) page.
2. Open a terminal and run:
   ```bash
   chmod +x KolkataPatcher-linux
   ./KolkataPatcher-linux "/path/to/Scam With Your Friends"
   ```
   *(Or copy `KolkataPatcher.exe` into the game folder and run it inside Proton).*
3. In Steam Launch Options for the game:
   ```bash
   WINEDLLOVERRIDES="OnlineFix64,winmm=n,b" %command%
   ```

### Restoring Original Files
The patcher automatically creates `.bak` backups before modifying any files. To restore the originals at any time, run:
```bash
KolkataPatcher.exe --restore
```

---

## 🤖 Configuring AI (OpenRouter)

1. Get a free API key from [OpenRouter.ai](https://openrouter.ai/).
2. In the game: go to **Host Settings** -> **Host AI**.
3. Select **OpenRouter** as the backend and paste your API key.
4. Pick a model from the list (e.g. `cohere/north-mini-code:free` or `deepseek/deepseek-chat`).
5. Start the lobby and enjoy talking to AI scam victims in English, Czech, or any supported language!

---

## 📦 Building from Source

Requirements: [.NET 8.0 SDK or .NET 10.0 SDK](https://dotnet.microsoft.com/download)

```bash
# Clone the repository
git clone https://github.com/your-username/scam-kolkata-patcher.git
cd scam-kolkata-patcher/src/KolkataPatcher

# Build standalone Windows executable
dotnet publish -c Release -r win-x64 --self-contained -p:PublishSingleFile=true -o ../../release/

# Build standalone Linux binary
dotnet publish -c Release -r linux-x64 --self-contained -p:PublishSingleFile=true -o ../../release/
```

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**. See [LICENSE](LICENSE) for details.

*Disclaimer: This tool modifies game binaries in-place via Mono.Cecil for compatibility and bugfix purposes. No copyrighted game assets or binaries are distributed in this repository.*
