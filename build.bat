uv pip install -e .
uv run pyinstaller --onefile --windowed --clean --path src --collect-all timeline_kun -n TimelineKun --icon=./src/timeline_kun/img/icon.ico --version-file=app.version --exclude sounddevice --exclude sound --exclude file --exclude numpy ./scripts/launch_previewer.py
uv run pyinstaller --onefile --windowed --clean --path src --collect-all timeline_kun -n TimelineKunTimer --version-file=app.version ./scripts/launch_timer.py

xcopy /s /e /i .\src\timeline_kun\sound .\dist\sound