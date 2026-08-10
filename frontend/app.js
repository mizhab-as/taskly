/* ═══════════════════════════════════════════════════════════
   TASKLY — Full Featured JS App
   Data layer: Python Flask API (primary) → localStorage (fallback)
   Visual behaviour is identical in both modes.
═══════════════════════════════════════════════════════════ */

/* ─── Constants ───────────────────────────────────────────── */
const EMOJI_OPTIONS = ["📝","🎯","💡","🏃","❤️","🎵","📚","🌍","🍕","⚽","🎮","💰","🏠","✈️","🌱","💪","🎨","🛒","🧘","🔧"];

const DEFAULT_LISTS = {
  today:    { name:"Today",    emoji:"☀️", bg:"var(--amber-tint)", custom:false },
  planned:  { name:"Planned",  emoji:"📅", bg:"var(--sky-tint)",   custom:false },
  personal: { name:"Personal", emoji:"🙂", bg:"var(--lilac-tint)", custom:false },
  work:     { name:"Work",     emoji:"💼", bg:"var(--cream-deep)", custom:false },
  shopping: { name:"Shopping", emoji:"🛍️", bg:"var(--pink-tint)",  custom:false },
};

const BG_PALETTE = ["var(--teal-tint)","var(--lilac-tint)","var(--sky-tint)","var(--pink-tint)","var(--amber-tint)","var(--coral-tint)"];

const API_BASE    = "http://localhost:5050";  // Flask server
const API_TIMEOUT = 800;                       // ms before assuming server is offline

/* ─── API mode flag (resolved during init) ───────────────── */
let USE_API = false;  // set to true if Flask server is detected

/* ─── Default seed data ───────────────────────────────────── */
function defaultData() {
  const today = new Date().toISOString().slice(0, 10);
  const now = new Date();

  function offsetDate(days) {
    const d = new Date(now);
    d.setDate(d.getDate() + days);
    return d.toISOString().slice(0, 10);
  }

  return {
    lists: { ...DEFAULT_LISTS },
    tasks: [
      { id:1,  list:"personal", title:"Go to morning workout session",      priority:"High",   done:false, due:today },
      { id:2,  list:"work",     title:"Review Q3 design system updates",    priority:"High",   done:false, due:today },
      { id:3,  list:"shopping", title:"Buy organic oat milk & coffee beans",priority:"Low",    done:true,  due:today },
      { id:4,  list:"work",     title:"Team sprint planning & demo",        priority:"High",   done:false, due:offsetDate(1) },
      { id:5,  list:"personal", title:"Pay monthly utility & internet bills",priority:"Medium", done:false, due:offsetDate(3) },
      { id:6,  list:"personal", title:"Plan weekend roadtrip itinerary",    priority:"Medium", done:false, due:offsetDate(6) },
      { id:7,  list:"personal", title:"Doctor checkup appointment",         priority:"High",   done:false, due:offsetDate(9) },
      { id:8,  list:"work",     title:"Submit quarterly client report",     priority:"High",   done:false, due:offsetDate(11) },
      { id:9,  list:"shopping", title:"Order noise-canceling headphones",   priority:"Low",    done:false, due:offsetDate(13) },
      { id:10, list:"personal", title:"Read 2 chapters of System Design",   priority:"Low",    done:false, due:offsetDate(16) },
      { id:11, list:"personal", title:"Renew car insurance policy",         priority:"Medium", done:false, due:offsetDate(-4) },
      { id:12, list:"work",     title:"Finalize Taskly mobile PWA build",   priority:"High",   done:true,  due:today },
    ],
    nextId: 13,
  };
}

/* ─── localStorage helpers ────────────────────────────────── */
function loadFromLocalStorage() {
  const raw = localStorage.getItem("taskly_v2");
  return raw ? JSON.parse(raw) : defaultData();
}
function saveToLocalStorage(data) {
  localStorage.setItem("taskly_v2", JSON.stringify(data));
}

/* ─── API helpers ─────────────────────────────────────────── */
async function apiFetch(path, opts = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), API_TIMEOUT);
  try {
    const res = await fetch(API_BASE + path, { ...opts, signal: controller.signal });
    clearTimeout(timer);
    return res;
  } catch (e) {
    clearTimeout(timer);
    throw e;
  }
}

/* ─── Unified save (writes to both localStorage + API) ───── */
function save() {
  saveToLocalStorage(DATA);
  if (USE_API) {
    apiFetch("/api/data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(DATA),
    }).catch(() => { /* server went offline mid-session — localStorage already saved */ });
  }
}

/* ─── App state ───────────────────────────────────────────── */
let DATA = loadFromLocalStorage();  // overwritten during init() if API is live
let _today = new Date();
let state = {
  view: "dashboard",
  list: "personal",
  tab: "All",
  search: "",
  calYear: _today.getFullYear(),
  calMonth: _today.getMonth(),
};
let _selectedPrio = "Medium";
let _selectedEmoji = "📝";

/* ─── Async init: detect API, load data, boot app ────────── */
async function init() {
  try {
    const health = await apiFetch("/api/health");
    if (health.ok) {
      USE_API = true;
      const dataRes = await apiFetch("/api/data");
      if (dataRes.status === 200) {
        const serverData = await dataRes.json();
        DATA = serverData;
        saveToLocalStorage(DATA);   // keep localStorage in sync
      } else {
        // Server up but no data yet — seed from localStorage then push to server
        save();
      }
    }
  } catch (_) {
    // Server not running — silently use localStorage (already loaded above)
  }
  render();
}

init();

/* ─── Helpers ─────────────────────────────────────────────── */
const $ = s => document.querySelector(s);
const el = (tag, cls, html) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
};
const esc = s => s.replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);

function tasksFor(listId) {
  if (listId === "today") {
    const t = new Date().toISOString().slice(0, 10);
    return DATA.tasks.filter(x => x.due === t);
  }
  if (listId === "planned") {
    return DATA.tasks.filter(x => x.due && x.due !== "");
  }
  return DATA.tasks.filter(x => x.list === listId);
}
function pendingCount(listId) { return tasksFor(listId).filter(t => !t.done).length; }

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

function motivationText() {
  const total = DATA.tasks.length;
  const done  = DATA.tasks.filter(t => t.done).length;
  const pct   = total ? Math.round(done / total * 100) : 0;
  if (pct === 100) return "All done! You crushed it today. 🎉";
  if (pct >= 60)   return `${pct}% done — almost there! 💪`;
  if (pct >= 30)   return `${pct}% complete. Keep the streak! 🔥`;
  return "Let's get started — one task at a time. ✨";
}

function isOverdue(due) { return due && due < new Date().toISOString().slice(0, 10); }

/* ─── Modal Helpers ───────────────────────────────────────── */
function openModal(id)  { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }

/* ─── New List Modal ──────────────────────────────────────── */
function openNewListModal() {
  $("#newListName").value = "";
  _selectedEmoji = "📝";
  const picker = $("#emojiPicker");
  picker.innerHTML = "";
  EMOJI_OPTIONS.forEach(e => {
    const btn = document.createElement("button");
    btn.textContent = e;
    btn.style.cssText = "font-size:22px;width:40px;height:40px;border-radius:10px;background:var(--cream);border:2px solid transparent;transition:all .15s;cursor:pointer;";
    if (e === _selectedEmoji) btn.style.borderColor = "var(--teal)";
    btn.onclick = () => {
      _selectedEmoji = e;
      picker.querySelectorAll("button").forEach(b => b.style.borderColor = "transparent");
      btn.style.borderColor = "var(--teal)";
    };
    picker.appendChild(btn);
  });
  openModal("newListModal");
  const nameInput = $("#newListName");
  nameInput.onkeydown = e => { if (e.key === "Enter") createList(); };
  setTimeout(() => nameInput.focus(), 80);
}

function createList() {
  const name = $("#newListName").value.trim();
  if (!name) return;
  const id = "custom_" + Date.now();
  const bgIdx = Object.keys(DATA.lists).filter(k => DATA.lists[k].custom).length % BG_PALETTE.length;
  DATA.lists[id] = { name, emoji:_selectedEmoji, bg:BG_PALETTE[bgIdx], custom:true };
  save();
  closeModal("newListModal");
  render();
}

function deleteList(id) {
  showConfirm(
    "Delete List",
    `Delete "${DATA.lists[id].name}" and all its tasks?`,
    () => {
      DATA.tasks = DATA.tasks.filter(t => t.list !== id);
      delete DATA.lists[id];
      if (state.list === id) { state.view = "dashboard"; }
      save(); render();
    }
  );
}

function clearListTasks(id) {
  showConfirm(
    "Clear All Tasks",
    `Are you sure you want to clear all tasks in "${DATA.lists[id].name}"?`,
    () => {
      DATA.tasks = DATA.tasks.filter(t => t.list !== id);
      save(); render();
    }
  );
}

/* ─── Task CRUD ───────────────────────────────────────────── */
function openAddTaskModal(defaultDue = "") {
  $("#taskModalTitle").textContent = "Add New Task";
  $("#taskModalSub").textContent = "Fill in the details below.";
  const titleInp = $("#modalTaskTitle");
  titleInp.value = "";
  $("#modalTaskDue").value = defaultDue || "";
  $("#editingTaskId").value = "";
  _selectedPrio = "Medium";
  document.querySelectorAll(".prio-pill").forEach(p => p.classList.toggle("selected", p.dataset.p === "Medium"));
  titleInp.onkeydown = e => { if (e.key === "Enter") saveTaskFromModal(); };
  openModal("taskModal");
  setTimeout(() => titleInp.focus(), 80);
}

function openEditModal(id) {
  const t = DATA.tasks.find(x => x.id == id);
  if (!t) return;
  $("#taskModalTitle").textContent = "Edit Task";
  $("#taskModalSub").textContent = "Update task details.";
  const titleInp = $("#modalTaskTitle");
  titleInp.value = t.title;
  $("#modalTaskDue").value = t.due || "";
  $("#editingTaskId").value = id;
  _selectedPrio = t.priority;
  document.querySelectorAll(".prio-pill").forEach(p => p.classList.toggle("selected", p.dataset.p === t.priority));
  titleInp.onkeydown = e => { if (e.key === "Enter") saveTaskFromModal(); };
  openModal("taskModal");
  setTimeout(() => titleInp.focus(), 80);
}

function selectPrio(btn) {
  _selectedPrio = btn.dataset.p;
  document.querySelectorAll(".prio-pill").forEach(p => p.classList.toggle("selected", p === btn));
}

function saveTaskFromModal() {
  const title = $("#modalTaskTitle").value.trim();
  if (!title) return;
  const due    = $("#modalTaskDue").value;
  const editId = $("#editingTaskId").value;

  if (editId) {
    const t = DATA.tasks.find(x => x.id == editId);
    if (t) { t.title = title; t.priority = _selectedPrio; t.due = due; }
  } else {
    const targetList = (state.view === "list" && DATA.lists[state.list]) ? state.list : (DATA.lists[state.list] ? state.list : "personal");
    DATA.tasks.push({ id:DATA.nextId++, list:targetList, title, priority:_selectedPrio, done:false, due });
  }
  save();
  closeModal("taskModal");
  render();
}

function toggleTask(id) {
  const t = DATA.tasks.find(x => x.id == id);
  if (t) { t.done = !t.done; save(); render(); }
}

function deleteTask(id) {
  showConfirm("Delete Task", "Are you sure you want to delete this task?", () => {
    DATA.tasks = DATA.tasks.filter(x => x.id != id);
    save(); render();
  });
}

/* ─── Confirm Dialog ──────────────────────────────────────── */
function showConfirm(title, msg, onYes) {
  $("#confirmTitle").textContent = title;
  $("#confirmMsg").textContent = msg;
  const btn = $("#confirmYesBtn");
  btn.onclick = () => { onYes(); closeModal("confirmModal"); };
  openModal("confirmModal");
}

/* ─── Sidebar Nav Render ──────────────────────────────────── */
function renderNav() {
  const nav = $("#navLists");
  nav.innerHTML = "";

  // Views section
  const viewsLabel = el("div", "nav-label", "Views");
  nav.appendChild(viewsLabel);

  const isDashActive = state.view === "dashboard";
  const dashBtn = el("button", "nav-item" + (isDashActive ? " active" : ""));
  dashBtn.innerHTML = `<span class="ic" style="background:var(--amber-tint)">🏠</span> Dashboard`;
  dashBtn.onclick = () => { state.view = "dashboard"; closeDrawer(); render(); };
  nav.appendChild(dashBtn);

  const isCalActive = state.view === "calendar";
  const calBtn = el("button", "nav-item" + (isCalActive ? " active" : ""));
  const scheduledCount = DATA.tasks.filter(t => t.due && t.due !== "").length;
  calBtn.innerHTML = `<span class="ic" style="background:var(--teal-tint)">📅</span> Calendar ${scheduledCount ? `<span class="count">${scheduledCount}</span>` : ""}`;
  calBtn.onclick = () => { state.view = "calendar"; closeDrawer(); render(); };
  nav.appendChild(calBtn);

  // Lists section
  const listsLabel = el("div", "nav-label", "My Lists");
  listsLabel.style.marginTop = "12px";
  nav.appendChild(listsLabel);

  Object.keys(DATA.lists).forEach(id => {
    const meta    = DATA.lists[id];
    const count   = tasksFor(id).length;
    const isActive = state.list === id && state.view === "list";
    const btn = el("button", "nav-item" + (isActive ? " active" : ""));
    btn.innerHTML = `<span class="ic" style="background:${meta.bg}">${meta.emoji}</span> ${esc(meta.name)} ${count ? `<span class="count">${count}</span>` : ""}${meta.custom ? `<button class="del-list" title="Delete list" onclick="event.stopPropagation();deleteList('${id}')">✕</button>` : ""}`;
    btn.onclick = () => { state.view = "list"; state.list = id; state.tab = "All"; closeDrawer(); render(); };
    nav.appendChild(btn);
  });
  $("#footerMotivation").textContent = motivationText();
}

/* ─── Dashboard View ──────────────────────────────────────── */
function renderDashboard(container) {
  const total   = DATA.tasks.length;
  const done    = DATA.tasks.filter(t => t.done).length;
  const pending = total - done;
  const pct     = total ? Math.round(done / total * 100) : 0;

  const hero = el("div", "hero", `
    <div class="hero-text">
      <h1>${greeting()}, ${esc(DATA.user?.name || "Ender")} 👋</h1>
      <p>${pending === 0 ? "Nothing due today — enjoy the calm! 🎉" : `You have <strong>${pending}</strong> task${pending !== 1 ? "s" : ""} waiting.`}</p>
    </div>
    <div class="hero-emoji">
      <svg viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="100" cy="146" rx="70" ry="8" fill="var(--cream-deep)"/>
        <circle cx="150" cy="30" r="18" fill="var(--amber)" opacity=".9"/>
        <path d="M40 60 q14 -12 28 0" stroke="var(--sky)" stroke-width="5" stroke-linecap="round" fill="none" opacity=".7"/>
        <path d="M30 74 q14 -12 28 0" stroke="var(--sky)" stroke-width="5" stroke-linecap="round" fill="none" opacity=".45"/>
        <rect x="58" y="86" width="58" height="42" rx="8" fill="var(--white)" stroke="var(--cream-deep)" stroke-width="2"/>
        <rect x="68" y="96" width="26" height="5" rx="2.5" fill="var(--teal-tint)"/>
        <rect x="68" y="96" width="${Math.round(20 * (pct / 100) + 6)}" height="5" rx="2.5" fill="var(--teal)"/>
        <rect x="68" y="107" width="26" height="5" rx="2.5" fill="var(--coral-tint)"/>
        <rect x="68" y="107" width="12" height="5" rx="2.5" fill="var(--coral)"/>
        <rect x="68" y="118" width="26" height="5" rx="2.5" fill="var(--amber-tint)"/>
        <circle cx="100" cy="70" r="17" fill="#FFE8CF"/>
        <path d="M84 63c0-10 7-15 16-15s16 5 16 15c0 2-6 4-16 4s-16-2-16-4Z" fill="#4A3B63"/>
        <circle cx="95" cy="70" r="1.6" fill="#4A3B63"/>
        <circle cx="105" cy="70" r="1.6" fill="#4A3B63"/>
        <path d="M95 74.5c1.4 1.1 4.1 1.1 5.6 0" stroke="#C77B4F" stroke-width="1.3" stroke-linecap="round" fill="none"/>
        <path d="M82 84c4-6 10-9 18-9s14 3 18 9" stroke="var(--lilac)" stroke-width="6" stroke-linecap="round" fill="none"/>
      </svg>
    </div>
  `);
  container.appendChild(hero);

  container.appendChild(el("div", "section-title", "My Lists"));
  const grid = el("div", "lists-grid");

  Object.keys(DATA.lists).forEach(id => {
    const meta  = DATA.lists[id];
    const count = tasksFor(id).length;
    const pend  = pendingCount(id);
    const card  = el("button", "list-card");
    card.innerHTML = `
      ${meta.custom ? `<button class="del-card" title="Delete list" onclick="event.stopPropagation();deleteList('${id}')">✕</button>` : ""}
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div class="blob" style="background:${meta.bg}">${meta.emoji}</div>
        ${pend ? `<div class="badge">${pend}</div>` : ""}
      </div>
      <h3>${esc(meta.name)}</h3>
      <div class="meta"><span>${count} task${count !== 1 ? "s" : ""}</span></div>
    `;
    card.onclick = () => { state.view = "list"; state.list = id; state.tab = "All"; render(); };
    grid.appendChild(card);
  });

  const newCard = el("button", "new-list-card", `<div class="plus-ic">+</div> Create new list`);
  newCard.onclick = openNewListModal;
  grid.appendChild(newCard);
  container.appendChild(grid);

  container.appendChild(el("div", "section-title", "Overview"));
  const circumference = 2 * Math.PI * 36;
  const overview = el("div", "overview-card", `
    <div class="ring-wrap">
      <svg width="86" height="86" viewBox="0 0 86 86">
        <circle cx="43" cy="43" r="36" fill="none" stroke="var(--cream-deep)" stroke-width="10"/>
        <circle cx="43" cy="43" r="36" fill="none" stroke="var(--teal)" stroke-width="10"
          stroke-linecap="round" stroke-dasharray="${circumference}"
          stroke-dashoffset="${circumference * (1 - pct / 100)}"
          transform="rotate(-90 43 43)"
          style="transition:stroke-dashoffset .6s ease"/>
        <text x="43" y="49" text-anchor="middle" font-family="Baloo 2" font-weight="700" font-size="18" fill="var(--ink)">${pct}%</text>
      </svg>
    </div>
    <div class="stat"><span class="num">${total}</span><span class="lbl">Total</span></div>
    <div class="overview-divider"></div>
    <div class="stat done"><span class="num">${done}</span><span class="lbl">Done</span></div>
    <div class="overview-divider"></div>
    <div class="stat pending"><span class="num">${pending}</span><span class="lbl">Pending</span></div>
  `);
  container.appendChild(overview);
}

/* ─── List Detail View ────────────────────────────────────── */
function renderListView(container) {
  const meta = DATA.lists[state.list];
  if (!meta) { state.view = "dashboard"; render(); return; }
  const listTasks = tasksFor(state.list);
  const pending   = listTasks.filter(t => !t.done).length;

  const back = el("button", "back-btn", "← Back to lists");
  back.onclick = () => { state.view = "dashboard"; render(); };
  container.appendChild(back);

  const header = el("div", "list-header", `
    <div style="display:flex;align-items:center;gap:18px;">
      <div class="blob" style="background:${meta.bg}">${meta.emoji}</div>
      <div>
        <h2>${esc(meta.name)}</h2>
        <p class="sub">${pending} pending · ${listTasks.length} total</p>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-left:auto;">
      ${meta.custom ? `
        <button class="btn-delete-list" onclick="deleteList('${state.list}')" title="Delete this list">
          🗑️ Delete List
        </button>
      ` : `
        <button class="btn-clear-list" onclick="clearListTasks('${state.list}')" title="Clear all tasks in list">
          🧹 Clear Tasks
        </button>
      `}
    </div>
  `);
  container.appendChild(header);

  // Add task inline row
  const addRow = el("div", "add-row");
  addRow.innerHTML = `
    <input type="text" id="newTaskInput" placeholder="Add a task and press Enter…">
    <input type="date" id="newTaskDue" class="due-input" title="Due date">
    <select id="newTaskPriority"><option>Low</option><option selected>Medium</option><option>High</option></select>
    <button class="submit" id="addTaskBtn">Add</button>
  `;
  container.appendChild(addRow);

  // Tabs: All / Active / Completed
  const tabs = el("div", "tabs");
  ["All", "Active", "Completed"].forEach(t => {
    const tab = el("button", "tab" + (state.tab === t ? " active" : ""), t);
    tab.onclick = () => { state.tab = t; render(); };
    tabs.appendChild(tab);
  });
  container.appendChild(tabs);

  let filtered = listTasks;
  if (state.tab === "Active")    filtered = listTasks.filter(t => !t.done);
  if (state.tab === "Completed") filtered = listTasks.filter(t =>  t.done);

  // Sort: pending first → priority → due date
  const prioOrder = { High:0, Medium:1, Low:2 };
  filtered.sort((a, b) => {
    if (a.done !== b.done) return a.done ? 1 : -1;
    if (prioOrder[a.priority] !== prioOrder[b.priority]) return prioOrder[a.priority] - prioOrder[b.priority];
    return (a.due || "9999") > (b.due || "9999") ? 1 : -1;
  });

  const taskList = el("div", "task-list");
  if (filtered.length === 0) {
    taskList.appendChild(el("div", "empty-state", `
      <div class="em">
        <svg viewBox="0 0 120 100" xmlns="http://www.w3.org/2000/svg">
          <ellipse cx="60" cy="92" rx="34" ry="6" fill="var(--cream-deep)"/>
          <path d="M40 60h40l-5 32H45Z" fill="var(--coral)"/>
          <path d="M40 60h40l-2 9H42Z" fill="var(--coral-tint)"/>
          <path d="M60 60c0-22-18-24-18-24s-2 18 18 24Z" fill="var(--teal)"/>
          <path d="M60 60c0-26 20-28 20-28s3 20-20 28Z" fill="var(--teal-deep)"/>
        </svg>
      </div>
      <p>Nothing here yet. Add your first task!</p>
    `));
  } else {
    filtered.forEach(t => {
      const row = el("div", `task-row priority-${t.priority}${t.done ? " done" : ""}`);
      const dueLabel = t.due ? `<span class="task-due${isOverdue(t.due) && !t.done ? " overdue" : ""}">📅 ${t.due}</span>` : "";
      row.innerHTML = `
        <button class="checkbox ${t.done ? "checked" : ""}" data-id="${t.id}" aria-label="Toggle task">${t.done ? "✓" : ""}</button>
        <div class="task-body">
          <p class="task-title">${esc(t.title)}</p>
          <span class="pill ${t.priority}">${t.priority}</span>${dueLabel}
        </div>
        <div class="task-actions">
          <button class="icon-btn edit-btn" data-id="${t.id}" title="Edit">✏</button>
          <button class="icon-btn del-btn" data-id="${t.id}" title="Delete">✕</button>
        </div>
      `;
      taskList.appendChild(row);
    });
  }
  container.appendChild(taskList);

  // Wire up task row event handlers
  container.querySelectorAll(".checkbox").forEach(cb => {
    cb.onclick = () => toggleTask(+cb.dataset.id);
  });
  container.querySelectorAll(".del-btn").forEach(btn => {
    btn.onclick = () => deleteTask(+btn.dataset.id);
  });
  container.querySelectorAll(".edit-btn").forEach(btn => {
    btn.onclick = () => openEditModal(+btn.dataset.id);
  });

  function addTask() {
    const input = $("#newTaskInput");
    const val   = input.value.trim();
    if (!val) return;
    const priority = $("#newTaskPriority").value;
    const due      = $("#newTaskDue").value;
    DATA.tasks.push({ id:DATA.nextId++, list:state.list, title:val, priority, done:false, due });
    save();
    render();
  }
  $("#addTaskBtn").onclick = addTask;
  $("#newTaskInput").onkeydown = e => { if (e.key === "Enter") addTask(); };
}

/* ─── Search View ─────────────────────────────────────────── */
function renderSearchView(container, query) {
  const q       = query.toLowerCase();
  const results = DATA.tasks.filter(t => t.title.toLowerCase().includes(q));

  container.appendChild(el("div", "search-results-title", `Search results for "${esc(query)}" · ${results.length} found`));

  if (results.length === 0) {
    container.appendChild(el("div", "empty-state", "<p>No tasks match that search.</p>"));
    return;
  }

  const taskList = el("div", "task-list");
  results.forEach(t => {
    const meta = DATA.lists[t.list];
    const row  = el("div", `task-row priority-${t.priority}${t.done ? " done" : ""}`);
    const hi   = esc(t.title).replace(new RegExp(`(${esc(q)})`, "gi"), '<mark class="search-highlight">$1</mark>');
    row.innerHTML = `
      <button class="checkbox ${t.done ? "checked" : ""}" data-id="${t.id}">${t.done ? "✓" : ""}</button>
      <div class="task-body">
        <p class="task-title">${hi}</p>
        <span class="pill ${t.priority}">${t.priority}</span>
        ${meta ? `<span style="font-size:11px;color:var(--ink-faint);margin-left:6px;">${meta.emoji} ${esc(meta.name)}</span>` : ""}
      </div>
      <div class="task-actions">
        <button class="icon-btn edit-btn" data-id="${t.id}" title="Edit">✏</button>
        <button class="icon-btn del-btn" data-id="${t.id}" title="Delete">✕</button>
      </div>
    `;
    taskList.appendChild(row);
  });
  container.appendChild(taskList);

  container.querySelectorAll(".checkbox").forEach(cb => cb.onclick = () => toggleTask(+cb.dataset.id));
  container.querySelectorAll(".del-btn").forEach(b  => b.onclick  = () => deleteTask(+b.dataset.id));
  container.querySelectorAll(".edit-btn").forEach(b => b.onclick  = () => openEditModal(+b.dataset.id));
}

/* ─── Calendar View ───────────────────────────────────────── */
const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];
const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function renderCalendarView(container) {
  const year = state.calYear;
  const month = state.calMonth; // 0-indexed

  // Header element
  const header = el("div", "calendar-header");

  // Title group: Month & Year Picker Button
  const titleGroup = el("div", "calendar-title-group");

  const monthYearBtn = el("button", "month-year-btn");
  monthYearBtn.innerHTML = `<span>📅 ${MONTH_NAMES[month]} ${year}</span><span class="chevron">▾</span>`;
  monthYearBtn.title = "Click to change month or year";
  monthYearBtn.onclick = () => openMonthYearPickerModal();
  titleGroup.appendChild(monthYearBtn);

  // Nav buttons: <, Today, >
  const navBtns = el("div", "calendar-nav-btns");

  const prevBtn = el("button", "btn-cal-nav", "◄");
  prevBtn.title = "Previous Month";
  prevBtn.onclick = () => {
    if (state.calMonth === 0) {
      state.calMonth = 11;
      state.calYear--;
    } else {
      state.calMonth--;
    }
    render();
  };

  const todayBtn = el("button", "btn-cal-nav btn-cal-today", "Today");
  todayBtn.onclick = () => {
    const now = new Date();
    state.calYear = now.getFullYear();
    state.calMonth = now.getMonth();
    render();
  };

  const nextBtn = el("button", "btn-cal-nav", "►");
  nextBtn.title = "Next Month";
  nextBtn.onclick = () => {
    if (state.calMonth === 11) {
      state.calMonth = 0;
      state.calYear++;
    } else {
      state.calMonth++;
    }
    render();
  };

  navBtns.appendChild(prevBtn);
  navBtns.appendChild(todayBtn);
  navBtns.appendChild(nextBtn);
  titleGroup.appendChild(navBtns);
  header.appendChild(titleGroup);

  // Calculate stats for this month
  const monthPrefix = `${year}-${String(month + 1).padStart(2, "0")}`;
  const monthTasks = DATA.tasks.filter(t => t.due && t.due.startsWith(monthPrefix));
  const monthCompleted = monthTasks.filter(t => t.done).length;

  const stats = el("div", "calendar-stats");
  stats.innerHTML = `
    <div class="cal-stat-pill">Scheduled: <strong>${monthTasks.length}</strong></div>
    <div class="cal-stat-pill">Completed: <strong>${monthCompleted}</strong></div>
  `;
  header.appendChild(stats);

  container.appendChild(header);

  // Calendar Grid
  const grid = el("div", "calendar-grid");

  // Render Day Headers (Sun-Sat)
  DAY_NAMES.forEach(dayName => {
    grid.appendChild(el("div", "calendar-day-header", dayName));
  });

  // Calculate calendar grid days
  const firstDayIndex = new Date(year, month, 1).getDay(); // 0 = Sun
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrevMonth = new Date(year, month, 0).getDate();

  const totalCells = Math.ceil((firstDayIndex + daysInMonth) / 7) * 7;
  const todayStr = new Date().toISOString().slice(0, 10);

  for (let i = 0; i < totalCells; i++) {
    let dayNum, dateStr, isCurrentMonth = true;

    if (i < firstDayIndex) {
      // Previous month trailing days
      isCurrentMonth = false;
      dayNum = daysInPrevMonth - firstDayIndex + i + 1;
      let prevM = month - 1, prevY = year;
      if (prevM < 0) { prevM = 11; prevY--; }
      dateStr = `${prevY}-${String(prevM + 1).padStart(2, "0")}-${String(dayNum).padStart(2, "0")}`;
    } else if (i >= firstDayIndex + daysInMonth) {
      // Next month leading days
      isCurrentMonth = false;
      dayNum = i - (firstDayIndex + daysInMonth) + 1;
      let nextM = month + 1, nextY = year;
      if (nextM > 11) { nextM = 0; nextY++; }
      dateStr = `${nextY}-${String(nextM + 1).padStart(2, "0")}-${String(dayNum).padStart(2, "0")}`;
    } else {
      // Current month days
      dayNum = i - firstDayIndex + 1;
      dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(dayNum).padStart(2, "0")}`;
    }

    const isToday = (dateStr === todayStr);
    const dayTasks = DATA.tasks.filter(t => t.due === dateStr);

    const cell = el("div", `calendar-cell${isToday ? " today" : ""}${!isCurrentMonth ? " other-month" : ""}`);
    cell.onclick = () => {
      openDayDetailModal(dateStr);
    };

    // Cell Header: Day Number + Add Button
    const cellHeader = el("div", "cell-header");
    cellHeader.innerHTML = `
      <span class="day-num">${dayNum}</span>
      <button class="cell-add-btn" title="Add task for this date" onclick="event.stopPropagation();openAddTaskModal('${dateStr}')">+</button>
    `;
    cell.appendChild(cellHeader);

    // Cell Tasks List — max 2 chips visible to strictly enforce 120px height
    const cellTasks = el("div", "cell-tasks");

    const maxVisible = 2;
    const visibleTasks = dayTasks.slice(0, maxVisible);

    visibleTasks.forEach(t => {
      const chip = el("div", `day-task-chip priority-${t.priority}${t.done ? " done" : ""}`);
      chip.title = `${t.title} (${t.priority})`;
      chip.innerHTML = `
        <span class="prio-dot ${t.priority}"></span>
        <span class="chip-title">${esc(t.title)}</span>
      `;
      chip.onclick = (e) => {
        e.stopPropagation();
        openEditModal(t.id);
      };
      cellTasks.appendChild(chip);
    });

    if (dayTasks.length > maxVisible) {
      const moreCount = dayTasks.length - maxVisible;
      const morePill = el("div", "day-task-more", `+${moreCount} more`);
      cellTasks.appendChild(morePill);
    }

    cell.appendChild(cellTasks);

    // Mobile task dots (rendered on phone view)
    if (dayTasks.length > 0) {
      const dots = el("div", "mobile-task-dots");
      dayTasks.slice(0, 3).forEach(t => {
        dots.appendChild(el("span", `prio-dot ${t.priority}`));
      });
      cell.appendChild(dots);
    }

    grid.appendChild(cell);
  }

  container.appendChild(grid);
}

/* ─── Month & Year Picker Modal ──────────────────────────── */
let _pickerYear = state.calYear;

function openMonthYearPickerModal() {
  _pickerYear = state.calYear;
  $("#pickerYearDisplay").textContent = _pickerYear;

  $("#btnPrevYear").onclick = () => {
    _pickerYear--;
    $("#pickerYearDisplay").textContent = _pickerYear;
    renderPickerMonths();
  };
  $("#btnNextYear").onclick = () => {
    _pickerYear++;
    $("#pickerYearDisplay").textContent = _pickerYear;
    renderPickerMonths();
  };

  renderPickerMonths();
  openModal("monthYearModal");
}

function renderPickerMonths() {
  const grid = $("#monthGrid");
  grid.innerHTML = "";
  MONTH_NAMES.forEach((mName, idx) => {
    const isActive = (idx === state.calMonth && _pickerYear === state.calYear);
    const tile = el("button", `month-tile${isActive ? " active" : ""}`, mName);
    tile.onclick = () => {
      state.calMonth = idx;
      state.calYear = _pickerYear;
      closeModal("monthYearModal");
      render();
    };
    grid.appendChild(tile);
  });
}

/* ─── Day Detail View Modal ──────────────────────────────── */
function openDayDetailModal(dateStr) {
  const [y, m, d] = dateStr.split("-").map(Number);
  const dateObj = new Date(y, m - 1, d);
  const options = { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' };
  const formattedDate = dateObj.toLocaleDateString('en-US', options);

  $("#dayDetailTitle").textContent = formattedDate;
  const dayTasks = DATA.tasks.filter(t => t.due === dateStr);
  $("#dayDetailSub").textContent = `${dayTasks.length} task${dayTasks.length !== 1 ? "s" : ""} scheduled for this day.`;

  const listContainer = $("#dayDetailTasksList");
  listContainer.innerHTML = "";

  if (dayTasks.length === 0) {
    listContainer.appendChild(el("div", "empty-state", `<p style="text-align:center;color:var(--ink-soft);padding:16px 0;">No tasks scheduled for ${formattedDate}.</p>`));
  } else {
    dayTasks.forEach(t => {
      const meta = DATA.lists[t.list];
      const row = el("div", `day-detail-row priority-${t.priority}${t.done ? " done" : ""}`);
      row.innerHTML = `
        <button class="checkbox ${t.done ? "checked" : ""}" data-id="${t.id}">${t.done ? "✓" : ""}</button>
        <div class="task-body" style="flex:1;">
          <p class="task-title" style="margin:0;font-weight:600;font-size:14px;color:var(--ink);">${esc(t.title)}</p>
          <span class="pill ${t.priority}" style="margin-top:2px;">${t.priority}</span>
          ${meta ? `<span style="font-size:11px;color:var(--ink-faint);margin-left:6px;">${meta.emoji} ${esc(meta.name)}</span>` : ""}
        </div>
        <div class="task-actions" style="display:flex;gap:6px;">
          <button class="icon-btn edit-btn" data-id="${t.id}" title="Edit">✏</button>
          <button class="icon-btn del-btn" data-id="${t.id}" title="Delete">✕</button>
        </div>
      `;
      listContainer.appendChild(row);
    });

    listContainer.querySelectorAll(".checkbox").forEach(cb => {
      cb.onclick = () => {
        toggleTask(+cb.dataset.id);
        openDayDetailModal(dateStr);
      };
    });
    listContainer.querySelectorAll(".edit-btn").forEach(btn => {
      btn.onclick = () => {
        closeModal("dayDetailModal");
        openEditModal(+btn.dataset.id);
      };
    });
    listContainer.querySelectorAll(".del-btn").forEach(btn => {
      btn.onclick = () => {
        deleteTask(+btn.dataset.id);
        closeModal("dayDetailModal");
      };
    });
  }

  $("#dayDetailAddTaskBtn").onclick = () => {
    closeModal("dayDetailModal");
    openAddTaskModal(dateStr);
  };

  openModal("dayDetailModal");
}

/* ─── Root Render ─────────────────────────────────────────── */
function render() {
  renderNav();
  const content = $("#content");
  content.innerHTML = "";
  const q = state.search.trim();
  if (q) {
    renderSearchView(content, q);
  } else if (state.view === "dashboard") {
    renderDashboard(content);
  } else if (state.view === "calendar") {
    renderCalendarView(content);
  } else {
    renderListView(content);
  }
}

/* ─── Mobile Drawer ───────────────────────────────────────── */
function openDrawer()  { $("#sidebar").classList.add("open");    $("#overlay").classList.add("show"); }
function closeDrawer() { $("#sidebar").classList.remove("open"); $("#overlay").classList.remove("show"); }
$("#hamburger").onclick   = openDrawer;
$("#drawerClose").onclick = closeDrawer;
$("#overlay").onclick     = closeDrawer;

/* ─── Search Bar ──────────────────────────────────────────── */
const searchInput = $("#searchInput");
const searchClearBtn = $("#searchClearBtn");

function updateSearch() {
  state.search = searchInput ? searchInput.value : "";
  if (searchClearBtn) {
    searchClearBtn.style.display = state.search ? "flex" : "none";
  }
  render();
}

if (searchInput) {
  searchInput.oninput = updateSearch;
  searchInput.onkeydown = e => {
    if (e.key === "Escape") {
      if (searchInput) searchInput.value = "";
      updateSearch();
    }
  };
}

if (searchClearBtn) {
  searchClearBtn.onclick = () => {
    if (searchInput) searchInput.value = "";
    updateSearch();
    if (searchInput) searchInput.focus();
  };
}

/* ─── Floating Action Button ──────────────────────────────── */
$("#fab").onclick = () => {
  if (state.view === "dashboard") { state.view = "list"; state.list = "personal"; state.tab = "All"; render(); }
  openAddTaskModal();
};

/* ─── Add List Button ─────────────────────────────────────── */
$("#addListBtn").onclick = openNewListModal;

/* ─── Keyboard Shortcuts ──────────────────────────────────── */
document.addEventListener("keydown", e => {
  if (document.querySelector(".modal-overlay.open")) return;
  if (e.key === "n" && !["INPUT","SELECT","TEXTAREA"].includes(document.activeElement.tagName)) {
    if (state.view === "list" || state.view === "calendar") openAddTaskModal();
  }
  if ((e.key === "c" || e.key === "C") && !["INPUT","SELECT","TEXTAREA"].includes(document.activeElement.tagName)) {
    state.view = "calendar"; render();
  }
  if (e.key === "/" && !["INPUT","SELECT","TEXTAREA"].includes(document.activeElement.tagName)) {
    e.preventDefault(); searchInput.focus();
  }
  if (e.key === "Escape" && (state.view === "list" || state.view === "calendar")) { state.view = "dashboard"; render(); }
});

/* ─── Profile Popover & Account Handlers ──────────────────── */
const avatarBtn      = $("#avatarBtn");
const profilePopover = $("#profilePopover");

function toggleProfilePopover(e) {
  e.stopPropagation();
  profilePopover.classList.toggle("open");
}

if (avatarBtn && profilePopover) {
  avatarBtn.onclick = toggleProfilePopover;
  document.addEventListener("click", e => {
    if (!profilePopover.contains(e.target) && !avatarBtn.contains(e.target)) {
      profilePopover.classList.remove("open");
    }
  });
}

function openAccountModal() {
  profilePopover.classList.remove("open");
  const nameInp = $("#accountNameInput");
  const emailInp = $("#accountEmailInput");
  nameInp.value  = DATA.user?.name  || "Ender";
  emailInp.value = DATA.user?.email || "ender@taskly.app";
  nameInp.onkeydown = e => { if (e.key === "Enter") saveAccountSettings(); };
  emailInp.onkeydown = e => { if (e.key === "Enter") saveAccountSettings(); };
  openModal("accountModal");
}

function saveAccountSettings() {
  const name  = $("#accountNameInput").value.trim()  || "Ender";
  const email = $("#accountEmailInput").value.trim() || "ender@taskly.app";
  DATA.user = { name, email };
  save();
  closeModal("accountModal");
  const popName = $("#popoverName");
  if (popName) popName.innerHTML = `${esc(name)} <span class="pro-badge">PRO</span>`;
  const popEmail = $("#popoverEmail");
  if (popEmail) popEmail.textContent = email;
  render();
}

function openShortcutsModal() {
  profilePopover.classList.remove("open");
  openModal("shortcutsModal");
}

function applyTheme(t) {
  state.theme = t || "light";
  if (state.theme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
  const tag = document.querySelector("#btn-theme-preset .p-tag");
  if (tag) {
    tag.textContent = state.theme === "dark" ? "AMOLED Black" : "Cream Pastel";
  }
  localStorage.setItem("taskly_theme", state.theme);
}

function toggleThemeNotice() {
  profilePopover.classList.remove("open");
  const newTheme = state.theme === "dark" ? "light" : "dark";
  applyTheme(newTheme);
}

// Auto-apply saved theme on boot
const savedTheme = localStorage.getItem("taskly_theme") || "light";
applyTheme(savedTheme);

function confirmSignOut() {
  profilePopover.classList.remove("open");
  showConfirm("Sign Out", "Are you sure you want to sign out of Taskly?", () => {
    alert("👋 Signed out successfully! Demo session reloaded.");
  });
}

/* ─── Close Modals on Backdrop Click ─────────────────────── */
document.querySelectorAll(".modal-overlay").forEach(ov => {
  ov.onclick = e => { if (e.target === ov) ov.classList.remove("open"); };
});

/* ─── Boot ── handled by init() above ────────────────────── */
// init() is called at the top of the file after state is declared.
// It detects the Flask API, loads data (server or localStorage), then calls render().
