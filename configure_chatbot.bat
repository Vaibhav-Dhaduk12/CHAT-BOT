@echo off
REM =====================================================
REM   Chatbot Configuration Generator for Windows
REM =====================================================

cls
echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║          🤖 AI Chatbot - Change Website Configuration          ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Current Configuration
echo 📊 CURRENT SETUP:
echo    Website: https://viphub.phoenixins.mu/
echo    Chatbot ID: phoenix_insurance_bot
echo    Status: Ready
echo.

REM Get user input
set /p website="🌐 Enter new website URL (or press Enter to skip): "
if "%website%"=="" (
    echo Aborted.
    pause
    exit /b
)

set /p chatbot_id="📛 Enter chatbot ID (e.g., my_company_bot): "
if "%chatbot_id%"=="" (
    echo Aborted.
    pause
    exit /b
)

set /p max_pages="📄 Enter max pages to crawl (default 50): "
if "%max_pages%"=="" set max_pages=50

set /p max_depth="🔗 Enter crawl depth (default 3): "
if "%max_depth%"=="" set max_depth=3

REM Confirm
echo.
echo ✅ Configuration:
echo    URL: %website%
echo    ID: %chatbot_id%
echo    Pages: %max_pages%
echo    Depth: %max_depth%
echo.

set /p confirm="Ready to proceed? (y/n): "
if /i not "%confirm%"=="y" (
    echo Aborted.
    pause
    exit /b
)

REM Run pipeline
echo.
echo 🚀 Starting chatbot indexing...
echo ════════════════════════════════════════════════════════
echo.

python run_pipeline.py ^
  --url "%website%" ^
  --chatbot-id "%chatbot_id%" ^
  --max-pages %max_pages% ^
  --max-depth %max_depth%

if %errorlevel%==0 (
    echo.
    echo ════════════════════════════════════════════════════════
    echo ✅ SUCCESS! Your chatbot is ready!
    echo.
    echo 🌐 Visit: http://localhost:8000
    echo ⚙️  Config: http://localhost:8000/config
    echo.
) else (
    echo.
    echo ❌ Error occurred. Check the output above.
    echo.
)

pause
