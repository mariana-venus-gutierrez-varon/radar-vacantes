"""Reglas de filtrado del Radar.

Cada regla recibe una vacante y devuelve:
  - None si la vacante pasa la regla, o
  - un texto corto con el motivo del descarte.

Las reglas salen de revisar 394 vacantes a mano. Todas leen sus umbrales
desde config.json, así que se ajustan sin tocar este archivo.
"""

import hashlib
import html
import re
import time
import unicodedata

# --- Utilidades ------------------------------------------------------------


def normalizar(texto):
    """Minúsculas y letras 'decoradas' convertidas a letras normales.

    Algunos avisos escriben el título con letras matemáticas (𝗕𝗶𝗹𝗹𝗶𝗻𝗴). Para una
    regla que busca 'a-z' eso es invisible y se salta los filtros. NFKC las
    convierte a ASCII normal.
    """
    return unicodedata.normalize("NFKC", texto or "").lower()


def titulo_normalizado(vacante):
    return normalizar(vacante.get("title"))


def texto_plano(vacante):
    """Convierte la descripción HTML en texto plano en minúsculas."""
    descripcion = vacante.get("description") or ""
    sin_etiquetas = re.sub(r"<[^>]+>", " ", descripcion)
    return re.sub(r"\s+", " ", normalizar(html.unescape(sin_etiquetas))).strip()


def nombres_de_paises(vacante):
    """Devuelve los países permitidos como lista de nombres.

    La documentación dice que son objetos {alpha2, name, slug}, pero la API
    real devolvió textos simples. Aceptamos los dos formatos.
    """
    paises = []
    for pais in vacante.get("locationRestrictions") or []:
        if isinstance(pais, dict):
            paises.append(pais.get("name", ""))
        else:
            paises.append(str(pais))
    return paises


def anios_exigidos(texto):
    """Busca frases como '3+ years of experience' o '2 años de experiencia'.

    Devuelve el mayor mínimo encontrado (el requisito más exigente), o None.
    """
    patrones = [
        r"(?<!\d)(\d{1,2})(?!\d)\s*\+?\s*(?:-|–|to|a)?\s*\d{0,2}\s*\+?\s*(?:years?|yrs?)\b[^.]{0,60}?experience",
        r"(?:minimum|at least|min\.?)\s*(?:of\s*)?(?<!\d)(\d{1,2})(?!\d)\s*\+?\s*(?:years?|yrs?)",
        r"(?<!\d)(\d{1,2})(?!\d)\s*\+?\s*(?:-|–|a)?\s*\d{0,2}\s*\+?\s*años\s*de\s*experiencia",
        # "experiencia mínima de 3 años", "mínimo 3 años", "al menos 3 años"
        r"(?:m[ií]nim[oa]s?|al menos|por lo menos)\s*(?:de\s*)?(?<!\d)(\d{1,2})(?!\d)\s*\+?\s*años",
        # "experiencia de 3 años", "experiencia previa de 3 años"
        r"experiencia\s*(?:previa\s*)?(?:de|mayor a)\s*(?<!\d)(\d{1,2})(?!\d)\s*\+?\s*años",
    ]
    encontrados = []
    for patron in patrones:
        for coincidencia in re.finditer(patron, texto):
            numero = int(coincidencia.group(1))
            if 0 < numero <= 20:  # Ignora cifras absurdas (fechas, porcentajes).
                encontrados.append(numero)
    return max(encontrados) if encontrados else None


def fecha_en_segundos(valor):
    """La documentación dice milisegundos, pero la API real envía segundos.

    Aceptamos los dos: un número mayor a 10^12 solo puede ser milisegundos.
    """
    if not valor:
        return None
    valor = float(valor)
    return valor / 1000 if valor > 1e12 else valor


def huella_descripcion(vacante):
    """Huella de la descripción para detectar textos copiados entre empresas."""
    return hashlib.sha1(texto_plano(vacante).encode("utf-8")).hexdigest()


# --- Reglas ----------------------------------------------------------------


def regla_expirada(vacante, config):
    vence = fecha_en_segundos(vacante.get("expiryDate"))
    if vence and vence < time.time():
        return "Vacante expirada"
    return None


def regla_tipo_de_contrato(vacante, config):
    tipo = vacante.get("employmentType")
    if tipo and tipo not in config["tipos_de_contrato_aceptados"]:
        return f"Tipo de contrato no buscado ({tipo})"
    # A veces la etiqueta dice Full Time pero el título dice medio tiempo.
    titulo = titulo_normalizado(vacante)
    if re.search(r"part[- ]time|medio tiempo", titulo) and "Part Time" not in config["tipos_de_contrato_aceptados"]:
        return "Contradicción: etiqueta de tiempo completo pero el título dice medio tiempo"
    return None


def regla_ubicacion(vacante, config):
    paises = nombres_de_paises(vacante)
    if paises and config["pais"].lower() not in [p.lower() for p in paises]:
        return f"No acepta {config['pais']}"
    return None


def regla_zona_horaria(vacante, config):
    zonas = vacante.get("timezoneRestrictions") or []
    offsets = []
    for zona in zonas:
        coincidencia = re.search(r"([+-]?\d+(?:\.\d+)?)", str(zona))
        if coincidencia:
            offsets.append(float(coincidencia.group(1)))
    if not offsets:
        return None
    mi_zona = config["zona_horaria_utc"]
    tolerancia = config["tolerancia_zona_horaria_horas"]
    if not any(abs(o - mi_zona) <= tolerancia for o in offsets):
        return f"Zona horaria incompatible ({', '.join(map(str, zonas))})"
    return None


def regla_contradiccion_ubicacion(vacante, config):
    """Metadatos abiertos (worldwide o Colombia) pero el texto exige otro país."""
    texto = texto_plano(vacante)
    frases = [
        r"(?:must|need to|required to) (?:be )?(?:based|located|reside|live) in the (?:u\.?s\.?|united states|uk|united kingdom|eu)",
        r"\b(?:us|u\.s\.) (?:citizens?|residents?) only",
        r"authori[sz]ed to work in the (?:u\.?s\.?|united states)",
        r"\bus[- ]based (?:candidates|applicants) only",
        r"(?:green card|security clearance) (?:is )?required",
        r"\bmust hold (?:a )?(?:us|u\.s\.) citizenship",
    ]
    for frase in frases:
        if re.search(frase, texto):
            return "Contradicción: la etiqueta permite Colombia pero el texto exige otro país"
    return None


def regla_seniority(vacante, config):
    niveles = vacante.get("seniority") or []
    if niveles and all(n in config["seniority_excluida"] for n in niveles):
        return f"Nivel demasiado alto ({', '.join(niveles)})"
    titulo = titulo_normalizado(vacante)
    for palabra in config["palabras_de_titulo_excluidas"]:
        palabra = palabra.strip().lower()
        # Busca la palabra completa: 'vp' no debe coincidir dentro de 'vpn'.
        if re.search(r"(?<![a-z])" + re.escape(palabra) + r"(?![a-z])", titulo):
            return f"Título de nivel alto ('{palabra}')"
    return None


def buscar_palabra(palabra, texto):
    """True si la palabra aparece completa (no dentro de otra palabra)."""
    return re.search(r"(?<![a-z])" + re.escape(palabra.lower()) + r"(?![a-z])", texto) is not None


def regla_fuera_de_perfil(vacante, config):
    """Puestos técnicos o de otras profesiones que no encajan con el perfil."""
    titulo = titulo_normalizado(vacante)
    for palabra in config.get("palabras_de_titulo_fuera_de_perfil", []):
        if buscar_palabra(palabra, titulo):
            return f"Fuera del perfil ('{palabra}' en el título)"
    return None


def regla_idioma(vacante, config):
    """El título pide un idioma que no está en el perfil (ej. 'Dutch AI Data Rater')."""
    titulo = titulo_normalizado(vacante)
    for idioma in config.get("idiomas_que_no_hablo", []):
        if buscar_palabra(idioma, titulo):
            return f"Pide un idioma que no hablo ({idioma})"
    return None


def regla_experiencia(vacante, config):
    anios = anios_exigidos(texto_plano(vacante))
    if anios is not None and anios > config["max_anios_experiencia"]:
        return f"Pide {anios}+ años de experiencia"
    return None


def regla_certificaciones(vacante, config):
    texto = texto_plano(vacante)
    for oracion in re.split(r"[.;\n•]", texto):
        if not re.search(r"\b(required|must|mandatory|requisito|indispensable|obligatori)", oracion):
            continue
        for cert in config["certificaciones_que_no_tengo"]:
            if re.search(r"\b" + re.escape(cert.lower()) + r"\b", oracion):
                return f"Exige certificación {cert}"
    return None


def regla_comision(vacante, config):
    texto = texto_plano(vacante) + " " + titulo_normalizado(vacante)
    frases = [
        r"commission[- ]only", r"commission[- ]based", r"100\s*% commission",
        r"uncapped commission", r"unlimited earning potential",
        r"solo comisi[oó]n", r"pago por comisi[oó]n",
    ]
    for frase in frases:
        if re.search(frase, texto):
            return "Posible venta por comisión disfrazada"
    return None


def regla_titulo_sospechoso(vacante, config):
    titulo = titulo_normalizado(vacante)
    if titulo.startswith("copy of"):
        return "Título 'Copy of': publicación copiada de una plantilla"
    return None


# El orden importa: primero lo barato y obvio, después lo que lee el texto.
REGLAS = [
    regla_expirada,
    regla_tipo_de_contrato,
    regla_ubicacion,
    regla_zona_horaria,
    regla_titulo_sospechoso,
    regla_seniority,
    regla_fuera_de_perfil,
    regla_idioma,
    regla_contradiccion_ubicacion,
    regla_comision,
    regla_experiencia,
    regla_certificaciones,
]


def marcar_plantillas(vacantes):
    """Detecta la misma descripción publicada por empresas distintas.

    Esta regla compara vacantes entre sí, por eso va aparte de REGLAS.
    Devuelve el conjunto de guids sospechosos.
    """
    empresas_por_huella = {}
    for vacante in vacantes:
        if len(texto_plano(vacante)) < 200:  # Textos muy cortos dan falsos positivos.
            continue
        huella = huella_descripcion(vacante)
        empresas_por_huella.setdefault(huella, set()).add(vacante.get("companyName"))
    sospechosas = set()
    for vacante in vacantes:
        huella = huella_descripcion(vacante)
        if len(empresas_por_huella.get(huella, ())) > 1:
            sospechosas.add(vacante.get("guid"))
    return sospechosas


def evaluar(vacantes, config):
    """Aplica todas las reglas. Devuelve (pasan, descartadas).

    pasan: lista de (vacante, notas)          notas = por qué pasa
    descartadas: lista de (vacante, motivo)   motivo = regla que la tumbó
    """
    plantillas = marcar_plantillas(vacantes)
    pasan, descartadas = [], []
    for vacante in vacantes:
        if vacante.get("guid") in plantillas:
            descartadas.append((vacante, "Misma descripción publicada por varias empresas"))
            continue
        motivo = None
        for regla in REGLAS:
            motivo = regla(vacante, config)
            if motivo:
                break
        if motivo:
            descartadas.append((vacante, motivo))
        else:
            pasan.append((vacante, notas_de_aprobacion(vacante, config)))
    pasan, repetidas = quitar_repetidas_de_la_misma_empresa(pasan)
    descartadas.extend(repetidas)
    return pasan, descartadas


def quitar_repetidas_de_la_misma_empresa(pasan):
    """Una empresa que publica el mismo aviso varias veces aparece una sola vez.

    Se conserva la primera y las demás pasan a descartadas con su motivo, para
    que el informe siga siendo auditable. Solo se compara entre las que ya
    pasaron las reglas: si el aviso era malo, ya lo tumbó otra regla.
    Misma empresa + misma descripción = repetida. Textos muy cortos no cuentan.
    """
    vistas = set()
    unicas, repetidas = [], []
    for vacante, notas in pasan:
        if len(texto_plano(vacante)) < 200:
            unicas.append((vacante, notas))
            continue
        clave = (vacante.get("companyName"), huella_descripcion(vacante))
        if clave in vistas:
            repetidas.append((vacante, "Repetida: la misma empresa publicó este aviso más de una vez (se conserva una)"))
        else:
            vistas.add(clave)
            unicas.append((vacante, notas))
    return unicas, repetidas


def notas_de_aprobacion(vacante, config):
    """Explica en pocas palabras por qué la vacante pasó."""
    notas = []
    paises = nombres_de_paises(vacante)
    notas.append("abierta a todo el mundo" if not paises else f"acepta {config['pais']}")
    anios = anios_exigidos(texto_plano(vacante))
    notas.append("no menciona años de experiencia" if anios is None else f"pide {anios} año(s)")
    niveles = vacante.get("seniority") or []
    if niveles:
        notas.append("nivel " + ", ".join(niveles))
    notas.append("sin señales de fraude detectadas")
    return notas
