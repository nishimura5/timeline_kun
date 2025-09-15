import importlib


def test_cli_importable():
    import timeline_kun.cli


def test_app_timer_importable():
    mod = importlib.import_module("timeline_kun.app_timer")
    assert hasattr(mod, "App")


def test_app_previewer_importable():
    mod = importlib.import_module("timeline_kun.app_previewer")
    assert hasattr(mod, "App")
