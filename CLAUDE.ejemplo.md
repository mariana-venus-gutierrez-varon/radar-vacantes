# Radar de Vacantes (instrucciones para Claude Code)

Copia este archivo como `CLAUDE.md`. Claude Code lo lee al abrir la carpeta.
`CLAUDE.md` no se sube a GitHub, así que puedes agregar notas personales.

## Qué es

Un reporte diario de vacantes remotas. Trae ofertas nuevas desde la API pública
de Himalayas, las filtra con reglas propias y escribe un informe en Markdown
con las que pasan (y por qué) y las descartadas (con la regla que las tumbó).
Nunca postula: el usuario decide y envía.

## Archivos

- config.json: búsquedas, país y umbrales. Es lo que cada persona ajusta.
- perfil.md: datos del usuario (privado, fuera de git). Plantilla en perfil.ejemplo.md.
- himalayas.py (trae y pagina), filtros.py (reglas), informe.py (Markdown),
  radar.py (orquesta), pruebas.py (pruebas sin internet).
- ejecutar_radar.bat: ejecución con doble clic o desde el Programador de tareas.
- datos/: memoria de vacantes vistas y última respuesta de la API (fuera de git).
- informes/: un informe por ejecución (fuera de git, salvo ejemplo.md).

## Cómo trabajar con el usuario

- Explica en lenguaje simple; no asumas que sabe programar.
- Antes de cambiar una regla, ejecuta `python pruebas.py` y agrega una prueba.
- Para revisar las reglas con datos reales, usa datos/ultima_respuesta.json.
- Nunca envíes postulaciones ni completes formularios en nombre del usuario.

## Detalles de la API de Himalayas (verificados con datos reales)

- Búsqueda: https://himalayas.app/jobs/api/search con q, country, page, sort.
  Filtrar por país incluye las vacantes worldwide (salvo exclude_worldwide).
- expiryDate y pubDate llegan en segundos, aunque la documentación diga milisegundos.
- locationRestrictions llega como lista de nombres de países; vacía = worldwide.
- Términos: usar applicationLink sin modificar, dar crédito visible a Himalayas,
  no redistribuir las vacantes, quitar las expiradas.

## Equipo de agentes (.claude/agents)

La sesión principal es el director (Sonnet, ver .claude/settings.json).
- buscador (Haiku): recolecta vacantes.
- revisor-vacantes (Sonnet): verifica requisitos reales y fraude contra perfil.md.
- redactor (Sonnet): borradores de postulación; el usuario revisa y envía.
- tutor-codigo (Sonnet): explica y revisa el código.
- estratega (Opus): solo decisiones de diseño, revisión final o casos ambiguos;
  recibe resúmenes, nunca datos crudos.
