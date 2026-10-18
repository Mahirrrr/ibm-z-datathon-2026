"""Shared paths, column lists and policy constants for the Second Look pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

IHP_RAW = RAW_DIR / "ihp_registrations_v2.parquet"
IHP_SLIM = PROCESSED_DIR / "ihp_slim.arrow"
COHORT = PROCESSED_DIR / "cohort.arrow"

IHP_URL = (
    "https://www.fema.gov/about/reports-and-data/openfema/v2/"
    "IndividualsAndHouseholdsProgramValidRegistrationsV2.parquet"
)

# Only these columns are read from the 100-column source file.
SLIM_COLUMNS = [
    "id",
    "disasterNumber",
    "declarationDate",
    "incidentTypeCode",
    "damagedStateAbbreviation",
    "county",
    "fips",
    "applicantAge",
    "householdComposition",
    "occupants65andOver",
    "grossIncome",
    "ownRent",
    "primaryResidence",
    "residenceType",
    "homeOwnersInsurance",
    "floodInsurance",
    "registrationMethod",
    "accessFunctionalNeeds",
    "selfAssessmentInformation",
    "ihpEligible",
    "ihpAmount",
    "ineligibleReason",
    "inspnReturned",
    "habitabilityRepairsRequired",
    "destroyed",
    "floodDamage",
    "roofDamage",
    "rpfvl",
    "ppfvl",
    "unmetNeedRp",
    "unmetNeedPp",
    "verifiedOwnership",
    "verifiedOccupancy",
    "appliedDate",
]

# Decimal money columns are cast to float32 to keep memory small.
MONEY_COLUMNS = ["ihpAmount", "rpfvl", "ppfvl", "unmetNeedRp", "unmetNeedPp"]

MODELS_DIR = ROOT / "models"
MODEL_PATH = MODELS_DIR / "second_look.joblib"
METRICS = PROCESSED_DIR / "model_metrics.json"
BENCHMARK = PROCESSED_DIR / "inference_benchmark.json"
FAIRNESS = PROCESSED_DIR / "fairness.arrow"
ADJUSTED_ODDS = PROCESSED_DIR / "adjusted_odds.arrow"
CALLBACKS = PROCESSED_DIR / "callbacks.arrow"
SCORES = PROCESSED_DIR / "scores.arrow"
AID = PROCESSED_DIR / "aid.arrow"
COUNTIES = PROCESSED_DIR / "counties.arrow"
DB_PATH = ROOT / "secondlook.db"

# Generative layer: FEMA policy corpus (IAPPG 1.1) and Granite-written notes.
POLICY_TEXT = ROOT / "data" / "policy" / "iappg-1.1.txt"
POLICY_CHUNKS = ROOT / "docs" / "data" / "iappg_chunks.json"
NOTES = PROCESSED_DIR / "callback_notes.jsonl"
LLM_URL = "http://127.0.0.1:8081/v1/chat/completions"  # llama-server on the VM, localhost only

# Model features: only what FEMA knows once an inspection confirms damage, BEFORE the
# eligibility decision. Decision fields (ihpEligible, ihpAmount, ineligibleReason,
# unmetNeed*, verifiedOwnership/Occupancy) would leak the label and are excluded.
CATEGORICAL_FEATURES = [
    "applicantAge",
    "householdComposition",
    "occupants65andOver",
    "grossIncome",
    "ownRent",
    "residenceType",
    "registrationMethod",
    "selfAssessmentInformation",
    "incidentTypeCode",
    "damagedStateAbbreviation",
]
BOOLEAN_FEATURES = [
    "primaryResidence",
    "homeOwnersInsurance",
    "floodInsurance",
    "accessFunctionalNeeds",
    "habitabilityRepairsRequired",
    "destroyed",
    "floodDamage",
    "roofDamage",
]
NUMERIC_FEATURES = ["rpfvl", "ppfvl", "declarationYear"]

# Groups the fairness audit reports on, with the reference category for ratios.
FAIRNESS_GROUPS = {
    "ownRent": "O",
    "grossIncome": "$60,001-$120,000",
    "applicantAge": "50-64",
    "accessFunctionalNeeds": False,
}

# Callback priority: explicit policy weights, shown in the UI. Not learned.
TIER_WEIGHTS = {
    "missing_documents": 1.0,
    "unverified_ownership_or_occupancy": 0.9,
    "lost_contact": 0.8,
}
VULNERABILITY_BONUS = 0.25  # added per vulnerability factor
HABITABILITY_BONUS = 0.5  # home not livable without repairs
