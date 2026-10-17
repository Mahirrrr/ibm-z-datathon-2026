// Shared helpers for every dashboard page.
const TIERS = {
  missing_documents: { label: "Denied for missing documents", color: "#da1e28" },
  unverified_ownership_or_occupancy: { label: "Ownership or occupancy never verified", color: "#ff8389" },
  lost_contact: { label: "Denied after FEMA lost contact", color: "#8d8d8d" },
};

// Static snapshot (GitHub Pages): static.js sets SECOND_LOOK_STATIC and the API's responses
// are read from data/*.json, written by pipeline/static_site.py from the real API.
const STATIC = window.SECOND_LOOK_STATIC || null;

function staticRequest(path) {
  const url = new URL(path, location.origin);
  const q = url.searchParams;
  const slice = (rows) => rows.slice(Number(q.get("offset") || 0), Number(q.get("offset") || 0) + Number(q.get("limit") || rows.length));
  let m;
  if (url.pathname === "/api/disasters") return ["data/disasters.json", slice];
  if ((m = url.pathname.match(/^\/api\/disasters\/(\d+)\/callbacks$/))) return [`data/callbacks/${m[1]}.json`, slice];
  if ((m = url.pathname.match(/^\/api\/disasters\/(\d+)$/))) return [`data/disasters/${m[1]}.json`, (x) => x];
  return [`data/${url.pathname.replace("/api/", "")}.json`, (x) => x];
}

async function api(path) {
  const [target, shape] = STATIC ? staticRequest(path) : [path, (x) => x];
  const res = await fetch(target);
  if (!res.ok) throw new Error(`${path} returned ${res.status}`);
  return shape(await res.json());
}

function csvUrl(number) {
  return STATIC ? `data/csv/second_look_${number}.csv` : `/api/disasters/${number}/callbacks.csv`;
}

if (STATIC) {
  document.addEventListener("DOMContentLoaded", () => {
    const live = STATIC.live_url ? [" · ", el("a", { href: STATIC.live_url }, "Open the live version on IBM LinuxONE")] : [];
    document.body.prepend(el("div", { class: "snapshot" },
      `Static snapshot (${STATIC.snapshot}) of the dashboard that runs in a hardened container on IBM z17. Same data, same API responses.`, ...live));
  });
}

const fmt = {
  int: (n) => Math.round(n).toLocaleString("en-US"),
  money: (n) => "$" + Math.round(n).toLocaleString("en-US"),
  compactMoney: (n) =>
    n >= 1e9 ? `$${(n / 1e9).toFixed(2)}B` : n >= 1e6 ? `$${(n / 1e6).toFixed(1)}M` : fmt.money(n),
  compact: (n) => (n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : fmt.int(n)),
  pct: (x, digits = 2) => `${(x * 100).toFixed(digits)}%`,
  ratio: (x) => `${x.toFixed(x >= 10 ? 0 : 2)}x`,
};

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "style") node.style.cssText = v;
    else node.setAttribute(k, v);
  }
  node.append(...children);
  return node;
}

function showError(target, err) {
  target.replaceChildren(el("p", { class: "note" }, `Couldn't load this section. ${err.message}`));
}
