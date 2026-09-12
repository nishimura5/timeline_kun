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
  commands, status parsing, or action-type branches.
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
configuration and UI belong alongside the concrete action. Only GoPro is
implemented in this change; multi-action UI/configuration is not added.

Automated regression tests use a fake BLE worker and do not require hardware.
Actual BLE connection, keep-alive, and recording should also be checked with
GoPro hardware using the existing workflow in `test_evidence_gopro.md`.
