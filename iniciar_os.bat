@echo off
set PORT=8000

echo [0/4] Liberando porta %PORT%...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%PORT% ^| findstr LISTENING') do taskkill /F /PID %%a 2>NUL

echo [1/4] Iniciando Backend Python (VENV 3.12)...
start /B .venv\Scripts\python api.py

echo [2/4] Iniciando Interface React...
start /B npm run dev

echo [3/4] Aguardando inicializacao dos servidores...
timeout /t 8 /nobreak > NUL

echo [4/4] Abrindo NeuroStrategy OS no Chromium (Modo App)...
start chrome --app=http://localhost:3000

echo Operacao concluida. Navegador Autonomo pronto para uso!
pause
