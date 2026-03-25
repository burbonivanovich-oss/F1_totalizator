"use strict";

/* ── Telegram WebApp SDK init ────────────────────────────────────────────── */
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  // Apply color scheme
  if (tg.colorScheme === "light") {
    document.body.classList.add("theme-light");
  }
}

/* ── Team colors (two per team for split dot) ────────────────────────────── */
const TEAM_COLORS = {
  "Red Bull Racing": ["#3671C6", "#1B2537"],  // синий + тёмно-синий
  "Ferrari":         ["#E8002D", "#FFCC00"],  // красный + жёлтый
  "Mercedes":        ["#27F4D2", "#1C1C1C"],  // бирюзовый + чёрный
  "McLaren":         ["#FF8000", "#000000"],  // оранжевый + чёрный
  "Aston Martin":    ["#229971", "#002D40"],  // зелёный + тёмный
  "Alpine":          ["#FF87BC", "#0054A6"],  // розовый + синий
  "Audi":            ["#C9213A", "#6B6B6B"],  // красный + серый
  "Williams":        ["#64C4FF", "#041E42"],  // голубой + тёмно-синий
  "Cadillac":        ["#C0C0C0", "#1C1C1C"],  // серебро + чёрный
  "Racing Bulls":    ["#6692FF", "#C8001E"],  // синий + красный
  "Haas":            ["#FFFFFF", "#B6BABD"],  // белый + серый
};

/* ── Parse URL params ────────────────────────────────────────────────────── */
const params = new URLSearchParams(window.location.search);
const RACE_ID   = (params.get("race_id") || "").toUpperCase();
const IS_SPRINT = params.get("is_sprint") === "1";
const TG_ID     = params.get("tg_id") ? parseInt(params.get("tg_id"), 10) : null;
const TOP_N     = IS_SPRINT ? 10 : 16;

/* ── State ───────────────────────────────────────────────────────────────── */
let allDrivers = [];      // full driver objects from /api/drivers
let orderedIds = [];      // current order (all 22 ids)

/* ── DOM refs ────────────────────────────────────────────────────────────── */
const $loading     = document.getElementById("loading");
const $errorScreen = document.getElementById("error-screen");
const $errorMsg    = document.getElementById("error-msg");
const $raceTitle   = document.getElementById("race-title");
const $raceMeta    = document.getElementById("race-meta");
const $deadlineBlock = document.getElementById("deadline-block");
const $instruction = document.getElementById("instruction");
const $topNHint    = document.getElementById("top-n-hint");
const $list        = document.getElementById("driver-list");
const $listTail    = document.getElementById("driver-list-tail");
const $divider     = document.getElementById("divider");

/* ── Boot ────────────────────────────────────────────────────────────────── */
async function boot() {
  try {
    const [driversResp, raceResp, predResp] = await Promise.all([
      fetch("/api/drivers"),
      RACE_ID ? fetch(`/api/race/${RACE_ID}`) : Promise.resolve(null),
      (RACE_ID && TG_ID)
        ? fetch(`/api/prediction?race_id=${RACE_ID}&is_sprint=${IS_SPRINT ? 1 : 0}&tg_id=${TG_ID}`)
        : Promise.resolve(null),
    ]);

    if (!driversResp.ok) throw new Error("Failed to load drivers");
    allDrivers = await driversResp.json();

    // Render race info
    if (raceResp && raceResp.ok) {
      const race = await raceResp.json();
      $raceTitle.textContent = `${race.flag} ${race.name}`;
      $raceMeta.textContent  = IS_SPRINT ? "🟣 Спринт" : "🏁 Гонка";

      const deadlineKey = IS_SPRINT ? race.sprint_time : race.race_time;
      if (deadlineKey) {
        const dl = new Date(deadlineKey);
        startDeadlineTimer(dl);
      }
    } else if (RACE_ID) {
      $raceTitle.textContent = `🏎 F1 2026 — ${RACE_ID}`;
      $raceMeta.textContent  = IS_SPRINT ? "🟣 Спринт" : "🏁 Гонка";
    }

    $topNHint.textContent = `Учитываются первые ${TOP_N} позиций.`;

    // Determine initial order
    let existingPositions = null;
    if (predResp && predResp.ok) {
      const pred = await predResp.json();
      existingPositions = pred?.positions ?? null;
    }

    if (existingPositions && existingPositions.length > 0) {
      // Put existing prediction order first, then remaining drivers
      const rest = allDrivers.map(d => d.id).filter(id => !existingPositions.includes(id));
      orderedIds = [...existingPositions, ...rest];
    } else {
      orderedIds = allDrivers.map(d => d.id);
    }

    renderList();
    hideLoading();
  } catch (err) {
    showError(err.message || "Ошибка загрузки данных.");
  }
}

/* ── Render ──────────────────────────────────────────────────────────────── */
function renderList() {
  $list.innerHTML = "";
  $listTail.innerHTML = "";

  const driverMap = Object.fromEntries(allDrivers.map(d => [d.id, d]));

  orderedIds.forEach((id, idx) => {
    const driver = driverMap[id];
    if (!driver) return;

    const pos      = idx + 1;
    const inTop    = pos <= TOP_N;
    const colors   = TEAM_COLORS[driver.team] || ["#888", "#444"];
    const dotStyle = `background:linear-gradient(135deg,${colors[0]} 50%,${colors[1]} 50%)`;

    const li = document.createElement("li");
    li.className    = `driver-item ${inTop ? "in-top" : "out-top"}`;
    li.dataset.id   = id;

    li.innerHTML = `
      <div class="pos-badge">${pos}</div>
      <div class="team-dot" style="${dotStyle}"></div>
      <div class="driver-info">
        <div class="driver-code">${driver.id}</div>
        <div class="driver-name">${driver.full_name}</div>
      </div>
      <div class="drag-handle">⠿</div>
    `;

    if (inTop) {
      $list.appendChild(li);
    } else {
      $listTail.appendChild(li);
    }
  });

  // Show divider only when there are items in tail
  if (orderedIds.length > TOP_N) {
    $divider.classList.remove("hidden");
  }
}

/* ── SortableJS setup ────────────────────────────────────────────────────── */
function initSortable() {
  const sortableOptions = {
    animation: 150,
    handle: ".drag-handle",
    ghostClass: "sortable-ghost",
    chosenClass: "sortable-chosen",
    group: "drivers",
    onEnd: onDragEnd,
  };

  Sortable.create($list, sortableOptions);
  Sortable.create($listTail, sortableOptions);
}

function onDragEnd() {
  // Rebuild orderedIds from both lists
  const topIds  = [...$list.querySelectorAll(".driver-item")].map(el => el.dataset.id);
  const tailIds = [...$listTail.querySelectorAll(".driver-item")].map(el => el.dataset.id);
  orderedIds = [...topIds, ...tailIds];
  renderList();
  // Re-init sortable since renderList clears innerHTML
  initSortable();
}

/* ── Deadline timer ──────────────────────────────────────────────────────── */
function startDeadlineTimer(deadline) {
  function update() {
    const diff = deadline - Date.now();
    if (diff <= 0) {
      $deadlineBlock.textContent = "⛔ Приём прогнозов закрыт";
      document.getElementById("confirm-btn").disabled = true;
      return;
    }
    const h = Math.floor(diff / 3_600_000);
    const m = Math.floor((diff % 3_600_000) / 60_000);
    const s = Math.floor((diff % 60_000) / 1_000);
    $deadlineBlock.textContent =
      `⏱ Закрытие через ${h > 0 ? h + "ч " : ""}${m}м ${s}с`;
    setTimeout(update, 1_000);
  }
  update();
}

/* ── Confirm ─────────────────────────────────────────────────────────────── */
function confirmPrediction() {
  const topIds = [...$list.querySelectorAll(".driver-item")].map(el => el.dataset.id);
  const positions = topIds.slice(0, TOP_N);

  if (positions.length < TOP_N) {
    alert(`Нужно минимум ${TOP_N} гонщиков в топе. Сейчас: ${positions.length}`);
    return;
  }

  const payload = {
    race_id:   RACE_ID || "UNKNOWN",
    is_sprint: IS_SPRINT,
    positions: positions,
  };

  const confirmed = confirm(
    `Подтвердить прогноз?\n\nТоп-${TOP_N}:\n` +
    positions.map((id, i) => `P${i + 1}: ${id}`).join("\n")
  );

  if (!confirmed) return;

  if (tg) {
    tg.sendData(JSON.stringify(payload));
  } else {
    // Dev fallback: show JSON
    alert("sendData:\n" + JSON.stringify(payload, null, 2));
  }
}

/* ── Helpers ─────────────────────────────────────────────────────────────── */
function hideLoading() {
  $loading.style.display = "none";
  initSortable();
}

function showError(msg) {
  $loading.style.display = "none";
  $errorMsg.textContent = msg;
  $errorScreen.classList.remove("hidden");
}

/* ── Start ───────────────────────────────────────────────────────────────── */
boot();
