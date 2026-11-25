"""Conexión con la API pública de Himalayas (https://himalayas.app/api).

Este módulo solo trae datos. No decide nada: eso lo hace filtros.py.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

URL_BUSQUEDA = "https://himalayas.app/jobs/api/search"
CABECERAS = {"User-Agent": "radar-vacantes (proyecto personal)"}


def pedir_pagina(termino, pais, pagina):
    """Pide una página de resultados de búsqueda y devuelve la lista de vacantes."""
    parametros = {"q": termino, "country": pais, "page": pagina, "sort": "recent"}
    url = URL_BUSQUEDA + "?" + urllib.parse.urlencode(parametros)
    solicitud = urllib.request.Request(url, headers=CABECERAS)

    for intento in range(2):
        try:
            with urllib.request.urlopen(solicitud, timeout=30) as respuesta:
                datos = json.load(respuesta)
                return datos.get("jobs", [])
        except urllib.error.HTTPError as error:
            # 429 = demasiados pedidos. Esperamos y reintentamos una sola vez.
            if error.code == 429 and intento == 0:
                espera = int(error.headers.get("Retry-After", "30"))
                print(f"  Himalayas pidió esperar {espera} s. Esperando...")
                time.sleep(espera)
                continue
            raise
    return []


def buscar(termino, pais, max_paginas, pausa):
    """Recorre las páginas de una búsqueda hasta que no lleguen más vacantes."""
    vacantes = []
    for pagina in range(1, max_paginas + 1):
        resultado = pedir_pagina(termino, pais, pagina)
        if not resultado:
            break
        vacantes.extend(resultado)
        time.sleep(pausa)  # Ser amables con la API.
    return vacantes


def traer_todas(config):
    """Ejecuta todas las búsquedas de config.json y quita duplicados por guid.

    Devuelve un diccionario {guid: vacante}. Cada vacante guarda además
    con qué búsqueda se encontró, para mostrarlo en el informe.
    """
    unicas = {}
    for termino in config["busquedas"]:
        print(f"Buscando '{termino}'...")
        encontradas = buscar(
            termino,
            config["pais"],
            config["max_paginas_por_busqueda"],
            config["pausa_entre_pedidos_segundos"],
        )
        print(f"  {len(encontradas)} resultados.")
        for vacante in encontradas:
            guid = vacante.get("guid")
            if not guid:
                continue
            if guid not in unicas:
                vacante["_busquedas"] = []
                unicas[guid] = vacante
            unicas[guid]["_busquedas"].append(termino)
    return unicas
