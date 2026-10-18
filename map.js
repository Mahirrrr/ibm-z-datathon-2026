// Story page map: Second Look households per county (FEMA's 5-digit FIPS), with Puerto Rico as an inset.
// Topology: us-atlas 3.0.1 counties-10m.json, vendored next to this file so the live demo needs no CDN fetch.
const MAP_W = 975, MAP_H = 610;
const PR_BOX = [[800, 470], [955, 540]]; // inset, in the Atlantic east of Florida
const DOMINANT_SHARE = 0.5; // a county links to its top disaster when that disaster holds at least half its cohort
const OFF_MAP = { "60": "American Samoa", "64": "Micronesia", "66": "Guam", "68": "Marshall Islands",
  "69": "Northern Mariana Islands", "70": "Palau", "78": "U.S. Virgin Islands" };
const RENAMED = { "02270": "02158", "46113": "46102" }; // FEMA keeps the pre-2015 codes; us-atlas uses the new ones
const BINS = [ // Carbon red scale, by cohort households in the county
  { max: 5, color: "#ffd7d9", label: "1–5" },
  { max: 25, color: "#ffb3b8", label: "6–25" },
  { max: 100, color: "#ff8389", label: "26–100" },
  { max: 500, color: "#da1e28", label: "101–500" },
  { max: 2000, color: "#a2191f", label: "501–2,000" },
  { max: Infinity, color: "#750e13", label: "2,000+" },
];

const binFor = (n) => BINS.find((b) => n <= b.max);
const countyName = (c) => `${(c.county || "Unknown county").replace(/\s*\(([^)]+)\)$/, " $1")}, ${c.state}`;

function mapTooltip(c, disaster) {
  const share = Math.round(c.top_share * 100);
  const top = disaster ? `${disaster.incident_name} #${c.top_disaster} (${disaster.year})` : `Disaster #${c.top_disaster}`;
  return [
    el("strong", {}, countyName(c)),
    el("div", { class: "big" }, `${fmt.int(c.cohort)} Second Look households`),
    el("div", {}, `${fmt.pct(c.rate, 1)} of ${fmt.int(c.verified_damage)} verified-damage households`),
    el("div", {}, `Top disaster: ${top}, ${share}% of them`),
    c.top_share >= DOMINANT_SHARE ? el("div", { class: "hint" }, "Click to open its callback list") : "",
  ];
}

async function renderMap() {
  const host = document.getElementById("map");
  const [topo, counties, disasters, summary] = await Promise.all([
    fetch("counties-10m.json").then((r) => r.json()),
    api("/api/counties"),
    api("/api/disasters?limit=1000"),
    api("/api/summary"),
  ]);
  const byFips = new Map();
  for (const c of counties) { // merge a retired code into its successor when FEMA used both
    const key = RENAMED[c.fips] || c.fips, prev = byFips.get(key);
    if (!prev) { byFips.set(key, { ...c, codes: [c.fips] }); continue; }
    const top = prev.top_disaster_cohort >= c.top_disaster_cohort ? prev : c;
    const cohort = prev.cohort + c.cohort, verified = prev.verified_damage + c.verified_damage;
    byFips.set(key, { ...top, cohort, verified_damage: verified, rate: cohort / verified,
      top_share: top.top_disaster_cohort / cohort, codes: [...prev.codes, c.fips] });
  }
  const disasterBy = new Map(disasters.map((d) => [d.disasterNumber, d]));

  const features = topojson.feature(topo, topo.objects.counties).features;
  const isPR = (f) => f.id.startsWith("72");
  const mainland = d3.geoPath(d3.geoAlbersUsa().scale(1300).translate([MAP_W / 2, MAP_H / 2]));
  const prProjection = d3.geoMercator().fitExtent(PR_BOX, { type: "FeatureCollection", features: features.filter(isPR) });
  const prPath = d3.geoPath(prProjection);

  const chart = svg("svg", { viewBox: `0 0 ${MAP_W} ${MAP_H}`, role: "img",
    "aria-label": "Map of U.S. counties shaded by number of Second Look households" });
  const tip = el("div", { class: "maptip", hidden: "" });
  let selected = null, lastPointer = "mouse";
  const drawn = new Set();

  const show = (c, event) => {
    tip.replaceChildren(...mapTooltip(c, disasterBy.get(c.top_disaster)));
    tip.hidden = false;
    const box = host.getBoundingClientRect();
    const x = event.clientX - box.left, y = event.clientY - box.top;
    tip.style.left = `${Math.min(Math.max(x + 12, 0), box.width - tip.offsetWidth)}px`;
    tip.style.top = `${y + 16 + tip.offsetHeight > box.height ? y - tip.offsetHeight - 12 : y + 16}px`;
  };
  const hide = () => { tip.hidden = true; selected = null; };

  for (const f of features) {
    const d = (isPR(f) ? prPath : mainland)(f);
    if (!d) continue; // territories outside the projection (Guam, USVI, ...)
    const c = byFips.get(f.id);
    if (c) c.codes.forEach((code) => drawn.add(code));
    const shape = svg("path", { d, fill: c ? binFor(c.cohort).color : "#f4f4f4", class: c ? "county on" : "county" });
    if (c) {
      const href = c.top_share >= DOMINANT_SHARE ? `disaster.html?d=${c.top_disaster}` : null;
      if (href) shape.classList.add("link");
      shape.addEventListener("pointerdown", (e) => (lastPointer = e.pointerType));
      shape.addEventListener("pointermove", (e) => e.pointerType === "mouse" && show(c, e));
      shape.addEventListener("pointerleave", (e) => e.pointerType === "mouse" && hide());
      shape.addEventListener("click", (e) => {
        if (lastPointer !== "mouse" && selected !== f.id) { // touch: first tap explains, second tap opens
          selected = f.id;
          show(c, e);
          return;
        }
        if (href) location.href = href;
      });
    }
    chart.append(shape);
  }
  const borders = topojson.mesh(topo, topo.objects.states, (a, b) => a !== b);
  chart.append(svg("path", { d: mainland(borders), class: "state-border" }));
  const [[x0, y0], [x1, y1]] = PR_BOX;
  chart.append(svg("rect", { x: x0 - 8, y: y0 - 22, width: x1 - x0 + 16, height: y1 - y0 + 30, class: "inset" }));
  const label = svg("text", { x: x0 - 2, y: y0 - 8, class: "inset-label" });
  label.textContent = "Puerto Rico";
  chart.append(label);

  host.replaceChildren(chart, tip);
  document.addEventListener("click", (e) => !host.contains(e.target) && hide());

  document.getElementById("maplegend").replaceChildren(
    el("span", { class: "legend-title" }, "Second Look households per county (count)"),
    ...BINS.map((b) => el("span", {}, el("i", { style: `background:${b.color}` }), b.label)),
    el("span", {}, el("i", { style: "background:#f4f4f4;outline:1px solid #c6c6c6" }), "none")
  );

  const sum = (rows) => rows.reduce((a, c) => a + c.cohort, 0);
  const mapped = counties.filter((c) => drawn.has(c.fips));
  const offMap = counties.filter((c) => !drawn.has(c.fips));
  const places = [...new Set(offMap.map((c) => OFF_MAP[c.fips.slice(0, 2)] || "other areas"))].sort();
  const noCounty = summary.cohort - sum(counties);
  document.getElementById("mapnote").textContent =
    `Shading is the count of Second Look households, so large disasters stand out. Hover or tap a county for its ` +
    `rate: the share of its verified-damage households that landed here. On the map: ${fmt.int(sum(mapped))} ` +
    `households in ${fmt.int(mapped.length)} counties. Not on the map: ${fmt.int(sum(offMap))} households in ` +
    `${places.join(", ")}; ${fmt.int(noCounty)} with no county on record.`;
}

renderMap().catch((e) => showError(document.getElementById("map"), e));
