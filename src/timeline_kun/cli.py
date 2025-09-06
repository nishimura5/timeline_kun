def main() -> None:
    import importlib

    mod = importlib.import_module("timeline_kun.app_previewer")
    if hasattr(mod, "main"):
        mod.main()
