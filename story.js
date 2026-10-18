// Story page: hero number, denial reasons, fairness gaps, top disasters.
const GAP_THRESHOLD = 1.1; // adjusted odds ratio above which a group is drawn as a gap
const SVG_NS = "http://www.w3.org/2000/svg";

function svg(tag, attrs) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

function renderSummary(s) {
  document.getElementById("hero").textContent = fmt.int(s.cohort);
  document.getElementById("records").textContent = `${fmt.compact(s.records)} FEMA aid records`;
  const stats = [
    ["Verified loss in this group", fmt.compactMoney(s.cohort_loss)],
    ["Aid left on the table (est.)", fmt.compactMoney(s.aid.total)],
    ["Homes not livable", fmt.int(s.needs_repairs)],
    ["Median verified loss", fmt.money(s.median_loss)],
    ["Disasters affected", fmt.int(s.disasters_with_cohort)],
  ];
  document.getElementById("stats").replaceChildren(
    ...stats.map(([label, value]) => el("div", { class: "stat" }, el("div", { class: "label" }, label), el("div", { class: "value" }, value)))
  );
  document.getElementById("aidnote").textContent =
    `Aid estimate: for each household, the median award FEMA paid to approved households with a similar verified loss ` +
    `in the same disaster (median ${fmt.money(s.aid.median)} per household). Medians make it a conservative floor. ` +
    `A modeled estimate, not a promise of eligibility.`;

  const total = Object.values(s.tiers).reduce((a, b) => a + b, 0);
  const order = Object.keys(TIERS);
  document.getElementById("tierbar").replaceChildren(
    ...order.map((t) => el("div", { style: `flex:${s.tiers[t]};background:${TIERS[t].color}`, title: TIERS[t].label }))
  );
  document.getElementById("tierlegend").replaceChildren(
    ...order.map((t) =>
      el("span", {}, el("i", { style: `background:${TIERS[t].color}` }), `${TIERS[t].label} `,
        el("strong", {}, fmt.int(s.tiers[t])), ` (${Math.round((s.tiers[t] / total) * 100)}%)`)
    )
  );
}

function gapRow(r, scaleMax) {
  const x = (v) => (v / scaleMax) * 100;
  const isGap = !r.is_reference && r.adjusted_odds_ratio >= GAP_THRESHOLD;
  const fill = r.is_reference ? "#525252" : isGap ? "#da1e28" : "#c6c6c6";
  const chart = svg("svg", { viewBox: "0 0 100 20", preserveAspectRatio: "none", "aria-hidden": "true" });
  chart.append(
    svg("rect", { x: 0, y: 5, width: x(r.rate), height: 10, fill }),
    svg("line", { x1: x(r.ci_low), x2: x(r.ci_high), y1: 10, y2: 10, stroke: "#161616", "stroke-width": 1.5, "vector-effect": "non-scaling-stroke" }),
    svg("line", { x1: x(r.ci_low), x2: x(r.ci_low), y1: 6, y2: 14, stroke: "#161616", "stroke-width": 1.5, "vector-effect": "non-scaling-stroke" }),
    svg("line", { x1: x(r.ci_high), x2: x(r.ci_high), y1: 6, y2: 14, stroke: "#161616", "stroke-width": 1.5, "vector-effect": "non-scaling-stroke" })
  );
  const ratioClass = r.is_reference ? "ratio ref" : isGap ? "ratio up" : "ratio";
  const ratioText = r.is_reference ? "reference" : fmt.ratio(r.adjusted_odds_ratio);
  return el("div", {
    class: "gaprow",
    title: `${r.label}: ${fmt.pct(r.rate)} of ${fmt.int(r.households)} households (95% CI ${fmt.pct(r.ci_low)} to ${fmt.pct(r.ci_high)}). Raw ratio ${fmt.ratio(r.ratio_vs_reference)}.`,
  }, el("span", {}, r.label), chart, el("span", { class: ratioClass }, ratioText));
}

function renderFairness(rows) {
  const groups = Map.groupBy ? Map.groupBy(rows, (r) => r.group_name) : rows.reduce((m, r) => m.set(r.group_name, [...(m.get(r.group_name) || []), r]), new Map());
  document.getElementById("gapchart").replaceChildren(
    ...[...groups].map(([name, items]) =>
      el("div", { class: "gapgroup" }, el("h3", {}, name), ...items.map((r) => gapRow(r, Math.max(...items.map((i) => i.ci_high)) * 1.05)))
    )
  );
  const renters = rows.find((r) => r.group === "ownRent" && r.category === "R");
  if (renters) {
    document.getElementById("hero-gap").textContent =
      `Renters had ${renters.adjusted_odds_ratio.toFixed(1)}x the odds of owners of ending up here, after accounting for how much damage they had.`;
  }
}

function renderDisasters(rows) {
  document.getElementById("disasters").replaceChildren(
    ...rows.map((d) => {
      const href = `disaster.html?d=${d.disasterNumber}`;
      const tr = el("tr", { tabindex: "0" },
        el("td", {}, `${d.incident_name} · #${d.disasterNumber}`),
        el("td", {}, String(d.year)),
        el("td", {}, d.states.split(",").length > 3 ? `${d.states.split(",").slice(0, 3).join(", ")} +${d.states.split(",").length - 3}` : d.states.replaceAll(",", ", ")),
        el("td", { class: "num" }, fmt.int(d.cohort)),
        el("td", { class: "num" }, fmt.compactMoney(d.cohort_loss)),
        el("td", { class: "go" }, "Open →")
      );
      tr.addEventListener("click", () => (location.href = href));
      tr.addEventListener("keydown", (e) => e.key === "Enter" && (location.href = href));
      return tr;
    })
  );
}

api("/api/summary").then(renderSummary).catch((e) => showError(document.getElementById("stats"), e));
api("/api/fairness").then(renderFairness).catch((e) => showError(document.getElementById("gapchart"), e));
api("/api/disasters?limit=10").then(renderDisasters).catch((e) => showError(document.getElementById("disasters"), e));
