"""Radar de Vacantes: punto de entrada.

Flujo diario:
  1. Lee la configuración (config.json).
  2. Trae vacantes de Himalayas para cada búsqueda (himalayas.py).
  3. Aparta las que ya se revisaron en días anteriores (datos/vistas.json).
  4. Aplica las reglas de filtrado (filtros.py).
  5. Escribe el informe del día en informes/ (informe.py).

Uso:  python radar.py                 (normal: solo vacantes nuevas)
      python radar.py --sin-memoria   (revisa todas, útil para pruebas o la demo)
"""

import json
import os
import sys
import time

import filtros
import himalayas
import informe

ARCHIVO_CONFIG = "config.json"
ARCHIVO_VISTAS = os.path.join("datos", "vistas.json")


def cargar_json(ruta, por_defecto):
    if not os.path.exists(ruta):
        return por_defecto
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_vistas(vistas):
    os.makedirs(os.path.dirname(ARCHIVO_VISTAS), exist_ok=True)
    ahora = time.time()
    # Olvida las vacantes que ya expiraron para que el archivo no crezca sin fin.
    vigentes = {g: d for g, d in vistas.items()
                if not d.get("expira") or filtros.fecha_en_segundos(d["expira"]) > ahora}
    with open(ARCHIVO_VISTAS, "w", encoding="utf-8") as archivo:
        json.dump(vigentes, archivo, ensure_ascii=False, indent=1)


def main():
    # Trabaja siempre desde la carpeta del proyecto, aunque se ejecute desde otro lugar.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    config = cargar_json(ARCHIVO_CONFIG, None)
    if config is None:
        raise SystemExit("No encontré config.json en la carpeta del proyecto.")

    sin_memoria = "--sin-memoria" in sys.argv
    vistas = {} if sin_memoria else cargar_json(ARCHIVO_VISTAS, {})
    todas = himalayas.traer_todas(config)

    # Copia de lo que respondió la API, para revisar las reglas con datos reales.
    os.makedirs("datos", exist_ok=True)
    with open(os.path.join("datos", "ultima_respuesta.json"), "w", encoding="utf-8") as archivo:
        json.dump(list(todas.values()), archivo, ensure_ascii=False)
    nuevas = [v for guid, v in todas.items() if guid not in vistas]
    ya_vistas = len(todas) - len(nuevas)
    print(f"{len(todas)} vacantes únicas, {len(nuevas)} nuevas.")

    if not nuevas:
        print("No hay vacantes nuevas desde la última revisión. No se crea informe.")
        return

    pasan, descartadas = filtros.evaluar(nuevas, config)

    if not sin_memoria:
        hoy = time.strftime("%Y-%m-%d")
        for vacante in nuevas:
            vistas[vacante["guid"]] = {"fecha": hoy, "expira": vacante.get("expiryDate")}
        guardar_vistas(vistas)

    ruta = informe.escribir(pasan, descartadas, ya_vistas)
    print(f"Listo: {len(pasan)} pasan, {len(descartadas)} descartadas.")
    print(f"Informe: {ruta}")


if __name__ == "__main__":
    main()
