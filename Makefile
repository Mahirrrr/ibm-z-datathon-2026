PY ?= .venv/bin/python
TF_IMAGE ?= registry.linuxone.cloud.marist.edu/l1cc/jupyterlab-image-s390x:latest
TF_RUN = podman run --rm --user 0 --entrypoint "" -v $(CURDIR):/work:Z -w /work $(TF_IMAGE) /opt/venv/bin/python -m pipeline.twin
TF_RUN_CPU = podman run --rm --user 0 --entrypoint "" -e NNPA_DEVICES=0 -v $(CURDIR):/work:Z -w /work $(TF_IMAGE) /opt/venv/bin/python -m pipeline.twin

.PHONY: data ingest pipeline all test policy notes twin

data:
	mkdir -p data/raw
	curl -sSL -C - -o data/raw/ihp_registrations_v2.parquet \
	  "https://www.fema.gov/about/reports-and-data/openfema/v2/IndividualsAndHouseholdsProgramValidRegistrationsV2.parquet"

# Reads FEMA's Parquet; run on a little-endian machine (see pipeline/frames.py).
ingest:
	$(PY) -m pipeline.ingest

# Everything after ingest; runs on LinuxONE (s390x).
pipeline:
	$(PY) -m pipeline.cohort
	$(PY) -m pipeline.train
	$(PY) -m pipeline.fairness
	$(PY) -m pipeline.rank
	$(PY) -m pipeline.benchmark
	$(PY) -m pipeline.store

all: ingest pipeline

# FEMA policy corpus for RAG (needs pdftotext); writes docs/data/iappg_chunks.json.
policy:
	mkdir -p data/policy
	curl -sSL -o data/policy/iappg-1.1.pdf https://www.fema.gov/sites/default/files/documents/fema_iappg-1.1.pdf
	pdftotext data/policy/iappg-1.1.pdf data/policy/iappg-1.1.txt
	$(PY) -m pipeline.policy

# Granite notes on LinuxONE: needs llama-server on 127.0.0.1:8081 (see README). Then rebuild the store.
notes:
	$(PY) -m pipeline.genai --disasters 10 --per-disaster 5
	$(PY) -m pipeline.store

# Keras twin on the Telum NNPA, inside IBM's TensorFlow + zDNN image.
twin:
	$(PY) -m pipeline.twin export
	$(TF_RUN_CPU) train
	$(TF_RUN_CPU) bench
	$(TF_RUN) bench
	$(PY) -m pipeline.twin combine

test:
	$(PY) -m pytest -q tests
