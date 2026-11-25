"""Escribe el informe diario en Markdown."""

import os
from datetime import datetime


def salario(vacante):
    minimo, maximo = vacante.get("minSalary"), vacante.get("maxSalary")
    if not minimo and not maximo:
        return "no indicado"
    moneda = vacante.get("currency") or ""
    periodo = {"annual": "año", "monthly": "mes", "hourly": "hora",
               "weekly": "semana", "fortnightly": "quincena"}.get(vacante.get("salaryPeriod"), "año")
    if minimo and maximo and minimo != maximo:
        return f"{minimo:,.0f} – {maximo:,.0f} {moneda} por {periodo}"
    return f"{(minimo or maximo):,.0f} {moneda} por {periodo}"


def escribir(pasan, descartadas, ya_vistas, carpeta="informes"):
    """Crea informes/AAAA-MM-DD_HHMM.md y devuelve la ruta del archivo.

    La hora en el nombre evita que una segunda ejecución el mismo día
    borre el informe anterior.
    """
    os.makedirs(carpeta, exist_ok=True)
    ahora = datetime.now()
    hoy = ahora.strftime("%Y-%m-%d")
    ruta = os.path.join(carpeta, f"{ahora.strftime('%Y-%m-%d_%H%M')}.md")

    lineas = [
        f"# Radar de Vacantes — {hoy}",
        "",
        f"**{len(pasan)} pasan** · {len(descartadas)} descartadas · "
        f"{ya_vistas} ya revisadas antes (no se repiten).",
        "",
        "## Vacantes que pasan",
        "",
    ]
    if not pasan:
        lineas.append("Hoy ninguna vacante nueva pasó los filtros.")
        lineas.append("")
    for vacante, notas in pasan:
        lineas += [
            f"### {vacante.get('title')} — {vacante.get('companyName')}",
            "",
            f"- **Por qué pasa:** {'; '.join(notas)}.",
            f"- **Contrato:** {vacante.get('employmentType') or 'no indicado'}",
            f"- **Salario:** {salario(vacante)}",
            f"- **Encontrada con:** {', '.join(vacante.get('_busquedas', []))}",
            f"- **Postular:** {vacante.get('applicationLink')}",
            "",
        ]

    lineas += ["## Descartadas", "", "| Vacante | Empresa | Regla que la descartó |", "|---|---|---|"]
    for vacante, motivo in descartadas:
        titulo = (vacante.get("title") or "").replace("|", "/")
        empresa = (vacante.get("companyName") or "").replace("|", "/")
        lineas.append(f"| {titulo} | {empresa} | {motivo} |")

    lineas += [
        "",
        "---",
        "Fuente de las vacantes: [Himalayas](https://himalayas.app). "
        "Los enlaces de postulación son los oficiales de Himalayas, sin modificar.",
        "",
    ]

    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write("\n".join(lineas))
    return ruta
