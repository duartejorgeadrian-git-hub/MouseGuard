@echo off
echo Instalando PyInstaller...
pip install pyinstaller

echo Compilando MouseGuard.exe...
pyinstaller --noconsole --onefile mouse_guard.py

echo Proceso terminado. Encontraras el ejecutable en la carpeta "dist".
pause
