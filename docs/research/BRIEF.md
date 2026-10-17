# Debate brief: IBM Z Datathon 2026 project choice

## Event facts
- 24h datathon, started 22:42 Oct 17 2026 (US Central), submission ~22:42 Oct 18. Devpost-style submission on hack2skill with event code SSF2026.
- Must use IBM Z / LinuxONE: participants get a LinuxONE Community Cloud VM (s390x, big-endian Linux). Jupyter Lab ML setup repo provided (linuxone-community-cloud/jupyter-lab-ml). Possible package pain on s390x.
- "Datathon" = AI/data science, "technology for good". Judges are IBM people.
- Pick ONE theme; "solution must clearly align from architecture to final pitch":
  - Theme 1 "Real-Time AI for Critical Decisions" (DETECT. DECIDE. RESPOND.): AI that analyzes streaming data, identifies risk, supports high-stakes decisions in real time. Examples: real-time payment fraud detector, predictive IT outage early warning, supply-chain disruption monitor, emergency resource prioritization, real-time insurance risk scoring. Core principle: data analyzed immediately, AI influences decisions while it matters.
  - Theme 2 "AI Secured: Innovation Without Exposure" (POWERFUL AI. PROTECTED DATA.): privacy-preserving AI that learns from sensitive datasets while protecting identity, trust, regulatory compliance. Examples: privacy-aware AI assistant, intelligent access anomaly detector, data-leakage prevention gateway, quantum-safe readiness scanner, AI-powered SecOps assistant. Core principle: build security and privacy directly into the application core.
  - Theme 3 "Wildcard: Beyond the Obvious": novel data-driven AI, responsible, ambitious. Examples: AI accessibility companion, food waste prediction, personalized student success coach, community infrastructure AI, disaster relief intelligence. Core principle: breakthrough ideas addressing significant societal challenges.

## The builder
- Mahir: UT Dallas Business Analytics & AI undergrad (sophomore-ish), Python/data/ML comfortable, has built a full-stack app. Team size unknown (assume 1-3). Will use AI coding assistants heavily.
- Interests: security + privacy; worried that AI makes reverse engineering trivial (REA tool, AI decompiling apps/games) and that AI makes privacy worse. Earlier raw ideas: professional icebreaker games; company-wide device software; house-mapping robot; new security measures vs AI.

## Signals from material he pasted (r/cybersecurity threads, Belfer "Attacking AI" report)
- Real practitioner pain: over-permissioned AI agents, sensitive data pasted into prompts, prompt injection via data the agent reads (emails, logs, web pages), memory poisoning, non-human identities outnumber humans ~45:1, time-to-exploit shrinking to hours, patch overload, AI-assisted triage, "prove the finding" vs "summarize the alert", reachability analysis of CVEs.
- AI reverse engineering: client code can always be decompiled; clones mostly replicate behavior via network APIs; security through obscurity is dead; keep secrets server-side.
- Belfer report: input (evasion) attacks, poisoning attacks, model theft via API outputs to build "copy models" that craft transferable evasion; AI Security Compliance (suitability tests, red teaming, attack response plans); FUSAG inflatable-tank deception analogy.

## Winning Devpost write-ups he admires (style to imitate)
Nudge, aide, Angel's Protection, AgriMind, HootHive, RaiderClaim, EpicRAG, SerenityAI: concrete "What it does" bullets each naming capability + tool; layered "How we built it"; tech table with why-it-mattered; measured numbers with eval-set sizes (e.g., "precision 1.000 / recall 0.896 on 140-window eval set"); honest about where AI is not the answer; folder skeleton.

## Ideas already on the table (attack them too)
1. Blindfold (Theme 2): privacy gateway on LinuxONE between bank AI agents and customer data. LLM only sees typed tokens; injection classifier; per-agent behavioral anomaly baseline; honeytokens; field-level policy scopes; Streamlit dashboard. Data: Berka bank dataset or synthetic PII, deepset/prompt-injections, simulated agent traces.
2. Mirage (Theme 1): protects a bank fraud-scoring model from extraction-then-evasion. Detect cloning query patterns (PRADA), serve a decoy model with a wrong boundary to flagged clients, trap evasion attempts crafted on the decoy. Data: ULB credit card fraud (284k rows).

## Judging lens to use (assumed; typical for IBM Z datathon)
Problem significance/impact, innovation/originality, technical execution + data/AI rigor, use of IBM Z/LinuxONE (structural not decorative), theme alignment, presentation/demo, feasibility within 24h for a small student team.
