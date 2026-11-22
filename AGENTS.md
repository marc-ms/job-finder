# AGENTS.md - Contrato de Arquitectura y Diseno

## 1. Objetivo del proyecto
Aplicacion web ligera y buscador de empleo personalizado para una candidata junior en traduccion (ingles), PLN/Python, correccion y copywriting, residente en Palma de Mallorca (local en Mallorca o 100% remoto).

## 2. Arquitectura obligatoria
- Lenguaje: Python 3.12 gestionado con `uv` y `pyproject.toml`.
- Separacion estricta en dos procesos que comparten base de datos:
  1. Pipeline CLI (`src/pipeline/run.py`): ejecuta scraping/APIs, filtro rapido (Capa 1) y evaluacion con IA (Capa 2). Nunca debe ejecutarse dentro de una peticion HTTP de Vercel para evitar timeouts.
  2. Aplicacion Web (`src/web/main.py`): FastAPI + Jinja2 + HTMX + CSS propio (`src/web/static/styles.css`). Solo lee de la base de datos y actualiza el estado de las ofertas (`new`, `saved`, `applied`, `discarded`).
- Base de datos: `SQLModel` compatible con SQLite en local (`sqlite:///./data/jobs.db`) y PostgreSQL en produccion (`Neon`) mediante `DATABASE_URL`.
- No introducir React, Vue, Next.js, npm, Tailwind CLI ni bundlers de JavaScript. HTMX se carga desde un unico script ligero en `base.html`.

## 3. Reglas tecnicas para Gemini 4 Hydrogen
- Usar EXCLUSIVAMENTE el SDK oficial `google-genai >= 2.34.0` (`from google import genai` y `from google.genai import types`). Prohibido usar el paquete obsoleto `google-generativeai`.
- Modelo por defecto: `gemini-4-hydrogen` (leido desde `GEMINI_MODEL` en `.env`).
- Nivel de razonamiento por defecto: `XHIGH` / `"xhigh"` (leido desde `GEMINI_THINKING_LEVEL` en `.env`).
  - Con `client.models.generate_content(...)`, configurar `thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.XHIGH)`.
  - IMPORTANTE: En `gemini-4-hydrogen`, NO pasar `thinking_budget`, NO usar nivel `MINIMAL` (devuelven error 400) y NO confiar en `temperature` (es ignorado).
  - Dejar `max_output_tokens` suficientemente alto (ej. `16384`) porque los tokens de razonamiento cuentan dentro del limite de salida y no deben cortar el JSON final.
- Usar siempre salidas estructuradas (esquema Pydantic con `response_mime_type="application/json"` y `response_schema=...`) para validar la respuesta antes de guardarla en base de datos.
- La fuente de verdad sobre el perfil de la candidata es `config/profile.md`. Nunca hardcodear el perfil dentro del codigo Python.

## 4. Contrato de Diseno (Estrictamente obligatorio)
La interfaz debe seguir una estetica editorial, sobria, limpia y de baja densidad (inspirada en herramientas de lectura y diseno tipografico suizo).

### Reglas positivas:
- Modo claro por defecto:
  - Fondo general: blanco roto calido (`#F9F9F7`).
  - Superficies/tarjetas: blanco puro (`#FFFFFF`) con borde fino (`1px solid #E6E5E0`), sin sombras llamativas.
  - Texto principal: carbon (`#1A1918`). Texto secundario: gris neutro (`#66645E`).
  - Un unico color de acento sobrio (`#1F4D3F`, verde pizarra oscuro) solo para el estado activo o accion primaria.
- Lectura en columna unica centrada (`max-width: 840px`), con espaciado generoso (`24px` a `32px` entre ofertas).
- Jerarquia basada en tipografia clara (sans-serif limpia del sistema / Inter y monoespaciada discreta para puntuaciones como `88 / 100` y fechas).
- Interacciones discretas: solo transiciones sutiles de color de borde o fondo (`150ms ease`).

### Prohibiciones absolutas (Anti-patrones de IA):
- CERO EMOJIS en toda la interfaz de usuario (ni en titulos, ni en botones, ni en etiquetas, ni en estados vacios, ni en mensajes de error).
- Prohibido cualquier degradado (ni en fondos, ni en botones, ni en textos).
- Prohibidos colores neon, brillos, sombras difusas de color, glassmorphism (`backdrop-filter`) o estetica "dark mode futurista".
- Prohibidas animaciones de rebote, desplazamientos o escalados al hacer hover (`transform: scale` o `translateY`).
- Prohibido llenar la parte superior de tarjetas de KPIs, graficos decorativos o "hero sections" de marketing.

## 5. Forma de trabajar en el repositorio
- Mantener los archivos pequenos, legibles y con tipado estatico (type hints).
- Cada fuente de empleo en `src/sources/` debe heredar de una clase base comun (`BaseSource`) y devolver una lista de objetos `RawJob`.
- No modificar archivos fuera de la fase solicitada por el usuario.
- Antes de implementar cambios de multiples archivos, presentar un plan breve de que archivos se crearan o modificaran.