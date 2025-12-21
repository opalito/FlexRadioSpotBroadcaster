@echo off
echo ============================================================
echo   FlexRadio Spot Broadcaster - Creador de Ejecutable
echo ============================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo Descarga Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Instalando dependencias...
pip install PyQt5 pyinstaller --quiet

echo.
echo [2/3] Creando ejecutable...
pyinstaller --onefile --windowed --name "FlexRadioSpotBroadcaster" ^
    --icon=dxspot.ico ^
    dxspot_forwarder_gui.py

echo.
echo [3/3] Limpiando archivos temporales...
rmdir /s /q build 2>nul
del /q *.spec 2>nul

echo.
echo ============================================================
echo   COMPLETADO!
echo   El ejecutable esta en: dist\FlexRadioSpotBroadcaster.exe
echo ============================================================
echo.

pause
