/* Agentic Observability Insights: a static, hash-routed browser for the repository.
   Reads content.json (built by scripts/build_site.py). No framework. */
(() => {
"use strict";

const app = document.getElementById("app");
const lightbox = document.getElementById("lightbox");
let C = null;                         // content.json
const GH = () => `https://github.com/${C.repo.owner}/${C.repo.name}`;
const BRANCH = () => (C.repo.branch && C.repo.branch !== "HEAD" ? C.repo.branch : "main");

const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const h = (tag, attrs = {}, html = "") => {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  el.innerHTML = html;
  return el;
};
function md(text) {
  const raw = window.marked ? marked.parse(text || "") : `<pre>${esc(text)}</pre>`;
  const html = window.DOMPurify ? DOMPurify.sanitize(raw) : raw;
  const div = h("div", {class: "md"}, html);
  highlight(div);
  return div;
}
function highlight(root) {
  if (!window.hljs) return;
  root.querySelectorAll("pre code").forEach(c => { try { hljs.highlightElement(c); } catch (e) {} });
}
function codeBlock(text, lang) {
  const pre = h("pre");
  const code = h("code", lang ? {class: `language-${lang}`} : {});
  code.textContent = text;
  pre.appendChild(code);
  highlight(pre);
  return pre;
}
async function copy(text, btn) {
  try { await navigator.clipboard.writeText(text); btn.textContent = "Copied"; }
  catch (e) { btn.textContent = "Select and copy manually"; }
  setTimeout(() => (btn.textContent = btn.dataset.label || "Copy"), 1800);
}
const langOf = p => ({py: "python", yaml: "yaml", yml: "yaml", md: "markdown", json: "json", toml: "ini", txt: "plaintext"})[p.split(".").pop()] || "plaintext";

/* ---------- routing ---------- */
const routes = {
  "": home, compare, insights, carousels, architecture, skill, review, files,
};
function route() {
  const raw = location.hash.replace(/^#\/?/, "");
  const [page, ...rest] = raw.split("/");
  const arg = decodeURIComponent(rest.join("/"));
  const fn = routes[page] || notFound;
  closeLightbox();
  app.innerHTML = "";
  fn(arg);
  document.querySelectorAll("nav#nav a").forEach(a => {
    a.setAttribute("aria-current", a.getAttribute("href") === `#/${page}` ? "page" : "false");
  });
  document.getElementById("nav").classList.remove("open");
  document.getElementById("menu-btn").setAttribute("aria-expanded", "false");
  window.scrollTo(0, 0);
  app.focus({preventScroll: true});
}
function notFound() {
  app.append(h("div", {class: "page-head"}, `<h1>Page not found</h1><p class="lede">That address doesn't match a page. <a href="#/">Go to the home page</a>.</p>`));
}

/* ---------- home ---------- */
function home() {
  const n = {p: C.platforms.platforms.length, c: C.criteria.criteria.length,
             i: C.insights.length, k: C.carousels.length, f: C.files.length};
  app.append(h("section", {class: "hero"}, `
    <div class="stack">
      <div class="eyebrow">LLM observability · strategy, comparison and tooling</div>
      <h1>Own the signal. Rent the screen.</h1>
      <p class="thesis">Own your <em>instrumentation</em> and your <em>pipeline</em>. Buy or build everything above them based on scale, sovereignty and what actually differentiates you.</p>
      <div class="row-wrap" style="margin-top:6px">
        <a class="btn primary" href="#/compare">Compare platforms</a>
        <a class="btn" href="#/carousels">View the carousel</a>
        <a class="btn" href="${GH()}">Open on GitHub</a>
      </div>
    </div>
    <div class="layers" aria-label="The four observability layers">
      <div class="layer own"><b>1</b><span>Instrumentation · OpenTelemetry</span><span class="pill ok">own</span></div>
      <div class="layer own"><b>2</b><span>Pipeline · sample, redact, route</span><span class="pill ok">own</span></div>
      <div class="layer"><b>3</b><span>Storage · hot vs cold</span><span class="pill">choose</span></div>
      <div class="layer"><b>4</b><span>Analysis and UI</span><span class="pill">choose</span></div>
    </div>`));
  app.append(h("div", {class: "stats"}, `
    <div class="stat"><b>${n.p}</b><span>platforms compared</span></div>
    <div class="stat"><b>${n.c}</b><span>evaluation criteria</span></div>
    <div class="stat"><b>${n.i}</b><span>insight documents</span></div>
    <div class="stat"><b>${n.k}</b><span>carousels</span></div>
    <div class="stat"><b>3</b><span>agent frameworks</span></div>`));
  const cards = [
    ["#/compare", "Compare", "Platform comparison", "Weight seven criteria, set must-haves and rank nine platforms. Full feature matrix by group."],
    ["#/insights", "Insights", "Build, buy or hybrid", "The decision framework, local tracing, the LexAgent walkthrough and the evaluation checklist."],
    ["#/carousels", "Carousels", "Executive carousel", "The 10-slide CTO/CIO carousel with caption and first comment. Expand to present."],
    ["#/architecture", "Agents", "Multi-framework agents", "Researcher, analyst, writer and reviewer, built in LangGraph, CrewAI and the OpenAI Agents SDK."],
    ["#/skill", "Skill", "Claude skill", "observability-platform-analyst: the same workflow as a portable Claude skill with a ranking script."],
    ["#/review", "Review", "Review queue", "Validation results, data freshness and drafts waiting for human review."],
  ];
  const grid = h("div", {class: "grid-cards"});
  cards.forEach(([href, eb, t, d]) => grid.append(h("a", {class: "panel card", href},
    `<span class="eyebrow">${eb}</span><h3 style="font-size:20px">${t}</h3><p class="muted">${d}</p><span class="go">Open →</span>`)));
  app.append(grid);
  const ex = h("section", {class: "stack", style: "margin-top:36px"}, `<h2>Interactive explorers</h2>
    <p class="muted">Standalone pages built during the course, kept in <code>site/explorers/</code>.</p>`);
  const eg = h("div", {class: "grid-cards"});
  [["explorers/lexagent_walkthrough.html", "LexAgent trace walkthrough", "14-step animated sequence diagram, span tree, demo runs and a quiz."],
   ["explorers/lexagent_local_tracing.html", "Local tracing guide", "Move from LangSmith to Phoenix, JSON files or self-hosted LangSmith."],
   ["explorers/llm_observability_compare.html", "Platform picker (standalone)", "The original single-page comparison tool."]]
    .forEach(([href, t, d]) => eg.append(h("a", {class: "panel card", href}, `<h3>${t}</h3><p class="muted">${d}</p><span class="go">Open →</span>`)));
  ex.append(eg);
  app.append(ex);
}

/* ---------- compare ---------- */
const CRIT_COLORS = {data: "var(--srv)", instr: "var(--nb)", agent: "#7a5cc4", eval: "var(--trace)", cost: "var(--ok)", ops: "#c0507a", ease: "var(--muted)"};
const GROUPS = {
  "Openness and cost": ["license", "selfhost", "free_tier", "paid_from"],
  "Tracing": ["otel", "agent_depth", "frameworks"],
  "Evaluation": ["datasets", "llm_judge", "online_evals", "human_annotation", "ci_gating"],
  "Operations": ["cost_tracking", "prompt_mgmt", "extras"],
  "Scores": "scores",
  "Best fit": ["best_for"],
};
const FIELD_LABEL = {license: "License", selfhost: "Self-hosting", free_tier: "Free tier", paid_from: "Paid from",
  otel: "OpenTelemetry", agent_depth: "Agent depth", frameworks: "Frameworks", datasets: "Datasets and experiments",
  llm_judge: "LLM-as-judge", online_evals: "Online evals", human_annotation: "Human annotation", ci_gating: "CI gating",
  cost_tracking: "Cost tracking", prompt_mgmt: "Prompt management", extras: "Extras", best_for: "Best for"};
const lvl = v => `<span class="lvl l${v}">${C.criteria.scale.labels[v]}</span>`;
function cell(v) {
  v = String(v);
  if (v === "No" || v.startsWith("No ")) return `<span class="v-no">${esc(v)}</span>`;
  if (v === "Not confirmed") return `<span class="v-nc">${esc(v)}</span>`;
  if (/^(Yes|Free|Native|Strong|First-party)/.test(v)) return `<span class="v-yes">${esc(v)}</span>`;
  return esc(v);
}
function compare() {
  const crit = C.criteria.criteria, presets = C.criteria.presets, musts = C.criteria.must_haves;
  const P = C.platforms.platforms;
  let state = {preset: "course", w: {...presets.course.weights}, m: {}};
  try { const s = JSON.parse(localStorage.getItem("aoi-rank") || "null"); if (s) state = {...state, ...s}; } catch (e) {}

  app.append(h("div", {class: "page-head"}, `<div class="eyebrow">Compare · data as of ${esc(C.platforms.as_of)}</div>
    <h1>Which observability platform fits?</h1>
    <p class="lede">Set how much each criterion matters and tick your must-haves. Scores are an editorial 0–3 assessment from published 2026 comparisons, not benchmarks. Prices change, so check vendor pages before buying.</p>`));

  const grid = h("div", {class: "rank-grid"});
  const controls = h("div", {class: "panel pad controls"});
  const ranking = h("div", {class: "panel pad"});
  grid.append(controls, ranking);
  app.append(grid);

  controls.innerHTML = `<div><div class="eyebrow" style="margin-bottom:8px">Start from a profile</div><div class="row-wrap" id="presets"></div></div>
    <div><div class="eyebrow" style="margin-bottom:10px">How much each matters (0–5)</div><div class="stack" style="gap:12px" id="weights"></div></div>
    <div><div class="eyebrow" style="margin-bottom:10px">Must-haves</div><div class="musts" id="musts"></div></div>`;
  const pEl = controls.querySelector("#presets");
  Object.entries(presets).forEach(([k, p]) => {
    const b = h("button", {class: "chip", type: "button", "data-k": k}, esc(p.name));
    b.onclick = () => { state.preset = k; state.w = {...p.weights}; sync(); render(); };
    pEl.append(b);
  });
  const wEl = controls.querySelector("#weights");
  crit.forEach(c => {
    const d = h("div", {class: "w"}, `<label for="w-${c.key}"><span><i style="display:inline-block;width:9px;height:9px;border-radius:2px;background:${CRIT_COLORS[c.key]};margin-right:6px"></i>${esc(c.name)}</span><span id="wv-${c.key}"></span></label>
      <input type="range" id="w-${c.key}" min="0" max="5" step="1"><small>${esc(c.looks_at)}</small>`);
    d.querySelector("input").addEventListener("input", e => { state.w[c.key] = +e.target.value; state.preset = null; render(); });
    wEl.append(d);
  });
  const mEl = controls.querySelector("#musts");
  musts.forEach(m => {
    const l = h("label", {for: `m-${m.key}`}, `<input type="checkbox" id="m-${m.key}"><span>${esc(m.name)}</span>`);
    l.querySelector("input").addEventListener("change", e => { state.m[m.key] = e.target.checked; render(); });
    mEl.append(l);
  });
  function sync() {
    crit.forEach(c => (document.getElementById(`w-${c.key}`).value = state.w[c.key]));
    musts.forEach(m => (document.getElementById(`m-${m.key}`).checked = !!state.m[m.key]));
  }
  function render() {
    crit.forEach(c => (document.getElementById(`wv-${c.key}`).textContent = state.w[c.key]));
    pEl.querySelectorAll(".chip").forEach(b => b.setAttribute("aria-pressed", b.dataset.k === state.preset));
    const total = crit.reduce((a, c) => a + state.w[c.key] * 3, 0) || 1;
    const rows = P.map(p => {
      const parts = crit.map(c => ({c, v: state.w[c.key] * p.scores[c.key] / total * 100}));
      const miss = musts.filter(m => state.m[m.key] && p.must[m.key] !== true)
        .map(m => m.name + (p.must[m.key] === null ? " (not confirmed)" : ""));
      return {p, parts, total: parts.reduce((a, x) => a + x.v, 0), miss};
    }).sort((a, b) => (a.miss.length > 0) - (b.miss.length > 0) || b.total - a.total);
    let rank = 0;
    ranking.innerHTML = `<div class="row-wrap" style="justify-content:space-between;margin-bottom:8px">
        <h2>${state.preset ? `Ranking for ${esc(presets[state.preset].name.toLowerCase())}` : "Ranking for your weights"}</h2>
        <span class="eyebrow">weighted score / 100</span></div>` +
      rows.map(r => {
        if (!r.miss.length) rank++;
        return `<div class="rrow${r.miss.length ? " out" : ""}">
          <span class="pos">${r.miss.length ? "–" : rank}</span>
          <span class="nm">${esc(r.p.name)}<small>${esc(r.p.owner)}</small></span>
          <span class="track" role="img" aria-label="Score ${Math.round(r.total)} of 100">${r.parts.map(x => `<span class="seg" title="${esc(x.c.name)}: ${x.v.toFixed(1)}" style="width:${x.v}%;background:${CRIT_COLORS[x.c.key]}"></span>`).join("")}</span>
          <span class="sc">${Math.round(r.total)}</span>
          ${r.miss.length ? `<span class="why">Missing: ${esc(r.miss.join(", "))}</span>` : ""}</div>`;
      }).join("") +
      `<div class="legend">${crit.map(c => `<span><i style="background:${CRIT_COLORS[c.key]}"></i>${esc(c.name)}</span>`).join("")}</div>`;
    try { localStorage.setItem("aoi-rank", JSON.stringify(state)); } catch (e) {}
  }
  sync(); render();

  // matrix
  const mx = h("section", {class: "stack", style: "margin-top:32px"}, `<h2>Full comparison</h2>`);
  const chips = h("div", {class: "row-wrap"});
  const box = h("div", {class: "panel tablebox matrix"});
  mx.append(chips, box, h("p", {class: "muted", style: "font-size:14px"}, `"Not confirmed" means the sources reviewed did not confirm the feature. It may still exist. Sources are listed on each platform in <a href="#/files/data/platforms.yaml">data/platforms.yaml</a>.`));
  app.append(mx);
  let group = "Openness and cost";
  Object.keys(GROUPS).forEach(g => {
    const b = h("button", {class: "chip", type: "button"}, g);
    b.onclick = () => { group = g; drawMatrix(); };
    chips.append(b);
  });
  function drawMatrix() {
    chips.querySelectorAll(".chip").forEach(b => b.setAttribute("aria-pressed", b.textContent === group));
    const head = `<thead><tr><th scope="col">${esc(group)}</th>${P.map(p => `<th scope="col">${esc(p.name)}</th>`).join("")}</tr></thead>`;
    const body = GROUPS[group] === "scores"
      ? crit.map(c => `<tr><th scope="row">${esc(c.name)}</th>${P.map(p => `<td>${lvl(p.scores[c.key])}</td>`).join("")}</tr>`).join("")
      : GROUPS[group].map(f => `<tr><th scope="row">${FIELD_LABEL[f]}</th>${P.map(p => `<td>${cell(p.facts[f])}</td>`).join("")}</tr>`).join("");
    box.innerHTML = `<table>${head}<tbody>${body}</tbody></table>`;
  }
  drawMatrix();

  const src = h("section", {class: "stack", style: "margin-top:28px"}, `<h2>Sources</h2>`);
  src.append(h("ul", {style: "margin:0;padding-left:20px"}, C.platforms.sources.map(s => `<li><a href="${esc(s.url)}">${esc(s.title)}</a></li>`).join("")));
  app.append(src);
}

/* ---------- insights ---------- */
function insights(slug) {
  const list = C.insights;
  const cur = list.find(i => i.slug === slug) || (slug ? null : list.find(i => !i.draft));
  const split = h("div", {class: "split"});
  const side = h("nav", {class: "panel side", "aria-label": "Insights"});
  list.forEach(i => side.append(h("a", {href: `#/insights/${encodeURIComponent(i.slug)}`, "aria-current": String(cur && i.slug === cur.slug)},
    `${esc(i.title)}<small>${i.draft ? "Draft · " : ""}${esc(i.audience || "")}</small>`)));
  const body = h("article", {class: "stack"});
  split.append(side, body);
  app.append(h("div", {class: "page-head"}, `<div class="eyebrow">Insights</div><h1>Insights and guides</h1>`), split);
  if (!cur) { body.append(h("p", {class: "muted"}, "That insight doesn't exist. Pick one from the list.")); return; }
  body.append(h("div", {class: "row-wrap"}, (cur.tags || []).map(t => `<span class="pill info">${esc(t)}</span>`).join("") +
    (cur.draft ? `<span class="pill warn">draft</span>` : "") +
    `<a class="btn" style="margin-left:auto" href="${GH()}/edit/${BRANCH()}/${cur.path}">Suggest an edit</a>`));
  body.append(md(cur.body));
}

/* ---------- carousels ---------- */
function slideHTML(s, i, total, doc) {
  const dark = i === 0 || i === total - 1;
  const body = (Array.isArray(s.body) ? s.body : [s.body || ""]).map(b => `<li>${esc(b)}</li>`).join("");
  return `<div class="slide${dark ? " dark" : ""}" role="group" aria-roledescription="slide" aria-label="Slide ${i + 1} of ${total}">
    <div class="s-top"><span>${esc(s.role || "")}</span><span>${String(i + 1).padStart(2, "0")} / ${String(total).padStart(2, "0")}</span></div>
    <h3>${esc(s.headline)}</h3><ul>${body}</ul>
    <div class="s-foot"><span>${esc(doc.audience ? "For " + doc.audience : "")}</span><span>${i < total - 1 ? "Swipe →" : ""}</span></div></div>`;
}
function buildCarousel(doc, {expanded = false} = {}) {
  const slides = doc.slides || [];
  let i = 0;
  const root = h("div", {class: "car", "aria-roledescription": "carousel", "aria-label": doc.title});
  root.innerHTML = `<div class="car-stage">
      <button class="car-nav" type="button" data-d="-1" aria-label="Previous slide">‹</button>
      <div class="car-viewport"><div class="car-track">${slides.map((s, k) => slideHTML(s, k, slides.length, doc)).join("")}</div></div>
      <button class="car-nav" type="button" data-d="1" aria-label="Next slide">›</button></div>
    <div class="car-bar"><div class="dots">${slides.map((_, k) => `<button class="dot" type="button" aria-label="Go to slide ${k + 1}" data-k="${k}"></button>`).join("")}</div>
      <div class="row-wrap"><button class="btn" type="button" data-act="notes" aria-pressed="false">Designer notes</button>
      <button class="btn${expanded ? "" : " primary"}" type="button" data-act="expand">${expanded ? "Close" : "Expand"}</button></div></div>
    <div class="visual-note" hidden></div>`;
  const track = root.querySelector(".car-track"), note = root.querySelector(".visual-note");
  const prev = root.querySelector('[data-d="-1"]'), next = root.querySelector('[data-d="1"]');
  function go(n) {
    i = Math.max(0, Math.min(slides.length - 1, n));
    track.style.transform = `translateX(-${i * 100}%)`;
    prev.disabled = i === 0; next.disabled = i === slides.length - 1;
    root.querySelectorAll(".dot").forEach((d, k) => d.setAttribute("aria-current", String(k === i)));
    note.innerHTML = `<b>Slide ${i + 1} visual:</b> ${esc(slides[i]?.visual || "No note.")}`;
    root.dataset.index = i;
  }
  prev.onclick = () => go(i - 1); next.onclick = () => go(i + 1);
  root.querySelectorAll(".dot").forEach(d => (d.onclick = () => go(+d.dataset.k)));
  const notesBtn = root.querySelector('[data-act="notes"]');
  notesBtn.onclick = () => { note.hidden = !note.hidden; notesBtn.setAttribute("aria-pressed", String(!note.hidden)); };
  root.querySelector('[data-act="expand"]').onclick = () => expanded ? closeLightbox() : openLightbox(doc, i);
  // swipe
  let x0 = null;
  const vp = root.querySelector(".car-viewport");
  vp.addEventListener("pointerdown", e => (x0 = e.clientX));
  vp.addEventListener("pointerup", e => { if (x0 === null) return; const dx = e.clientX - x0; if (Math.abs(dx) > 40) go(i + (dx < 0 ? 1 : -1)); x0 = null; });
  root.go = go;
  root.keys = e => { if (e.key === "ArrowRight") go(i + 1); if (e.key === "ArrowLeft") go(i - 1); };
  root.tabIndex = 0;
  root.addEventListener("keydown", root.keys);
  go(0);
  return root;
}
let lbReturn = null, lbKeys = null;
function openLightbox(doc, index) {
  lbReturn = document.activeElement;
  lightbox.innerHTML = `<button class="lb-close" type="button">Close (Esc)</button>`;
  const car = buildCarousel(doc, {expanded: true});
  lightbox.append(car);
  car.go(index || 0);
  lightbox.hidden = false;
  document.body.classList.add("locked");
  lightbox.querySelector(".lb-close").onclick = closeLightbox;
  lbKeys = e => { if (e.key === "Escape") closeLightbox(); else car.keys(e); };
  document.addEventListener("keydown", lbKeys);
  lightbox.querySelector(".lb-close").focus();
}
function closeLightbox() {
  if (lightbox.hidden) return;
  lightbox.hidden = true; lightbox.innerHTML = "";
  document.body.classList.remove("locked");
  if (lbKeys) document.removeEventListener("keydown", lbKeys);
  if (lbReturn && lbReturn.focus) lbReturn.focus();
}
function carousels(id) {
  const list = C.carousels;
  const doc = list.find(c => c.id === id) || list[0];
  app.append(h("div", {class: "page-head"}, `<div class="eyebrow">Carousels · ${list.length} in repo</div><h1>${esc(doc ? doc.title : "Carousels")}</h1>
    ${doc ? `<p class="lede">${esc(doc.thesis || "")}</p>` : ""}`));
  if (!doc) { app.append(h("p", {class: "muted"}, "No carousels yet. Add a YAML file to carousels/.")); return; }
  if (list.length > 1) {
    const pick = h("div", {class: "row-wrap", style: "margin-bottom:18px"});
    list.forEach(c => pick.append(h("a", {class: "chip", href: `#/carousels/${encodeURIComponent(c.id)}`, "aria-pressed": String(c.id === doc.id)}, esc(c.title) + (c.draft ? " (draft)" : ""))));
    app.append(pick);
  }
  const lay = h("div", {class: "car-layout"});
  const left = h("div", {class: "stack"}); left.append(buildCarousel(doc));
  const right = h("div", {class: "stack"});
  right.append(h("div", {class: "row-wrap"}, `<span class="pill">${esc(doc.format || "")}</span>
    <span class="pill ${doc.problems.length ? "bad" : "ok"}">${doc.problems.length ? doc.problems.length + " validation issue(s)" : "passes validation"}</span>
    <span class="pill warn">${esc(doc.status || "draft")}</span>`));
  if (doc.problems.length) right.append(h("div", {class: "note bad"}, `<ul style="margin:0;padding-left:18px">${doc.problems.map(p => `<li>${esc(p)}</li>`).join("")}</ul>`));
  for (const [label, key] of [["LinkedIn caption", "caption"], ["First comment", "first_comment"]]) {
    if (!doc[key]) continue;
    const sec = h("section", {class: "stack", style: "gap:8px"});
    const head = h("div", {class: "row-wrap", style: "justify-content:space-between"}, `<h3>${label}</h3>`);
    const btn = h("button", {class: "btn", type: "button", "data-label": "Copy"}, "Copy");
    btn.onclick = () => copy(doc[key], btn);
    head.append(btn);
    sec.append(head, h("div", {class: "copybox"}, esc(doc[key])));
    right.append(sec);
  }
  right.append(h("div", {class: "row-wrap"}, `<a class="btn" href="#/files/${doc.path}">View source YAML</a><a class="btn" href="${GH()}/edit/${BRANCH()}/${doc.path}">Suggest an edit</a>`));
  lay.append(left, right);
  app.append(lay);
}

/* ---------- architecture ---------- */
function architecture() {
  app.append(h("div", {class: "page-head"}, `<div class="eyebrow">Agents</div><h1>One workflow, three frameworks</h1>
    <p class="lede">Four roles share one set of tools and one dataset. The same workflow is implemented in LangGraph, CrewAI and the OpenAI Agents SDK so the designs can be compared, plus an offline pipeline with no LLM for CI.</p>`));
  const svg = `<svg viewBox="0 0 900 430" role="img" aria-label="Agent architecture: four roles, shared tools and data, three framework implementations">
    <defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.6"/></marker></defs>
    <rect x="20" y="20" width="860" height="56" rx="10" style="fill:var(--sunk);stroke:var(--line)"/>
    <text x="40" y="44" style="fill:var(--muted);font-size:12px;font-family:var(--mono)">ORCHESTRATION (pick one)</text>
    ${[["LangGraph", "state graph + review loop", 300], ["CrewAI", "sequential crew", 520], ["OpenAI Agents SDK", "orchestrator, agents as tools", 740]].map(([n, s, x]) =>
      `<text x="${x}" y="46" text-anchor="middle" style="fill:var(--ink);font-size:14px;font-weight:600">${n}</text><text x="${x}" y="64" text-anchor="middle" style="fill:var(--muted);font-size:12px">${s}</text>`).join("")}
    ${[["Researcher", "facts, freshness, web", 40], ["Analyst", "rank, compare, decide", 255], ["Writer", "insight + carousel", 470], ["Reviewer", "validate, fact-check", 685]].map(([n, s, x], k) =>
      `<rect x="${x}" y="110" width="175" height="64" rx="10" style="fill:var(--nb-soft);stroke:var(--nb)"/>
       <text x="${x + 87}" y="137" text-anchor="middle" style="fill:var(--nb);font-size:15px;font-weight:600">${n}</text>
       <text x="${x + 87}" y="157" text-anchor="middle" style="fill:var(--muted);font-size:12px">${s}</text>
       ${k < 3 ? `<line x1="${x + 177}" y1="142" x2="${x + 213}" y2="142" style="stroke:var(--muted);stroke-width:1.4" marker-end="url(#ah)"/>` : ""}`).join("")}
    <path d="M772 176 C772 214, 557 214, 557 178" fill="none" style="stroke:var(--trace);stroke-width:1.6;stroke-dasharray:5 4" marker-end="url(#ah)"/>
    <text x="664" y="222" text-anchor="middle" style="fill:var(--trace);font-size:12px">REVISE (max 2)</text>
    <rect x="20" y="250" width="860" height="78" rx="10" style="fill:var(--srv-soft);stroke:var(--srv)"/>
    <text x="40" y="274" style="fill:var(--srv);font-size:12px;font-family:var(--mono)">SHARED TOOLS · agent_system/core/tools.py</text>
    <text x="40" y="300" style="fill:var(--ink);font-size:13px">list_platforms · get_platform · rank_platforms · compare_platforms · check_freshness · web_search</text>
    <text x="40" y="318" style="fill:var(--ink);font-size:13px">validate_carousel · fact_check · save_insight · save_carousel</text>
    <rect x="20" y="350" width="420" height="60" rx="10" style="fill:var(--surface);stroke:var(--line)"/>
    <text x="40" y="374" style="fill:var(--muted);font-size:12px;font-family:var(--mono)">DATA</text>
    <text x="40" y="395" style="fill:var(--ink);font-size:13px">data/platforms.yaml · data/criteria.yaml</text>
    <rect x="460" y="350" width="420" height="60" rx="10" style="fill:var(--surface);stroke:var(--line)"/>
    <text x="480" y="374" style="fill:var(--muted);font-size:12px;font-family:var(--mono)">OUTPUT (drafts for human review)</text>
    <text x="480" y="395" style="fill:var(--ink);font-size:13px">insights/drafts/ · carousels/drafts/ → this site</text>
  </svg>`;
  app.append(h("div", {class: "panel pad tablebox arch"}, svg));
  const fw = h("section", {class: "stack", style: "margin-top:28px"}, `<h2>How the three designs differ</h2>`);
  fw.append(h("div", {class: "panel tablebox"}, `<table><thead><tr><th>Aspect</th><th>LangGraph</th><th>CrewAI</th><th>OpenAI Agents SDK</th></tr></thead><tbody>
    <tr><td>Control flow</td><td>Explicit graph; code decides order</td><td>Sequential tasks with context</td><td>Orchestrator LLM decides</td></tr>
    <tr><td>Review loop</td><td>Conditional edge, max 2 revisions</td><td>One extra crew pass on REVISE</td><td>Instructed in the orchestrator prompt</td></tr>
    <tr><td>Predictability</td><td>Highest</td><td>High</td><td>Lowest, most flexible</td></tr>
    <tr><td>Tracing</td><td>LangSmith or OpenTelemetry via LangChain</td><td>Built-in events, OpenTelemetry integrations</td><td>Built-in tracing, OpenTelemetry processors</td></tr>
    <tr><td>Best when</td><td>You need auditable routing</td><td>You think in roles and handoffs</td><td>Tasks vary and need dynamic planning</td></tr>
    <tr><td>Code</td><td><a href="#/files/agent_system/frameworks/langgraph_flow.py">langgraph_flow.py</a></td><td><a href="#/files/agent_system/frameworks/crewai_flow.py">crewai_flow.py</a></td><td><a href="#/files/agent_system/frameworks/openai_agents_flow.py">openai_agents_flow.py</a></td></tr>
    </tbody></table>`));
  app.append(fw);
  const run = h("section", {class: "stack", style: "margin-top:28px"}, `<h2>Run it</h2>
    <p class="muted">CrewAI and the OpenAI Agents SDK need different versions of the <code>openai</code> package, so use one virtual environment per framework.</p>`);
  run.append(codeBlock(`# Offline: no API keys, same workflow, used by CI
pip install -r requirements.txt
python -m agent_system.run --framework offline --preset regulated --must selfhost,otel

# LLM-backed (one venv each)
pip install -r requirements-langgraph.txt
export OPENAI_API_KEY=...          # optional: TAVILY_API_KEY for web search
python -m agent_system.run --framework langgraph "Carousel on observability for regulated banks"
python -m agent_system.run --framework crewai    "Insight comparing Langfuse and Phoenix for a course"
python -m agent_system.run --framework openai    "Rank platforms for a startup and draft a carousel"`, "bash"));
  app.append(run);
}

/* ---------- skill ---------- */
function skill() {
  const f = C.files.find(x => x.path === "skills/observability-platform-analyst/SKILL.md");
  app.append(h("div", {class: "page-head"}, `<div class="eyebrow">Claude skill</div><h1>observability-platform-analyst</h1>
    <p class="lede">The same workflow packaged as a portable skill: the dataset, the decision framework and a ranking script travel with it.</p>`));
  const install = h("section", {class: "panel pad stack", style: "margin-bottom:24px"}, `<h3>Install</h3>
    <p class="muted">Copy the folder into your skills directory, or zip it and upload it as a custom skill. The data in <code>references/</code> is kept in sync with <code>data/</code> by the build script.</p>`);
  install.append(codeBlock(`cp -r skills/observability-platform-analyst ~/.claude/skills/
python ~/.claude/skills/observability-platform-analyst/scripts/rank.py --preset startup --must otel`, "bash"));
  app.append(install);
  if (f) {
    const body = f.content.replace(/^---[\s\S]*?---\n/, "");
    const meta = (f.content.match(/^---\n([\s\S]*?)\n---/) || [])[1] || "";
    app.append(h("div", {class: "note", style: "margin-bottom:18px;font-family:var(--mono);font-size:13px;white-space:pre-wrap"}, esc(meta)));
    app.append(md(body));
  }
  const tree = h("p", {style: "margin-top:20px"}, `Files: ${C.files.filter(x => x.path.startsWith("skills/")).map(x => `<a href="#/files/${x.path}"><code>${esc(x.path.replace("skills/observability-platform-analyst/", ""))}</code></a>`).join(" · ")}`);
  app.append(tree);
}

/* ---------- review ---------- */
function review(preset) {
  const r = C.review, fr = C.freshness;
  const drafts = [...C.insights.filter(i => i.draft).map(i => ({t: i.title, k: "Insight", href: `#/insights/${i.slug}`, path: i.path})),
                  ...C.carousels.filter(c => c.draft || /review/.test(c.status || "")).map(c => ({t: c.title, k: "Carousel", href: `#/carousels/${c.id}`, path: c.path}))];
  app.append(h("div", {class: "page-head"}, `<div class="eyebrow">Review · built ${esc(C.built_at)}${C.repo.commit ? " · commit " + esc(C.repo.commit) : ""}</div>
    <h1>Review queue</h1><p class="lede">What the reviewer role checked on this build, and what needs a human decision.</p>`));
  const top = h("div", {class: "grid-cards", style: "margin-bottom:24px"});
  top.append(h("div", {class: "panel card"}, `<span class="eyebrow">Automated review</span><h3 style="font-size:22px">${r.approved ? "Approved" : "Needs revision"}</h3>
    <p class="muted">${r.approved ? "All carousels pass validation and no price mismatches were found." : r.problems.length + " problem(s) found."}</p>`));
  top.append(h("div", {class: "panel card"}, `<span class="eyebrow">Data freshness</span><h3 style="font-size:22px">${fr.stale ? "Stale" : "Current"}</h3>
    <p class="muted">Dataset as of ${esc(fr.as_of)}, ${fr.age_months} month(s) old. Re-verify after ${fr.max_age_months} months.</p>`));
  top.append(h("div", {class: "panel card"}, `<span class="eyebrow">Waiting for review</span><h3 style="font-size:22px">${drafts.length} item(s)</h3>
    <p class="muted">Drafts and items marked for review.</p>`));
  app.append(top);
  if (!r.approved) app.append(h("div", {class: "note bad", style: "margin-bottom:24px"}, `<ul style="margin:0;padding-left:18px">${r.problems.map(p => `<li>${esc(p)}</li>`).join("")}</ul>`));
  const q = h("section", {class: "stack", style: "margin-bottom:28px"}, `<h2>Items</h2>`);
  q.append(drafts.length ? h("div", {class: "panel tablebox"}, `<table><thead><tr><th>Item</th><th>Type</th><th>Actions</th></tr></thead><tbody>${drafts.map(d =>
    `<tr><td><a href="${d.href}">${esc(d.t)}</a></td><td>${d.k}</td><td class="row-wrap"><a class="btn" href="${GH()}/edit/${BRANCH()}/${d.path}">Edit on GitHub</a>
     <a class="btn" href="${GH()}/issues/new?title=${encodeURIComponent("Review: " + d.t)}&body=${encodeURIComponent("File: " + d.path + "\n\nFeedback:\n")}">Leave feedback</a></td></tr>`).join("")}</tbody></table>`)
    : h("p", {class: "muted"}, "Nothing waiting."));
  app.append(q);
  const keys = Object.keys(C.reports);
  const cur = keys.includes(preset) ? preset : "course";
  const b = h("section", {class: "stack"}, `<h2>Offline analyst briefs</h2><p class="muted">Generated on every build by the no-LLM pipeline. Pick an audience.</p>`);
  const chips = h("div", {class: "row-wrap"});
  keys.forEach(k => chips.append(h("a", {class: "chip", href: `#/review/${k}`, "aria-pressed": String(k === cur)}, esc(C.criteria.presets[k].name))));
  b.append(chips, h("div", {class: "panel pad"}, "")); b.lastChild.append(md(C.reports[cur]));
  app.append(b);
}

/* ---------- files ---------- */
function buildTree(paths) {
  const root = {};
  paths.forEach(p => { let node = root; p.split("/").forEach((part, i, arr) => { node[part] = node[part] || (i === arr.length - 1 ? null : {}); node = node[part] || {}; }); });
  return root;
}
function treeHTML(node, prefix, openPath) {
  const entries = Object.entries(node).sort(([a, av], [b, bv]) => (av === null) - (bv === null) || a.localeCompare(b));
  return entries.map(([name, kids]) => {
    const path = prefix ? `${prefix}/${name}` : name;
    if (kids === null) return `<a href="#/files/${path}" aria-current="${path === openPath}">${esc(name)}</a>`;
    const open = openPath.startsWith(path + "/") || !prefix;
    return `<details${open ? " open" : ""}><summary>${esc(name)}/</summary><div class="kids">${treeHTML(kids, path, openPath)}</div></details>`;
  }).join("");
}
function files(path) {
  const all = C.files;
  const cur = all.find(f => f.path === path) || all.find(f => f.path === "README.md") || all[0];
  app.append(h("div", {class: "page-head"}, `<div class="eyebrow">Files · ${all.length} in repo</div><h1>Repository browser</h1>`));
  const split = h("div", {class: "split"});
  const side = h("nav", {class: "panel side tree", "aria-label": "Repository files"}, treeHTML(buildTree(all.map(f => f.path)), "", cur.path));
  const view = h("article", {class: "stack"});
  split.append(side, view);
  app.append(split);
  const head = h("div", {class: "filehead"}, `<code>${esc(cur.path)}</code><span class="row-wrap"><span class="pill">${(cur.size / 1024).toFixed(1)} KB</span>
    <a class="btn" href="${GH()}/blob/${BRANCH()}/${cur.path}">GitHub</a><a class="btn" href="${GH()}/edit/${BRANCH()}/${cur.path}">Edit</a></span>`);
  view.append(head);
  if (cur.content === undefined) {
    const isPage = cur.path.startsWith("site/") && cur.path.endsWith(".html");
    view.append(h("p", {class: "muted"}, isPage ? `This is a page of the site. <a href="${cur.path.replace(/^site\//, "")}">Open it</a>.` : "Binary or large file. Open it on GitHub."));
  } else if (cur.path.endsWith(".md")) {
    view.append(md(cur.content.replace(/^---[\s\S]*?---\n/, "")));
  } else {
    view.append(codeBlock(cur.content, langOf(cur.path)));
  }
}

/* ---------- boot ---------- */
document.getElementById("menu-btn").onclick = e => {
  const nav = document.getElementById("nav");
  nav.classList.toggle("open");
  e.currentTarget.setAttribute("aria-expanded", String(nav.classList.contains("open")));
};
fetch("content.json", {cache: "no-cache"})
  .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
  .then(data => {
    C = data;
    document.getElementById("foot").innerHTML = `<span>Built ${esc(C.built_at)}${C.repo.commit ? " · " + esc(C.repo.commit) : ""} · data as of ${esc(C.platforms.as_of)}</span>
      <span><a href="${GH()}">${esc(C.repo.owner)}/${esc(C.repo.name)}</a> · scores are editorial, not benchmarks</span>`;
    window.addEventListener("hashchange", route);
    route();
  })
  .catch(err => {
    app.innerHTML = `<div class="note bad"><b>Couldn't load content.json.</b> Run <code>python scripts/build_site.py</code>, then serve the <code>site/</code> folder (for example <code>python -m http.server -d site</code>). Opening index.html directly from disk blocks the request. (${esc(err.message)})</div>`;
  });
})();
