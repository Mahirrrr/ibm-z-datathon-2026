"""Shared paths, column lists and policy constants for the Second Look pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

IHP_RAW = RAW_DIR / "ihp_registrations_v2.parquet"
IHP_SLIM = PROCESSED_DIR / "ihp_slim.parquet"
COHORT = PROCESSED_DIR / "cohort.parquet"

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
