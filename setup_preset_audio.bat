@echo off
chcp 65001 >nul
echo ========================================
echo LiveTalking 预设音频快速配置工具
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [1/4] 检查依赖...
python -c "import edge_tts" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装 edge-tts...
    pip install edge-tts
)

echo.
echo [2/4] 生成预设音频...
echo 这可能需要几分钟，请耐心等待...
python generate_preset_audio.py
if errorlevel 1 (
    echo [错误] 音频生成失败
    pause
    exit /b 1
)

echo.
echo [3/4] 检查配置文件...
if not exist "data\custom_config.json" (
    echo [错误] 配置文件生成失败
    pause
    exit /b 1
)

echo.
echo [4/4] 准备图像序列...
echo.
echo ┌─────────────────────────────────────┐
echo │  ⚠️  重要提示                        │
echo ├─────────────────────────────────────┤
echo │  音频文件已生成，但还需要图像序列   │
echo │                                      │
echo │  选项A：使用现有图像                 │
echo │    将图像复制到各个预设的 image 目录 │
echo │                                      │
echo │  选项B：临时测试（推荐）             │
echo │    按任意键创建占位符图像           │
echo │                                      │
echo │  选项C：稍后配置                     │
echo │    跳过此步骤，手动准备图像         │
echo └─────────────────────────────────────┘
echo.
set /p choice="请选择 (A/B/C): "

if /i "%choice%"=="B" (
    echo 正在创建占位符图像...
    python -c "import os; import numpy as np; from PIL import Image; dirs = [d for d in os.listdir('data/custom_audio') if os.path.isdir(os.path.join('data/custom_audio', d))]; [os.makedirs(os.path.join('data/custom_audio', d, 'image'), exist_ok=True) or [Image.fromarray(np.zeros((512, 512, 3), dtype=np.uint8)).save(os.path.join('data/custom_audio', d, 'image', f'{i:04d}.jpg')) for i in range(25)] for d in dirs]; print('✓ 占位符图像已创建')"
)

echo.
echo ========================================
echo ✅ 配置完成！
echo ========================================
echo.
echo 📁 生成的文件：
echo   - data/custom_config.json     (配置文件)
echo   - data/preset_mapping.json    (映射文件)
echo   - data/custom_audio/          (音频和图像目录)
echo.
echo 🚀 下一步：
echo   1. 启动服务: python app.py
echo   2. 打开测试页面: http://localhost:8010/preset-audio-test.html
echo   3. 点击按钮测试预设音频功能
echo.
echo 📖 详细文档：
echo   - PRESET_AUDIO_QUICKSTART.md  (快速开始)
echo   - 预设音频使用指南.md         (完整指南)
echo.
pause
