"use strict";

/* ── Telegram WebApp SDK ─────────────────────────────────────────────────── */
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  if (tg.colorScheme === "light") document.body.classList.add("theme-light");
}

/* ── Static data ─────────────────────────────────────────────────────────── */
const DRIVERS = [
  {id:"VER", name:"Verstappen",  full_name:"Max Verstappen",        team:"Red Bull Racing"},
  {id:"HAD", name:"Hadjar",      full_name:"Isack Hadjar",           team:"Red Bull Racing"},
  {id:"LEC", name:"Leclerc",     full_name:"Charles Leclerc",        team:"Ferrari"},
  {id:"HAM", name:"Hamilton",    full_name:"Lewis Hamilton",         team:"Ferrari"},
  {id:"RUS", name:"Russell",     full_name:"George Russell",         team:"Mercedes"},
  {id:"ANT", name:"Antonelli",   full_name:"Andrea Kimi Antonelli",  team:"Mercedes"},
  {id:"NOR", name:"Norris",      full_name:"Lando Norris",           team:"McLaren"},
  {id:"PIA", name:"Piastri",     full_name:"Oscar Piastri",          team:"McLaren"},
  {id:"ALO", name:"Alonso",      full_name:"Fernando Alonso",        team:"Aston Martin"},
  {id:"STR", name:"Stroll",      full_name:"Lance Stroll",           team:"Aston Martin"},
  {id:"GAS", name:"Gasly",       full_name:"Pierre Gasly",           team:"Alpine"},
  {id:"COL", name:"Colapinto",   full_name:"Franco Colapinto",       team:"Alpine"},
  {id:"HUL", name:"Hulkenberg",  full_name:"Nico Hulkenberg",        team:"Audi"},
  {id:"BOR", name:"Bortoleto",   full_name:"Gabriel Bortoleto",      team:"Audi"},
  {id:"SAI", name:"Sainz",       full_name:"Carlos Sainz",           team:"Williams"},
  {id:"ALB", name:"Albon",       full_name:"Alexander Albon",        team:"Williams"},
  {id:"PER", name:"Perez",       full_name:"Sergio Perez",           team:"Cadillac"},
  {id:"BOT", name:"Bottas",      full_name:"Valtteri Bottas",        team:"Cadillac"},
  {id:"LAW", name:"Lawson",      full_name:"Liam Lawson",            team:"Racing Bulls"},
  {id:"LIN", name:"Lindblad",    full_name:"Arvid Lindblad",         team:"Racing Bulls"},
  {id:"OCO", name:"Ocon",        full_name:"Esteban Ocon",           team:"Haas"},
  {id:"BEA", name:"Bearman",     full_name:"Oliver Bearman",         team:"Haas"},
];

// 24 rounds; sprints: CHN, MIA, AUT, USA, BRA, QAT
const RACES = [
  {id:"AUS", name:"Australian Grand Prix",       flag:"🇦🇺", race_time:"2026-03-15T05:00:00+00:00", sprint_time:null},
  {id:"CHN", name:"Chinese Grand Prix",          flag:"🇨🇳", race_time:"2026-03-22T07:00:00+00:00", sprint_time:"2026-03-21T07:30:00+00:00"},
  {id:"JPN", name:"Japanese Grand Prix",         flag:"🇯🇵", race_time:"2026-04-05T05:00:00+00:00", sprint_time:null},
  {id:"BHR", name:"Bahrain Grand Prix",          flag:"🇧🇭", race_time:"2026-04-19T15:00:00+00:00", sprint_time:null},
  {id:"SAU", name:"Saudi Arabian Grand Prix",    flag:"🇸🇦", race_time:"2026-04-26T17:00:00+00:00", sprint_time:null},
  {id:"MIA", name:"Miami Grand Prix",            flag:"🇺🇸", race_time:"2026-05-10T19:00:00+00:00", sprint_time:"2026-05-09T19:00:00+00:00"},
  {id:"EMI", name:"Emilia Romagna Grand Prix",   flag:"🇮🇹", race_time:"2026-05-24T13:00:00+00:00", sprint_time:null},
  {id:"MON", name:"Monaco Grand Prix",           flag:"🇲🇨", race_time:"2026-06-07T13:00:00+00:00", sprint_time:null},
  {id:"ESP", name:"Spanish Grand Prix",          flag:"🇪🇸", race_time:"2026-06-21T13:00:00+00:00", sprint_time:null},
  {id:"CAN", name:"Canadian Grand Prix",         flag:"🇨🇦", race_time:"2026-07-05T18:00:00+00:00", sprint_time:null},
  {id:"AUT", name:"Austrian Grand Prix",         flag:"🇦🇹", race_time:"2026-07-12T13:00:00+00:00", sprint_time:"2026-07-11T11:00:00+00:00"},
  {id:"GBR", name:"British Grand Prix",          flag:"🇬🇧", race_time:"2026-07-26T14:00:00+00:00", sprint_time:null},
  {id:"HUN", name:"Hungarian Grand Prix",        flag:"🇭🇺", race_time:"2026-08-02T13:00:00+00:00", sprint_time:null},
  {id:"BEL", name:"Belgian Grand Prix",          flag:"🇧🇪", race_time:"2026-08-30T13:00:00+00:00", sprint_time:null},
  {id:"NED", name:"Dutch Grand Prix",            flag:"🇳🇱", race_time:"2026-09-06T13:00:00+00:00", sprint_time:null},
  {id:"ITA", name:"Italian Grand Prix",          flag:"🇮🇹", race_time:"2026-09-13T13:00:00+00:00", sprint_time:null},
  {id:"AZE", name:"Azerbaijan Grand Prix",       flag:"🇦🇿", race_time:"2026-09-27T11:00:00+00:00", sprint_time:null},
  {id:"SGP", name:"Singapore Grand Prix",        flag:"🇸🇬", race_time:"2026-10-04T12:00:00+00:00", sprint_time:null},
  {id:"USA", name:"United States Grand Prix",    flag:"🇺🇸", race_time:"2026-10-18T19:00:00+00:00", sprint_time:"2026-10-17T19:00:00+00:00"},
  {id:"MEX", name:"Mexico City Grand Prix",      flag:"🇲🇽", race_time:"2026-11-01T20:00:00+00:00", sprint_time:null},
  {id:"BRA", name:"São Paulo Grand Prix",        flag:"🇧🇷", race_time:"2026-11-08T17:00:00+00:00", sprint_time:"2026-11-07T17:00:00+00:00"},
  {id:"LVG", name:"Las Vegas Grand Prix",        flag:"🇺🇸", race_time:"2026-11-22T06:00:00+00:00", sprint_time:null},
  {id:"QAT", name:"Qatar Grand Prix",            flag:"🇶🇦", race_time:"2026-11-29T15:00:00+00:00", sprint_time:"2026-11-28T14:00:00+00:00"},
  {id:"ABU", name:"Abu Dhabi Grand Prix",        flag:"🇦🇪", race_time:"2026-12-06T13:00:00+00:00", sprint_time:null},
];

const RACE_BY_ID = Object.fromEntries(RACES.map(r => [r.id, r]));

/* ── Team colors for position badges ─────────────────────────────────────── */
const TEAM_COLORS = {
  "Mercedes":        "#00D4AA",  /* Mint */
  "Ferrari":         "#DC0000",  /* Red */
  "McLaren":         "#FF8700",  /* Orange */
  "Audi":            "#550000",  /* Maroon */
  "Alpine":          "#0082FA",  /* Light blue */
  "Red Bull Racing": "#0600EF",  /* Blue */
  "Racing Bulls":    "#5E72E4",  /* Purple-blue */
  "Williams":        "#005AFF",  /* Bright blue */
  "Haas":            "#EBEBEB",  /* Light gray */
  "Cadillac":        "#C5C5C5",  /* Medium gray */
  "Aston Martin":    "#229971",  /* Green */
};

/* ── Team logos (SVG) ────────────────────────────────────────────────────── */
const TEAM_LOGOS = {
  "Red Bull Racing": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#0600EF"/><text x="12" y="14" text-anchor="middle" font-weight="bold" font-size="10" fill="white" font-family="sans-serif">RB</text></svg>',
  "Ferrari":         '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#DC0000"/><text x="12" y="14" text-anchor="middle" font-weight="bold" font-size="10" fill="white" font-family="sans-serif">F</text></svg>',
  "Mercedes":        '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#00D4AA"/><text x="12" y="14" text-anchor="middle" font-weight="bold" font-size="10" fill="white" font-family="sans-serif">M</text></svg>',
  "McLaren":         '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#FF8700"/><text x="12" y="14" text-anchor="middle" font-weight="bold" font-size="10" fill="white" font-family="sans-serif">L</text></svg>',
  "Aston Martin":    '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#229971"/><text x="12" y="14" text-anchor="middle" font-weight="bold" font-size="9" fill="white" font-family="sans-serif">A</text></svg>',
  "Alpine":          '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#0082FA"/><text x="12" y="14" text-anchor="middle" font-weight="bold" font-size="10" fill="white" font-family="sans-serif">A</text></svg>',
  "Audi":            '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#550000"/><text x="12" y="14" text-anchor="middle" font-weight="bold" font-size="10" fill="white" font-family="sans-serif">A</text></svg>',
  "Williams":        '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#005AFF"/><text x="12" y="14" text-anchor="middle" font-weight="bold" font-size="10" fill="white" font-family="sans-serif">W</text></svg>',
  "Cadillac":        '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#C5C5C5"/><text x="12" y="14" text-anchor="middle" font-weight="bold" font-size="9" fill="#333" font-family="sans-serif">C</text></svg>',
  "Racing Bulls":    '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#5E72E4"/><text x="12" y="14" text-anchor="middle" font-weight="bold" font-size="9" fill="white" font-family="sans-serif">B</text></svg>',
  "Haas":            '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#EBEBEB"/><text x="12" y="14" text-anchor="middle" font-weight="bold" font-size="10" fill="#333" font-family="sans-serif">H</text></svg>',
};

/* ── URL params ──────────────────────────────────────────────────────────── */
const params    = new URLSearchParams(window.location.search);
const RACE_ID   = (params.get("race_id") || "").toUpperCase();
const IS_SPRINT = params.get("is_sprint") === "1";
// Existing prediction passed as comma-separated driver IDs: ?positions=VER,NOR,LEC,...
const EXISTING  = params.get("positions")
  ? params.get("positions").split(",").map(s => s.trim().toUpperCase()).filter(Boolean)
  : [];
const TOP_N     = IS_SPRINT ? 10 : 16;
const LOCK_MIN  = 5;

/* ── State ───────────────────────────────────────────────────────────────── */
let orderedIds = [];

/* ── DOM refs ────────────────────────────────────────────────────────────── */
const $loading      = document.getElementById("loading");
const $errorScreen  = document.getElementById("error-screen");
const $errorMsg     = document.getElementById("error-msg");
const $raceTitle    = document.getElementById("race-title");
const $raceMeta     = document.getElementById("race-meta");
const $deadlineBlock= document.getElementById("deadline-block");
const $topNHint     = document.getElementById("top-n-hint");
const $list         = document.getElementById("driver-list");
const $listTail     = document.getElementById("driver-list-tail");
const $divider      = document.getElementById("divider");

/* ── Boot ────────────────────────────────────────────────────────────────── */
function boot() {
  try {
    const race = RACE_BY_ID[RACE_ID];

    if (race) {
      $raceTitle.textContent = `${race.flag} ${race.name}`;
      $raceMeta.textContent  = IS_SPRINT ? "🟣 Спринт" : "🏁 Гонка";

      const raceTimeStr = IS_SPRINT ? race.sprint_time : race.race_time;
      if (raceTimeStr) {
        const deadline = new Date(new Date(raceTimeStr).getTime() - LOCK_MIN * 60_000);
        if (deadline <= new Date()) {
          showError("Приём прогнозов на эту гонку уже закрыт.");
          return;
        }
        startDeadlineTimer(deadline);
      }
    } else if (RACE_ID) {
      $raceTitle.textContent = `🏎 F1 2026 — ${RACE_ID}`;
      $raceMeta.textContent  = IS_SPRINT ? "🟣 Спринт" : "🏁 Гонка";
    } else {
      $raceTitle.textContent = "🏎 F1 Тотализатор 2026";
    }

    $topNHint.textContent = `Учитываются первые ${TOP_N} позиций.`;

    // Determine initial order: existing prediction first, then the rest
    const allIds = DRIVERS.map(d => d.id);
    if (EXISTING.length > 0) {
      const rest = allIds.filter(id => !EXISTING.includes(id));
      orderedIds = [...EXISTING, ...rest];
    } else {
      orderedIds = allIds;
    }

    renderList();
    hideLoading();
  } catch (err) {
    showError(err.message || "Ошибка инициализации.");
  }
}

/* ── Render ──────────────────────────────────────────────────────────────── */
function renderList() {
  $list.innerHTML = "";
  $listTail.innerHTML = "";

  const driverMap = Object.fromEntries(DRIVERS.map(d => [d.id, d]));

  orderedIds.forEach((id, idx) => {
    const driver = driverMap[id];
    if (!driver) return;

    const pos        = idx + 1;
    const inTop      = pos <= TOP_N;
    const teamColor  = TEAM_COLORS[driver.team] || "#999";
    const logoSvg    = TEAM_LOGOS[driver.team] || '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#666"/></svg>';

    const li = document.createElement("li");
    li.className  = `driver-item ${inTop ? "in-top" : "out-top"}`;
    li.dataset.id = id;
    li.innerHTML  = `
      <div class="pos-badge" style="background-color: ${teamColor}">${pos}</div>
      <div class="team-logo">${logoSvg}</div>
      <div class="driver-info">
        <div class="driver-code">${driver.id}</div>
        <div class="driver-name">${driver.full_name}</div>
      </div>
      <div class="drag-handle">⠿</div>`;

    (inTop ? $list : $listTail).appendChild(li);
  });

  $divider.classList.toggle("hidden", orderedIds.length <= TOP_N);
}

/* ── SortableJS ──────────────────────────────────────────────────────────── */
function initSortable() {
  const opts = {
    animation: 150,
    ghostClass: "sortable-ghost",
    chosenClass: "sortable-chosen",
    group: "drivers",
    onEnd() {
      const topIds  = [...$list.querySelectorAll(".driver-item")].map(el => el.dataset.id);
      const tailIds = [...$listTail.querySelectorAll(".driver-item")].map(el => el.dataset.id);
      orderedIds = [...topIds, ...tailIds];
      updateTopNClasses();
    },
  };
  Sortable.create($list,     opts);
  Sortable.create($listTail, opts);
}

/* ── Update top-n classes without re-rendering ────────────────────────────── */
function updateTopNClasses() {
  const driverMap = Object.fromEntries(DRIVERS.map(d => [d.id, d]));
  const allItems = [...$list.querySelectorAll(".driver-item"), ...$listTail.querySelectorAll(".driver-item")];
  allItems.forEach((item, idx) => {
    const pos = idx + 1;
    const inTop = pos <= TOP_N;
    const badge = item.querySelector(".pos-badge");
    if (badge) {
      badge.textContent = pos;
      const driverId = item.dataset.id;
      const driver = driverMap[driverId];
      const teamColor = TEAM_COLORS[driver?.team] || "#999";
      badge.style.backgroundColor = teamColor;
    }
    item.classList.toggle("in-top", inTop);
    item.classList.toggle("out-top", !inTop);
  });
  $divider.classList.toggle("hidden", orderedIds.length <= TOP_N);
}

/* ── Deadline timer ──────────────────────────────────────────────────────── */
function startDeadlineTimer(deadline) {
  let timerId = null;
  function update() {
    const diff = deadline - Date.now();
    if (diff <= 0) {
      $deadlineBlock.textContent = "⛔ Приём прогнозов закрыт";
      document.getElementById("confirm-btn").disabled = true;
      return; // stop scheduling
    }
    const h = Math.floor(diff / 3_600_000);
    const m = Math.floor((diff % 3_600_000) / 60_000);
    const s = Math.floor((diff % 60_000) / 1_000);
    $deadlineBlock.textContent =
      `⏱ Закрытие через ${h > 0 ? h + "ч " : ""}${m}м ${s}с`;
    timerId = setTimeout(update, 1_000);
  }
  update();
}

/* ── Confirm ─────────────────────────────────────────────────────────────── */
function confirmPrediction() {
  const topIds   = [...$list.querySelectorAll(".driver-item")].map(el => el.dataset.id);
  const positions = topIds.slice(0, TOP_N);

  if (positions.length < TOP_N) {
    alert(`Нужно минимум ${TOP_N} гонщиков в топе. Сейчас: ${positions.length}`);
    return;
  }

  if (!RACE_ID) {
    alert("Ошибка: не указана гонка. Закрой окно и попробуй снова.");
    return;
  }
  const payload = { race_id: RACE_ID, is_sprint: IS_SPRINT, positions };

  if (!confirm(`Подтвердить прогноз?\n\nТоп-3:\nP1: ${positions[0]}\nP2: ${positions[1]}\nP3: ${positions[2]}\n…`))
    return;

  if (tg) {
    tg.sendData(JSON.stringify(payload));
  } else {
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
  $errorMsg.textContent  = msg;
  $errorScreen.classList.remove("hidden");
}

/* ── Start ───────────────────────────────────────────────────────────────── */
boot();
