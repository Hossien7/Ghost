# OPERATION ECLIPSE — Squadron Multiplayer Update

A local-network military sci-fi space shooter for Windows PCs and mobile browsers. The Windows PC hosts the authoritative game server; phones and other PCs join over the same Wi-Fi/LAN. Internet access is not required during play after dependencies are installed.

## What's new

### Multiplayer rooms
- **Solo:** 1 pilot.
- **Duo:** exactly 2 pilot slots.
- **Squadron:** up to 8 simultaneous pilots in one shared battlefield.
- Each browser connection receives its own server-generated pilot ID. Scanning the QR code from another phone creates another player; it does not replace an existing player.
- The first connected pilot is the room commander and controls game mode, campaign start, mission deployment, retry and chapter progression. If the commander disconnects, leadership is transferred to the next connected pilot.
- A unique six-character Room ID is displayed in the lobby.
- QR code and room are hosted locally. No cloud service or external matchmaking is used.

### Starfighter selection
- **Vanguard:** balanced handling and triple-shot support.
- **Phantom:** faster movement, slightly lower weapon damage.
- **Titan:** slower movement, higher weapon damage.
- **Medic:** support-oriented fighter with balanced movement and triple-shot support.

Each player can set a callsign and select a ship before deployment. Ship choice affects movement and damage on the authoritative server.

### Combat and HUD
- Every player is simulated by the server and shares enemies, boss fights, projectiles, score and campaign progress.
- Enemy fire patterns now include aimed shots, bomber spread, gunship/elite triple volleys, phantom bursts and boss-specific patterns.
- Boss health scales upward with squadron size.
- Live individual player health bars, weapon levels, shields and player names are shown in the HUD.
- Existing enemy classes, random supply drops, comic campaign, three bosses, mobile touch controls and procedural offline audio are retained.
- Player ships have differentiated Vanguard, Phantom, Titan and Medic silhouettes with layered gradients, engine glow and shield effects (stylized 2.5D canvas rendering, not a real-time 3D engine).

## Windows 10/11 setup
1. Install Python 3.10 or newer.
2. Extract this ZIP.
3. Run `install.bat` once. Internet is needed only if Python packages are not already installed.
4. Run `run_game.bat` on the Windows host PC.
5. The host browser opens automatically. Select Solo, Duo or Squadron, enter a callsign, and choose a starfighter.
6. Keep the host PC and phones on the same Wi-Fi/LAN. Scan the QR code from each additional device.
7. Allow Python through Windows Defender Firewall on **Private networks**.
8. When the roster is ready, the room commander clicks **BEGIN OPERATION**.

## Controls
- Keyboard on PC: WASD or arrow keys to move; Space/J to fire; K for pulse.
- Touch on phones: virtual joystick, FIRE and PULSE buttons.
- Any connected browser can control its own pilot. The room commander controls campaign progression.
- Audio: tap/click AUDIO once to enable music and sound effects (browser autoplay policy).

## Network notes
- Host server listens on `0.0.0.0:8000`.
- QR code points to the host's LAN address and `/?join=1` (the query marker simply opens the join experience).
- All game state is authoritative on the host PC and broadcast to connected browsers over WebSocket.
- Guest Wi-Fi/client isolation must be disabled for devices to communicate.

## EXE build
Run `build_exe.bat` on Windows to create `dist\OperationEclipse.exe`. This source ZIP contains the build script, not a precompiled EXE. Build and test the EXE on the target Windows PC.

## Verification
- Python syntax compilation: passed.
- JavaScript syntax check: passed.
- Local HTTP lobby and QR PNG response: passed.
- WebSocket smoke test with three simultaneous pilots in Squadron mode: passed.
- Full physical Windows + multiple-phone LAN playtest, browser touch feel, audio behavior and balance still require testing on the target network/devices.
