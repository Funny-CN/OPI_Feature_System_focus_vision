@echo off
REM 启动旧版 PyQt6 Widgets UI
echo [VisionFlow] 启动旧版界面 (PyQt6)...
call conda activate opi_vision
python main_gui_pyqt6.py
if errorlevel 1 (
    echo [VisionFlow] 启动失败，请检查 Conda 环境
    pause
)
