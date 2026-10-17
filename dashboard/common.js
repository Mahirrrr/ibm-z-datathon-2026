// Shared helpers for every dashboard page.
const TIERS = {
  missing_documents: { label: "Denied for missing documents", color: "#da1e28" },
  unverified_ownership_or_occupancy: { label: "Ownership or occupancy never verified", color: "#ff8389" },
  lost_contact: { label: "Denied after FEMA lost contact", color: "#8d8d8d" },
};

async function api(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} returned ${res.status}`);
  return res.json();
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
