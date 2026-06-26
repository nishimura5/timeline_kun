import inspect

import pytest


def parse_args(argv):
    # Use build_parser directly to avoid launching the GUI
    from timeline_kun import app_timer

    parser = app_timer.build_parser()
    return parser.parse_args(argv)


def test_missing_required_file_path_exits(capsys):
    with pytest.raises(SystemExit) as e:
        parse_args([])
    assert e.value.code == 2
    err = capsys.readouterr().err
    # Lightly verify that usage appears and that it mentions the required argument
    assert "usage:" in err
    assert "file_path" in err


@pytest.mark.parametrize(
    "bad_value",
    ["NaN", "one", "1.2", ""],
)
def test_start_index_non_int_exits(bad_value, capsys):
    with pytest.raises(SystemExit) as e:
        parse_args(["--file_path", "dummy.csv", "--start_index", bad_value])
    assert e.value.code == 2
    err = capsys.readouterr().err
    # argparse often outputs wording like 'invalid int value'
    # To absorb version differences, just check that the word 'start_index' is included
    assert "start_index" in err


def test_unknown_option_exits(capsys):
    with pytest.raises(SystemExit) as e:
        parse_args(["--file_path", "dummy.csv", "--unknown", "x"])
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "unrecognized arguments" in err or "unrecognized argument" in err


def test_help_shows_and_exits_zero(capsys):
    # Ensure that -h or --help shows help and exits normally
    with pytest.raises(SystemExit) as e:
        parse_args(["-h"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    # Ensure that the main options are included in the help
    assert "--file_path" in out
    assert "--fg_color" in out
    assert "--start_index" in out
    assert "--hmmss" in out


def test_valid_minimal_args_do_not_launch_gui(monkeypatch):
    """
    Include just one normal (success) case.
    Substitute the functions related to GUI launch with dummies to verify it is not launched for invalid input.
    Here we use build_parser so the GUI should not be invoked.
    Also confirm that importing does not create a Tk instance.
    """
    import importlib

    mod = importlib.import_module("timeline_kun.app_timer")

    created = {"tk": False}

    def fake_tk(*args, **kwargs):
        created["tk"] = True
        raise AssertionError("Tk should not be created during argument parsing")

    # Even if we monkeypatch tkinter.Tk, it should not be called when only parse_args is used
    monkeypatch.setitem(mod.__dict__, "tkinter", type("T", (), {"Tk": fake_tk}))

    # Verify that parse_args does not touch the GUI
    ns = parse_args(["--file_path", "dummy.csv"])
    assert hasattr(ns, "file_path")
    assert ns.file_path == "dummy.csv"
    assert created["tk"] is False


def test_app_flush_enabled_defaults_to_false():
    import importlib

    mod = importlib.import_module("timeline_kun.app_timer")
    signature = inspect.signature(mod.App.__init__)

    assert signature.parameters["flush_enabled"].default is False


def test_app_flush_dimensions_default_to_36():
    import importlib

    mod = importlib.import_module("timeline_kun.app_timer")
    signature = inspect.signature(mod.App.__init__)

    assert signature.parameters["flush_width"].default == 36
    assert signature.parameters["flush_height"].default == 36


def test_stage_flash_is_noop_when_flush_disabled():
    import importlib

    mod = importlib.import_module("timeline_kun.app_timer")
    app = mod.App.__new__(mod.App)
    app.flush_enabled = False
    app._stage_flash_after_id = None

    app.start_stage_flash()

    assert app._stage_flash_after_id is None


def test_config_flush_defaults_to_false():
    import importlib

    mod = importlib.import_module("timeline_kun.app_timer")

    assert mod._get_flush_enabled({}) is False


@pytest.mark.parametrize("value", [True, False])
def test_config_flush_accepts_bool(value):
    import importlib

    mod = importlib.import_module("timeline_kun.app_timer")

    assert mod._get_flush_enabled({"flush": value}) is value


@pytest.mark.parametrize("value", ["true", 1, None])
def test_config_flush_rejects_non_bool(value):
    import importlib

    mod = importlib.import_module("timeline_kun.app_timer")

    with pytest.raises(ValueError, match="flush"):
        mod._get_flush_enabled({"flush": value})


@pytest.mark.parametrize("key", ["flush_width", "flush_height"])
def test_config_flush_dimension_defaults_to_36(key):
    import importlib

    mod = importlib.import_module("timeline_kun.app_timer")

    assert mod._get_flush_dimension({}, key) == 36


@pytest.mark.parametrize("key", ["flush_width", "flush_height"])
def test_config_flush_dimension_accepts_positive_int(key):
    import importlib

    mod = importlib.import_module("timeline_kun.app_timer")

    assert mod._get_flush_dimension({key: 72}, key) == 72


@pytest.mark.parametrize("value", [0, -1, 1.5, "36", True])
@pytest.mark.parametrize("key", ["flush_width", "flush_height"])
def test_config_flush_dimension_rejects_invalid_values(key, value):
    import importlib

    mod = importlib.import_module("timeline_kun.app_timer")

    with pytest.raises(ValueError, match=key):
        mod._get_flush_dimension({key: value}, key)


def test_member_text_keeps_previous_value_when_stage_member_is_empty():
    import importlib

    mod = importlib.import_module("timeline_kun.app_timer")
    app = mod.App.__new__(mod.App)
    app._last_member_text = ""

    assert app._member_text_for_stage({"member": "Alice"}) == "Alice"
    assert app._member_text_for_stage({"member": ""}) == "Alice"
    assert app._member_text_for_stage({"member": "Bob"}) == "Bob"


def test_flash_background_updates_only_flush_rectangle():
    import importlib

    class FakeFlushRectangle:
        def __init__(self):
            self.background = None

        def configure(self, **kwargs):
            self.background = kwargs["background"]

    mod = importlib.import_module("timeline_kun.app_timer")
    app = mod.App.__new__(mod.App)
    app.flush_rectangle = FakeFlushRectangle()

    app._set_flush_rectangle_color("white")

    assert app.flush_rectangle.background == "white"
