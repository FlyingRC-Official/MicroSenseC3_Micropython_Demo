@echo off
setlocal
set "TOOLROOT=%~dp0"
set "PYTHONPATH=%TOOLROOT%mpremote-local"
python -m mpremote %*