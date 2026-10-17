// Method page: model metrics, feature importance, ranking policy, LinuxONE runtime evidence.
const FEATURE_LABELS = {
  habitabilityRepairsRequired: "Home needs repairs to be livable",
  declarationYear: "Year of disaster",
  ownRent: "Owner or renter",
  ppfvl: "Personal property loss",
  rpfvl: "Real property loss",
  applicantAge: "Applicant age",
  damagedStateAbbreviation: "State",
  residenceType: "Residence type",
  grossIncome: "Household income",
  householdComposition: "Household size",
  registrationMethod: "How they applied",
  incidentTypeCode: "Disaster type",
  selfAssessmentInformation: "Self-assessment",
  occupants65andOver: "Occupants 65+",
  primaryResidence: "Primary residence",
  homeOwnersInsurance: "Homeowners insurance",
  floodInsurance: "Flood insurance",
  accessFunctionalNeeds: "Access or functional needs",
  destroyed: "Home destroyed",
  floodDamage: "Flood damage",
  roofDamage: "Roof damage",
};

// Steps still to do on the VM; flip to true as each is measured there.
const STACK = [
  ["IBM LinuxONE Community Cloud (s390x)", "Runs the pipeline, model, API, and dashboard", "machine"],
  ["IBM Snap ML", "Gradient-boosted model training and batch scoring", "backend"],
  ["Telum on-chip AI accelerator (NNPA)", "Snap ML zdnn_tensors engine scores every household on the AI accelerator", "nnpa"],
  ["llama.cpp local LLM", "Writes callback scripts without data leaving the machine", null],
  ["Podman container", "Packages the API and dashboard", null],
];

function tile(label, value, accent) {
  return el("div", { class: "tile" }, el("div", { class: "label" }, label), el("div", { class: accent ? "value accent" : "value" }, value));
}

function stat(label, value, sub = "") {
  return el("div", { class: "stat" }, el("div", { class: "label" }, label), el("div", { class: "value" }, value), el("div", { class: "sub" }, sub));
}

function render({ metrics: m, feature_importance: fi, policy }) {
  const lift = (p) => `${Math.round(p / m.positive_rate)}x base rate`;
  document.getElementById("metrics").replaceChildren(
    stat("ROC AUC, unseen disasters", m.roc_auc.toFixed(3)),
    stat("Average precision", m.average_precision.toFixed(3), lift(m.average_precision)),
    stat("Precision, top 1,000", fmt.pct(m.precision_at_1000, 1), lift(m.precision_at_1000)),
    stat("Precision, top 10,000", fmt.pct(m.precision_at_10000, 1), lift(m.precision_at_10000))
  );
  document.getElementById("metricnote").textContent =
    `Trained on ${fmt.int(m.rows_train)} households; tested on ${fmt.int(m.rows_test)} households from ${m.disasters_test} disasters held out entirely. ` +
    `Base rate: ${fmt.pct(m.positive_rate)} of verified-damage households land in the group.`;

  const top = fi.slice(0, 10);
  const max = Math.max(...top.map((f) => f.importance));
  document.getElementById("importance").replaceChildren(
    ...top.map((f) =>
      el("div", { class: "hbar" },
        el("span", {}, FEATURE_LABELS[f.feature] || f.feature),
        el("div", { class: "track", style: "background:var(--gray-20)" },
          el("div", { class: "fill", style: `width:${(Math.max(0, f.importance) / max) * 100}%;background:var(--blue-60)` })),
        el("span", { class: "n" }, f.importance.toFixed(3)))
    )
  );

  const weights = Object.entries(policy.tier_weights)
    .map(([t, w]) => `  ${w.toFixed(1)}  ${policy.tier_labels[t]}`).join("\n");
  document.getElementById("formula").textContent =
    `priority = loss percentile within the disaster\n` +
    `         × reason weight\n` +
    `         × (1 + ${policy.habitability_bonus} if the home isn't livable\n` +
    `              + ${policy.vulnerability_bonus} per factor: renter, lowest income band, age 65+, needs accessibility support)\n\n` +
    `reason weights:\n${weights}`;

  const onZ = m.machine === "s390x";
  const engines = m.inference_benchmark ? Object.values(m.inference_benchmark.engines) : [];
  const fastest = Math.max(m.records_per_second, ...engines.map((e) => e.records_per_second));
  document.getElementById("runtime").replaceChildren(
    tile("Machine", m.machine, onZ),
    tile("Model backend", m.backend),
    tile("Households scored", fmt.int(m.score_rows)),
    tile("Fastest scoring", `${fmt.compact(fastest)}/s`, true),
    tile("Training time", `${m.fit_seconds}s`)
  );

  const bench = m.inference_benchmark;
  const nnpa = bench && bench.engines.zdnn_tensors && bench.engines.zdnn_tensors.engine === "zdnn_tensors";
  const done = { machine: onZ, backend: m.backend === "snapml", nnpa };
  document.getElementById("stack").replaceChildren(
    ...STACK.map(([name, what, key]) => {
      const ok = key ? done[key] : false;
      return el("tr", {},
        el("td", {}, name),
        el("td", {}, what),
        el("td", {}, el("span", { class: ok ? "status ok" : "status pending" }, ok ? "● running" : "○ pending")));
    })
  );
  renderEngines(bench);
}

const ENGINE_LABELS = {
  cpu_default: "CPU, standard trees",
  compress_trees: "CPU, Snap ML compressed trees",
  zdnn_tensors: "Telum AI accelerator (NNPA)",
};

function renderEngines(bench) {
  const target = document.getElementById("engines");
  if (!bench) {
    target.replaceChildren(el("p", { class: "note" }, "Engine benchmark runs on LinuxONE with Snap ML."));
    return;
  }
  const rows = Object.entries(bench.engines);
  const max = Math.max(...rows.map(([, e]) => e.records_per_second));
  target.replaceChildren(
    el("p", { class: "panel-title" }, `Scoring all ${fmt.int(bench.rows)} verified-damage households, by inference engine`),
    ...rows.map(([key, e]) =>
      el("div", { class: "hbar" },
        el("span", {}, ENGINE_LABELS[key] || key),
        el("div", { class: "track" }, el("div", { class: "fill", style: `width:${(e.records_per_second / max) * 100}%;background:${key === "zdnn_tensors" ? "#42be65" : "#78a9ff"}` })),
        el("span", { class: "n", style: "width:auto" }, `${fmt.compact(e.records_per_second)}/s`))),
    el("p", { class: "note" }, "Every engine returns the same scores (max difference shown in the API). Measured, not claimed.")
  );
}

api("/api/model").then(render).catch((e) => showError(document.getElementById("metrics"), e));
