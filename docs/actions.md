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
configuration and UI belong alongside the concrete action. Only GoPro is
implemented as an executable action; generic settings are described below.

Automated regression tests use a fake BLE worker and do not require hardware.
Actual BLE connection, keep-alive, and recording should also be checked with
GoPro hardware using the existing workflow in `test_evidence_gopro.md`.

## 汎用Action設定

既存の `[ble.orange]`、`[ble.cyan]`、`[ble.lightgreen]` は変更しません。
選択したtimer colorのBLE設定から、従来通りGoProActionを構成します。
`[log]`、`[excel]` の読み込みも従来通りです。GoProの汎用設定への統合は
将来のメジャーバージョンで行う予定で、今回は移行しません。

```toml
[actions.pose_streamer]
type = "window_key"
keyword = "(pose_recording)"
start_lead_sec = 5
stop_delay_sec = 2
window_title = "カメラ位置確認"
start_hotkey = ["F9"]
stop_hotkey = ["F10"]
```

`[actions.<action_id>]` は色に依存しないグローバル設定です。
異なるIDで複数定義でき、同じkeywordを共有できます。IDは空でない文字列で、
重複したTOMLテーブルはTOML読み込み時にエラーになります。
`[actions]` がなければ空の設定として扱い、従来の環境で動作します。
配布用configと新規生成configの例は全行コメントアウトしてあります。

| 項目 | 仕様 |
| --- | --- |
| `type` | 現在の設定型は `"window_key"` のみ。将来 `command`、`http` などを追加予定 |
| `keyword` | 空でない文字列。CSVの `instruction` に対するcase-sensitiveな部分文字列一致 |
| `start_lead_sec` | 開始の何秒前にstartするか。0以上の有限数（小数可） |
| `stop_delay_sec` | active区間終了からstopまでの秒数。0以上の有限数（小数可） |
| `window_title` | 空でない文字列。常に完全一致。`window_match` は設けない |
| `start_hotkey` | 空でない文字列配列。配列内のキーは同時押し（例：`["CTRL", "SHIFT", "R"]`） |
| `stop_hotkey` | 同上。startと同じキーも指定可能 |

全項目を必須とし、未指定・型不正・未知の項目・未対応typeは項目のパス付きの
`ValueError` にします。文字列の大文字小文字や前後の空白は変換しません。
キー名のOS別サポート検証は、今後の送信実装で扱います。

読み込み経路は `config.toml → App用設定のactions → parse_action_configs →
ActionManager(action_configs=...)` です。設定は不変のdataclassに変換され、
`manager.action_configs[action_id]` から参照できます。ホットキーはtupleとして
保持します。ActionConfigに共通のトリガー設定を置き、WindowKeyActionConfigに
Window固有の設定を置いています。新しいtypeは設定型とパーサーを追加して拡張します。

**今回、汎用設定から実行Actionの生成・登録やTriggerの作成は行いません。**
設定を有効にしただけではWindow検索やキー送信は発生しません。
設定の保持と、`register()` による実行Actionの登録は別です。

## PreviewerのWindow存在確認

Previewerの `Check Windows` はCSV未ロードでも実行できます。起動時に読み込んだ
`config.toml` の `[actions]` のうち `type = "window_key"` だけを確認し、
Action ID、`window_title`、Found / Not foundを表示します。全件見つかった場合は
成功を表示し、対象Actionがなければその旨を通知します。`[ble.*]` は対象外です。

検索はWindows専用です。非Windowsでは探索や設定検証を行わず、
`WindowKey actions are supported on Windows only.` と表示します。
Windows APIの読み込みはplatform判定後に行います。WindowKeyAction設定があっても
macOS/Linuxでのimportや通常機能の起動を妨げません。
共用関数 `actions.window.find_window()` は、タイトルが完全一致するトップレベル
Windowのハンドルを返します。大文字小文字や前後の空白も区別します。
[FindWindowWは大文字小文字を区別しない](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-findwindoww)
ため、EnumWindowsで列挙したタイトルを比較しています。
foreground化、キー送信、アプリ起動は行いません。

Previewer起動時は未確認です。未確認のまま `Send to timer` を押すと
`Window check has not been performed` と表示し、続行かキャンセルを選択できます。
確認ボタンを実行した後は、未検出や確認エラーがあってもこの追加警告を表示しません。
存在確認は実行時点の結果であり、Timer起動を禁止するものではありません。
設定変更後はPreviewerを再起動して再確認してください。CSVの `Reload` は
設定の再読み込みではありません。

手動確認には `python tools/action_manager_test_app.py` を使い、設定の
`window_title` を `timeline_kun action manager test` にします。
アプリの起動・終了に応じてFound / Not foundが変わり、確認操作によって
テストアプリの状態がIdleから変わらないことを確認できます。

## 今後の実行実装で満たす仕様（今回未実装）

- Actionごとにactive状態を独立して管理する。
- keywordなしからありへの遷移でstartし、連続するkeyword付きStage群は1つの
  active区間として扱う。途中でstartを繰り返さない。
- 区間開始の `start_lead_sec` 秒前にstartする。途中StageからのTimer開始などで
  先行実行できない場合は即時実行する。
- keywordありからなしへの遷移で、`stop_delay_sec` 秒後にstopする。
- Timer終了・Reset時はactiveなActionを遅延なしで即時stopする。
- Windowタイトルは完全一致で検索する。Window未検出やキー送信失敗を記録し、
  外部Actionの失敗によってTimer本体を終了させない。

今回の設定追加では既存GoPro Triggerの終了・Reset時を含む挙動は変更しません。
