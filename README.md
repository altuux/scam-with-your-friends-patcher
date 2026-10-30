# Kolkata OS Patcher & Auth Bypass for Scam With Your Friends

A standalone binary patcher for Scam With Your Friends (Unity 6 Mono).

This tool resolves engine crashes, bypasses the remote authentication loop, and restores desktop and taskbar functionality in offline, LAN, and custom environments.

---

## Technical Details

1. `MissingMethodException: PlayerPrefs.SetInt`
   - Unity 6 managed code stripping removed PlayerPrefs methods (`SetInt`, `SetFloat`, `DeleteKey`, `Save`, `DeleteAll`) from `UnityEngine.CoreModule.dll`.
   - Injects clean method stubs so `KolkataOsSingleton.Start()` and `KolkataOsController` initialize properly.

2. Authentication Loop (`STEAM_REJECTED` / HTTP 401)
   - In offline or local setups, the game attempts to authenticate continuously against `kolkata-auth.jataterworldwide.com`.
   - Modifies `EnsureEdgeSessionAsync` and `EdgePostAsync` to mark the session as locally authenticated with the Unlimited membership role.

3. Taskbar, Desktop & Caller Queue UI Failure
   - `KolkataOsCallerQueueApp` raises a `NullReferenceException` when attempting to register the workshop button (`workshop-page`) if absent from the template.
   - The unhandled exception aborts `BuildDesktop()`. The patch makes this registration null-safe, enabling the complete desktop UI to load.

4. `UnityWebRequest.Get(Uri)` Overload
   - Restores the missing URI overload in `UnityEngine.UnityWebRequestModule.dll`.

5. Piracy Alarm Handling
   - Disables the repeating siren alarm routine triggered by unauthenticated states.

6. In-Game Browser Initialization
   - Bypasses the modal privacy prompt in `KolkataOsController` and internal approval gate in `KolkataOsBrowserHost`, allowing the CEF/UWB browser instance to initialize directly.

---

## Installation & Usage

### Windows

1. Download `KolkataPatcher.exe` from the Releases page.
2. Place `KolkataPatcher.exe` in the game directory containing `Scam With Your Friends.exe`.
3. Run `KolkataPatcher.exe`.
4. Start the game.

### Linux / Steam Deck (Proton)

1. Download `KolkataPatcher-linux` from the Releases page.
2. In a terminal:
   ```bash
   chmod +x KolkataPatcher-linux
   ./KolkataPatcher-linux "/path/to/Scam With Your Friends"
   ```
3. In Steam Launch Options for the game:
   ```bash
   WINEDLLOVERRIDES="OnlineFix64,winmm=n,b" %command%
   ```

### Restoring Original Assemblies

Backups (`.bak`) are created automatically prior to modifying files. To revert:
```bash
KolkataPatcher.exe --restore
```

---

## AI Configuration (OpenRouter)

1. Obtain an API key from [OpenRouter.ai](https://openrouter.ai/).
2. In the game, navigate to **Host Settings** -> **Host AI**.
3. Select **OpenRouter** and enter your API key.
4. Select a supported model (such as `deepseek/deepseek-v4-flash`).
5. A helper script is provided in `tools/check_ai_config.py` to inspect and validate your local configuration and connectivity.

---

## Compiling from Source

Prerequisites: [.NET 8.0 SDK or .NET 10.0 SDK](https://dotnet.microsoft.com/download)

```bash
git clone https://github.com/altuux/swyf-patcher.git
cd swyf-patcher/src/KolkataPatcher

# Windows x64 binary
dotnet publish -c Release -r win-x64 --self-contained -p:PublishSingleFile=true -o ../../release/

# Linux x64 binary
dotnet publish -c Release -r linux-x64 --self-contained -p:PublishSingleFile=true -o ../../release/
```

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**. See [LICENSE](LICENSE) for details.

*Disclaimer: This tool modifies local assemblies in-place via Mono.Cecil for interoperability and debugging purposes. No proprietary game assets or game binaries are hosted or distributed in this repository.*
