# Release v2.0.3

## What's Changed in v2.0.3 (Critical Fresh-Install Hotfix)

### Fixes

- **Fixed Gateway Never Receiving Calls on Fresh Installs (`HostAiSettings.SelectedModel`)**:
  - On clean installations where a player never manually selected an OpenRouter model inside the in-game Host Settings menu (`MetaSave/local.json`), `HostAiSettings.SelectedModel` returned `null`.
  - After bypassing the `"Choose an OpenRouter model in Host Settings."` check in `CompleteOpenRouterAsync`, `PrepareDirectOpenRouterBody` immediately dereferenced `model.Id` on `null`, throwing a `NullReferenceException` inside Unity before any HTTP request could be sent to `http://127.0.0.1:8888/v1/chat/completions`.
  - `KolkataPatcher` now patches `HostAiSettings.SelectedModel`, `ApiKey`, `HasSavedKey`, and `HasInvalidKey` in `ScriptsAssDef.dll` with a valid built-in gateway `OpenRouterModel` profile so calls reach `SWYF-Gateway` out-of-the-box with zero in-game menu configuration.

---

## Previous Changes in v2.0.2

- **Workstation Webcam & Camera App Restored (`DelayedEnableImmediateDisable`)**:
  - Restored missing `IImmediateCameraTargetDisabler.get_TargetCamera` property on `DelayedEnableImmediateDisable` in `Assembly-CSharp.dll` so the Kolkata OS **Camera** and **Zoomy** apps display the live character webcam feed instead of staying stuck on the 3D monitor logo.
- **Groq API Gateway & Tester Fixes (`tools/`)**:
  - Resolved Cloudflare Error 1010 (`HTTP 403`), updated Groq model pool to `qwen/qwen3.8-27b` with automatic fallbacks, stripped OpenRouter-only payload fields when forwarding to Groq/DeepSeek, and fixed `swyf_config.json` persistence next to standalone Nuitka `--onefile` binaries.

---

## Assets

- `SWYF-Complete-Package-v2.0.3.zip`: All-in-one package for Windows (`KolkataPatcher.exe` + `SWYF-Gateway.exe` + `README.md`).
- `SWYF-Complete-Package-Linux-v2.0.3.tar.gz` / `.zip`: All-in-one package for Linux / Steam Deck (`KolkataPatcher-linux` + `SWYF-Gateway-linux` + `README.md`).
- Standalone binaries: `KolkataPatcher.exe`, `KolkataPatcher-linux`, `SWYF-Gateway.exe`, `SWYF-Gateway-linux`.
