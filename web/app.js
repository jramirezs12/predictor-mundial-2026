"use strict";

const API = "/api";
const pct = (x) => (x * 100).toFixed(1) + "%";
const fmt = (x) => (x * 100).toFixed(0);

async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error("HTTP " + r.status);
  return r.json();
}

/* ---------- Tabs ---------- */
const loaded = {};
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    const id = tab.dataset.tab;
    document.getElementById(id).classList.add("active");
    loadTab(id);
  });
});

function loadTab(id) {
  if (loaded[id]) return;
  loaded[id] = true;
  ({
    sim: loadSim,
    recommend: loadRecommend,
    groups: loadGroups,
    predictor: loadPredictor,
    value: loadValue,
    schedule: loadSchedule,
    teams: loadTeams,
    stadiums: loadStadiums,
    about: () => {},
  })[id]?.();
}

/* ---------- Simulación / favoritos ---------- */
async function loadSim() {
  await runSim();
}
document.getElementById("run-sim").addEventListener("click", runSim);

async function runSim() {
  const n = document.getElementById("sim-n").value;
  const btn = document.getElementById("run-sim");
  const hint = document.getElementById("sim-hint");
  const tbody = document.querySelector("#sim-table tbody");
  btn.disabled = true;
  hint.innerHTML = `<span class="spinner"></span>Simulando ${(+n).toLocaleString("es")} torneos...`;
  tbody.innerHTML = "";
  try {
    const data = await getJSON(`${API}/simulate?n=${n}`);
    const teams = await getJSON(`${API}/teams`);
    const eloMap = Object.fromEntries(teams.map((t) => [t.name, t]));
    const rows = Object.entries(data.probabilities);
    const maxChamp = Math.max(...rows.map(([, p]) => p.champion)) || 1;
    tbody.innerHTML = rows
      .map(([name, p], i) => {
        const t = eloMap[name] || {};
        const host = t.is_host ? '<span class="host-badge">SEDE</span>' : "";
        const bar = (v, cls = "") =>
          `<td class="pcell"><div class="pbar ${cls}" style="width:${v * 100}%"></div><span>${pct(v)}</span></td>`;
        return `<tr>
          <td class="rank-cell">${i + 1}</td>
          <td class="team-cell">${name}${host}</td>
          <td class="rank-cell">${t.elo ?? ""}</td>
          ${bar(p.r16)}${bar(p.qf)}${bar(p.sf)}${bar(p.final)}
          <td class="pcell"><div class="pbar champ-bar" style="width:${(p.champion / maxChamp) * 100}%"></div><span><b>${pct(p.champion)}</b></span></td>
        </tr>`;
      })
      .join("");
    hint.textContent = `${(+n).toLocaleString("es")} torneos simulados con Monte Carlo. Las barras muestran la probabilidad de alcanzar cada ronda.`;
  } catch (e) {
    hint.textContent = "Error: " + e.message;
  } finally {
    btn.disabled = false;
  }
}

/* ---------- Grupos ---------- */
async function loadGroups() {
  const grid = document.getElementById("groups-grid");
  grid.innerHTML = '<div class="loading"><span class="spinner"></span>Calculando predicciones de grupos...</div>';
  const [groups, gs, status, standings] = await Promise.all([
    getJSON(`${API}/groups`),
    getJSON(`${API}/group-stage`),
    getJSON(`${API}/live/status`).catch(() => ({ has_live_data: false })),
    getJSON(`${API}/live/standings`).catch(() => ({})),
  ]);
  const live = status.has_live_data;
  grid.innerHTML = Object.entries(groups)
    .map(([g, teams]) => {
      let standing;
      if (live && standings[g]) {
        // Clasificación REAL según partidos jugados.
        standing = standings[g]
          .map(
            (r, i) =>
              `<div class="group-team"><span>${i + 1}. ${r.team}${r.played ? "" : ""}</span><span class="elo">${r.pts} pts · ${r.played}PJ · ${r.gd >= 0 ? "+" : ""}${r.gd}</span></div>`
          )
          .join("");
      } else {
        standing = teams
          .map(
            (t) =>
              `<div class="group-team"><span>${t.name}${t.is_host ? '<span class="host-badge">SEDE</span>' : ""}</span><span class="elo">ELO ${t.elo}</span></div>`
          )
          .join("");
      }
      const matches = (gs[g] || [])
        .map((m, idx) => matchRow(m, g, idx))
        .join("");
      const tag = live && standings[g] ? '<span style="font-size:10px;color:#3ddc84;font-weight:600;margin-left:8px">● REAL</span>' : "";
      return `<div class="group-card">
        <h3>Grupo ${g}${tag}</h3>
        <div class="group-standing">${standing}</div>
        <div class="group-matches">${matches}</div>
      </div>`;
    })
    .join("");
  grid.querySelectorAll(".gm").forEach((el) => {
    el.addEventListener("click", () =>
      openMatchModal(el.dataset.home, el.dataset.away, "group")
    );
  });
}

function matchRow(m, g, idx) {
  const r = m.result_1x2;
  const win = Math.max(r.home_win, r.draw, r.away_win);
  const chip = (v, lbl) =>
    `<span class="chip ${v === win ? "win" : ""}">${lbl} ${fmt(v)}</span>`;
  return `<div class="gm" data-home="${m.home_team}" data-away="${m.away_team}">
    <span class="teams">${m.home_team} <span style="color:var(--muted)">vs</span> ${m.away_team}</span>
    <span class="odds">${chip(r.home_win, "1")}${chip(r.draw, "X")}${chip(r.away_win, "2")}</span>
  </div>`;
}

/* ---------- Predictor ---------- */
async function loadPredictor() {
  const teams = await getJSON(`${API}/teams`);
  const opts = teams
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((t) => `<option value="${t.name}">${t.name} (ELO ${t.elo})</option>`)
    .join("");
  const hs = document.getElementById("home-select");
  const as = document.getElementById("away-select");
  hs.innerHTML = opts;
  as.innerHTML = opts;
  hs.value = "Spain";
  as.value = "France";
  document.getElementById("predict-btn").addEventListener("click", async () => {
    const home = hs.value, away = as.value;
    const stage = document.getElementById("stage-select").value;
    if (home === away) {
      document.getElementById("match-result").innerHTML =
        '<p class="hint">Elige dos selecciones distintas.</p>';
      return;
    }
    const m = await getJSON(`${API}/match?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}&stage=${stage}`);
    document.getElementById("match-result").innerHTML = renderPrediction(m);
  });
}

/* ---------- Render de una predicción completa ---------- */
function renderPrediction(m) {
  const r = m.result_1x2;
  const top = m.most_likely_scores[0];
  const lead = (a, b, c) => (a >= b && a >= c ? "lead" : "");
  const eg = m.expected_goals;

  const market = (lbl, v) =>
    `<div class="stat-row"><span class="k">${lbl}</span><span class="v">${pct(v)}</span></div>`;

  const players = (arr, side) =>
    arr.length
      ? arr
          .map(
            (p) =>
              `<div class="player-row"><div><div class="pname">${p.name}</div><div class="pmeta">${p.position} · ${p.club}</div></div><div class="pscore">${pct(p.prob_to_score)}</div></div>`
          )
          .join("")
      : '<p class="pmeta" style="color:var(--muted)">Sin datos de jugadores para esta selección.</p>';

  const gm = m.goals_markets;
  const c = m.cards, co = m.corners;

  return `<div class="pred">
    <div class="pred-hero">
      <div class="matchup">${m.home_team} vs ${m.away_team}</div>
      <div class="score-big">${top.score.replace("-", " – ")}</div>
      <div class="xg">Marcador más probable (${pct(top.prob)}) · Goles esperados ${eg.home} – ${eg.away}</div>
    </div>

    <div class="split3">
      <div class="outcome ${lead(r.home_win, r.draw, r.away_win)}"><div class="lbl">Gana ${m.home_team}</div><div class="val">${pct(r.home_win)}</div></div>
      <div class="outcome ${lead(r.draw, r.home_win, r.away_win)}"><div class="lbl">Empate</div><div class="val">${pct(r.draw)}</div></div>
      <div class="outcome ${lead(r.away_win, r.home_win, r.draw)}"><div class="lbl">Gana ${m.away_team}</div><div class="val">${pct(r.away_win)}</div></div>
    </div>

    <div class="cards-grid">
      <div class="stat-card">
        <h4>Mercado de goles</h4>
        ${market("Over 1.5", gm.over_1_5)}
        ${market("Over 2.5", gm.over_2_5)}
        ${market("Over 3.5", gm.over_3_5)}
        ${market("Ambos anotan (BTTS)", gm.btts_yes)}
      </div>
      <div class="stat-card">
        <h4>Doble oportunidad</h4>
        ${market("1X (local o empate)", m.double_chance["1X"])}
        ${market("12 (no empate)", m.double_chance["12"])}
        ${market("X2 (empate o visita)", m.double_chance["X2"])}
        ${market(m.home_team + " deja portería a 0", m.clean_sheet.home)}
        ${market(m.away_team + " deja portería a 0", m.clean_sheet.away)}
      </div>
      <div class="stat-card">
        <h4>Marcadores probables</h4>
        ${m.most_likely_scores
          .map(
            (s) =>
              `<div class="stat-row"><span class="k">${s.score.replace("-", " – ")}</span><span class="v">${pct(s.prob)}</span></div>`
          )
          .join("")}
      </div>
      <div class="stat-card">
        <h4>Tarjetas</h4>
        <div class="stat-row"><span class="k">Amarillas (total esperadas)</span><span class="v">${c.yellow_total}</span></div>
        <div class="stat-row"><span class="k">${m.home_team} / ${m.away_team}</span><span class="v">${c.yellow_home} / ${c.yellow_away}</span></div>
        <div class="stat-row"><span class="k">Prob. de roja en el partido</span><span class="v">${pct(c.prob_any_red)}</span></div>
        <div class="stat-row"><span class="k">Over 3.5 amarillas</span><span class="v">${pct(c.prob_over_3_5_yellows)}</span></div>
      </div>
      <div class="stat-card">
        <h4>Córners</h4>
        <div class="stat-row"><span class="k">Total esperado</span><span class="v">${co.corners_total}</span></div>
        <div class="stat-row"><span class="k">${m.home_team} / ${m.away_team}</span><span class="v">${co.corners_home} / ${co.corners_away}</span></div>
        <div class="stat-row"><span class="k">Over 9.5 córners</span><span class="v">${pct(co.prob_over_9_5_corners)}</span></div>
      </div>
      <div class="stat-card">
        <h4>Hándicap asiático</h4>
        ${market(m.home_team + " -1", m.asian_handicap["home_-1"])}
        ${market("Empate hándicap (push)", m.asian_handicap.push)}
        ${market(m.away_team + " +1", m.asian_handicap["away_+1"])}
      </div>
      <div class="stat-card">
        <h4>Goleadores · ${m.home_team}</h4>
        ${players(m.players.home, "home")}
      </div>
      <div class="stat-card">
        <h4>Goleadores · ${m.away_team}</h4>
        ${players(m.players.away, "away")}
      </div>
    </div>
  </div>`;
}

/* ---------- Modal ---------- */
async function openMatchModal(home, away, stage) {
  const modal = document.getElementById("modal");
  const content = document.getElementById("modal-content");
  content.innerHTML = '<div class="loading"><span class="spinner"></span>Calculando...</div>';
  modal.classList.remove("hidden");
  const m = await getJSON(`${API}/match?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}&stage=${stage}`);
  content.innerHTML = renderPrediction(m);
}
document.getElementById("modal-close").addEventListener("click", () =>
  document.getElementById("modal").classList.add("hidden")
);
document.getElementById("modal").addEventListener("click", (e) => {
  if (e.target.id === "modal") document.getElementById("modal").classList.add("hidden");
});

/* ---------- Valor / EV / Kelly ---------- */
const portfolio = [];
const money = (x) => Math.round(x).toLocaleString("es") + " $";

function kellyMult() { return parseFloat(document.getElementById("kelly-mult").value); }
function bankroll() { return Math.max(1, parseFloat(document.getElementById("bankroll").value) || 0); }

async function loadValue() {
  const teams = await getJSON(`${API}/teams`);
  const opts = teams
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((t) => `<option value="${t.name}">${t.name}</option>`)
    .join("");
  const hs = document.getElementById("v-home");
  const as = document.getElementById("v-away");
  hs.innerHTML = opts; as.innerHTML = opts;
  hs.value = "Argentina"; as.value = "Jordan";
  document.getElementById("v-load").addEventListener("click", loadMarkets);
  document.getElementById("sim-bankroll").addEventListener("click", simulateBankroll);
  // Recalcular stakes si cambia banca o Kelly.
  ["bankroll", "kelly-mult"].forEach((id) =>
    document.getElementById(id).addEventListener("input", () => {
      document.querySelectorAll("#value-table .odds-input").forEach((inp) => recalcRow(inp));
    })
  );
  await loadMarkets();
}

async function loadMarkets() {
  const home = document.getElementById("v-home").value;
  const away = document.getElementById("v-away").value;
  const stage = document.getElementById("v-stage").value;
  const wrap = document.getElementById("value-table-wrap");
  if (home === away) { wrap.innerHTML = '<p class="hint">Elige dos selecciones distintas.</p>'; return; }
  wrap.innerHTML = '<div class="loading"><span class="spinner"></span>Cargando mercados...</div>';
  const data = await getJSON(`${API}/markets?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}&stage=${stage}`);
  const rows = data.markets
    .map(
      (m) => `<tr data-key="${m.key}" data-label="${m.label}" data-prob="${m.model_prob}">
        <td>${m.label}</td>
        <td>${pct(m.model_prob)}</td>
        <td>${m.fair_odds}</td>
        <td><input class="odds-input" type="number" step="0.01" min="1.01" placeholder="cuota" value="${suggestBookOdds(m.fair_odds)}"></td>
        <td class="c-implied">—</td>
        <td class="c-edge">—</td>
        <td class="c-ev">—</td>
        <td class="c-kelly">—</td>
        <td><button class="add-btn" disabled>+ Añadir</button></td>
      </tr>`
    )
    .join("");
  wrap.innerHTML = `<div class="table-wrap" id="value-table">
    <table>
      <thead><tr>
        <th>Mercado</th><th>Prob. modelo</th><th>Cuota justa</th>
        <th>Cuota casa</th><th>Implícita</th><th>Ventaja</th><th>EV</th><th>Stake Kelly</th><th></th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>
  </div>
  <p class="hint" style="margin-top:12px">Pre-rellenado con la <b>cuota justa</b> del modelo (EV ≈ 0%, sin valor). Ingresa la cuota <b>real</b> de tu casa: si es <b>más alta</b> que la justa, aparece el valor en <span class="ev-pos">verde</span> y podrás añadirla a la cartera. Solo se añade lo que tenga <span class="ev-pos">EV positivo</span>.</p>`;

  wrap.querySelectorAll(".odds-input").forEach((inp) => {
    inp.addEventListener("input", () => recalcRow(inp));
    recalcRow(inp);
  });
  wrap.querySelectorAll(".add-btn").forEach((btn) => {
    btn.addEventListener("click", () => addToPortfolio(btn.closest("tr"), home, away));
  });
}

// Pre-rellena con la cuota justa (EV neutro): el usuario la reemplaza por la real.
function suggestBookOdds(fair) { return Number(fair).toFixed(2); }

function recalcRow(input) {
  const tr = input.closest("tr");
  const p = parseFloat(tr.dataset.prob);
  const o = parseFloat(input.value);
  const cells = {
    implied: tr.querySelector(".c-implied"),
    edge: tr.querySelector(".c-edge"),
    ev: tr.querySelector(".c-ev"),
    kelly: tr.querySelector(".c-kelly"),
  };
  const btn = tr.querySelector(".add-btn");
  if (!o || o <= 1) {
    Object.values(cells).forEach((c) => (c.textContent = "—"));
    tr.classList.remove("row-value"); btn.disabled = true; return;
  }
  const implied = 1 / o;
  const edge = p - implied;
  const ev = p * o - 1;
  const kFull = Math.max(0, (p * o - 1) / (o - 1));
  const stake = bankroll() * kFull * kellyMult();
  cells.implied.textContent = pct(implied);
  cells.edge.textContent = (edge >= 0 ? "+" : "") + (edge * 100).toFixed(1) + "%";
  cells.ev.innerHTML = `<span class="${ev > 0 ? "ev-pos" : "ev-neg"}">${(ev >= 0 ? "+" : "") + (ev * 100).toFixed(1)}%</span>`;
  cells.kelly.textContent = ev > 0 ? money(stake) : "—";
  tr.classList.toggle("row-value", ev > 0);
  btn.disabled = !(ev > 0);
}

function pushBet(bet) {
  // Evita duplicados exactos (mismo partido + mercado).
  if (portfolio.some((b) => b.match === bet.match && b.market === bet.market)) return false;
  portfolio.push(bet);
  renderPortfolio();
  return true;
}

function addToPortfolio(tr, home, away) {
  pushBet({
    match: `${home} vs ${away}`,
    market: tr.dataset.key,
    label: tr.dataset.label,
    model_prob: parseFloat(tr.dataset.prob),
    book_odds: parseFloat(tr.querySelector(".odds-input").value),
  });
}

function renderPortfolio() {
  const box = document.getElementById("portfolio");
  const list = document.getElementById("portfolio-list");
  if (!portfolio.length) { box.classList.add("hidden"); return; }
  box.classList.remove("hidden");
  list.innerHTML = portfolio
    .map((b, i) => {
      const ev = b.model_prob * b.book_odds - 1;
      return `<div class="pf-bet">
        <div><div class="pf-label">${b.label}</div><div class="pf-meta">${b.match}</div></div>
        <div class="pf-meta">cuota ${b.book_odds}</div>
        <div class="pf-ev">EV +${(ev * 100).toFixed(1)}%</div>
        <button class="pf-remove" data-i="${i}">✕</button>
      </div>`;
    })
    .join("");
  list.querySelectorAll(".pf-remove").forEach((btn) =>
    btn.addEventListener("click", () => { portfolio.splice(+btn.dataset.i, 1); renderPortfolio(); document.getElementById("portfolio-result").innerHTML = ""; })
  );
}

async function simulateBankroll() {
  const btn = document.getElementById("sim-bankroll");
  const res = document.getElementById("portfolio-result");
  if (!portfolio.length) return;
  btn.disabled = true;
  res.innerHTML = '<div class="loading"><span class="spinner"></span>Simulando 10.000 escenarios de banca...</div>';
  try {
    const r = await fetch(`${API}/portfolio-sim`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        bets: portfolio,
        start: bankroll(),
        target: parseFloat(document.getElementById("target").value) || 4000000,
        kelly_multiplier: kellyMult(),
        n: 10000,
      }),
    });
    const d = await r.json();
    if (d.error) { res.innerHTML = `<p class="hint">Error: ${d.error}</p>`; return; }
    res.innerHTML = renderSim(d);
  } finally {
    btn.disabled = false;
  }
}

function renderSim(d) {
  const cols = [
    ["Peor 10%", d.p10], ["25%", d.p25], ["Mediana", d.median], ["75%", d.p75], ["Mejor 10%", d.p90],
  ];
  const max = Math.max(...cols.map((c) => c[1]), 1);
  const bars = cols
    .map(([lbl, v]) => `<div class="col"><div class="amt">${money(v)}</div><div class="bar" style="height:${Math.max(4, (v / max) * 70)}px"></div><div class="lbl">${lbl}</div></div>`)
    .join("");
  return `<div class="sim-result">
    <div class="sim-headline">
      <div class="big">${pct(d.prob_reach_target)} de alcanzar ${money(d.target)}</div>
      <div class="sub">Partiendo de ${money(d.start)} con ${d.n_bets} apuestas de valor · ${d.n_sims.toLocaleString("es")} simulaciones · Kelly fraccionado</div>
    </div>
    <div class="sim-stats">
      <div class="sim-stat"><div class="k">Banca final mediana</div><div class="v">${money(d.median)}</div></div>
      <div class="sim-stat"><div class="k">Prob. de ganancia</div><div class="v">${pct(d.prob_profit)}</div></div>
      <div class="sim-stat"><div class="k">Prob. alcanzar objetivo</div><div class="v">${pct(d.prob_reach_target)}</div></div>
      <div class="sim-stat"><div class="k">Prob. de quiebra</div><div class="v">${pct(d.prob_bust)}</div></div>
    </div>
    <div class="sim-dist">${bars}</div>
    <p class="hint">Distribución de la banca final según el percentil. Kelly maximiza el crecimiento a largo plazo, pero con pocas apuestas la varianza es enorme: el objetivo de 80x sigue siendo poco probable. Apostar siempre implica riesgo de pérdida.</p>
  </div>`;
}

/* ---------- Calendario ---------- */
async function loadSchedule() {
  const list = document.getElementById("schedule-list");
  list.innerHTML = '<div class="loading"><span class="spinner"></span>Cargando calendario...</div>';
  const sched = await getJSON(`${API}/schedule`);
  const byGroup = {};
  sched.forEach((m) => {
    (byGroup[m.group] = byGroup[m.group] || []).push(m);
  });
  list.innerHTML = Object.entries(byGroup)
    .map(([g, matches]) => {
      const rows = matches
        .map((m) => {
          const r = m.prediction?.result_1x2;
          const odds = r
            ? `<span class="odds"><span class="chip">1 ${fmt(r.home_win)}</span><span class="chip">X ${fmt(r.draw)}</span><span class="chip">2 ${fmt(r.away_win)}</span></span>`
            : "";
          return `<div class="sched-row" data-home="${m.home}" data-away="${m.away}">
            <span class="md">J${m.matchday}</span>
            <span class="matchup">${m.home} vs ${m.away}</span>
            <span class="venue">${m.venue}</span>
            ${odds}
          </div>`;
        })
        .join("");
      return `<div class="sched-group"><h3>Grupo ${g} · ${matches[0].window}</h3>${rows}</div>`;
    })
    .join("");
  list.querySelectorAll(".sched-row").forEach((el) => {
    el.addEventListener("click", () =>
      openMatchModal(el.dataset.home, el.dataset.away, "group")
    );
  });
}

/* ---------- Equipos ---------- */
async function loadTeams() {
  const teams = await getJSON(`${API}/teams`);
  const tbody = document.querySelector("#teams-table tbody");
  tbody.innerHTML = teams
    .map(
      (t, i) =>
        `<tr>
          <td class="rank-cell">${i + 1}</td>
          <td class="team-cell">${t.name}${t.is_host ? '<span class="host-badge">SEDE</span>' : ""}</td>
          <td>${t.group}</td>
          <td style="font-variant-numeric:tabular-nums;font-weight:600">${t.elo}</td>
          <td class="rank-cell">${t.fifa_rank ?? "—"}</td>
          <td style="color:var(--muted)">${t.confederation}</td>
        </tr>`
    )
    .join("");
}

/* ---------- Estadios ---------- */
async function loadStadiums() {
  const stadiums = await getJSON(`${API}/stadiums`);
  document.getElementById("stadiums-grid").innerHTML = stadiums
    .map(
      (s) =>
        `<div class="stadium-card">
          <h4>${s.name}</h4>
          <div class="loc">${s.city}, ${s.country}</div>
          <div class="cap">Capacidad: ${s.capacity.toLocaleString("es")}</div>
          ${s.note ? `<div class="note">${s.note}</div>` : ""}
        </div>`
    )
    .join("");
}

/* ---------- Recomendadas (escáner de torneo) ---------- */
function fmtKickoff(iso) {
  if (!iso) return "fecha por confirmar";
  try {
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    return d.toLocaleString("es", {
      weekday: "short", day: "numeric", month: "short",
      hour: "2-digit", minute: "2-digit",
    });
  } catch (e) {
    return iso;
  }
}

async function loadRecommend() {
  await renderRecommend();
  document.getElementById("rescan-btn").addEventListener("click", async () => {
    await triggerRefresh();
    await renderRecommend();
  });
}

async function renderRecommend() {
  const box = document.getElementById("recommend-content");
  box.innerHTML = '<div class="loading"><span class="spinner"></span>Escaneando el torneo…</div>';
  const [rec, scan] = await Promise.all([
    getJSON(`${API}/recommendations?top=12`),
    getJSON(`${API}/value/scan`),
  ]);

  if (!scan.has_odds) {
    let html = `<div class="no-odds">⏳ Aún no hay cuotas de partidos próximos cargadas (o el torneo aún no las publica). Mientras tanto, estos son los <b>picks de mayor convicción del modelo</b> (no son "valor", solo las predicciones más seguras):</div><div class="rec-cards">`;
    html += (rec.bets || [])
      .map(
        (b) => `<div class="rec-card" style="border-color:var(--border)">
          <div class="rc-match">${b.match}</div>
          <div class="rc-bet">${b.label}</div>
          <div class="rc-ev" style="color:var(--teal-bright)">${pct(b.model_prob)}</div>
          <div class="rc-row"><span>Cuota justa</span><b>${b.fair_odds}</b></div>
        </div>`
      )
      .join("");
    html += "</div>";
    box.innerHTML = html;
    return;
  }

  // Sección destacada: recomendada de hoy (o la próxima).
  const td = rec.today || {};
  let todayHtml = "";
  if (td.bet) {
    const b = td.bet;
    const heading = td.when === "hoy"
      ? `⭐ Recomendada de hoy${td.matches_today ? ` · ${td.matches_today} partido(s) hoy` : ""}`
      : "⏭️ Próxima recomendada (no hay partidos con valor hoy)";
    todayHtml = `<div class="today-hero">
      <div class="th-label">${heading}</div>
      <div class="th-bet">${b.label}</div>
      <div class="th-match">${b.match} · ${fmtKickoff(b.date)}</div>
      <div class="th-stats">
        <div><span>EV</span><b>${(b.ev * 100).toFixed(0)}%</b></div>
        <div><span>Edge</span><b>+${(b.edge * 100).toFixed(1)}%</b></div>
        <div><span>Modelo</span><b>${pct(b.model_prob)}</b></div>
        <div><span>Mercado</span><b>${pct(b.market_prob)}</b></div>
        <div><span>Cuota</span><b>${b.book_odds}</b></div>
      </div>
    </div>`;
  }

  const cards = (rec.bets || [])
    .map(
      (b, i) => `<div class="rec-card">
        <div class="rc-kick">🕐 ${fmtKickoff(b.date)}</div>
        <div class="rc-match">${b.match} · ${b.provider || ""}</div>
        <div class="rc-bet">${b.label}</div>
        <div class="rc-ev">EV ${(b.ev * 100).toFixed(0)}%</div>
        <div class="rc-row"><span>Modelo</span><b>${pct(b.model_prob)}</b></div>
        <div class="rc-row"><span>Mercado (sin margen)</span><b>${pct(b.market_prob)}</b></div>
        <div class="rc-row"><span>Edge</span><b>+${(b.edge * 100).toFixed(1)}%</b></div>
        <div class="rc-row"><span>Cuota</span><b>${b.book_odds}</b></div>
        <button class="add-btn rc-add" data-i="${i}">+ Añadir a la cartera</button>
      </div>`
    )
    .join("");

  const discRows = (scan.high_discrepancy || [])
    .slice(0, 20)
    .map(
      (b) => `<div class="sched-row" style="grid-template-columns:1fr auto auto auto">
        <span class="matchup">${b.label}</span>
        <span class="pf-meta">${b.match}</span>
        <span class="pf-meta">modelo ${pct(b.model_prob)} vs mercado ${pct(b.market_prob)}</span>
        <span class="pf-ev" style="color:#e07a7a">edge +${(b.edge * 100).toFixed(0)}%</span>
      </div>`
    )
    .join("");

  box.innerHTML = `
    ${todayHtml}
    <h3 style="font-size:15px;margin:6px 0 12px;color:var(--muted)">Todas las recomendadas · de la más próxima a la más lejana</h3>
    <div class="rec-cards">${cards || '<p class="hint">No se encontraron apuestas de valor plausibles ahora mismo. El mercado está eficiente.</p>'}</div>
    <p class="hint">${rec.note || ""} Fuente de cuotas: <b>${scan.source}</b>. Apuestas de valor plausibles encontradas: <b>${scan.count_plausible}</b>.</p>
    <details class="disc">
      <summary>⚠️ Ver ${scan.count_high} discrepancias altas descartadas (NO fiables)</summary>
      <div class="warn-box"><b>Por qué se descartan:</b> el modelo discrepa del mercado en más de 12 puntos. En apuestas, cuando tu modelo cree ver un "chollo" enorme contra una casa profesional, casi siempre es que el modelo está mal (ELO desactualizado, no sabe de lesiones), no que la casa regale dinero. Míralas con escepticismo.</div>
      ${discRows}
    </details>`;

  box.querySelectorAll(".rc-add").forEach((btn) => {
    btn.addEventListener("click", () => {
      const b = rec.bets[+btn.dataset.i];
      const ok = pushBet({
        match: b.match, market: b.market, label: b.label,
        model_prob: b.model_prob, book_odds: b.book_odds,
      });
      btn.textContent = ok ? "✓ Añadida (ver pestaña Valor)" : "Ya estaba en la cartera";
      btn.disabled = true;
    });
  });
}

/* ---------- Barra en vivo + auto-actualización ---------- */
let lastPlayed = -1;
async function pollLive() {
  try {
    const s = await getJSON(`${API}/live/status`);
    const dot = document.querySelector(".live-dot");
    const text = document.getElementById("live-text");
    if (s.has_live_data) {
      dot.classList.remove("off");
      const sum = s.summary || {};
      text.innerHTML = `<b>En vivo</b> · ${s.played} jugados de ${sum.total_matches || "?"} · ${sum.with_odds || 0} con cuotas · actualizado ${s.last_updated || ""} · fuente: ${sum.source_results || "—"}`;
      // Si se jugó un partido nuevo, recargar la pestaña activa.
      if (lastPlayed !== -1 && s.played !== lastPlayed) {
        const active = document.querySelector(".tab.active")?.dataset.tab;
        loaded[active] = false;
        loadTab(active);
      }
      lastPlayed = s.played;
    } else {
      dot.classList.add("off");
      text.textContent = "Datos en vivo no disponibles (sin conexión o torneo sin publicar). Usando ratings base.";
    }
  } catch (e) {
    document.querySelector(".live-dot")?.classList.add("off");
  }
}

async function triggerRefresh() {
  const btn = document.getElementById("live-refresh-btn");
  btn.classList.add("spinning");
  try {
    await getJSON(`${API}/live/refresh`);
    // invalidar caches de pestañas para que recarguen con datos frescos
    Object.keys(loaded).forEach((k) => (loaded[k] = false));
    await pollLive();
  } finally {
    btn.classList.remove("spinning");
  }
}

document.getElementById("live-refresh-btn").addEventListener("click", async () => {
  await triggerRefresh();
  const active = document.querySelector(".tab.active")?.dataset.tab;
  loadTab(active);
});

/* ---------- Init ---------- */
loadTab("sim");
pollLive();
setInterval(pollLive, 60000);
