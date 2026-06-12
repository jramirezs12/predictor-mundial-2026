# 🚀 Cómo desplegar el Predictor Mundial 2026 (gratis)

Tu app es perfecta para hospedar: **no tiene dependencias** y es un proceso
Python normal que lee el puerto de la variable de entorno `PORT`. Solo necesita
acceso a internet (para ESPN), que cualquier host gratuito da.

---

## ⭐ Opción recomendada: Render.com (URL pública gratis, sin tarjeta)

Te da un dominio permanente tipo **`predictor-mundial-2026.onrender.com`**.

### Paso 1 — Subir el código a GitHub
Tienes `git` instalado. En la carpeta del proyecto:

```bash
cd C:\predictor
git init
git add .
git commit -m "Predictor Mundial 2026"
```

Luego crea un repositorio vacío en https://github.com/new (por ejemplo
`predictor-mundial-2026`, **sin** README) y conecta:

```bash
git remote add origin https://github.com/TU_USUARIO/predictor-mundial-2026.git
git branch -M main
git push -u origin main
```
(La primera vez Git te pedirá iniciar sesión en GitHub en el navegador.)

### Paso 2 — Crear el servicio en Render
1. Entra a https://render.com y regístrate con tu cuenta de GitHub (gratis).
2. Clic en **New +** → **Blueprint**.
3. Selecciona tu repositorio. Render leerá el archivo **`render.yaml`** y
   configurará todo solo (plan **Free**, comando `python server.py`).
4. Clic en **Apply** / **Create**. En 1–2 minutos estará desplegado.
5. Tu app quedará en `https://predictor-mundial-2026.onrender.com` 🎉

> Si prefieres no usar el Blueprint: **New + → Web Service**, eliges el repo, y
> pones Build Command `pip install -r requirements.txt` y Start Command
> `python server.py`. Runtime: Python. Plan: Free.

### Paso 3 (opcional) — Claves para mejores datos
En el panel de Render → tu servicio → **Environment** → Add Environment Variable:
- `FOOTBALL_DATA_KEY` = tu clave de football-data.org
- `ODDS_API_KEY` = tu clave de the-odds-api.com

No son obligatorias: sin ellas usa ESPN (gratis) igual.

### ⚠️ Nota del plan gratuito de Render
El servicio **se duerme tras 15 min sin visitas** y tarda ~30–60 s en despertar
en la siguiente visita (normal en planes gratis). Al despertar, vuelve a cargar
los datos en vivo automáticamente. Para mantenerlo despierto puedes usar
https://uptimerobot.com (gratis) haciendo ping a tu URL cada 5 min.

---

## Alternativas gratuitas

| Plataforma | Ventaja | Nota |
|---|---|---|
| **Replit** (replit.com) | No necesita GitHub: subes los archivos y le das *Run* | URL pública mientras el repl corre; "Deployments" persistentes pueden requerir plan pago |
| **Railway** (railway.app) | Despliegue muy simple desde GitHub | Da ~$5 de crédito gratis/mes |
| **Koyeb** (koyeb.com) | Tier gratis, desde GitHub o Docker | Similar a Render |
| **PythonAnywhere** | Popular para estudiantes | Usa modelo WSGI; este servidor `http.server` con hilo de fondo encaja mejor en Render |

Todas usan el mismo principio: el servidor ya lee `PORT` del entorno, así que
funciona sin cambios.

---

## Local (sin desplegar)
```bash
python server.py   # -> http://localhost:8000
```
