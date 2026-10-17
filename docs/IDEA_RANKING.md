# IBM Z Datathon 2026: idea debate and final ranking

## How the debate ran

Six agents in two rounds, about 25 minutes total, using grill-me (Socratic, one question at a time) and GSD explore (probe constraints and risks, spike the feasibility).

**Round 1: three idea generators, 12 new ideas plus the two existing ones**
- Theme 2 security lens
- Theme 1 real-time lens
- Contrarian / Theme 3 lens, which also researched past winners

**Round 2: three graders**
- IBM Z judge: scored all 14 ideas and grilled the top 4
- Skeptical engineer: made live network calls to check that datasets actually download, and estimated hours
- Devil's advocate: argued passion vs what has actually won, and invented 2 hybrid ideas

## What the research found (this changed everything)

- **Past IBM Z Datathon winners** were simple supervised ML on labeled public data with visible social good:
  - a hate-speech BERT model
  - lake encroachment from satellite images
  - agriculture
  - healthcare access

  The recurring IBM Z credit was the **s390x / big-endian porting story**. No adversarial-security project showed up among the winners we found, and no rubric is published. 2024 had 320+ submissions and 13 winners.
- **s390x packages:**
  - PyPI has no s390x wheels for pandas, pyarrow, scikit-learn, xgboost or torch. **Install them from Anaconda `defaults`, not pip.**
  - Snap ML (IBM) has s390x wheels for Python 3.9–3.12 only, so **pin Python 3.12**.
  - It's unknown whether the Community Cloud VM exposes the Telum AI accelerator. Run `grep nnpa /proc/cpuinfo` before claiming it.
- **FEMA's API was down (503) during testing**, but the 760 MB parquet bulk file downloads fine.

## The main disagreement, and how it was settled

The IBM judge ranked **Sealed Witness #1**, because IBM Z hardware crypto is the product itself. The engineer measured its dataset at **4.82 GB** and estimated 25 person-hours against about 30 available, putting its chance of shipping a convincing demo at 40%.

**Decision:** the engineer's live measurements beat the judge's opinion. #1 has to survive both lenses, and Second Look is the idea that does.

## Final ranking (16 ideas)

| Rank | Idea | Theme | One line | Why here |
|---|---|---|---|---|
| **1** | **Second Look** | 3 (Disaster relief) | Finds FEMA aid denials that had verified damage but were rejected for a fixable reason, checks fairness by age, income, renter status and disability, and ranks who caseworkers should call back | Real labeled government data, verified downloadable (26.2M rows). Strongest emotional hook. Matches the winner pattern. Few teams will build it. Chance of a convincing demo ~75% |
| 2 | Second Look, Sealed | 2 (Privacy) | Same as #1, plus applicant identities tokenized with LinuxONE hardware crypto, and an audited unmask only when a caseworker calls | Carries your security passion and makes IBM Z structural. **Hole:** the public FEMA data is already de-identified, so the privacy layer protects nothing real in the demo. Best kept as an add-on (see below) |
| 3 | Tripwire | 1 (Real-time) | Catches card-testing bots (small charges on stolen cards) before the big cash-out, using IBM's own TabFormer dataset | Strong IBM fit (verified 279 MB IBM dataset). But fraud is the most crowded topic, and there are no campaign labels, so you'd be grading attacks you injected yourself |
| 4 | Pager Zero | 1 | Early warning for IT outages from labeled system logs, deciding when to page a human | Safest build (57 MB labeled data, ~85% chance of a demo). Low originality, since it's a well-studied problem |
| 5 | Doppel | 2 | Privacy clean room: only releases models and synthetic data that pass an automated privacy attack (IBM diffprivlib + IBM ART) | Small data, IBM's own libraries. Feels like a tutorial and has no victim on screen |
| 6 | Sealed Witness | 2 | Insider-threat detection where analysts see only tokens; unmasking needs two key holders, with a hash-chained audit | Best idea on paper (the judge's #1). 4.8 GB synthetic data and too much scope for 24h |
| 7 | Hang Up | 2 | Detects scam texts targeting seniors, stress-tested against scams rewritten by AI | Verified dataset (5,971 texts) and a strong statistic ($4.9B lost by people 60+). But SMS spam is a beginner Kaggle project and IBM Z adds nothing |
| 8 | Second Opinion | 1 | Fraud triage under a limit on how many cases human analysts can review | Clever, but abstract to demo, and the dataset needs a Kaggle login and has a non-commercial license |
| 9 | Surge | 3 | Forecasts unemployment-claim surges so mainframe benefit systems can scale up in time | Good IBM Z story (the 2020 New Jersey COBOL crisis), but thin AI |
| 10 | Blindfold | 2 | My earlier pick: a token gateway for bank AI agents | Five subsystems, self-generated traces, only 662-row injection data, tokenization is a commodity |
| 11 | Driftguard | 1 | Catches poisoned fraud labels before retraining | Interesting, but monthly batches make the "real-time" claim weak |
| 12 | Memory Poison Sentinel | 2 | Screens content before it enters an AI agent's memory | Hot topic, weak IBM Z role, unverified data |
| 13 | Least-Privilege Lens | 2 | Drafts minimal permissions for machine identities from cloud logs | No labels, IBM Z role nearly zero |
| 14 | Mirage | 1 | My earlier backup: fraud-model clone defense | Threat model doesn't hold: payment attackers only see approve/decline, the anonymized features can't be controlled, and the results are circular |
| 15 | Unmasked | 2 | Re-identification attack on "anonymized" data | Done many times before |
| 16 | LeakyClient | 2 | Scans apps for leaked secrets (the reverse-engineering angle) | No ground truth, ethics issues, no IBM Z role |

Dropped early: icebreaker games (no dataset), house-mapping robot (hardware, not a datathon project).

## #1 in detail: Second Look

### Inspiration
After a disaster, FEMA confirms a family's home is damaged, then denies aid because a document is missing or occupancy wasn't verified. Many never appeal. Elderly, disabled and renter households may be hit hardest.

### What it does
- Loads OpenFEMA's Individuals and Households Program records (26.2M rows, 100 fields) onto a LinuxONE VM.
- Builds the **"Second Look cohort":** households with **verified damage** (`rpfvl`/`ppfvl` > 0, inspection returned, habitability repairs required) whose aid was **denied for a fixable reason**.
- Trains a model on **what predicts landing in that cohort** (not on whether the household was eligible).
- Measures **fairness gaps** across `applicantAge`, `grossIncome`, `ownRent` and `accessFunctionalNeeds`.
- Outputs a **ranked callback list per disaster** for caseworkers. It flags cases for human review and never decides a case.
- Reports **s390x throughput** for scoring all 26M records in one batch.

### The trap the engineer found (build around it)
`ihpEligible` is almost a direct function of "verified loss > 0 and not insured." A plain classifier hits about 0.99 AUC just by learning that rule, and a judge will take it apart with one question. **The deliverable is the cohort and the fairness gaps, not the AUC.**

### Riskiest assumption: check in hour one
`ineligibleReason` is a numeric code (`'1'` to `'9'`), not text. Decode it with the OpenFEMA data dictionary and confirm it splits cleanly into **fixable** (documentation, ownership, occupancy) vs **genuinely ineligible** (insured, no damage). If it doesn't, the cohort definition collapses, and you want to know that at 00:30, not at 14:00.

### Stack (verified constraints)

| What | Why |
|---|---|
| LinuxONE VM, Python 3.12 via conda `defaults` | Snap ML has no 3.13 wheel; pandas, pyarrow and sklearn have no s390x pip wheels |
| pyarrow, reading by column and row group | The 760 MB parquet has 214 row groups, so load only the columns needed |
| IBM Snap ML (fallback: sklearn / xgboost from conda) | IBM's library, and it can use the Telum accelerator if the VM exposes it |
| Fairness metrics (e.g. AIF360 or hand-rolled disparate-impact ratios) | Subgroup gaps by age, income, renter status, disability |
| Streamlit | Callback list, fairness charts, per-disaster drilldown |
| Big-endian / porting notes | Past winners got credit for this, so write it up |

### Metrics
- Cohort size per disaster
- Precision@K on a hand-checked sample of the callback list
- Disparate-impact ratio per subgroup with confidence intervals
- Records/sec scored on s390x

### Optional add-on (your security passion): only if the cohort works by hour 6
**Re-identification risk audit:** measure how many FEMA public rows are unique on quasi-identifiers (geography + age bin + income bin + renter status). Report aggregate uniqueness only (k-anonymity), never individual rows. Then show the production design: applicant IDs tokenized with LinuxONE hardware crypto, with an audited unmask at callback time. This turns rank #1 into rank #2 without betting the whole project on it.

## Open questions only you can answer
1. **Team size and skills?** Solo means no add-on and a minimal UI.
2. **Theme 3 with social good (#1), or Theme 2 for your security passion (#2)?**
3. **Is your LinuxONE VM approved yet?** If not, start the 760 MB parquet download on your laptop now.
