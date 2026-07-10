@echo off
echo Limpiando compilaciones anteriores...
rmdir /s /q build
rmdir /s /q dist
del /q *.spec

echo Compilando MouseGuard v2.0...
python -m PyInstaller --noconsole --onefile --icon="icon.ico" --add-data "purge_siren.mp3;." --add-data "icon.ico;." mouse_guard.py

echo.
echo Compilacion terminada. Revisa la carpeta 'dist'.
pause
