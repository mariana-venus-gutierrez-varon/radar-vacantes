# Guía para usar el Radar en tu propia búsqueda de empleo

Tiempo estimado: 30 minutos la primera vez. Pensado para Windows.

## 1. Lo que necesitas

- Una cuenta de Claude con plan Pro o superior (para Claude Code y los agentes).
  El Radar en sí funciona sin Claude: solo necesita Python.
- Una cuenta de GitHub (opcional, solo si quieres guardar tu copia en línea).

## 2. Instalar los programas

Abre la terminal (escribe `cmd` en el menú Inicio) y ejecuta, uno a la vez:

```
winget install 9NQ7512CXL7T
winget install --id Git.Git -e --source winget
winget install --id Microsoft.VisualStudioCode -e
```

El primero instala Python; el segundo, Git; el tercero, VS Code (editor).
Para Claude Code:

```
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

Si al final dice que `.local\bin` no está en el PATH, agrégalo
(Configuración de Windows → Variables de entorno → Path → Nuevo →
`C:\Users\TU_USUARIO\.local\bin`). Cierra y abre la terminal después de instalar todo.

## 3. Descargar el Radar

```
git clone https://github.com/mariana-venus-gutierrez-varon/radar-vacantes.git
cd radar-vacantes
```

## 4. Hacerlo tuyo (lo único que tienes que editar)

1. Copia `perfil.ejemplo.md` como `perfil.md` y llénalo con tus datos.
2. Copia `CLAUDE.ejemplo.md` como `CLAUDE.md`.
3. Abre `config.json` y cambia:
   - `hora_del_informe`: a qué hora quieres el informe diario.
   - `busquedas`: 2 o 3 cargos en inglés (ej. "accountant", "customer success").
   - `pais`: tu país en inglés (ej. "Mexico", "Peru").
   - `zona_horaria_utc`: tu diferencia con UTC (Colombia y Perú: -5; México: -6).
   - `max_anios_experiencia`: cuántos años de experiencia tienes.
   - `tipos_de_contrato_aceptados`, `certificaciones_que_no_tengo`,
     `idiomas_que_no_hablo` y `palabras_de_titulo_fuera_de_perfil`, según tu caso.

## 5. Usarlo

- Doble clic en `ejecutar_radar.bat`. El informe aparece en la carpeta `informes`.
- O desde la terminal: `python radar.py`.
- Para revisar todo de nuevo (por ejemplo, después de cambiar config.json):
  `python radar.py --sin-memoria`.

Para que corra solo cada día:

1. En `config.json`, pon tu hora en `hora_del_informe` (formato 24 h, ej. "10:00" o "18:30").
2. Doble clic en `programar.bat` (o `python programar.py`).

Si el PC está apagado a esa hora, el Radar corre apenas lo enciendas.
Para cambiar la hora después: edita `config.json` y vuelve a abrir `programar.bat`.

## 6. Usar los agentes (opcional)

En la carpeta del proyecto, abre la terminal y escribe `claude`. Inicia sesión
con tu cuenta. Puedes pedir, por ejemplo:

- "Revisa esta vacante con el revisor: [enlace]"
- "Prepara con el redactor una carta para esta vacante: [enlace]"
- "Explícame con el tutor cómo funciona la regla de experiencia"

## Reglas importantes

- El Radar nunca postula por ti. Tú revisas y envías.
- Tus datos personales (perfil.md, CLAUDE.md, datos/, informes/) no se suben a GitHub.
- Las vacantes vienen de Himalayas: no publiques ni redistribuyas los informes.
