PY ?= .venv/bin/python

.PHONY: data ingest pipeline all test

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

test:
	$(PY) -m pytest -q tests
