"use strict";
const $ = id => document.getElementById(id);
const SPEEDS = [1, 2, 4, 8, 16, 40, 100]; // search steps per animation frame
const canvas = $("maze"), ctx = canvas.getContext("2d");

let M = null;   // { rows, cols, grid, start, goal }
let cell = 20;  // pixel size of one grid cell
const S = {
  phase: "idle",              // idle | loading | running | paused | done
  steps: [], result: null, idx: 0,
  frontier: new Set(), closed: new Set(), pathSet: new Set(),
  drag: null, token: 0,
};
const key = (r, c) => r * M.cols + c;

// ---------- API ----------
async function api(path, body) {
  const res = await fetch("/api" + path, body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : undefined);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed (" + res.status + ")");
  return data;
}
function showError(msg) { const e = $("error"); e.textContent = msg; e.hidden = !msg; }
const mazePayload = () => ({ grid: M.grid, start: M.start, goal: M.goal, heuristic: $("heuristic").value });

// ---------- drawing ----------
function layout() {
  const avail = $("stage").clientWidth - 28;
  cell = Math.max(8, Math.min(24, Math.floor(avail / M.cols)));
  const w = M.cols * cell, h = M.rows * cell, dpr = window.devicePixelRatio || 1;
  canvas.style.width = w + "px"; canvas.style.height = h + "px";
  canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  draw();
}

function draw() {
  if (!M) return;
  const css = getComputedStyle(document.documentElement);
  const col = n => css.getPropertyValue("--c-" + n).trim();
  const C = { open: col("open"), wall: col("wall"), frontier: col("frontier"), closed: col("closed"),
              path: col("path"), start: col("start"), goal: col("goal"), grid: col("grid") };
  ctx.fillStyle = C.grid;
  ctx.fillRect(0, 0, M.cols * cell, M.rows * cell);
  for (let r = 0; r < M.rows; r++) {
    for (let c = 0; c < M.cols; c++) {
      const k = key(r, c);
      let color = C.open;
      if (M.grid[r][c] === 1) color = C.wall;
      else if (S.pathSet.has(k)) color = C.path;
      else if (S.closed.has(k)) color = C.closed;
      else if (S.frontier.has(k)) color = C.frontier;
      ctx.fillStyle = color;
      ctx.fillRect(c * cell + 1, r * cell + 1, cell - 1, cell - 1);
    }
  }
  for (const [pt, color] of [[M.start, C.start], [M.goal, C.goal]]) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(pt[1] * cell + cell / 2 + .5, pt[0] * cell + cell / 2 + .5, cell * 0.38, 0, Math.PI * 2);
    ctx.fill();
  }
}

// ---------- UI state ----------
function setStatus(t) { $("status").textContent = t; }
function updateUI() {
  const label = { running: "Pause", paused: "Resume", loading: "Solving…" }[S.phase] || "Start search";
  $("start").textContent = label;
  $("start").disabled = S.phase === "loading";
  $("sExpanded").textContent = S.closed.size;
  $("sFrontier").textContent = S.frontier.size;
  const r = S.phase === "done" ? S.result : null;
  $("sPath").textContent = r && r.found ? r.cost + " steps" : "–";
  $("sTime").textContent = S.result ? S.result.ms + " ms" : "–";
}

function resetSearch(msg = "Ready. Press Start search.") {
  S.token++;
  Object.assign(S, { phase: "idle", steps: [], result: null, idx: 0 });
  S.frontier.clear(); S.closed.clear(); S.pathSet.clear();
  $("cmp").hidden = true;
  setStatus(msg); updateUI(); draw();
}

// ---------- search animation ----------
async function toggleSearch() {
  if (S.phase === "running") { S.phase = "paused"; setStatus("Paused"); updateUI(); return; }
  if (S.phase === "paused") { S.phase = "running"; setStatus("Searching…"); updateUI(); tick(); return; }
  resetSearch();
  const token = S.token;
  S.phase = "loading"; setStatus("Asking the backend to solve…"); updateUI();
  try {
    const result = await api("/solve", mazePayload());
    if (token !== S.token) return; // maze was edited meanwhile
    showError("");
    S.result = result; S.steps = result.steps; S.idx = 0;
    S.phase = "running"; setStatus("Searching…"); updateUI(); tick();
  } catch (e) {
    if (token !== S.token) return;
    S.phase = "idle"; setStatus("Ready."); updateUI();
    showError("Could not solve: " + e.message);
  }
}

function advance() {
  if (S.idx >= S.steps.length) {
    const r = S.result;
    S.phase = "done";
    r.path.forEach(([pr, pc]) => S.pathSet.add(key(pr, pc)));
    setStatus(r.found ? `Path found! Shortest path is ${r.cost} steps.` : "No path exists.");
    return;
  }
  const [r, c, opened] = S.steps[S.idx++];
  const k = key(r, c);
  S.closed.add(k); S.frontier.delete(k);
  for (const [or, oc] of opened) S.frontier.add(key(or, oc));
}

function tick() {
  if (S.phase !== "running") return;
  const n = SPEEDS[+$("speed").value];
  for (let i = 0; i < n && S.phase === "running"; i++) advance();
  draw(); updateUI();
  if (S.phase === "running") requestAnimationFrame(tick);
}

// ---------- editing ----------
function cellAt(e) {
  const rect = canvas.getBoundingClientRect();
  const c = Math.floor((e.clientX - rect.left) / cell), r = Math.floor((e.clientY - rect.top) / cell);
  return r >= 0 && c >= 0 && r < M.rows && c < M.cols ? [r, c] : null;
}
const same = (a, b) => a[0] === b[0] && a[1] === b[1];

function paint(rc) {
  if (!rc || !S.drag) return;
  const [r, c] = rc;
  let changed = false;
  if (S.drag === "start" && !M.grid[r][c] && !same(rc, M.goal) && !same(rc, M.start)) { M.start = rc; changed = true; }
  else if (S.drag === "goal" && !M.grid[r][c] && !same(rc, M.start) && !same(rc, M.goal)) { M.goal = rc; changed = true; }
  else if ((S.drag === "wall" || S.drag === "erase") && !same(rc, M.start) && !same(rc, M.goal)) {
    const v = S.drag === "wall" ? 1 : 0;
    if (M.grid[r][c] !== v) { M.grid[r][c] = v; changed = true; }
  }
  if (changed) resetSearch();
}

canvas.addEventListener("contextmenu", e => e.preventDefault());
canvas.addEventListener("pointerdown", e => {
  if (e.button !== 0 && e.button !== 2) return;
  const rc = cellAt(e); if (!rc) return;
  canvas.setPointerCapture(e.pointerId);
  if (same(rc, M.start)) S.drag = "start";
  else if (same(rc, M.goal)) S.drag = "goal";
  else S.drag = (e.button === 2 || M.grid[rc[0]][rc[1]] === 1) ? "erase" : "wall";
  paint(rc);
});
canvas.addEventListener("pointermove", e => { if (S.drag) paint(cellAt(e)); });
["pointerup", "pointercancel"].forEach(t => canvas.addEventListener(t, () => { S.drag = null; }));

// ---------- maze generation ----------
async function newMaze(kind) {
  const [rows, cols] = $("size").value.split("x").map(Number);
  try {
    M = await api("/generate", { kind, rows, cols });
    showError("");
    layout();
    resetSearch(kind === "obstacles" ? "Random obstacles added. A path may not exist." : "New maze ready.");
  } catch (e) { showError("Could not create a maze: " + e.message); }
}

async function compare() {
  try {
    const { results } = await api("/compare", mazePayload());
    const best = Math.min(...results.filter(r => r.found).map(r => r.expanded));
    $("cmp").querySelector("tbody").innerHTML = results.map(r =>
      `<tr class="${r.found && r.expanded === best ? "best" : ""}"><td>${r.heuristic}</td><td>${r.found ? r.cost : "none"}</td><td>${r.expanded}</td><td>${r.ms}</td></tr>`).join("");
    $("cmp").hidden = false; showError("");
  } catch (e) { showError("Could not compare: " + e.message); }
}

// ---------- start-up ----------
async function init() {
  $("start").onclick = toggleSearch;
  $("reset").onclick = () => resetSearch();
  $("new").onclick = () => newMaze("maze");
  $("obstacles").onclick = () => newMaze("obstacles");
  $("clear").onclick = () => { M.grid = M.grid.map(r => r.map(() => 0)); resetSearch("Walls cleared."); };
  $("compare").onclick = compare;
  $("heuristic").onchange = () => resetSearch();
  $("size").onchange = () => newMaze("maze");
  $("speed").oninput = () => { $("speedV").textContent = SPEEDS[+$("speed").value] + " steps/frame"; };
  $("speed").oninput();
  window.addEventListener("resize", () => M && layout());
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
  window.addEventListener("keydown", e => {
    if (e.code === "Space" && !/^(SELECT|INPUT|BUTTON)$/.test(e.target.tagName)) { e.preventDefault(); toggleSearch(); }
  });
  try {
    const cfg = await api("/config");
    $("heuristic").innerHTML = cfg.heuristics.map(h => `<option>${h}</option>`).join("");
  } catch (e) {
    showError("Cannot reach the backend. Start it with: python main.py"); setStatus("Offline"); return;
  }
  newMaze("maze");
}
init();
