@echo off
rem Tarefa semanal: dump do banco, conferido, espelhado na pasta do
rem BACKUP_ESPELHO e enviado ao repositorio privado.
rem
rem O `cd` nao e enfeite: o db.py procura o .streamlit/secrets.toml a partir do
rem diretorio de trabalho, e o Agendador de Tarefas nao tem onde configurar isso.
rem `%~dp0..` = a pasta acima desta, ou seja a raiz do repositorio, sem depender
rem de caminho absoluto nenhum.
cd /d "%~dp0.."

rem O log e o unico jeito de descobrir que o backup parou de acontecer: sem ele,
rem uma falha semanal fica invisivel ate o dia em que o backup for necessario.
if not exist backups\nul mkdir backups
echo. >> backups\backup_semanal.log
echo ===== %date% %time% ===== >> backups\backup_semanal.log
python scripts\backup_banco.py --manter 3 --empurrar >> backups\backup_semanal.log 2>&1
if errorlevel 1 echo FALHOU (codigo %errorlevel%) >> backups\backup_semanal.log
