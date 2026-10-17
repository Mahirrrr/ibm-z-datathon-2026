PY ?= .venv/bin/python

.PHONY: data pipeline test

data:
	mkdir -p data/raw
	curl -sSL -C - -o data/raw/ihp_registrations_v2.parquet \
	  "https://www.fema.gov/about/reports-and-data/openfema/v2/IndividualsAndHouseholdsProgramValidRegistrationsV2.parquet"

pipeline:
	$(PY) -m pipeline.ingest
	$(PY) -m pipeline.cohort
	$(PY) -m pipeline.train
	$(PY) -m pipeline.fairness
	$(PY) -m pipeline.rank
	$(PY) -m pipeline.store

test:
	$(PY) -m pytest -q tests
