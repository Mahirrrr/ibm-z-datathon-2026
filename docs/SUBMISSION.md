# Submission kit (Hack2Skill, IBM Z Datathon 2026)

Submit at https://hack2skill.com/event/datathon-2026. The deadline is about Sun Oct 18, 11:29 AM CDT; aim to finish by 9 AM.

## Checklist

- [ ] **Project title** contains the team name: `Second Look: finding the disaster survivors FEMA turned away`
- [ ] **Description** contains the event code **SSF2026** (text below).
- [ ] **Demo video**, 3:00 or less, recorded on the LinuxONE VM (see `docs/VIDEO_PLAN.md`), uploaded as unlisted YouTube and linked.
- [ ] **Pitch deck PDF** named exactly `Second Look_IBM Z Datathon 2026 Project.pdf`.
- [x] **Working prototype** (optional): https://mahirrrr.github.io/ibm-z-datathon-2026/ (static snapshot, always up). Live on the z17, best effort: https://divisions-films-jesse-nsw.trycloudflare.com (the URL changes if the VM restarts; rebuild the snapshot to update its banner link).
- [ ] **Repository link.** The repo is private now. Before making it public:
  - [ ] Remove `docs/research/*.pdf` (the event guidebook and kickoff deck). They are in git history, so `git rm` alone still leaves them reachable. Either rewrite history (`git filter-repo --path "docs/research/IBM Z Datathon 2026 Guidebook.pdf" --path "docs/research/IBM Z Datathon Kickoff Deck.pdf" --invert-paths`) or publish a fresh repo from a clean squash. **Mahir decides; both are destructive to history.**
  - [ ] Confirm no keys or tokens are in the tree: `git grep -n -I -E "BEGIN .*PRIVATE|token=|Your_Token"`.
- [ ] **Open-source links** (list below).
- [ ] Optional: architecture flowchart (the Mermaid diagram in README.md, exported as PNG).
- [ ] Team: confirm with the organizers that a solo entry is accepted (the rules say 4–6). The message is drafted in Discord #helpdesk.
- [ ] Both mandatory labs done, with screenshots.

## Description (paste into the form)

> Second Look finds disaster survivors FEMA turned away even though an inspector verified their damage, and gets them a callback. Event code: SSF2026.
>
> In 26.2 million OpenFEMA aid applications, 94,395 households had verified damage and were denied for a fixable reason: missing documents, lost contact, or ownership or occupancy that was never verified. That adds up to $612M in verified loss. Renters face 1.88x adjusted odds of landing in this group, and households reporting $0 income face 3.02x.
>
> Everything runs on IBM LinuxONE (IBM z17, s390x):
> - an IBM Snap ML model that scores who is at risk (ROC AUC 0.785 on 114 disasters it never saw)
> - a TensorFlow twin of that model on the Telum on-chip AI accelerator, through IBM's zDNN plugin
> - IBM Granite 3.3 running locally in llama.cpp, which writes a callback note and script for each household, grounded in FEMA's Individual Assistance Program and Policy Guide with cited sections (RAG)
> - a rootless, read-only Podman container that serves the caseworker dashboard
>
> It runs IBM's Predictive + Generative loan-approval lab in reverse. The lab explains why a bank said no; we find the families a system said no to, wrongly.

## Open-source and public resources

| Resource | Link |
|---|---|
| OpenFEMA IHP Valid Registrations V2 (data) | https://www.fema.gov/openfema-data-page/individuals-and-households-program-valid-registrations-v2 |
| FEMA Individual Assistance Program and Policy Guide v1.1 (RAG corpus) | https://www.fema.gov/sites/default/files/documents/fema_iappg-1.1.pdf |
| IBM Granite 3.3 2B Instruct | https://huggingface.co/ibm-granite/granite-3.3-2b-instruct |
| Big-endian Granite GGUF for s390x | https://huggingface.co/taronaeo/Granite-3.3-2B-Instruct-BE-GGUF |
| llama.cpp | https://github.com/ggml-org/llama.cpp |
| IBM Snap ML | https://www.zurich.ibm.com/snapml/ |
| TensorFlow / Keras | https://www.tensorflow.org/ |
| IBM Z Accelerated for TensorFlow (zDNN plugin) | https://github.com/IBM/ibmz-accelerated-for-tensorflow |
| zDNN | https://github.com/IBM/zDNN |
| LinuxONE jupyter-lab-ml image | https://github.com/linuxone-community-cloud/jupyter-lab-ml |
| pandas, Apache Arrow, scikit-learn, NumPy | https://pandas.pydata.org/ · https://arrow.apache.org/ · https://scikit-learn.org/ · https://numpy.org/ |
| FastAPI, Uvicorn, SQLite | https://fastapi.tiangolo.com/ · https://www.uvicorn.org/ · https://sqlite.org/ |
| Podman, Miniconda | https://podman.io/ · https://docs.anaconda.com/miniconda/ |
| IBM Plex, Carbon Design System | https://github.com/IBM/plex · https://carbondesignsystem.com/ |
