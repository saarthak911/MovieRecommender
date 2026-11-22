/* CineMatch frontend: plain JS, no build step.
 * Behaviour (views, likes, searches, genre taps) is kept in localStorage and sent to the
 * API on each request; the ML model on the server turns it into a taste profile. */
(() => {
  "use strict";

  const LS_KEY = "cinematch.events.v1";
  const MAX_EVENTS = 200;
  const state = { events: loadEvents(), genres: [], activeGenre: null, mode: "home", homeDirty: true, reqId: 0 };
  const $ = (id) => document.getElementById(id);
  const view = $("view"), chipsEl = $("chips"), modal = $("modal"), modalBody = $("modal-body");
  let lastFocus = null, toastTimer = null, searchTimer = null, logTimer = null, lastLoggedQuery = "";

  // ---------- storage ----------
  function loadEvents() {
    try {
      const parsed = JSON.parse(localStorage.getItem(LS_KEY));
      return Array.isArray(parsed) ? parsed.slice(-MAX_EVENTS) : [];
    } catch { return []; }
  }
  function saveEvents() {
    try { localStorage.setItem(LS_KEY, JSON.stringify(state.events)); } catch { /* private mode: keep in memory */ }
  }
  function logEvent(ev) {
    state.events.push({ ...ev, ts: Date.now() });
    state.events = state.events.slice(-MAX_EVENTS);
    state.homeDirty = true;
    saveEvents();
    updateActivity();
  }
  function reaction(id) {
    for (let i = state.events.length - 1; i >= 0; i--) {
      const e = state.events[i];
      if (e.movie_id === id && (e.type === "like" || e.type === "dislike")) return e.type;
    }
    return null;
  }
  function setReaction(id, type) {
    const current = reaction(id);
    state.events = state.events.filter((e) => !(e.movie_id === id && (e.type === "like" || e.type === "dislike")));
    if (current !== type) logEvent({ type, movie_id: id });
    else { state.homeDirty = true; saveEvents(); updateActivity(); }
    return current === type ? null : type;
  }

  // ---------- helpers ----------
  function h(tag, attrs, ...kids) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
      else if (k === "class") node.className = v;
      else if (k === "style") node.setAttribute("style", v);
      else node.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat()) {
      if (kid == null || kid === false) continue;
      node.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    }
    return node;
  }
  // Served by Flask (port 5000 or a real domain) -> same origin. Opened from another static
  // server (VS Code Live Server on 5500, file://, ...) -> talk to the Flask API directly.
  const API_BASE = window.CINEMATCH_API ?? (location.protocol === "file:" || !["", "5000"].includes(location.port) ? "http://127.0.0.1:5000" : "");
  async function api(path, body) {
    const res = await fetch(API_BASE + path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : undefined);
    if (!res.ok) throw new Error(`${path} → ${res.status}`);
    return res.json();
  }
  function hueFor(genre = "") {
    let n = 0;
    for (const c of genre) n = (n * 31 + c.charCodeAt(0)) % 360;
    return n;
  }
  function toast(msg) {
    const t = $("toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 2200);
  }
  function updateActivity() {
    const n = state.events.length;
    $("activity").textContent = n ? `${n} action${n === 1 ? "" : "s"} remembered in this browser.` : "No history yet: open movies, search or tap genres to teach the model your taste.";
  }

  // ---------- rendering ----------
  function movieCard(m) {
    const liked = reaction(m.id) === "like";
    return h("button", { class: "card", type: "button", "aria-label": `${m.title}${m.year ? ", " + m.year : ""}`, onclick: () => openMovie(m.id) },
      h("div", { class: "poster", "data-id": m.id, style: `--h:${hueFor(m.genres[0])}` },
        h("span", { class: "rating" }, `★ ${m.rating.toFixed(1)}`),
        liked && h("span", { class: "badge-liked", "aria-label": "You liked this" }, "❤️"),
        h("span", { class: "ptitle" }, m.title),
        h("span", { class: "pyear" }, m.year || "")),
      h("div", { class: "meta" },
        h("span", { class: "genres" }, m.genres.slice(0, 2).join(" · ")),
        m.reason && h("span", { class: "reason" }, m.reason)));
  }
  function section(title, movies, { grid = false, sub = "" } = {}) {
    return h("section", { class: "section" },
      h("div", { class: "section-head" }, h("h2", null, title), sub && h("span", { class: "sub" }, sub)),
      h("div", { class: grid ? "grid" : "row" }, movies.map(movieCard)));
  }
  function tastePanel(taste) {
    if (!taste.length) return null;
    return h("section", { class: "taste", "aria-label": "Your taste profile" },
      h("h2", null, "Your taste so far"),
      h("p", null, "Learned from what you opened, liked, searched and tapped. Recent activity counts more."),
      h("div", { class: "taste-bars" }, taste.map((t) =>
        h("div", { class: "bar" },
          h("span", null, t.genre),
          h("div", { class: "bar-track" }, h("div", { class: "bar-fill", style: `width:${Math.round(t.share * 100)}%` })),
          h("span", { class: "bar-pct" }, `${Math.round(t.share * 100)}%`)))));
  }
  function setView(...nodes) {
    view.replaceChildren(...nodes.filter(Boolean));
    hydratePosters(view);
  }

  // ---------- posters (optional: needs TMDB_API_KEY on the server) ----------
  // Cards always render with a coloured placeholder first; real posters fade in on top.
  const posterCache = new Map(); // movie id -> url | null
  let postersEnabled = false;
  function applyPoster(node, url) {
    if (!url) return;
    const img = h("img", { src: url, alt: "", decoding: "async", referrerpolicy: "no-referrer", loading: node.classList.contains("poster") ? "lazy" : "eager" });
    img.addEventListener("load", () => node.classList.add("has-img"));
    img.addEventListener("error", () => img.remove()); // keep the placeholder if the image fails
    node.prepend(img);
  }
  async function hydratePosters(root) {
    if (!postersEnabled) return;
    const nodes = [...root.querySelectorAll("[data-id]")].filter((n) => !n.dataset.posterDone);
    nodes.forEach((n) => { n.dataset.posterDone = "1"; });
    const need = [...new Set(nodes.map((n) => Number(n.dataset.id)))].filter((id) => !posterCache.has(id));
    try {
      for (let i = 0; i < need.length; i += 60) {
        const chunk = need.slice(i, i + 60);
        const data = await api("/api/posters", { ids: chunk });
        chunk.forEach((id) => posterCache.set(id, data.posters[String(id)] ?? null));
      }
    } catch (err) { console.warn("posters unavailable", err); return; }
    nodes.forEach((n) => applyPoster(n, posterCache.get(Number(n.dataset.id))));
  }
  function empty(msg) { return h("p", { class: "empty" }, msg); }

  // ---------- screens ----------
  async function showHome() {
    state.mode = "home"; state.activeGenre = null; renderChips();
    const id = ++state.reqId;
    try {
      const data = await api("/api/home", { events: state.events });
      if (id !== state.reqId) return;
      state.homeDirty = false;
      const nodes = [];
      if (!data.personalised) nodes.push(h("p", { class: "empty", style: "padding-bottom:0" }, "Tap a genre, search, or open a few movies. Your recommendations adapt straight away."));
      nodes.push(tastePanel(data.taste));
      for (const row of data.rows) nodes.push(section(row.title, row.movies));
      if (data.recent.length) nodes.push(section("Recently viewed", data.recent));
      setView(...nodes);
    } catch (err) { showError(err); }
  }
  async function showGenre(name) {
    state.mode = "genre"; state.activeGenre = name; renderChips();
    const id = ++state.reqId;
    try {
      const data = await api(`/api/genre/${encodeURIComponent(name)}`, { events: state.events });
      if (id !== state.reqId) return;
      setView(data.results.length ? section(`${name}, ranked for you`, data.results, { grid: true, sub: `${data.results.length} picks` }) : empty(`No ${name} movies found.`));
    } catch (err) { showError(err); }
  }
  async function showSearch(q) {
    state.mode = "search"; state.activeGenre = null; renderChips();
    const id = ++state.reqId;
    try {
      const data = await api("/api/search", { q, events: state.events });
      if (id !== state.reqId) return;
      setView(data.results.length ? section(`Results for “${q}”`, data.results, { grid: true }) : empty(`Nothing found for “${q}”. Try a genre, an actor or a few words from the plot.`));
    } catch (err) { showError(err); }
  }
  function showError(err) {
    console.error(err);
    setView(empty("Couldn't reach the recommendation server. Open a terminal in the backend folder, run “python app.py”, then reload this page."));
  }
  function renderChips() {
    const mk = (label, pressed, fn) => h("button", { class: "chip", type: "button", "aria-pressed": String(pressed), onclick: fn }, label);
    chipsEl.replaceChildren(
      mk("For you", state.mode === "home", () => { $("q").value = ""; showHome(); }),
      ...state.genres.map((g) => mk(g, state.activeGenre === g, () => {
        $("q").value = "";
        if (state.activeGenre === g) return showHome();
        logEvent({ type: "genre", genre: g });
        showGenre(g);
      })));
  }

  // ---------- movie details ----------
  async function openMovie(id) {
    if (modal.hidden) lastFocus = document.activeElement;
    try {
      const data = await api(`/api/movie/${id}`);
      const recent = [...state.events].reverse().find((e) => e.type === "view" && e.movie_id === id);
      if (!recent || Date.now() - recent.ts > 60_000) logEvent({ type: "view", movie_id: id });
      renderModal(data.movie, data.similar);
      hydratePosters(modalBody);
      modal.hidden = false;
      document.body.style.overflow = "hidden";
      $("modal-close").focus();
      modalBody.parentElement.scrollTop = 0;
    } catch (err) { console.error(err); toast("Couldn't load that movie."); }
  }
  function renderModal(m, similar) {
    const likeBtn = h("button", { class: "btn", type: "button", "aria-pressed": String(reaction(m.id) === "like") });
    const dislikeBtn = h("button", { class: "btn", type: "button", "aria-pressed": String(reaction(m.id) === "dislike") });
    const sync = () => {
      likeBtn.textContent = reaction(m.id) === "like" ? "❤️ Liked" : "🤍 Like";
      dislikeBtn.textContent = "👎 Not for me";
      likeBtn.setAttribute("aria-pressed", String(reaction(m.id) === "like"));
      dislikeBtn.setAttribute("aria-pressed", String(reaction(m.id) === "dislike"));
    };
    likeBtn.onclick = () => { const r = setReaction(m.id, "like"); sync(); toast(r ? "Noted. You'll see more like this." : "Like removed."); };
    dislikeBtn.onclick = () => { const r = setReaction(m.id, "dislike"); sync(); toast(r ? "Got it. Fewer picks like this." : "Removed."); };
    sync();

    modalBody.replaceChildren(
      h("div", { class: "detail-hero", style: `--h:${hueFor(m.genres[0])}` },
        h("div", { class: "hero-flex" },
          h("div", { class: "detail-poster", "data-id": m.id }),
          h("div", { class: "hero-text" },
            h("h2", { id: "m-title" }, m.title),
            h("div", { class: "facts" },
              h("span", { class: "star" }, `★ ${m.rating.toFixed(1)}`),
              h("span", null, `${m.votes.toLocaleString()} votes`),
              m.year && h("span", null, m.year),
              m.director && h("span", null, `Directed by ${m.director}`)),
            h("div", { class: "tags" }, m.genres.map((g) => h("span", { class: "tag" }, g)))))),
      h("div", { class: "detail-body" },
        h("p", null, m.overview || "No description available."),
        m.cast.length && h("p", { class: "credit" }, h("b", null, "Starring "), m.cast.join(", ")),
        h("div", { class: "actions" }, likeBtn, dislikeBtn)),
      similar.length && section("More like this", similar));
  }
  function closeModal() {
    if (modal.hidden) return;
    modal.hidden = true;
    document.body.style.overflow = "";
    if (lastFocus && document.contains(lastFocus)) lastFocus.focus();
    if (state.mode === "home" && state.homeDirty) showHome();
  }

  // ---------- search box ----------
  const input = $("q");
  input.addEventListener("input", () => {
    clearTimeout(searchTimer); clearTimeout(logTimer);
    const q = input.value.trim();
    if (q.length < 2) { if (!q && state.mode === "search") showHome(); return; }
    searchTimer = setTimeout(() => showSearch(q), 300);
    // remember the search as a taste signal once the user pauses on it
    logTimer = setTimeout(() => commitSearch(q), 1500);
  });
  $("search-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (q.length < 2) return;
    clearTimeout(searchTimer); clearTimeout(logTimer);
    commitSearch(q);
    showSearch(q);
  });
  function commitSearch(q) {
    if (q.toLowerCase() === lastLoggedQuery) return;
    lastLoggedQuery = q.toLowerCase();
    logEvent({ type: "search", query: q });
  }

  // ---------- wiring ----------
  $("modal-close").addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });
  $("clear").addEventListener("click", () => {
    if (state.events.length && !confirm("Forget your viewing history and start over?")) return;
    state.events = []; lastLoggedQuery = ""; saveEvents(); updateActivity(); input.value = "";
    toast("History cleared.");
    showHome();
  });

  (async function init() {
    updateActivity();
    try {
      const info = await api("/api/info");
      state.genres = info.genres;
      postersEnabled = !!info.posters;
      $("tmdb-credit").hidden = !postersEnabled;
      const notes = [];
      if (info.source === "demo") notes.push("Demo catalogue (", String(info.count), " movies). Add ", h("code", null, "tmdb_5000_movies.csv"), " and ", h("code", null, "tmdb_5000_credits.csv"), " to the ", h("code", null, "data/"), " folder and restart to use the full TMDB 5000 dataset. ");
      if (!postersEnabled) notes.push("Posters are off: set the ", h("code", null, "TMDB_API_KEY"), " environment variable and restart the server to show them.");
      if (notes.length) { const n = $("notice"); n.hidden = false; n.replaceChildren(...notes); }
    } catch (err) { return showError(err); }
    renderChips();
    showHome();
  })();
})();
