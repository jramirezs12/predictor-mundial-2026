# ⚽ Predictor Mundial 2026

Programa de predicción de **todos los partidos y estadísticas** del Mundial 2026
(USA · Canadá · México). Combina los cuatro enfoques de la investigación del
proyecto en un solo motor y los muestra en un **dashboard web interactivo**.

> Datos reales actuales: sorteo oficial (12 grupos / 48 selecciones), ratings
> ELO (eloratings.net, jun 2026), ranking FIFA, 16 estadios sede y plantillas
> 2025/26 de los principales contendientes.

## 🚀 Cómo ejecutarlo

**No requiere instalar nada** (solo Python 3.10+). Sin `pip install`, sin
dependencias externas — usa únicamente la librería estándar.

```bash
cd C:\predictor
python server.py
```

Se abre automáticamente en **http://localhost:8000**

## 🔴 Modo en vivo (tiempo real)

La app se actualiza sola: cada ~3 minutos obtiene los resultados y cuotas reales
del Mundial y recalcula **todo** (ELO → predicciones → clasificaciones → valor).
La barra superior muestra el estado en vivo y la hora de la última actualización.

**Funciona sin configurar nada:** usa la API pública de **ESPN** (sin clave),
que entrega resultados *y* cuotas reales (DraftKings). Tras cada partido:
- el ELO de los equipos se recalcula según el resultado,
- las clasificaciones de grupo pasan a ser **reales** (marcadas con ● REAL),
- las predicciones de los partidos restantes usan la forma real del torneo,
- el escáner de valor se actualiza con las nuevas cuotas.

**Claves opcionales** (mejoran cobertura/fiabilidad) — en `config.py` o variables
de entorno:
- `FOOTBALL_DATA_KEY` → resultados desde football-data.org (gratis).
- `ODDS_API_KEY` → cuotas desde The Odds API (gratis, 500 req/mes).

Si no hay internet, la app cae con elegancia a los ratings base (no se rompe).

## 🧠 El modelo (stack combinado)

Igual que los modelos de Goldman Sachs / FiveThirtyEight, combina varios enfoques:

| Paso | Enfoque | Archivo |
|------|---------|---------|
| 1 | **ELO Rating** — fuerza relativa de cada selección | `engine/elo.py` |
| 2 | **Goles esperados (λ)** — ELO + promedio goleador → ataque/defensa | `engine/match_model.py` |
| 3 | **Poisson + Dixon-Coles** — matriz de marcadores, corrige marcadores bajos | `engine/poisson.py` |
| 4 | **Monte Carlo** — simula el torneo completo 10.000+ veces | `engine/monte_carlo.py` |

### Fórmulas clave
- **Poisson:** `P(X=k) = e^(-λ) · λ^k / k!`
- **Dixon-Coles:** corrige `0-0, 1-0, 0-1, 1-1` con el parámetro `ρ = -0.13`
- **ELO:** `P(gana A) = 1 / (1 + 10^(-Δ/400))`

## 📊 Qué predice (todas las estadísticas)

Para **cada partido**:
- **Resultado 1X2** (gana local / empate / gana visitante)
- **Goles esperados (xG)** de cada equipo y marcadores más probables
- **Mercados de goles:** Over/Under 1.5, 2.5, 3.5 · Ambos anotan (BTTS)
- **Doble oportunidad** (1X, 12, X2) y **portería a cero**
- **Hándicap asiático** (-1 / +1)
- **Tarjetas:** amarillas esperadas por equipo, prob. de roja, Over 3.5 amarillas
- **Córners** esperados y Over 9.5
- **Goleadores:** probabilidad de que cada jugador clave marque

Para el **torneo completo** (Monte Carlo):
- Probabilidad de cada selección de llegar a octavos, cuartos, semis, final y de
  ser **campeón**.

### 🔥 Apuestas recomendadas (pestaña "Recomendadas")
Escanea **todos** los partidos próximos con cuotas reales y compara el modelo
contra el mercado **sin su margen** (de-vig). Clasifica cada apuesta de valor:
- **Plausible (edge 2–12%)** → recomendada, con stake de Kelly.
- **Discrepancia alta (>12%)** → se muestra aparte como **NO fiable**. Cuando un
  modelo simple cree ver un "chollo" enorme contra una casa profesional, casi
  siempre es que el modelo está mal (ELO desactualizado, no sabe de lesiones),
  no que la casa regale dinero. Honestidad ante todo.

### 💰 Análisis de valor (pestaña "Valor")
La forma matemáticamente correcta de buscar ganancia: comparar la probabilidad
del modelo con la cuota de la casa.
- **Valor esperado (EV):** `EV = p·cuota − 1`. Si es positivo, la casa subestima
  el resultado → **apuesta de valor**.
- **Criterio de Kelly:** fracción óptima de la banca a apostar,
  `f* = (p·cuota − 1)/(cuota − 1)` (se recomienda Kelly fraccionado ¼ o ½).
- **Simulador de banca (Monte Carlo):** dada tu cartera de apuestas de valor,
  simula 10.000 escenarios y reporta la mediana, percentiles, probabilidad de
  ganancia y **probabilidad de alcanzar tu objetivo** (p. ej. 50k → 4M).
  *Spoiler honesto: incluso con value betting + Kelly, multiplicar por 80x es
  extremadamente improbable. El modelo te lo demuestra con números.*

## 🗂️ Estructura

```
predictor/
├── server.py            # Servidor web (librería estándar, sin deps)
├── api.py               # Une motor + datos
├── engine/              # Motor de predicción
│   ├── elo.py
│   ├── poisson.py       # Poisson + Dixon-Coles + mercados
│   ├── match_model.py   # λ y predicción completa del partido
│   ├── monte_carlo.py   # Simulación del torneo
│   └── value.py         # Valor esperado, Kelly, de-vig y simulación de banca
├── live/                # Modo en vivo (tiempo real)
│   ├── sources.py       # Fetchers: ESPN (sin clave), football-data, The Odds API
│   ├── state.py         # Recalcula ELO + clasificaciones desde resultados
│   └── refresh.py       # Orquesta la actualización y elige fuentes
├── config.py            # Claves de API (opcionales) y ajustes en vivo
├── data/                # Datos reales del Mundial 2026
│   ├── teams.py         # 48 selecciones, grupos, ELO, ranking FIFA
│   ├── players.py       # Jugadores clave (goal_share)
│   ├── stadiums.py      # 16 estadios sede
│   └── schedule.py      # Calendario + bracket
├── web/                 # Dashboard (HTML/CSS/JS)
├── test_models.py       # Test del motor (predicción, EV, Kelly)
└── test_live.py         # Test del modo en vivo (parser, ELO, escáner)
```

## 🔄 Actualizar los datos

Todo está centralizado y es fácil de actualizar (también vía API/scraper):
- **ELO / ranking:** edita `data/teams.py` → `TEAM_DATA`.
- **Grupos:** `data/teams.py` → `GROUP_DRAW`.
- **Jugadores:** `data/players.py` → `KEY_PLAYERS` (con su `goal_share`).
- **Estadios:** `data/stadiums.py`.

Si añades estadísticas reales de goles a un equipo (`gf_avg`, `ga_avg` en
`TEAM_DATA`), el modelo las mezcla automáticamente con el ELO (35% peso datos).

## 🌐 API JSON

| Endpoint | Devuelve |
|----------|----------|
| `/api/teams` | 48 selecciones (ELO, grupo, ranking) |
| `/api/groups` | Los 12 grupos |
| `/api/group-stage` | Predicción de los 72 partidos de grupos |
| `/api/match?home=X&away=Y` | Predicción completa de un partido |
| `/api/simulate?n=10000` | Probabilidades del torneo (Monte Carlo) |
| `/api/stadiums` · `/api/schedule` | Estadios y calendario |
| `/api/markets?home=X&away=Y` | Mercados de un partido con prob. modelo + cuota justa |
| `POST /api/value` | Análisis EV + Kelly de una lista de apuestas |
| `POST /api/portfolio-sim` | Simulación de banca (50k→objetivo) con Kelly |
| `/api/recommendations` | Apuestas recomendadas (valor plausible) del torneo |
| `/api/value/scan` | Escaneo de valor de todos los partidos (de-vig + fiabilidad) |
| `/api/live/status` | Estado en vivo: última actualización, jugados, cambios de ELO |
| `/api/live/refresh` | Fuerza una actualización de resultados/cuotas |
| `/api/live/standings` | Clasificaciones reales de grupo según partidos jugados |

## ⚠️ Límites del modelo

La precisión típica de los mejores modelos ronda **55-65% en 1X2** y **~72% en
Over/Under 2.5**. Factores como lesiones de última hora, clima y arbitraje
desequilibran cualquier modelo — por eso ninguno llega al 100%.

---
*Proyecto académico. Datos verificados en junio 2026 de fuentes públicas
(Wikipedia, eloratings.net, Sofascore, ESPN).*
