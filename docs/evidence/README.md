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
| Snap ML `zdnn_tensors` engine | 37.3 | 239,909 |

All three return the same scores (max difference 1e-16). Because the NNPA computes in reduced precision, identical scores mean this run doesn't prove Snap ML used the accelerator. The TensorFlow twin below does. On this shared 3-vCPU VM, Snap ML's compressed trees were the fastest engine for this tree ensemble, so that is the one we report as fastest.

### Telum NNPA via TensorFlow ([twin_benchmark.json](twin_benchmark.json))

A Keras twin of the model scores 1,961,754 held-out households inside IBM's jupyter-lab-ml image (TensorFlow 2.18.1, ibm-zdnn-plugin 2.3.0):

| Device | Records/sec |
|---|---|
| CPU (`NNPA_DEVICES=0`) | 1,424,337 |
| Telum NNPA (zDNN plugin) | 1,745,681 (**1.23x**) |

The maximum score difference is 0.0033, from reduced-precision NNPA math, so the accelerator really ran.

### Generative layer ([callback_notes.jsonl](callback_notes.jsonl), [granite_runtime.txt](granite_runtime.txt))

- IBM Granite 3.3 2B Instruct (Q4_0, big-endian GGUF) runs in llama.cpp on the z17, on 127.0.0.1:8081 only.
- 50 cited notes cover the top 5 callbacks in each of the 10 largest disasters. All 50 passed the citation, dollar-amount and no-promise checks.
- Median 142s and 252 generated tokens per note. Throughput on the shared VM ranged from 1.1 to 4.5 tokens/s.
- [dashboard_disaster_4559_granite.png](dashboard_disaster_4559_granite.png) and [dashboard_method_genai.png](dashboard_method_genai.png) are served by the Podman container on the z17.

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
- **No inbound port.** The container binds `127.0.0.1:8000` only. Caseworkers use an SSH tunnel with key-only auth, and the public demo uses an outbound Cloudflare quick tunnel to the same read-only API.
- **No direct identifiers.** The OpenFEMA dataset has no names, addresses or phone numbers; households are opaque record IDs.

## Dashboard served from LinuxONE

These screenshots were taken through the SSH tunnel from the Podman container on the z17:

- [dashboard_story.png](dashboard_story.png): the cohort, the modeled aid estimate ($385.0M), denial reasons, fairness gaps with 95% intervals, the county map, top disasters
- [dashboard_story_map.png](dashboard_story_map.png): county map of the 94,395 households, with Puerto Rico as an inset
- [aid_run.log](aid_run.log): the cohort and aid steps on the z17 (`/usr/bin/time -v`), with the estimate total, median and fallback counts
- [dashboard_disaster_4559.png](dashboard_disaster_4559.png): caseworker console for Hurricane Laura (LA, 2020) with the ranked callback list
- [dashboard_method_linuxone.png](dashboard_method_linuxone.png): method, model metrics, and the LinuxONE runtime panel (s390x, Snap ML, NNPA, Podman)

## Mandatory labs ([labs/](labs/))

Both labs ran end to end on the z17 on Oct 17, inside IBM's jupyter-lab-ml image (`registry.linuxone.cloud.marist.edu/l1cc/jupyterlab-image-s390x`). JupyterLab ran with a private token, published on 127.0.0.1 only and reached through an SSH tunnel; the public default token was not used. Each folder has the executed `.ipynb` and an HTML export, and no cell raised an error.

| Lab | Notebook | Screenshots |
|---|---|---|
| Predictive + Generative AI (loan approval: XGBoost, BM25 RAG, Granite on llama.cpp with zDNN) | `Loan_Approval_Demo.ipynb`, 9/9 cells | [JupyterLab](labs/Loan_Approval_Demo_jupyterlab.png), [features and risk](labs/Loan_Approval_Demo_features_risk.png), [recommendation and Q&A](labs/Loan_Approval_Demo_recommendation.png) |
| Predictive AI hybrid multi-model (client churn: scikit-learn + PyTorch) | `Churn_Scikit_PyTorch.ipynb`, 31/33 cells (the other 2 are empty) | [JupyterLab](labs/Churn_Scikit_PyTorch_jupyterlab.png), [PyTorch training](labs/Churn_Scikit_PyTorch_pytorch_training.png) |

## Provisioned instance

[portal_instance_details.png](portal_instance_details.png) is the LinuxONE Community Cloud portal's instance details: flavor **AI_LAB**, 3 vCPU, 8192 MB RAM, 50 GB disk, image **Ubuntu24.04-Datathon**. The portal's status row reads ERROR, but that label is stale. `uptime` on the VM shows it has run continuously since it was created, and the organizers have been asked to reset the label.
