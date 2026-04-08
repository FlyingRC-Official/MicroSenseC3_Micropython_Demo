@echo off
setlocal
set "TOOLROOT=%~dp0"
set "PYTHONPATH=%TOOLROOT%"
python -m mpy_cross %*