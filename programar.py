"""Programa (o reprograma) la ejecución diaria del Radar en Windows.

Lee la hora de config.json ("hora_del_informe", formato 24 h, ej. "10:00")
y crea la tarea "Radar de Vacantes" en el Programador de tareas.
Si el PC está apagado a esa hora, la tarea corre apenas se encienda.

Uso:  python programar.py      (o doble clic en programar.bat)
Para cambiar la hora: edita config.json y vuelve a ejecutarlo.
"""

import json
import os
import re
import subprocess
import sys

NOMBRE_TAREA = "Radar de Vacantes"


def main():
    carpeta = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(carpeta, "config.json"), encoding="utf-8") as archivo:
        hora = json.load(archivo).get("hora_del_informe", "10:00")

    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", hora):
        raise SystemExit(f"La hora '{hora}' no es válida. Usa formato 24 h, por ejemplo 09:30 o 18:00.")
    if sys.platform != "win32":
        raise SystemExit("Este programador es para Windows. En otros sistemas usa cron o similar.")

    bat = os.path.join(carpeta, "ejecutar_radar.bat")
    comando = (
        f"$a = New-ScheduledTaskAction -Execute '{bat}' -WorkingDirectory '{carpeta}'; "
        f"$t = New-ScheduledTaskTrigger -Daily -At '{hora}'; "
        "$s = New-ScheduledTaskSettingsSet -StartWhenAvailable; "
        f"Register-ScheduledTask -TaskName '{NOMBRE_TAREA}' -Action $a -Trigger $t -Settings $s -Force | Out-Null"
    )
    resultado = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", comando],
        capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        raise SystemExit("No se pudo crear la tarea:\n" + resultado.stderr)
    print(f"Listo: el Radar correrá todos los días a las {hora}.")
    print("Si el PC está apagado a esa hora, correrá apenas se encienda.")


if __name__ == "__main__":
    main()
