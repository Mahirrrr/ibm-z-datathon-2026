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

  In the tech prep session, IBM said **Technical Design carries the most weight**. Their scoring checklist:
  - Criterion 3: video screenshots of workloads running live on L1CC; at least 2 open-source AI frameworks; a Docker/Podman deployment; platform security or Telum acceleration.
  - Novelty: don't submit the lab notebooks unchanged; pair predictive models with **Granite** LLM reasoning.
  - Pitch: show each team member's role, and record the live demo on LinuxONE.
  - Community: a quantified beneficiary population, "AI for Good" framing, and transparent decision reasoning.

  Full notes: `docs/research/TECH_PREP_SESSION_NOTES.md`.
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
  - A **Generative AI layer** (predictive + generative hybrid), modelled on IBM's Loan Approval lab:
    - **IBM Granite** runs locally through llama.cpp in the jupyter-lab-ml container.
    - It uses **RAG over the FEMA IHP policy guide (IAPPG)**.
    - For each household it writes a plain-language "why flagged" note and a callback script, citing the policy section that makes the denial fixable.
    - Pitch it as the reverse of the lab: a bank deciding whether to approve loans vs. finding the people the system wrongly turned away.
  - **Telum proof:** NNPA only accelerates TensorFlow ops (MatMul/Dense/ReLU/Softmax) through `ibm-zdnn-plugin`. Trees (sklearn/XGBoost/snapml) don't go through it.
    - Build a small Keras MLP twin of the cohort model and benchmark it with the NNPA vs. CPU only.
    - This also covers the "2 frameworks" item.
  - Run the app in a **Podman container** on the VM and screenshot it.
- **Optional Sealed add-on** (only if the cohort works by about hour 6):
  - CPACF-backed HMAC tokenization of identities (synthetic names on top of the real rows)
  - two-person audited unmask with a hash-chained log
  - quasi-identifier uniqueness audit on the public release (aggregate only)

- **Personal hook (pitch opener):** Mahir grew up in Bangladesh watching floods devastate families. Use it as the video's opening.
  - The bridge to FEMA data: the paperwork barrier is universal. Families without formal proof of ownership or occupancy get turned away, and FEMA is one of the few agencies that publishes every application, which makes the problem measurable.
  - "What's next" goes back to Bangladesh, where informal land tenure makes ownership-proof barriers worse.
  - Keep the Bangladesh claims qualitative unless sourced. The data stays US FEMA, because no labeled Bangladesh aid-decision dataset exists.

## Work queue (what to build next, in order; updated Oct 17)

Done so far: cohort, model, fairness, ranking and SQLite store, all on the Mac (see Progress log). Dashboard design is agreed. Everything below is still open. Tick items off here as they land.

1. **VM up.** Register with SSF2026 → AI LAB flavor, `-datathon` image. Start the jupyter-lab-ml container with our own token. Run the 2 mandatory labs and screenshot them.
2. **Pipeline on the VM.**
   - Use the conda `defaults` env on Python 3.12, then run `make pipeline`.
   - Watch peak RSS in the cohort step (8 GB limit).
   - Retrain on the VM; never copy pickles across.
   - Record the s390x scoring throughput.
3. **GenAI layer.** Granite via llama.cpp, plus RAG over the FEMA IAPPG. It writes a why-flagged note and a callback script per household.
4. **Telum benchmark.** A Keras MLP twin through `ibm-zdnn-plugin`, comparing NNPA vs. CPU throughput. Claim only what we measured.
5. **Disaster Declarations join**, so disaster numbers show as names.
6. **Dashboard**, per "Dashboard design decisions" below. FastAPI + static HTML + Carbon from a CDN.
7. **Podman container** for the app. Screenshot the container, `lscpu | grep nnpa`, the SSH tunnel and the custom token for criterion 3.
8. **Submission.**
   - Deck PDF `[Team Name]_IBM Z Datathon 2026 Project`.
   - A video of 3 min or less, recorded on the VM, opening with the Bangladesh hook and showing team roles.
   - Devpost write-up with SSF2026 in the description, the repo link and open-source links.
9. *(Optional, only if ahead of schedule)* Sealed add-on.

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

- **Oct 17, ~03:30 CDT: model, fairness and ranking built** (Mac, sklearn backend). **Superseded:** the z17 run below is the source of truth for every number in the video, deck and write-up. The figures in this entry are dev-run history only.
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

## LinuxONE VM (created Oct 17, ~2:58 AM CDT)

- Connect: `ssh -i ~/.ssh/linuxdatathon.pem linux1@<vm-ip>`. The key was generated by the portal and lives only on Mac.
- Instance `second-look`: flavor AI_LAB (3 vCPU, 8 GB RAM, 50 GB disk), image Ubuntu24.04-Datathon (Ubuntu 24.04.5).
- `machine: 9175` is **IBM z17**. **NNPA is present** in the /proc/cpuinfo features (Telum II AI accelerator).
- The portal shows status **ERROR**, but the VM boots, SSH works and it reports s390x. Ask #ibm-z-sme-helpdesk about the label before taking screenshots.
- Out of the box: Python 3.12.3, git, passwordless sudo. Missing: conda, gcc, podman.
- Set up on Oct 17:
  - Miniconda at `~/miniconda3`; env `secondlook` (py3.12, pandas, pyarrow 19.0.0, sklearn, snapml 1.17.2, fastapi).
  - apt packages: make, podman 4.9.3, libzdnn0.
  - 8 GB swapfile.
  - Code synced with rsync, because the repo is private and the VM has no GitHub credentials.
- **Gotchas found on the VM (all fixed in code):**
  1. **FEMA's CDN returns 403 Access Denied to the VM's IP.** Upload the raw parquet from the Mac instead.
  2. **pyarrow 19 (the only s390x build) reads numeric Parquet columns as null on big-endian**, even for files it wrote itself. Intermediates are now Arrow IPC/Feather (`pipeline/frames.py`), which round-trips and byte-swaps correctly. `make ingest` (raw Parquet to `ihp_slim.arrow`) runs on the Mac; `make pipeline` (cohort to store) runs on the VM.
  3. Loading 26M rows × 33 columns into pandas used more than 16 GB. Cohort labeling now streams record batches (peak 364 MB), and readers use `frames.read(..., where=...)`.
  4. Snap ML only takes its NNPA (zDNN) path when the system libstdc++ is preloaded, because the conda env's copy is too old for libzdnn. Run with `LD_PRELOAD=/lib/s390x-linux-gnu/libstdc++.so.6`.
  5. Snap ML on s390x heap-crashes (`malloc(): invalid size`) on NaN features. Train swaps NaN for -1 on the snapml backend.
  6. Snap ML rejects `n_jobs=-1`; pass `os.cpu_count()`.
- Run on the VM: `cd ~/ibm-z-datathon-2026 && LD_PRELOAD=/lib/s390x-linux-gnu/libstdc++.so.6 make pipeline PY=~/miniconda3/envs/secondlook/bin/python`

## Progress: pipeline on IBM z17 (Oct 17, ~4:30 AM CDT). These are the official numbers.

- `make pipeline` ran end to end on LinuxONE (s390x, IBM Snap ML backend). `secondlook.db` was built there and copied back to the Mac.
- Cohort matches the Mac run exactly: 26,242,788 rows, 8,938,750 with verified damage, **94,395 in the cohort**.
- **Model (Snap ML BoostingMachine, 100 rounds):**
  - ROC AUC **0.785** on 114 disasters the model never saw (sklearn on the Mac: 0.778)
  - average precision 0.078
  - precision@1000 41.9%, precision@10k 18.4%
  - fit takes 87.6s on 7.0M rows with 3 vCPU
- **Inference engines, scoring all 8,938,750 households** (`pipeline/benchmark.py`):
  - CPU standard: 419k/s (21.3s)
  - **Snap ML compressed trees: 2.31M/s (3.9s), 5.5x faster**
  - Telum NNPA (`zdnn_tensors`): 240k/s (37.3s)
  - All three return identical scores (max diff 1e-16).
  - Pitch it honestly: the NNPA path is verified working, but on this shared 3-vCPU VM, compressed trees were fastest for tree ensembles.
- **Adjusted odds ratios on the z17.** The 1.5M sample is seeded (seed=7), so each machine reproduces its own numbers. The Mac numbers differ because pandas 3.0 vs 2.2 and sklearn 1.9 vs 1.6 change the sample and the solver path. Quote these:
  - renters 1.88
  - $0 income 3.02
  - <$15k 2.08
  - $15–30k 1.88
  - age 19–34 1.27
  - 65+ 0.78
  - access/functional needs 0.70
- **Podman container (Oct 17, ~5:40 AM CDT):** the `Containerfile` image (`localhost/second-look`) is built natively on the VM.
  - It runs rootless and hardened: read-only rootfs, all capabilities dropped, no-new-privileges, UID 1000, DB mounted `:ro`, bound to 127.0.0.1:8000. The run command is in the Containerfile header.
  - Evidence (system, software, container, benchmark, log, 3 dashboard screenshots) is indexed in `docs/evidence/README.md`. The portal details-panel screenshot is still needed from Mahir.
- **Dashboard served from the VM:** the container listens on 127.0.0.1:8000 on the VM (it replaced the bare uvicorn). On the Mac, open a tunnel with `ssh -f -N -i ~/.ssh/linuxdatathon.pem -L 8100:127.0.0.1:8000 linux1@<vm-ip>`, then browse http://localhost:8100. The Method page shows machine s390x, the Snap ML backend, NNPA running, and the engine chart.

## Progress: GenAI layer, TF/NNPA twin, deck (Oct 17, ~9 AM CDT). Not committed yet.

- **Granite + RAG is done, deployed, and served from Podman on the z17.**
  - Code: `pipeline/policy.py` (89 IAPPG 1.1 ch. 3 passages in `docs/data/iappg_chunks.json`, TF-IDF, sections pinned per tier) and `pipeline/genai.py` (llama-server JSON with citation, dollar-amount and no-promise checks).
  - Data: the store loads `callback_notes.jsonl` into a `callback_notes` table. The API attaches `note` to callback rows, and the drawer shows it, falling back to the template.
  - Results: 50 notes (top 5 × 10 largest disasters), all of which passed the checks. Median 142s and 252 tokens each.
  - Server: llama.cpp is built in `~/llama.cpp`, without `-march=arch15` (GCC 13) and with `-mvx -mzvector` (without those flags it runs scalar at 1.2 tok/s). Start it with `~/granite_server.sh` (`--cache-ram 0 -np 1 --load-mode none -t 2`). It is stopped now to free RAM. Model: `~/models/granite-3.3-2b-instruct-be.Q4_0.gguf` (taronaeo BE GGUF).
  - Generation speed on the shared host ranged 1.1–4.5 tok/s.
- **TF twin** (`pipeline/twin.py`, `make twin`): runs in IBM's jupyter-lab-ml image (TF 2.18.1, ibm-zdnn-plugin 2.3.0). NNPA scores 1,745,681/s vs 1,424,337/s on the CPU (**1.23x**). Scores differ by up to 0.0033, which is proof the NNPA ran. Twin AUC 0.716. `NNPA_DEVICES=0` gives the CPU baseline.
- **Honesty fix:** Snap ML `zdnn_tensors` scores were identical to CPU (1e-16), so it's no longer claimed as accelerator evidence anywhere. The TF twin is the NNPA claim.
- **Docs:** `docs/VIDEO_PLAN.md`, `docs/SUBMISSION.md` (form text with SSF2026, links, public-repo checklist) and `docs/deck/deck.html`, rendered to `docs/deck/Second Look_IBM Z Datathon 2026 Project.pdf`.
- Evidence added: `docs/evidence/{twin_benchmark.json, callback_notes.jsonl, granite_runtime.txt, dashboard_disaster_4559_granite.png, dashboard_method_genai.png}`. VM DB backup from before GenAI: `~/secondlook.db.pre-genai`.
- **Team update (Oct 17, evening): team "Second Look" now has 4 members: Mahir Abdullah, Arnab Dev, Azfar Islam and Raihan Ahmed, all from Bangladesh.** Mahir built everything; the other three were added to meet the 4–6 member rule. Deck slide 12 and the video credit the build to Mahir and list the others as members with no roles (Mahir chose names only). Never invent roles for them. Mahir records the whole voice-over. Still open: add all 4 to the Hack2Skill team.
- **Public demo (Oct 17, ~10 AM CDT).**
  - Static snapshot: https://mahirrrr.github.io/ibm-z-datathon-2026/, served from the `gh-pages` branch. Build it with `python -m pipeline.static_site --out <dir> --live-url <url>`, then push that dir to `gh-pages` from a separate clone. Never switch branches in this checkout.
  - Live: a Cloudflare quick tunnel. `~/cloudflared` was cross-compiled for s390x and runs as the systemd user service `second-look-tunnel` (linger is on), with logs in `~/tunnel.log`.
  - The current URL is https://divisions-films-jesse-nsw.trycloudflare.com. It **changes whenever the tunnel restarts**. Get the new one with `grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" ~/tunnel.log | tail -1`, then rebuild and push the Pages banner, the README and SUBMISSION.md.
  - The container now runs with `--restart=always`, with `podman-restart.service` enabled.
- **Repo is public (Oct 17).** History was rewritten: the event PDFs were removed and the VM IP is shown as `<vm-ip>`. The real IP is only in the gitignored `.claude/memory/linuxone-vm-address.md`, so never commit it.
- Done: the portal screenshot and both lab runs (`docs/evidence/labs`).
- Still open with Mahir:
  - Discord helpdesk answers: whether a solo entry is allowed, which notebook is the "hybrid" lab, and a reset of the ERROR label.
  - Recording the video.
  - The Hack2Skill form.

## Progress: aid estimate and county map (Oct 17, ~7:30 PM CDT). Official z17 numbers.

- **Aid left on the table** (`pipeline/aid.py`, runs in `make pipeline` before `store`): for each cohort household, the median `ihpAmount` of APPROVED verified-damage households in the same disaster and verified-loss band (bands at $1k, 2.5k, 5k, 10k, 25k, 50k). Cells under 30 approvals fall back to the disaster, then the band across disasters.
  - z17 result: **$384,968,257 total (quote "$385M"), median $2,314 per household**, all 94,395 estimated. Basis: 93,787 disaster×band, 482 disaster, 126 band. Mac run is identical.
  - Caveat to always say: a modeled estimate, not a promise of eligibility. Medians make it a conservative floor (approved awards: median $2,000, mean ~$4,355). The median estimate exceeds the median verified loss ($1,680) because IHP also pays rental assistance and other needs.
  - Stored as `aid_estimate`/`aid_basis` columns on `callbacks`; `/api/summary` returns `aid`.
- **County map** on the Story page (`dashboard/map.js`): counties shaded by cohort **count** (Carbon red bins), rate in the tooltip, Puerto Rico inset, click goes to the county's top disaster when it holds ≥50% of the county's cohort. Topology is us-atlas 3.0.1 `counties-10m.json`, vendored in `dashboard/`; d3-array 3.2.4, d3-geo 3.1.1, topojson-client 3.1.0 from jsDelivr. `/api/counties` from the `counties` table.
  - 1,786 counties on the map (90,806 households). Not mapped: 3,186 in other territories (USVI, Guam, ...), 403 with no county. FEMA's retired FIPS 02270/46113 map to 02158/46102.
- `fips` was added to `SLIM_COLUMNS`; `ihp_slim.arrow` was re-ingested on the Mac and uploaded. The z17 rerun was only cohort → aid → store; the model, scores, fairness and benchmark files were **not** retrained, so every earlier number stands. VM DB backup: `~/secondlook.db.pre-aid`.
- Redeployed: container rebuilt on the VM, gh-pages snapshot pushed, tunnel URL unchanged. Evidence: `docs/evidence/{dashboard_story.png, dashboard_story_map.png, aid_run.log}`.
- `01_story.mp4` predates the map and the aid tile; re-record it if there's time. Video script has one added line (380 words).

## Game plan from here (written Oct 17, ~6 AM CDT; deadline Sun Oct 18 11:29 AM CDT, target 9 AM)

**Done and pushed** (commits c981f0b through 8e0a66b on `main`, private repo Mahirrrr/ibm-z-datathon-2026):
- cohort, model, fairness, ranking, store
- 3-page dashboard
- LinuxONE port with Snap ML and the engine benchmark
- hardened Podman container serving the dashboard on the VM
- docs/evidence captures
- judge-facing README.md

**Inputs from the Tech Prep session** (full notes in `docs/research/TECH_PREP_SESSION_NOTES.md`):
- Their "Predictive + Generative" lab is a loan-approval demo: XGBoost score, then RAG over bank policy in a vector DB, then IBM **Granite** explains the decision. We mirror it in reverse: FEMA's IHP policy guide replaces the bank policy, and Granite explains why a denied household deserves a second look and drafts the callback script. Don't submit lab notebooks unchanged (novelty).
- Technical design is weighted most heavily. Their checklist:
  - at least 2 open-source AI frameworks
  - a Docker/Podman container (done)
  - video of it running live on the LinuxONE VM
  - security and/or Telum acceleration
- Telum acceleration, as they described it, is TensorFlow via IBM's zDNN plugin. Our Snap ML `zdnn_tensors` run matched CPU scores to 1e-16, which is suspicious for real NNPA (reduced precision). Plan: a small Keras model mirroring the cohort model, benchmarked with and without NNPA. It is also the 2nd framework. Claim only what is measured.
- Community value needs a quantified group of beneficiaries: 94,395 households and $612M (have it).
- Pitch should show each team member's role. Record the demo on the VM through the tunnel, not on the Mac.
- VM rules: SSF2026 goes in the project description. Default Jupyter token `Your_Token1` was public; if jupyter-lab-ml runs, set our own token.

**Remaining work, in priority order:**
1. **GenAI layer: Granite plus RAG over FEMA IHP policy** (Predictive + Generative).
   - On the VM, run Granite locally (llama.cpp, or whatever the jupyter-lab-ml container ships; GGUF needs care on big-endian) with a small vector store over the FEMA IHP Unified Guidance (IHPUG) sections on denial reasons and appeals.
   - Generate a cited "why flagged" note and callback script for the top-N callbacks per disaster, and store them in secondlook.db.
   - Show them in the Disasters drawer, replacing the template draft.
   - Timebox this. The template script is the fallback.
2. **Keras/TensorFlow model plus NNPA benchmark** (2nd framework, honest Telum claim). Add it to `pipeline/benchmark.py` and the Method page.
3. Before recording, check that the dashboard copy says "Runs on IBM LinuxONE" and that every number matches the z17 run.
4. **Pitch deck PDF** named `Second Look_IBM Z Datathon 2026 Project`: problem with the Bangladesh opener, data, solution, IBM Z usage, evidence screenshots, team roles, limits, what's next.
5. **Demo video, 3 minutes or less**, recorded on the VM through the tunnel.
6. Submission: Hack2Skill form with SSF2026 in the description, links to all open-source resources, the repo made **public** after removing `docs/research/*.pdf` (event PDFs), and team name "Second Look".

**Open items with Mahir:**
- He registered solo. The deck says 4–6 members; ask Discord #helpdesk (message drafted earlier) and track the answer.
- Confirm both mandatory labs are done.
- Screenshot the portal's expanded instance-details panel (not the ERROR status row).
- Check-in form: team "Second Look", mode Virtual unless he attends UTD in person.

## s390x environment facts (verified Oct 17 2026)

- PyPI has **no s390x wheels** for pandas, pyarrow, scikit-learn, xgboost, torch or onnxruntime. Install them from **conda `defaults`**; conda-forge doesn't have them either.
- `snapml` 1.17.2 ships s390x wheels for cp39–cp312 only, so pin **Python 3.12**.
- Run `grep nnpa /proc/cpuinfo` to see if the Telum accelerator is exposed. Don't claim acceleration unless measured.
- **VM spec** (from the tech prep session):
  - z17 (type 9175), 3 vCPU, **8 GB RAM**, 50 GB disk, 30 days, **one server per team**, user `linux1`.
  - Register with **SSF2026** in the project description, or the **AI LAB** flavor won't appear.
  - Pick the `-datathon` image: Ubuntu 24.04.4 or RHEL 9.8.
- **Jupyter security:** the VM has a public IP, and the default token `Your_Token1` was shown on a public slide. Always set our own token, and serve the dashboard only over the SSH tunnel.
- **Memory risk:** `pipeline/cohort.py` loads all of `ihp_slim.parquet` (26.2M × 33).
  - On the Mac, peak RSS is 2.7 GB, but pandas reports 8.5 GB deep usage.
  - Check RSS on the VM (`/usr/bin/time -v`). If it runs out of memory, filter or project with pyarrow before pandas.
- Train models on the VM. Don't move pickles across architectures. Parquet is endian-neutral.

## Where things run

- Code is written on the Mac in this repo (Claude Code), pushed to GitHub, and pulled/run on the LinuxONE VM.
- Pipeline, model, LLM and API all run on the VM. The dashboard is served from the VM and viewed in a browser through an SSH tunnel; screen-record that for the video.
- No public website is required. Mahir wants the UI to look polished and wants a say in the design, so agree on the frontend look with him before building it.

## Dashboard design decisions (agreed with Mahir, Oct 17)

- Style: editorial (ProPublica-like) for the story pages, plus an IBM ops console for the callback list and the LinuxONE stats.
- Built on IBM's open-source stack, not IBM branding:
  - IBM Plex fonts: Serif for headlines, Sans for body text, Mono for numbers.
  - Carbon Design System tokens: the White theme on editorial pages, the g100 dark theme on console pages.
  - Carbon Charts for all charts.
- No IBM logo or 8-bar mark, and nothing that implies an official IBM product.
- Colors:
  - IBM Blue 60 `#0F62FE` for interactive elements and model stats.
  - Carbon Red 60 `#DA1E28` for fairness gaps (groups above the reference).
  - Gray for groups at or below the reference.
- Pages (3, in the order of the demo video):
  1. **Story** (editorial): the hero number 94,395 with one sentence; adjusted-odds bars with CI whiskers, Carbon red for gaps; top disasters list, click to drill in.
  2. **Disaster** (console): pick a disaster, then see cohort, verified loss and the denial-reason split; local fairness bars; the ranked callback table with why-flagged; a side panel with the LLM callback script; CSV export.
  3. **Method + LinuxONE** (editorial top, console bottom): cohort definition, leakage guard, model metrics (AUC, precision@k, lift), s390x throughput and container proof.
- Stack: FastAPI serving static HTML and vanilla JS. Carbon web components and Carbon Charts load from CDN, with no Node build step, so nothing needs compiling on s390x.

## Docs map

- `docs/SECOND_LOOK_BUILD.md`: full build spec in Devpost format (architecture, layers, API, folder skeleton, setup, metrics, timeline)
- `docs/IDEA_RANKING.md`: all 16 ideas ranked, debate method, verified facts
- `docs/ideas/`: earlier rejected plans (Blindfold, Clonewall/Mirage)
- `docs/research/TECH_PREP_SESSION_NOTES.md`: IBM tech prep session takeaways. The VM is 3 vCPU / 8 GB / 50 GB with the AI LAB flavor. Use Granite + RAG for the GenAI layer. NNPA acceleration only applies to TensorFlow via zDNN.
- `docs/research/`: debate brief, idea pool, official guidebook and kickoff deck PDFs

## Open questions for Mahir

1. Team: who is on it, and are there 4–6 members registered on hack2skill? What is the team name (needed in the title)?
2. Was the abstract submitted by Oct 5? Are the two mandatory labs done?
3. Is the LinuxONE VM provisioned yet?
4. ~~Frontend look~~: resolved, see "Dashboard design decisions".
5. Attend the UTD in-person hub on Oct 17?

## Mahir's preferences (from this planning session)

- Devpost write-ups in the style of winners he linked: Nudge, aide, AgriMind, Angel's Protection, HootHive, RaiderClaim. Concrete "What it does" bullets naming the tool, layered "How we built it", a tech table with why-it-mattered, measured numbers with eval sizes, a folder skeleton.
- He is passionate about AI security/privacy (agents, AI reverse engineering, privacy erosion). Keep that angle available through the Sealed add-on.
- He wants deep deliberation (multi-agent debate) before big decisions, not quick answers.
