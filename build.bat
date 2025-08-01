@echo off
REM Build script for Windows

if "%1"=="clean" (
    echo Cleaning build artifacts...
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    for /d %%i in (*.egg-info) do rmdir /s /q "%%i"
    goto end
)

if "%1"=="build" (
    echo Building package...
    python -m build
    goto end
)

if "%1"=="check" (
    echo Checking package...
    twine check dist/*
    goto end
)

if "%1"=="install" (
    echo Installing package locally...
    pip install -e .
    goto end
)

if "%1"=="test" (
    echo Running tests...
    python -m pytest tests/ -v
    goto end
)

if "%1"=="all" (
    echo Running full build process...
    call %0 clean
    call %0 build
    call %0 check
    call %0 install
    call %0 test
    goto end
)

echo Usage: build.bat [clean^|build^|check^|install^|test^|all]

:end
