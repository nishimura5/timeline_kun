# Test evidence: GoPro automatic recording control (Timeline-kun)

This deposit provides test evidence (timeline CSV, config, and full-session videos) demonstrating practical GoPro control by Timeline-kun, including automatic reconnection after an unexpected power loss (standby state) and long-run operation with up to two cameras.

## Contents

### In this repository
- `tests/fixtures/valid__recording__example_1.csv`
- `tests/fixtures/valid__recording__example_3hour.csv`

### Archived on Zenodo (DOI): `[DOI here]`
- `recording__example_1.mp4` (full test video)
- `recording__example_3hour.mp4` (full test video)

## Software version
- Timeline-kun version: v1.0.1
- Release URL: https://github.com/nishimura5/timeline_kun/releases/tag/v1.0.1
- Repository URL: https://github.com/nishimura5/timeline_kun

---

## Test 1: Recovery from unexpected power loss (during TASK D, not recording)

### Goal
Verify that Timeline-kun automatically recovers BLE connectivity after the camera loses power while not recording, and that scheduled recording control continues without requiring any user operation within Timeline-kun.

### Environment
- OS: Windows 11  
- Camera: GoPro HERO12  
- Power: battery removed, USB power only  
- Timeline CSV: `tests/fixtures/valid__recording__example_1.csv`  
- Config: `config.toml`

### Procedure
1. Start Timeline-kun and begin the timer/schedule.
2. Confirm the GoPro connection indicator shows **Connected**.
3. During **TASK D** (while the camera is not recording), unplug the USB cable to cut power (forced shutdown).
4. Observe the connection indicator transition to **Disconnected**.
5. Reconnect the USB cable to restore power and wait for the camera to boot.
6. Observe the connection indicator transition back to **Connected**.
7. Confirm that the next scheduled task (**TASK E**) successfully starts recording.

### Success criteria
- Connected → Disconnected is detected after power loss.
- Disconnected → Connected is recovered automatically after power restoration (no Timeline-kun operation required).
- A subsequent scheduled recording start (TASK E) succeeds after reconnection.

### Observed results (from video)
Video: `recording__example_1.mp4`

- USB cable unplugged during TASK D (camera not recording), causing forced power loss.
- Approximately 8 seconds after power loss: **Connected → Disconnected**.
- After USB power restoration: approximately 15 seconds later (including GoPro boot time), **Disconnected → Connected**.
- The next scheduled task (**TASK E**) successfully initiates recording.

### Notes
- Reconnection is automatic; Timeline-kun does not require any user operation.
- The timer/schedule continues running even if the camera remains unavailable, enabling fallback workflows (e.g., manual recording with an alternative camera).

---

## Test 2: Long-run operation with two cameras (3 hours)

### Goal
Verify practical performance of scheduled start/stop control over a 3-hour continuous run with two GoPro cameras.

### Environment
- OS: Raspberry Pi Desktop  
- Cameras: GoPro HERO11 (Camera 1) and GoPro HERO12 (Camera 2)  
- Timeline CSV: `tests/fixtures/valid__recording__example_3hour.csv`  
- Config: `config.toml`

### Schedule summary
- 5-minute recordings × 12 sets  
- 1-hour recording × 1 set

### Observed results (from video)
Video: `recording__example_3hour.mp4`

**Recording start**
- Target behavior: start recording 4 seconds before each event start.
- Observed behavior (all 12 sets + the long 1 set):
  - Camera 1 (HERO11) starts recording about 4 seconds before each event start.
  - Camera 2 (HERO12) starts recording about 3 seconds before each event start.
- The consistent offset between the two cameras is likely due to commands being issued sequentially. In all cases, recording begins before the event start.

**Recording stop**
- Target behavior: stop recording 2 seconds after each event end.
- Observed behavior (all 12 sets + the long 1 set):
  - Both cameras stop recording about 2 seconds after each event end.

### Success criteria
Across the full 3-hour continuous run (all 12 sets + the long 1 set), both cameras:
- start recording before each event start, and
- stop recording about 2 seconds after each event end.

