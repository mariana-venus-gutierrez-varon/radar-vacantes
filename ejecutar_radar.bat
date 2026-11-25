@echo off
REM Ejecuta el Radar desde su carpeta y guarda lo que imprime en datos\registro.txt.
REM Este archivo es el que usa el Programador de tareas de Windows.
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist datos mkdir datos
echo ===== %date% %time% ===== >> datos\registro.txt
python radar.py >> datos\registro.txt 2>&1
