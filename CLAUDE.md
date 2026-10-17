# IBM Z Datathon 2026: project context

Mahir's entry for the IBM Z Datathon 2026 (Shooting Stars Foundation × IBM). Read this file first in any new session. Detailed docs live in `docs/`.

## Event facts (from docs/research/*.pdf)

- **Submission deadline (confirmed on the hack2skill countdown, Oct 17 2:04 AM CDT: "01d:09h:25m"):** about **Sun Oct 18, 11:29 AM CDT**. Target finishing by **Oct 18, 9 AM CDT** to leave a buffer.
  - In-person Day 1 at UTD runs Oct 17, 9 AM–5 PM ET (8 AM–4 PM CDT). The Americas closing ceremony is Oct 18, 10:30 AM ET.
  - Mahir is registered for the Hybrid event. Whether an online registration can join the UTD hub in person is unconfirmed; ask in Discord #helpdesk.
- **Submit at:** https://hack2skill.com/event/datathon-2026 (video guide: https://youtu.be/3_L3T__zEco)
- **Required:**
  - Demo video of **≤3 min**: problem, supporting data, solution, how it uses IBM Z, plus show the tech stack, the LinuxONE instance and the model.
  - GitHub/GitLab link or zip.
  - Pitch deck PDF named `[Team Name]_IBM Z Datathon 2026 Project`.
  - Links to all open-source resources used.
  - Project title must contain the team name.
  - Event code **SSF2026** in the project description.
- **Optional:** architecture flowchart, working prototype.
- **Rules:**
  - Teams of **4–6** (stated as mandatory).
  - All code written during the event window. No pre-built projects.
  - The abstract was due Oct 5.
  - Completing the two provided AI/ML labs is a **mandatory prerequisite**: (1) Predictive AI Hybrid multi-model, (2) Predictive AI + Generative AI.
- **Judging:** 4 criteria × 10 points = 40.
  1. Value to community + theme alignment
  2. Novelty / originality
  3. Technical design + use of LinuxONE Community Cloud + AI/ML open-source packages. They want **screenshots as evidence** of containers, security, scalability and compute.
  4. Execution + pitch quality

  A separate AI Innovation Excellence Award rewards unconventional AI and technical excellence.
- **Themes:** (1) Real-Time AI for Critical Decisions, (2) AI Secured: Innovation Without Exposure, (3) Wildcard: Beyond the Obvious.
- **Platform:**
  - LinuxONE Community Cloud: https://linuxone.cloud.marist.edu (s390x, big-endian)
  - Jupyter Lab ML: https://github.com/linuxone-community-cloud/jupyter-lab-ml
  - Fast Start guides: https://community.ibm.com/zsystems/l1cc/faststart/
- **Help:** Discord https://discord.gg/vVUwEJh3fH (#ibm-z-sme-helpdesk for technical questions, #helpdesk for general ones).
- **Prizes:** $1000 / $750 / $500 per region and per campus, plus 6 months of IBM Z access and an IBM Z Day feature. UTD is an in-person hub.

## Chosen project: Second Look (ranked #1 of 16 after a multi-agent debate)

**One-liner:** Find the disaster survivors FEMA turned away even though their damage was verified, and get them a callback.

- **Theme:** 3 (Wildcard, disaster relief / community impact). The upgrade path is "Second Look, Sealed" under Theme 2.
- **Data:** OpenFEMA IHP Valid Registrations V2, 26.2M rows, 100 fields. Use the bulk Parquet (~760 MB); the API returned 503 on Oct 17. Join with OpenFEMA Disaster Declarations Summaries.
- **Core idea:** a rule-based cohort. Verified damage (`rpfvl`/`ppfvl` > 0, `inspnReturned`, `habitabilityRepairsRequired`), AND denied (`ihpEligible = false`), AND a fixable `ineligibleReason`. Then:
  - an ML model of who lands in the cohort
  - fairness gaps by `applicantAge`, `grossIncome`, `ownRent`, `accessFunctionalNeeds`
  - a ranked caseworker callback list
  - s390x batch-scoring throughput
- **Leakage trap:** eligibility is nearly the rule "loss > 0 and uninsured", so a naive model reaches ~0.99 AUC and learns nothing. Train only on verified-damage households and split by disaster. Pitch the cohort and the fairness gaps, not AUC.
- **Hour-one risk:** `ineligibleReason` is a numeric code '1'–'9'. Decode it from the OpenFEMA data dictionary and confirm it splits into fixable vs genuinely ineligible.
- **Add for the judging rubric (labs + criterion 3):**
  - A **Generative AI layer** (predictive + generative hybrid): a local LLM on LinuxONE (llama.cpp ships in jupyter-lab-ml) writes a plain-language "why flagged" note and a callback script for each household.
  - Run the app in a **Podman container** on the VM and screenshot it.
- **Optional Sealed add-on** (only if the cohort works by about hour 6):
  - CPACF-backed HMAC tokenization of identities (synthetic names on top of the real rows)
  - two-person audited unmask with a hash-chained log
  - quasi-identifier uniqueness audit on the public release (aggregate only)

- **Personal hook (pitch opener):** Mahir grew up in Bangladesh watching floods devastate families. Use it as the video's opening.
  - The bridge to FEMA data: the paperwork barrier is universal. Families without formal proof of ownership or occupancy get turned away, and FEMA is one of the few agencies that publishes every application, which makes the problem measurable.
  - "What's next" goes back to Bangladesh, where informal land tenure makes ownership-proof barriers worse.
  - Keep the Bangladesh claims qualitative unless sourced. The data stays US FEMA, because no labeled Bangladesh aid-decision dataset exists.

## Progress log

- **Oct 17, 02:40 CDT: go/no-go passed.**
  - Decoded `ineligibleReason` codes are in `pipeline/codebook.py`.
  - Fixable tiers: 4 = missing documents; 3 = lost contact; 7/9 count only when ownership or occupancy was unverified.
  - Full-data run (Mac): 26,242,788 rows → 8,938,750 with verified damage → 2,033,722 of those denied → **94,395 in the Second Look cohort** (70,072 missing docs, 14,624 lost contact, 9,699 unverified). Cohort verified loss totals $612M (median $1,680). 71,674 cohort homes needed repairs to be livable.
  - First gaps, as the share of verified-damage households that end up in the cohort:
    - renters 1.80% vs owners 0.73% (2.5x)
    - $0 income 2.12% vs $120–175k 0.48% (4.4x)
    - age 19–34 1.60% vs 65+ 0.76%
    - disability flag shows **no** gap (0.94% vs 1.07%). Report that honestly.
  - Top disasters by cohort size: 4559 LA hurricane (6,039), 1603 LA hurricane (5,493), 4339 PR hurricane (4,963), 4586 TX severe ice storm (3,739).
  - Local env: `uv venv --python 3.12 .venv`; 11 cohort tests pass (`.venv/bin/python -m pytest tests`). Ingest takes 15s and the cohort step 26s on the Mac.

- **Oct 17, ~03:30 CDT: model, fairness and ranking built** (Mac, sklearn backend). Run everything with `make pipeline`.
  - **Model** (`pipeline/train.py`):
    - Population: 8.94M verified-damage households. Features: only what FEMA knows after inspection, before the decision.
    - Test set: 1.96M rows from 114 disasters the model never saw.
    - Results: ROC AUC 0.778; average precision 0.082 vs a 0.0106 base rate (7.8x lift); precision@1000 = 43.4% (41x the base rate); precision@10k = 19.0%.
    - Top features: habitability, declaration year, own/rent, ppfvl, rpfvl, age, state, residence type.
    - Fit takes 60s. Scoring all 8.94M rows takes 18.5s (484k records/sec on arm64).
  - **Fairness** (`pipeline/fairness.py`). Adjusted odds ratios control for loss, habitability, destroyed, incident type and year:
    - renters vs owners: OR 2.00 (raw 2.47x)
    - $0 income vs $60–120k: 2.70 (raw 3.68x)
    - <$15k: 1.86
    - 19–34 vs 50–64: 1.32
    - 65+: 0.85
    - access/functional needs: 0.70. Disabled applicants are *less* likely, so say so honestly.
  - **Ranking** (`pipeline/rank.py`): 94,395 households across 548 disasters, each with a priority and a "why flagged" sentence.
  - **Store** (`pipeline/store.py`): `secondlook.db` (26 MB) with tables disasters, callbacks (joined with risk_score), fairness, adjusted_odds, feature_importance, model_metrics, reason_codes.
  - Top disasters (numbers only; names still need the Disaster Declarations join): 4559 LA 2020 hurricane, 1603 2005 hurricane, 4339 PR 2017 hurricane, 4586 TX Feb 2021 ice storm.
  - 21 tests pass.

## s390x environment facts (verified Oct 17 2026)

- PyPI has **no s390x wheels** for pandas, pyarrow, scikit-learn, xgboost, torch or onnxruntime. Install them from **conda `defaults`**; conda-forge doesn't have them either.
- `snapml` 1.17.2 ships s390x wheels for cp39–cp312 only, so pin **Python 3.12**.
- Run `grep nnpa /proc/cpuinfo` to see if the Telum accelerator is exposed. Don't claim acceleration unless measured.
- Train models on the VM. Don't move pickles across architectures. Parquet is endian-neutral.

## Where things run

- Code is written on the Mac in this repo (Claude Code), pushed to GitHub, and pulled/run on the LinuxONE VM.
- Pipeline, model, LLM and API all run on the VM. The dashboard is served from the VM and viewed in a browser through an SSH tunnel; screen-record that for the video.
- No public website is required. Mahir wants the UI to look polished and wants a say in the design, so agree on the frontend look with him before building it.

## Docs map

- `docs/SECOND_LOOK_BUILD.md`: full build spec in Devpost format (architecture, layers, API, folder skeleton, setup, metrics, timeline)
- `docs/IDEA_RANKING.md`: all 16 ideas ranked, debate method, verified facts
- `docs/ideas/`: earlier rejected plans (Blindfold, Clonewall/Mirage)
- `docs/research/`: debate brief, idea pool, official guidebook and kickoff deck PDFs

## Open questions for Mahir

1. Team: who is on it, and are there 4–6 members registered on hack2skill? What is the team name (needed in the title)?
2. Was the abstract submitted by Oct 5? Are the two mandatory labs done?
3. Is the LinuxONE VM provisioned yet?
4. Frontend look: Streamlit with a custom theme, or a custom web page (FastAPI + HTML/React)?
5. Attend the UTD in-person hub on Oct 17?

## Mahir's preferences (from this planning session)

- Devpost write-ups in the style of winners he linked: Nudge, aide, AgriMind, Angel's Protection, HootHive, RaiderClaim. Concrete "What it does" bullets naming the tool, layered "How we built it", a tech table with why-it-mattered, measured numbers with eval sizes, a folder skeleton.
- He is passionate about AI security/privacy (agents, AI reverse engineering, privacy erosion). Keep that angle available through the Sealed add-on.
- He wants deep deliberation (multi-agent debate) before big decisions, not quick answers.
