# Actions

`App` registers a `GoProAction` as `gopro` in an `ActionManager` and binds
`(recording)` to that name through `Trigger`.

```text
Timeline → Trigger → ActionManager → GoProAction → BleThread → BleManager
BLE Connect UI ────────────────────→ GoProAction
```

- `ActionManager.register(name, action)` adds an action. Empty or duplicate names
  raise `ValueError`; looking up an unknown name raises `KeyError`.
- The `Action` protocol defines `connect()`, `start()`, `stop()`, `get_status()`,
  and `update_status()`. No inheritance is required. The first three operations
  return a boolean success result; status methods return display strings.
  `start` and `stop` refer to the action's operation, not its worker lifecycle.
- `ActionManager` delegates these operations by name. It contains no GoPro
  commands or status parsing. On non-Windows platforms, configured `window_key`
  actions resolve to an unsupported fallback, even if a runtime action was registered:
  `connect()`, `start()`, and `stop()` return `False`, and status methods return
  `WindowKey actions are supported on Windows only.` Other actions are unaffected.
- `Trigger(manager, name, keyword, offset_sec=5, delay_sec=1)` handles keyword
  entry/exit and delayed stopping. The app supplies the existing `(recording)`
  keyword and configured `stop_delay_sec` (default 2 seconds). Consecutive
  matching stages do not restart or stop recording. Start failures retain the
  previous behavior: no retry until the trigger exits and enters again.
- `GoProAction` owns device names, BLE connection, recording commands, and
  GoPro status interpretation. The BLE worker and keep-alive implementation
  are reused unchanged. The GoPro-specific UI uses the same registered instance
  for configuration, connection, and status display.

To add another action, implement the protocol and register an instance under a
new name. Bind a `Trigger` to that name and the desired keyword where needed;
no changes to `ActionManager` or `Trigger` are required. Actions that need no
connection can implement `connect()` as a successful no-op. Device-specific
configuration and UI belong alongside the concrete action. GoPro and Windows
keyboard actions are executable; generic settings are described below.

Automated regression tests use a fake BLE worker and do not require hardware.
Actual BLE connection, keep-alive, and recording should also be checked with
GoPro hardware using the existing workflow in `test_evidence_gopro.md`.

## Generic action configuration

The existing `[ble.orange]`, `[ble.cyan]`, and `[ble.lightgreen]` sections
remain unchanged. GoProAction is still configured from the BLE settings for
the selected timer color. Loading `[log]` and `[excel]` also works as before.
Moving GoPro settings into the generic action configuration is planned for a
future major version; this implementation does not migrate them.

```toml
[actions.pose_streamer]
type = "window_key"
keyword = "(pose_recording)"
start_lead_sec = 5
stop_delay_sec = 2
window_title = "timeline_kun action manager test"
start_hotkey = ["F9"]
stop_hotkey = ["F10"]
```

`[actions.<action_id>]` defines global settings independent of timer color.
You can define multiple actions with different IDs, and they may share a
keyword. IDs must be non-empty strings. Duplicate TOML tables cause an error
when the TOML file is loaded.
If `[actions]` is absent, the configuration is treated as empty, preserving
compatibility with existing setups. The example in newly generated configuration
files is fully commented out. You may enable it in your local `config.toml`
for testing.

| Field | Specification |
| --- | --- |
| `type` | Currently only `"window_key"` is supported. Types such as `command` and `http` are planned for the future. |
| `keyword` | A non-empty string matched as a case-sensitive substring of the CSV `instruction` field. |
| `start_lead_sec` | How many seconds before the active interval to start. A finite, non-negative number; fractional values are allowed. |
| `stop_delay_sec` | How many seconds to wait after the active interval ends before stopping. A finite, non-negative number; fractional values are allowed. |
| `window_title` | A non-empty string requiring an exact match. There is no `window_match` option. |
| `start_hotkey` | A non-empty array of key names to press together, such as `["CTRL", "SHIFT", "R"]`. |
| `stop_hotkey` | The same format as `start_hotkey`. The start and stop combinations may be identical. |

All fields are required. Missing fields, invalid types, unknown fields, and
unsupported action types raise a `ValueError` that includes the field path.
Parsing preserves string case and leading or trailing whitespace.

Key names are validated at runtime on Windows. Supported keys are letters,
digits, F1 through F24, CTRL/CONTROL, SHIFT, ALT, WIN, ENTER/RETURN, TAB,
ESC/ESCAPE, SPACE, BACKSPACE, DELETE, INSERT, HOME, END, PAGEUP, PAGEDOWN,
and LEFT/UP/RIGHT/DOWN. Key names are case-insensitive. Unknown or duplicate
keys are logged as failures, and no keys are sent.

The configuration loading path is:

```text
config.toml -> actions in the App configuration -> parse_action_configs
            -> ActionManager(action_configs=...)
```

Settings are converted to immutable dataclasses and can be accessed through
`manager.action_configs[action_id]`. Hotkeys are stored as tuples.
`ActionConfig` contains the shared trigger settings, while
`WindowKeyActionConfig` contains the window-specific settings. New action types
can be supported by adding configuration types and extending the parser.

The Timer registers WindowKeyAction instances with `register_configured()`
and runs them through `ActionTimeline`. Registration does not operate on
windows. After Start, keys are sent according to the CSV instructions and
configured keywords, regardless of whether BLE is configured or connected.

## Window checks in the Previewer

The Previewer's `Check Windows` button works even before a CSV file is loaded.
It checks only entries with `type = "window_key"` in the `[actions]` section
of the `config.toml` loaded at startup. It displays each action ID,
`window_title`, and Found / Not found result. It reports success if all target
windows are found, or indicates that no applicable actions are configured.
The `[ble.*]` sections are not checked.

Window lookup is supported only on Windows. On other platforms, the check
displays `WindowKey actions are supported on Windows only.` without searching
for windows or validating the configuration. Windows APIs are loaded only
after checking the platform, so WindowKeyAction settings do not prevent imports
or normal application startup on macOS or Linux.

The shared `actions.window.find_window()` function returns the handle of a
top-level window whose title matches exactly, including case and leading or
trailing whitespace. It compares titles enumerated by EnumWindows because
[FindWindowW is case-insensitive](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-findwindoww).
The check does not bring windows to the foreground, send keys, or launch
applications.

The window check is initially marked as not performed when the Previewer
starts. Clicking `Send to timer` before checking displays
`Window check has not been performed` and lets you continue or cancel.
After the check button has been used, this additional warning is no longer
shown, even if windows were missing or the check failed.
The result reflects window availability at the time of the check and does not
block the Timer from launching. After changing the configuration, restart the
Previewer and check again. The CSV `Reload` button does not reload configuration.

For manual checks, run `python tools/action_manager_test_app.py` and set
`window_title` to `timeline_kun action manager test`. Verify that the result
changes between Found and Not found as the test application opens and closes,
and that checking windows leaves the test application's state at Idle.

## Timer execution behavior

- Each action's active state is managed independently.
- An action starts when its keyword becomes present. Consecutive stages
  containing the keyword form one active interval; the action is not started
  again between those stages.
- An action starts `start_lead_sec` seconds before the interval begins.
  If starting in advance is not possible, such as when the Timer starts from
  a stage inside a matching interval, it starts immediately.
- When the keyword is no longer present, the action stops after
  `stop_delay_sec` seconds.
- Timer completion and Reset stop active actions immediately, without a delay.
- Window titles require an exact match. Missing windows and key transmission
  failures are logged. External action failures do not terminate the Timer.

The existing GoPro Trigger behavior, including completion and Reset, remains
unchanged.

If intervals overlap because of their start lead times, or an action enters
another matching interval while waiting to stop, it remains active without
sending duplicate start or stop keys. Skip affects the start lead calculation,
but stop delays use a monotonic clock. Conditions are evaluated on Timer updates,
approximately every 100 ms. A failed start is not retried within the same
interval; it is retried on entry into the next matching interval.
Reset, session completion, and closing the Timer cancel pending stop delays
and stop active actions immediately.

Before each key transmission, the action searches for an exact window title
match and restores the window if it is minimized. It calls
`SetForegroundWindow`, confirms that the target is in the foreground, and then
uses `SendInput` to press the configured keys together and release them in
reverse order. If Windows refuses foreground activation, no keys are sent.
Because of
[Windows foreground activation restrictions](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow),
start the Timer by clicking its Start button. Interacting with another application
during execution may cause later foreground activation requests to be rejected.
Sending input may also fail if the target application runs with higher privileges,
as described in the
[SendInput restrictions](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput).

Successes and failures are appended to `log/<CSV name>_actions.jsonl` under the
directory containing the CSV file. Each entry records the timestamp, action ID,
start/stop operation, success flag, and result or failure details.
Success means that input was sent successfully; the action does not query
the target application's recording state.

### Verification

1. Run `python tools/action_manager_test_app.py`.
2. In the configuration read by the Timer, set `window_title` to
   `timeline_kun action manager test`, the start key to F9, the stop key to F10,
   and `keyword` to `(pose_recording)`.
3. Add `(pose_recording)` to the `instruction` field of the target CSV stages.
4. Use Check Windows in the Previewer, then click Start in the Timer.
5. Verify that the test window shows Focused / Recording at the configured
   lead time, and Stopped after the matching interval ends and the configured
   stop delay has elapsed.
6. Verify that Reset and Timer completion or closure also produce Stopped
   while recording is active.

The Windows integration test opens a dedicated Timer and target window and
sends mouse input to the Start button. Run it without interacting with the
desktop:

```powershell
$env:TIMELINE_KUN_GUI_TEST = "1"
python -m pytest tests/test_action_runtime_windows.py -q
```
