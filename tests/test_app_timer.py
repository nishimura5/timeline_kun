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
