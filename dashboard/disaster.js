// Disaster console: pick a disaster, see its cohort, and work the ranked callback list.
const PAGE_SIZE = 25;
const FACTORS = ["renter", "lowest income band", "age 65+", "needs accessibility support"];
const state = { disaster: null, offset: 0, rows: [], selected: null };

const $ = (id) => document.getElementById(id);

function bars(target, items, total) {
  const max = Math.max(1, ...items.map((i) => i.n));
  target.replaceChildren(
    ...items.map((i) =>
      el("div", { class: "hbar" },
        el("span", {}, i.label),
        el("div", { class: "track" }, el("div", { class: "fill", style: `width:${(i.n / max) * 100}%;background:${i.color}` })),
        el("span", { class: "n" }, `${Math.round((i.n / total) * 100)}%`))
    )
  );
}

function renderDisaster(d) {
  state.disaster = d;
  document.title = `Second Look · ${d.incident_name} #${d.disasterNumber}`;
  $("crumb").textContent = `second-look / disasters / ${d.disasterNumber}`;
  $("title").textContent = `${d.incident_name} · #${d.disasterNumber} · ${d.states.replaceAll(",", ", ")} · ${d.year}`;
  $("csv").href = csvUrl(d.disasterNumber);

  const tiles = [
    ["Second Look households", fmt.int(d.cohort), true],
    ["Verified loss", fmt.compactMoney(d.cohort_loss)],
    ["Not livable without repairs", fmt.int(d.needs_repairs)],
    ["Verified damage, then denied", fmt.pct(d.denied_verified / d.verified_damage, 1)],
    ["Applications", fmt.int(d.applications)],
  ];
  $("tiles").replaceChildren(
    ...tiles.map(([label, value, accent]) =>
      el("div", { class: "tile" }, el("div", { class: "label" }, label), el("div", { class: accent ? "value accent" : "value" }, value)))
  );

  bars($("tiers"), Object.entries(TIERS).map(([t, meta]) => ({ label: meta.label, n: d[`tier_${t}`], color: meta.color })), d.cohort);
  bars($("factors"), FACTORS.map((f) => ({ label: f[0].toUpperCase() + f.slice(1), n: d.factor_counts[f] || 0, color: "#78a9ff" })), d.cohort);
}

function draftScript(r) {
  const fix = {
    missing_documents: "Your application was denied because a document was missing. We can help you get it in and ask FEMA to take another look.",
    lost_contact: "FEMA tried to reach you and couldn't. We'd like to reopen your file and confirm the best way to reach you.",
    unverified_ownership_or_occupancy: "FEMA couldn't confirm you owned or lived in the home. A utility bill, lease, or a written statement from a landlord or neighbor can count as proof.",
  }[r.tier];
  return `Hello, this is a caseworker following up on your FEMA disaster aid application.\n\nAn inspector confirmed ${fmt.money(r.verified_loss)} in damage to your home. ${fix}\n\nCan we go through what's needed together now?`;
}

// Granite cites passages as [P1]; show the FEMA policy section instead.
function withSections(text, citations) {
  const bySection = Object.fromEntries(citations.map((c) => [c.ref, c.section]));
  return text.replace(/\[(P\d+)\]/g, (m, ref) => (bySection[ref] ? `[§${bySection[ref]}]` : m));
}

function scriptBlock(r) {
  const n = r.note;
  if (!n) {
    return [
      el("p", { class: "panel-title" }, "Draft callback script"),
      el("div", { class: "script" }, draftScript(r)),
      el("p", { class: "note" }, "Template draft. Granite-written notes cover the top callbacks in the largest disasters."),
    ];
  }
  return [
    el("p", { class: "panel-title" }, "Why this denial looks fixable ", el("span", { class: "tag granite" }, "Granite · cited")),
    el("p", { class: "llm" }, withSections(n.why_flagged, n.citations)),
    el("p", { class: "panel-title" }, "Callback script"),
    el("div", { class: "script" }, withSections(n.callback_script, n.citations)),
    el("p", { class: "panel-title" }, "FEMA policy cited"),
    el("ol", { class: "cites" },
      ...n.citations.map((c) => el("li", {}, el("details", {}, el("summary", {}, c.label), el("blockquote", {}, `${c.quote}…`))))),
    el("p", { class: "note" }, `Written by ${n.model} on IBM LinuxONE. Every citation was checked against the retrieved FEMA passages; dollar amounts were checked against the verified loss.`),
  ];
}

function renderDrawer(r) {
  if (!r) {
    $("drawer").replaceChildren(el("h3", {}, "Select a household"), el("p", { class: "note" }, "Pick a row to see why it was flagged and a draft callback script."));
    return;
  }
  $("drawer").replaceChildren(
    el("div", { class: "crumb" }, `rank ${r.rank_in_disaster} · record ${r.id}`),
    el("h3", {}, TIERS[r.tier].label),
    el("p", { class: "why" }, r.why_flagged),
    el("dl", {},
      el("dt", {}, "Priority"), el("dd", {}, r.priority.toFixed(2)),
      el("dt", {}, "Model score"), el("dd", {}, r.risk_score == null ? "n/a" : r.risk_score.toFixed(2)),
      el("dt", {}, "Loss percentile"), el("dd", {}, `${Math.round(r.loss_pct * 100)}th in this disaster`),
      el("dt", {}, "County"), el("dd", {}, `${r.county || "Unknown"}, ${r.damagedStateAbbreviation}`)),
    ...scriptBlock(r)
  );
}

function selectRow(r, tr) {
  state.selected = r;
  document.querySelectorAll("#callbacks tr.selected").forEach((n) => n.classList.remove("selected"));
  tr.classList.add("selected");
  renderDrawer(r);
}

async function loadCallbacks() {
  const d = state.disaster;
  const rows = await api(`/api/disasters/${d.disasterNumber}/callbacks?limit=${PAGE_SIZE}&offset=${state.offset}`);
  const trs = rows.map((r) => {
    const tr = el("tr", { tabindex: "0" },
      el("td", { class: "num" }, String(r.rank_in_disaster)),
      el("td", { class: "num hide-sm" }, r.priority.toFixed(2)),
      el("td", {}, el("span", { class: `tag ${r.tier}` }, TIERS[r.tier].label.replace(/^Denied (for|after) /, ""))),
      el("td", { class: "num" }, fmt.money(r.verified_loss)),
      el("td", {}, r.county || "Unknown"),
      el("td", { class: "hide-sm" }, r.factors || "none"));
    tr.addEventListener("click", () => {
      selectRow(r, tr);
      if (matchMedia("(max-width: 960px)").matches) $("drawer").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    tr.addEventListener("keydown", (e) => e.key === "Enter" && selectRow(r, tr));
    return tr;
  });
  $("callbacks").replaceChildren(...trs);
  const end = state.offset + rows.length;
  $("pageinfo").textContent = `${fmt.int(state.offset + 1)}–${fmt.int(end)} of ${fmt.int(d.cohort)}`;
  $("prev").disabled = state.offset === 0;
  $("next").disabled = end >= d.cohort;
  if (rows.length && state.offset === 0 && !state.selected) selectRow(rows[0], trs[0]);
}

async function openDisaster(number) {
  try {
    const d = await api(`/api/disasters/${number}`);
    state.offset = 0;
    state.selected = null;
    renderDisaster(d);
    history.replaceState(null, "", `?d=${number}`);
    await loadCallbacks();
  } catch (e) {
    showError($("tiles"), e);
  }
}

async function init() {
  const list = await api("/api/disasters?limit=1000");
  $("picker").replaceChildren(
    ...list.map((d) => el("option", { value: d.disasterNumber },
      `#${d.disasterNumber} · ${d.incident_name} · ${d.states.split(",").slice(0, 3).join(", ")} · ${d.year} (${fmt.int(d.cohort)})`))
  );
  const wanted = Number(new URLSearchParams(location.search).get("d")) || list[0].disasterNumber;
  $("picker").value = String(wanted);
  $("picker").addEventListener("change", (e) => openDisaster(e.target.value));
  $("prev").addEventListener("click", () => { state.offset = Math.max(0, state.offset - PAGE_SIZE); loadCallbacks(); });
  $("next").addEventListener("click", () => { state.offset += PAGE_SIZE; loadCallbacks(); });
  renderDrawer(null);
  await openDisaster(wanted);
}

init().catch((e) => showError($("tiles"), e));
