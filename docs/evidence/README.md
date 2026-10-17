# LinuxONE evidence

Everything here was captured from the project's IBM LinuxONE Community Cloud VM on Oct 17, 2026. The judging rubric (criterion 3) asks for proof of containers, security, scalability, and compute.

## Compute

| File | Shows |
|---|---|
| [system.txt](system.txt) | `uname -m` = **s390x**, `machine = 9175` (**IBM z17**), CPU features include **`nnpa`** (Telum II on-chip AI accelerator), 3 vCPU, 8 GB RAM, Ubuntu 24.04, `libzdnn` installed |
| [software.txt](software.txt) | Python 3.12 env with pandas, pyarrow, scikit-learn and **IBM Snap ML 1.17.2**; Snap ML imports its zDNN (NNPA) build |
| [pipeline_run.log](pipeline_run.log) | Full `make pipeline` run on the z17: cohort, Snap ML training, fairness, ranking, store |
| [model_metrics.json](model_metrics.json) | `"machine": "s390x"`, `"backend": "snapml"`, ROC AUC 0.785 on 114 held-out disasters, fit 87.6s on 6.98M rows |
| [inference_benchmark.json](inference_benchmark.json) | Scoring all 8,938,750 verified-damage households with three Snap ML engines |

### Inference engines on the z17 (8,938,750 households)

| Engine | Seconds | Records/sec |
|---|---|---|
| CPU, standard trees | 21.3 | 419,197 |
| CPU, Snap ML compressed trees | 3.9 | **2,306,666** |
| Telum AI accelerator (NNPA, `zdnn_tensors`) | 37.3 | 239,909 |

All three return the same scores (max difference 1e-16). The NNPA path runs end to end. On this shared 3-vCPU VM, Snap ML's compressed trees were the fastest engine for this tree ensemble, so that is the one we report as fastest.

## Containers

| File | Shows |
|---|---|
| [../../Containerfile](../../Containerfile) | Image definition: python:3.12-slim, FastAPI and uvicorn only, non-root user |
| [container.txt](container.txt) | Podman 4.9.3, image built natively for s390x (148 MB), container running, security settings from `podman inspect` |

## Security

Settings below are visible in `container.txt`:

- **Rootless Podman** (`rootless=true`), seccomp on, cgroups v2.
- **Read-only root filesystem** (`ReadonlyRootfs=true`), **all Linux capabilities dropped**, `no-new-privileges`, runs as UID 1000.
- **Database mounted read-only** (`rw=false`). The API also opens SQLite with `mode=ro`.
- **No public port.** The container binds `127.0.0.1:8000` only, and the dashboard is reached through an SSH tunnel with key-only auth.
- **No direct identifiers.** The OpenFEMA dataset has no names, addresses or phone numbers; households are opaque record IDs.

## Dashboard served from LinuxONE

These screenshots were taken through the SSH tunnel from the Podman container on the z17:

- [dashboard_story.png](dashboard_story.png): the cohort, denial reasons, fairness gaps with 95% intervals, top disasters
- [dashboard_disaster_4559.png](dashboard_disaster_4559.png): caseworker console for Hurricane Laura (LA, 2020) with the ranked callback list
- [dashboard_method_linuxone.png](dashboard_method_linuxone.png): method, model metrics, and the LinuxONE runtime panel (s390x, Snap ML, NNPA, Podman)

## Still to add (manual)

- Screenshot of the LinuxONE Community Cloud portal's **expanded instance details** (image Ubuntu24.04-Datathon, flavor AI_LAB, 3 vCPU, 8192 MB, 50 GB). Don't use the status row: it shows ERROR although the VM runs (see CLAUDE.md).
