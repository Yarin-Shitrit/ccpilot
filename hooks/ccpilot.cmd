@echo off
rem ccpilot UserPromptSubmit hook launcher (Windows).
setlocal
if "%CCPILOT_PYTHON%"=="" (
    set "PY=python"
) else (
    set "PY=%CCPILOT_PYTHON%"
)
%PY% -m ccpilot route 2>> "%USERPROFILE%\.claude\ccpilot\hook.err"
exit /b 0