# Kolkata OS Patcher & AI Gateway for Scam With Your Friends

A standalone binary patcher and local multi-provider AI Gateway for *Scam With Your Friends* (Unity 6 Mono).

This project resolves Unity 6 engine crashes, bypasses the remote authentication loop, fixes the missing desktop/taskbar bug, and provides a local AI gateway proxy supporting key rotation and multi-provider failover (Groq, DeepSeek, OpenRouter).

---

## Quick Start Guide

### 1. Patch the Game (All Players)
Both the host and joining clients must patch their game files once to resolve engine and UI crashes.

#### Windows
1. Download `KolkataPatcher.exe` from the [Releases](https://github.com/altuux/swyf-patcher/releases) page.
2. Place `KolkataPatcher.exe` into your game directory (the folder containing `Scam With Your Friends.exe`).
3. Run `KolkataPatcher.exe`. You will see a success message once patches are applied.

#### Linux / Steam Deck (Proton)
1. Download `KolkataPatcher-linux` from [Releases](https://github.com/altuux/swyf-patcher/releases).
2. Run the patcher in terminal:
   ```bash
   chmod +x KolkataPatcher-linux
   ./KolkataPatcher-linux "/path/to/Scam With Your Friends"
   ```
3. Set your Steam Launch Options:
   ```bash
   WINEDLLOVERRIDES="OnlineFix64,winmm=n,b" %command%
   ```

---

### 2. AI Setup (Host Only)
*Scam With Your Friends* requires an LLM backend to drive caller interactions. In peer-to-peer multiplayer, **only the lobby host** handles AI generation calls.

The included AI Gateway runs locally on port 8888 and routes game calls to external providers with automatic key rotation and fallback cascade.

1. Run the interactive CLI:
   ```bash
   python tools/cli.py
   ```
   *(Or launch `SWYF-Gateway.exe` on Windows / `./SWYF-Gateway-linux` on Linux from Releases)*
2. In the menu, choose `[2] Manage API Keys`.
3. Add at least one API key from your preferred provider:
   - **Groq** (*Recommended, 100% Free & Fastest*): [console.groq.com/keys](https://console.groq.com/keys)
   - **DeepSeek**: [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)
   - **OpenRouter**: [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)
4. (Optional) Run `[3] Test All Active Keys` to verify connection.
5. Select `[1] Launch AI Gateway`. Keep this window open in the background while hosting.
6. Start the game and host your lobby. In-game AI calls are routed through the local gateway automatically.

---

## Technical Details

### Engine & UI Patches (Mono.Cecil)
1. **`PlayerPrefs` Method Injection (`UnityEngine.CoreModule.dll`)**
   - Unity 6 code stripping stripped `PlayerPrefs` helper methods (`SetInt`, `SetFloat`, `DeleteKey`, `Save`, `DeleteAll`).
   - Injects clean method stubs so `KolkataOsSingleton.Start()` and `KolkataOsController` initialize properly without throwing `MissingMethodException`.

2. **Kolkata OS Remote Auth Bypass**
   - Intercepts `EnsureEdgeSessionAsync` and `EdgePostAsync` in `KolkataApi`.
   - Marks sessions locally as `SignedIn` with `Unlimited` and `Deluxe` entitlement flags, eliminating the 401 loop against `kolkata-auth.jataterworldwide.com`.

3. **Desktop & Taskbar Failure Fix**
   - `KolkataOsCallerQueueApp` threw an unhandled `NullReferenceException` when registering the workshop UI button (`workshop-page`).
   - Because desktop loading halted upon exception, players saw an empty desktop without taskbar or applications. The patch makes UI button registration null-safe.

4. **In-Game CEF Browser Bypass**
   - NOPs the privacy confirmation modal requirement in `KolkataOsController.RequestBrowserPrivacyWarning` and `KolkataOsBrowserHost.EnsureBrowserClient`, enabling the internal browser to load directly.

5. **Local AI Gateway Endpoint Redirection**
   - Rewrites the target URL in `KolkataApi.CompleteOpenRouterAsync` from the public OpenRouter API to `http://127.0.0.1:8888/v1/chat/completions`.
   - Forces `HostAiSettings.OpenRouterSelected` and `UseDirectOpenRouter` in `ScriptsAssDef.dll` to `true`, routing all gameplay through the local gateway regardless of in-game host settings.
   - Stubs `KolkataApi.ResolveEdgePromptAsync` and `EdgeBase` to prevent unauthenticated 401 calls to remote cloud servers.
   - NOPs client-side exceptions for missing in-game keys or model definitions.

6. **Piracy Alarm Silencing**
   - Disables the repeating siren alarm triggered by unauthenticated game states.

---

## AI Gateway & Key Rotation Architecture

The gateway acts as an OpenAI-compatible reverse proxy running on `127.0.0.1:8888`:

- **Automatic Cascade & Fallback:**
  Requests flow sequentially:
  $$\text{Groq (Llama 3.3 70B)} \longrightarrow \text{DeepSeek (Chat)} \longrightarrow \text{OpenRouter (DeepSeek V4 Flash)}$$
  If a provider experiences rate limiting, downtime, or key exhaustion, the request immediately falls back to the next provider in the chain.

- **Round-Robin Key Pool:**
  Add multiple keys per provider. Calls alternate across keys to distribute quota and bypass rate limits.

- **Payload Sanitization:**
  Strips game-specific custom metadata headers (`lobby_session_id`, `gameplay_route`, etc.) that cause external APIs to reject payloads.

- **Reasoning Model Compatibility:**
  Normalizes responses from reasoning models that output replies inside `reasoning` / `reasoning_details` instead of standard `content`.

---

## Restoring Original Game Files

Backups (`.bak`) of modified DLLs are created automatically before any changes are written.

To restore untouched original files:
```bash
KolkataPatcher.exe --restore
```
Or on Linux:
```bash
./KolkataPatcher-linux "/path/to/Scam With Your Friends" --restore
```

---

## Compiling from Source

### KolkataPatcher (.NET 8/10 SDK)
```bash
git clone https://github.com/altuux/swyf-patcher.git
cd swyf-patcher/src/KolkataPatcher

# Windows x64 binary:
dotnet publish -c Release -r win-x64 --self-contained -p:PublishSingleFile=true -o ../../release/

# Linux x64 binary:
dotnet publish -c Release -r linux-x64 --self-contained -p:PublishSingleFile=true -o ../../release/
```

### AI Gateway Standalone Binary (Nuitka)
To build a standalone executable of the AI Gateway on Windows:
```bash
python -m pip install nuitka
python -m nuitka --onefile --standalone --output-filename=SWYF-Gateway.exe tools/cli.py
```

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**. See [LICENSE](LICENSE) for details.

*Disclaimer: This tool modifies local assemblies in-place via Mono.Cecil for interoperability and debugging purposes. No proprietary game assets or game binaries are hosted or distributed in this repository.*
