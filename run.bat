@echo off
REM 启动新版 QML UI (PySide6)
echo [VisionFlow] 启动新版界面 (PySide6 + QML)...
call conda activate opi_vision
python main_gui.py
if errorlevel 1 (
    echo [VisionFlow] 启动失败，请检查 Conda 环境
    pause
)
