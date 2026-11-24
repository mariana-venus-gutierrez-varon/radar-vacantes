import json
import urllib.request
URL = "https://himalayas.app/jobs/api?limit=5"
solicitud = urllib.request.Request(URL, headers={"User-Agent": "radar-vacantes (proyecto personal)"})
with urllib.request.urlopen(solicitud) as respuesta:
    datos = json.load(respuesta)
    print("Total de vacantes en Himalayas:", datos ["totalCount"])
    for vacante in datos["jobs"]:
        print("-", vacante["title"], "|", vacante["companyName"])