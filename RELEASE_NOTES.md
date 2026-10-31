# Release v2.0.2

## What's Changed in v2.0.2 (Hotfix)

### Fixes & Engine Improvements

- **Workstation Webcam & Camera App Restored (`DelayedEnableImmediateDisable`)**:
  - Fixed a `TypeLoadException` and Unity scene deserialization failure (`Read 32 bytes but expected 60 bytes`) caused by `DelayedEnableImmediateDisable` in `Assembly-CSharp.dll` missing the `IImmediateCameraTargetDisabler.get_TargetCamera` interface property required by `ScriptsAssDef.dll`.
  - Restores the `Webcam Camera` transition when sitting at a workstation so the Kolkata OS **Camera** and **Zoomy** apps display the live selfie feed instead of being stuck staring at the 3D monitor's idle logo wallpaper.
- **Documentation Cleanup**:
  - Removed emojis across project documentation and release notes.

---

## Previous Changes in v2.0.1

- **Persistent `PlayerPrefs` Engine Restoration (`SWYF.Prefs.dll`)**:
  - **Scamazon Purchases Fixed**: Permanent apps and items bought in Scamazon properly unlock and persist on the Kolkata OS desktop across game sessions.
  - **Notification Toast Spam Resolved**: Fixed the recurring bottom-right notification toast ("You now have enough money for {0} in Scamazon") spamming every 4 seconds.
  - **Crash-Proof Storage**: Player preferences are persisted to `swyf_playerprefs.dat` (targeting Unity's stripped `.NET 4.x` `mscorlib.dll` `4.0.0.0`) with automatic Windows Registry migration, compatible with Windows, Steam Deck, Wine, and Proton.

---

## Assets

- `SWYF-Complete-Package-v2.0.2.zip`: All-in-one package for Windows (`KolkataPatcher.exe` + `SWYF-Gateway.exe` + `README.md`).
- `SWYF-Complete-Package-Linux-v2.0.2.tar.gz` / `.zip`: All-in-one package for Linux / Steam Deck (`KolkataPatcher-linux` + `SWYF-Gateway-linux` + `README.md`).
- Standalone binaries: `KolkataPatcher.exe`, `KolkataPatcher-linux`, `SWYF-Gateway.exe`, `SWYF-Gateway-linux`.
