# Release v1.0.0

## Description

KolkataPatcher is a standalone binary patcher for Scam With Your Friends. It fixes multiple engine-level issues present in the Unity 6 Mono build that prevent the game and Kolkata OS from running properly in offline or non-Steam environments.

## Fixes

1. PlayerPrefs MissingMethodException
   - Unity 6 managed stripping removed PlayerPrefs.SetInt, SetFloat, DeleteKey, Save, and DeleteAll from UnityEngine.CoreModule.dll.
   - Restores clean method stubs to prevent runtime crashes during Kolkata OS startup.

2. UnityWebRequest Missing Method
   - Restores missing UnityWebRequest.Get(Uri) overload in UnityEngine.UnityWebRequestModule.dll.

3. Kolkata OS Authentication Bypass
   - Bypasses remote HTTP checks to kolkata-auth.jataterworldwide.com in EnsureEdgeSessionAsync and EdgePostAsync.
   - Sets the local session state to SignedIn with the Unlimited role and Deluxe entitlements.

4. Taskbar, Desktop and Caller Queue UI Crash
   - Fixes a NullReferenceException in KolkataOsCallerQueueApp.BuildContent caused by attempting to bind a non-existent workshop-page button.
   - Allows BuildDesktop() to complete fully, restoring desktop icons, the taskbar, and the system tray.

5. Piracy Alarm Suppression
   - Disables the in-game siren alarm triggered by rejected auth states.

## Instructions

### Windows
1. Download KolkataPatcher.exe from this release.
2. Place KolkataPatcher.exe into the game root directory (where Scam With Your Friends.exe is located).
3. Run KolkataPatcher.exe.
4. Launch the game normally.

### Linux / Steam Deck
1. Download KolkataPatcher-linux.
2. Run:
   ```bash
   chmod +x KolkataPatcher-linux
   ./KolkataPatcher-linux "/path/to/Scam With Your Friends"
   ```
3. In Steam launch options:
   ```bash
   WINEDLLOVERRIDES="OnlineFix64,winmm=n,b" %command%
   ```

### Restoring Original Files
Backups (.bak) are automatically created before modifying files. To restore the originals:
```bash
KolkataPatcher.exe --restore
```
