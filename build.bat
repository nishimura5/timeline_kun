uv run pyinstaller --onedir --onefile --windowed --clean -n TimelineKun --icon=./src/img/icon.ico --version-file=app.version ./src/app_previewer.py
uv run pyinstaller --onedir --onefile --windowed --clean  --version-file=app.version ./src/app_timer.py

xcopy /s /e /i .\src\sound .\dist\sound