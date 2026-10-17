# LinuxONE Setup & Tech Prep Session: notes

Source: https://www.youtube.com/live/HrNNkVyFots (55:16, IBM's Alex Osadchyy and Bruce, the L1CC program manager). Analysed from the auto-captions and sampled slide frames on Oct 17, 2026. Timestamps point into the video.

## What changes for Second Look

1. **Use IBM Granite for the generative layer, not just "a local LLM".** (31:17, 47:42, playbook slide 52:30) The new flagship lab (Predictive + Generative "Loan Approval") is the closest template to our design: XGBoost risk score on structured data + bank policy chunked into a vector DB (RAG) + Granite writes a structured decision and answers "why was this applicant approved/denied". The playbook slide says outright: "Pair structured predictive models with LLM reasoning (Granite)".
   - Our mapping: the cohort model replaces the XGBoost risk score. **RAG over the FEMA IHP policy guide (IAPPG)** replaces the bank policy. Granite writes the "why flagged" note and the callback script, citing the policy section that makes the denial fixable (missing documents, lost contact, ownership/occupancy proof).
   - Novelty warning on the same slide: "Avoid submitting reference ML lab notebooks without changes". Our angle (bank approves loans → we find people the system wrongly turned away) is an inversion of their lab, so say that in the pitch.
2. **Technical Design is the criterion they weight most.** (51:50) The speaker called it "the highly weighted criteria", even though the slide shows all four as max 10. The checklist on the slide:
   - include video screenshots of workloads running live on L1CC
   - use **at least 2 AI open-source frameworks** (their example: PyTorch + XGBoost)
   - demonstrate containerized deployment with Docker/Podman
   - highlight platform security **or** Telum hardware AI acceleration
3. **Telum (NNPA) acceleration is real but only for specific ops.** (25:10, 44:20) `lscpu | grep nnpa` shows the flag on the VM. The labs route TensorFlow MatMul/Dense/ReLU/Softmax to the NNPA through `ibm-zdnn-plugin` (`_zdnn.so`). Their numbers: MNIST CNN median 3.6 ms per 1,000-image batch on 3 vCPU; LSTM fraud model 10,395 sequences/s.
   - XGBoost/sklearn trees do **not** go through zDNN. If we want a Telum claim, add a small Keras MLP twin of the cohort model, run it with the zDNN plugin, and benchmark it against the CPU run. That also gives us the "2 frameworks" item (XGBoost + TensorFlow).
   - The labs export models to **ONNX** (tf2onnx) as the portability path. That's an option for a model trained elsewhere, but our plan to train on the VM still stands.
4. **Community value: quantify the beneficiaries.** (52:30) Slide asks for "a specific, quantified real-world beneficiary population", "AI for Good" framing, and "ethical AI and transparent decision reasoning". We already have 94,395 households, $612M verified loss, and the renter/income/age gaps. That's a direct hit. Theme 3's example list on the slide includes disaster relief.
5. **Pitch: show team roles.** (52:30) The slide says "Clearly present team member roles and contributions" and "Showcase live interactive demo recorded on LinuxONE environment". The demo must be recorded on the VM, not on the Mac.

## VM facts

| Item | Value | Where |
|---|---|---|
| Size | 3 vCPU, **8 GB RAM**, 50 GB disk, 30 days | 08:27 |
| Hardware | z17 (machine type 9175), Telum II, z/VM hypervisor, big-endian | 23:16 |
| Image | **Ubuntu 24.04.4-datathon** or **RHEL 9.8-datathon** (pick the `-datathon` one) | 16:03 |
| Flavor | **AI LAB**. It only appears if you registered with event code **SSF2026** in the project description | 16:53 |
| Login | user `linux1`, SSH key from the dashboard, full sudo | 19:22 |
| Quota | **one server per team** | 26:23 |
| Provisioning | 15–20 min at peak. If status is "shut down", press Start | 18:45 |

Wrong or missing event code: email the L1CC support address (spoken as Linux1 at us.ibm.com, check the FAQ for the exact address) or ask on Discord to delete the registration, then register again.

### Jupyter container (Step 5 of the jupyter-lab-ml README, 37:20)

```bash
docker pull registry.linuxone.cloud.marist.edu/l1cc/jupyterlab-image-s390x:latest
mkdir shared && chmod a+w shared
```

The `docker run` line is only partly legible in the video. It uses `--network host`, `--name notebook`, mounts `/home/linux1/shared` into `/home/ibm-user/shared`, and you may need `--security-opt seccomp=unconfined`. Copy it from the README instead of the video. Then open the port with `sudo iptables -I INPUT -p tcp --dport 38888 -j ACCEPT`.

**Security:** The VM has a **public IP** and the default Jupyter token is `Your_Token1`, which is printed on the public slide. Set your own token (`--ServerApp.token=...`). Serve our dashboard over the SSH tunnel only. This also gives us a security talking point for criterion 3.

## Risk for our pipeline on 8 GB

`pipeline/cohort.py` loads all of `ihp_slim.parquet` into pandas (26.2M rows × 33 columns). On the Mac, peak RSS was 2.7 GB, but pandas reports 8.5 GB deep usage. That's fine on the Mac and tight on the VM. Run it once on the VM early with `/usr/bin/time -v` (RSS check). If it OOMs, project only the columns cohort needs, or filter verified-damage rows with pyarrow before going to pandas. Ingest already streams row groups, so it's safe.

## Links (from the closing slide, 53:30)

- Instructions: https://ibm.biz/BdPcL8
- Register: https://linuxone.cloud.marist.edu/#/register?flag=VM
- Dashboard: https://linuxone.cloud.marist.edu/#/login
- Jupyter Lab ML: https://github.com/linuxone-community-cloud/jupyter-lab-ml
- Datathon FAQ: https://community.ibm.com/zsystems/datathon/
- L1CC landing page: https://community.ibm.com/zsystems/l1cc/
- Server deploy and access guides: https://github.com/linuxone-community-cloud/technical-resources

## The four labs (for the mandatory-lab check)

1. Credit-card fraud: 2-layer LSTM on 24M IBM synthetic transactions (also on Kaggle), NNPA inference, ONNX export.
2. **Predictive + Generative loan approval**: XGBoost + RAG + Granite. This one is new this year.
3. Churn/profitability: sklearn + PyTorch (decision trees, random forest, logistic regression).
4. MNIST digits: TensorFlow/Keras CNN with zDNN acceleration and ONNX export.

CLAUDE.md lists two labs as mandatory: "Predictive AI Hybrid multi-model" and "Predictive AI + Generative AI". Those likely map to labs 1/3 and 2.
