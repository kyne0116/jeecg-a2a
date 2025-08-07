@echo off
REM JEECG A2A Platform - Windows Start Script

setlocal enabledelayedexpansion

REM Colors (Windows doesn't support colors in batch easily, so we'll use echo)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

echo ==================================================
echo 🚀 JEECG A2A Platform Startup Script (Windows)
echo ==================================================
echo.

REM Change to script directory
cd /d "%~dp0\.."
echo %INFO% Working directory: %cd%

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% Python is not installed or not in PATH
    echo Please install Python 3.9 or higher and add it to your PATH
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo %INFO% Found Python %python_version%

REM Check if uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% uv is not installed or not in PATH
    echo Please install uv first:
    echo https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('uv --version 2^>^&1') do set uv_version=%%i
echo %INFO% Found %uv_version%

REM Create necessary directories
echo %INFO% Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "uploads" mkdir uploads
if not exist "ui\static\uploads" mkdir ui\static\uploads
echo %SUCCESS% Directories created

REM Setup environment
echo %INFO% Setting up environment...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo %SUCCESS% Created .env file from .env.example
        echo %WARNING% Please edit .env file with your configuration
    ) else (
        echo %WARNING% .env.example not found, please create .env manually
    )
) else (
    echo %INFO% .env file already exists
)

REM Setup virtual environment and install dependencies if --install flag is provided
if "%1"=="--install" (
    echo %INFO% Setting up virtual environment...
    if exist ".venv" (
        echo %INFO% Virtual environment already exists
    ) else (
        uv venv
        if errorlevel 1 (
            echo %ERROR% Failed to create virtual environment
            pause
            exit /b 1
        )
        echo %SUCCESS% Virtual environment created
    )

    echo %INFO% Installing dependencies...
    if exist "pyproject.toml" (
        uv sync
        if errorlevel 1 (
            echo %ERROR% Failed to install dependencies
            pause
            exit /b 1
        )
        echo %SUCCESS% Dependencies installed successfully
    ) else (
        echo %ERROR% pyproject.toml not found
        pause
        exit /b 1
    )
    shift
)

if "%1"=="-i" (
    echo %INFO% Setting up virtual environment...
    if exist ".venv" (
        echo %INFO% Virtual environment already exists
    ) else (
        uv venv
        if errorlevel 1 (
            echo %ERROR% Failed to create virtual environment
            pause
            exit /b 1
        )
        echo %SUCCESS% Virtual environment created
    )

    echo %INFO% Installing dependencies...
    if exist "pyproject.toml" (
        uv sync
        if errorlevel 1 (
            echo %ERROR% Failed to install dependencies
            pause
            exit /b 1
        )
        echo %SUCCESS% Dependencies installed successfully
    ) else (
        echo %ERROR% pyproject.toml not found
        pause
        exit /b 1
    )
    shift
)

REM Check port availability (basic check)
netstat -an | find "6000" | find "LISTENING" >nul
if not errorlevel 1 (
    echo %WARNING% Port 6000 appears to be in use
    echo You may need to stop the existing service or change the port in .env
) else (
    echo %INFO% Port 6000 appears to be available
)

echo.
echo %INFO% All checks passed. Starting platform...
echo.

REM Start the platform
if "%1"=="--dev" (
    echo %INFO% Starting in development mode with auto-reload
    uv run main.py --reload --debug
) else if "%1"=="-d" (
    echo %INFO% Starting in development mode with auto-reload
    uv run main.py --reload --debug
) else if "%1"=="--help" (
    goto :help
) else if "%1"=="-h" (
    goto :help
) else (
    uv run main.py
)

goto :end

:help
echo JEECG A2A Platform Start Script (Windows)
echo.
echo Usage: %0 [OPTIONS]
echo.
echo Prerequisites:
echo   - Python 3.9+
echo   - uv package manager (https://docs.astral.sh/uv/)
echo.
echo Options:
echo   --install, -i    Setup virtual environment and install dependencies
echo   --dev, -d        Start in development mode with auto-reload
echo   --help, -h       Show this help message
echo.
echo Examples:
echo   %0               Start the platform
echo   %0 --install     Setup and start
echo   %0 --dev         Start in development mode
echo   %0 -i -d         Setup and start in dev mode
echo.
echo Manual setup:
echo   uv venv          Create virtual environment
echo   uv sync          Install dependencies
echo   uv run main.py   Start platform
echo.
pause
goto :end

:end
endlocal
