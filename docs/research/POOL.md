# Round 1 idea pool (14 ideas)

Self-scores are the proposer's own: Impact / Originality / Feasibility-24h / IBM-fit / Theme-fit.

## Theme 2 (AI Secured)

1. **Blindfold**
   - Privacy gateway between bank AI agents and customer data. The LLM sees typed tokens only.
   - Layers: injection classifier, per-agent anomaly baseline, honeytokens, field scopes.
   - Data: Berka/synthetic PII, deepset/prompt-injections (~660 rows), simulated agent traces.
   - Critique: five subsystems; self-generated traces; tokenization is commodity (Presidio); LinuxONE is only a host unless crypto is central.

2. **Sealed Witness**
   - Insider-threat detection (UEBA) on pseudonymized logs. Identities are HMAC-tokenized on LinuxONE (CPACF hardware crypto).
   - Unmasking requires two key shares plus a justification, recorded in a hash-chained audit log.
   - Snap ML scoring.
   - Data: CMU CERT Insider Threat r4.2 (1,000 users, labeled insiders; multi-GB synthetic; realism critiques).
   - Metrics: precision@50; identities exposed per true positive; CPACF tokens/sec.
   - Self-score: 7/8/7/8/10

3. **Doppel**
   - Privacy clean room: raw credit data stays on LinuxONE.
   - Releases DP models and synthetic tables, gated by an automated membership-inference attack (block if AUC > 0.55).
   - Uses IBM diffprivlib + IBM ART.
   - Data: UCI Default of Credit Card Clients (30k).
   - Self-score: 7/7/8/7/9

4. **Least-Privilege Lens**
   - Learns what non-human identities actually do from CloudTrail and drafts minimal IAM policies.
   - Data: flaws.cloud CloudTrail (1.9M events, unlabeled, mostly attack traffic).
   - Self-score: 8/7/6/5/8

5. **Memory Poison Sentinel**
   - Screens content before it enters agent memory or a RAG index.
   - Data: Microsoft BIPIA.
   - Weak Z story.
   - Self-score: 8/6/6/4/8

## Theme 1 (Real-Time AI)

6. **Mirage**
   - Detects fraud-model extraction, serves a decoy boundary, traps evasions.
   - Data: ULB credit card (PCA features).
   - Critiques:
     - Payment attackers only see approve/decline, and each query costs a stolen card.
     - PCA features aren't attacker-controllable.
     - Attacker and evasions are self-generated (circular).
     - The decoy mis-decides real payments.

7. **Tripwire**
   - Real-time card-testing campaign detector: catches bots probing stolen cards with small authorizations, before the cash-out.
   - Actions: block merchant/BIN, step-up, rate-limit.
   - Data: IBM TabFormer (24M synthetic transactions by IBM, with merchant, MCC, Errors? field: Bad CVV / Bad Card Number). Download via git-lfs/Box, liveness unverified.
   - Risk: no campaign labels, so labels must be heuristic or injected.
   - Metrics: campaign recall at FP/10k; lead time (probes before cash-out); p99 latency on s390x.
   - Self-score: 8/7/7/9/9

8. **Pager Zero**
   - IT outage early warning from logs, with a page-a-human decision.
   - Data: Loghub BGL/HDFS (Zenodo, labeled).
   - Well-worn space.
   - Self-score: 7/5/9/6/9

9. **Second Opinion**
   - Capacity-aware triage of fraud cases: auto-approve / auto-decline / route to a human.
   - Data: Feedzai BAF (Kaggle login, CC BY-NC-ND).
   - Self-score: 8/8/6/7/9

10. **Driftguard**
    - Detects label-flip poisoning in the confirmed-fraud feedback loop and freezes retraining.
    - Data: BAF + injected flips.
    - Self-score: 7/8/6/6/7

## Theme 3 (Wildcard) and cross-theme

11. **Second Look**
    - Audit model flagging likely-wrongful FEMA disaster-aid denials (verified damage but denied for a fixable reason).
    - Fairness by age/income/disability/renter; ranked caseworker call-back list.
    - Data: OpenFEMA IHP Valid Registrations, 26.2M rows via public API, with labels like ihpEligible and ineligibleReason.
    - Z role: batch-scoring a government system of record; s390x throughput.
    - Risk: "wrongful" is a proxy label.
    - Self-score: 9/8/8/7/9

12. **Surge**
    - Forecasts state unemployment-claim surges so mainframe benefit systems can scale up (NJ 2020).
    - Data: DOL ar539.csv.
    - Self-score: 7/7/9/8/7

13. **Unmasked**
    - Re-identification linkage attack on "anonymized" data, plus a DP/synthetic fix.
    - Data: UCI Adult.
    - Done many times before.
    - Self-score: 7/5/9/5/7

14. **LeakyClient**
    - Scans F-Droid app source for client-side secrets (AI reverse-engineering angle).
    - No ground truth.
    - Self-score: 6/6/5/3/6

## Research facts gathered

**Past IBM Z Datathon winners**
- 2024: 9,000+ registrations, 320+ submissions, 13 winning teams.
- Examples: BERT hate-speech classifier with big-endian model save and <1s inference on LinuxONE; lake-encroachment CNN on satellite images (had to fix PyTorch on s390x); agriculture ML; healthcare access; symptom-to-disease logistic regression.
- Pattern: simple, readable supervised ML on labeled public data with visible social good. The recurring Z detail is the s390x/big-endian porting story.
- No adversarial-security winner found. No published rubric found.

**IBM tooling on s390x**
- Snap ML has s390x wheels on PyPI; install numpy/scipy via conda first. It can use zDNN, the Telum accelerator.
- zDLC compiles ONNX for Telum; its container needs icr.io.
- No official onnxruntime pip wheel for s390x.
- The jupyter-lab-ml container has TF, PyTorch, XGBoost, sklearn and llama.cpp on Ubuntu 24.04 or RHEL.
- Unknown whether Community Cloud VMs expose NNPA. Check with `grep nnpa /proc/cpuinfo`.
- IBM's own libraries: diffprivlib, ART (Adversarial Robustness Toolbox), TabFormer dataset.
