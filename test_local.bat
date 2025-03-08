@echo off
start cmd /k "python src/run_server.py"
timeout /t 2
start cmd /k "python src/main.py" 