"""OpenFEMA `ineligibleReason` codes and which ones Second Look treats as fixable.

Source: OpenFEMA IndividualsAndHouseholdsProgramValidRegistrations v2 data dictionary
(docs/data/ihp_fields.json).
"""

INELIGIBLE_REASONS = {
    "1": "No disaster-eligible damages or needs",
    "2": "Has insurance",
    "3": "Did not respond to FEMA outreach or withdrew",
    "4": "Needs to submit documentation",
    "5": "Duplicate application",
    "6": "Flood zone related reason",
    "7": "Other",
    "8": "Pending",
    "9": "Other non-identified eligibility code",
}

# Reasons a caseworker callback can plausibly resolve.
FIXABLE_TIERS = {
    "4": "missing_documents",
    "3": "lost_contact",
}

# "Other" reasons count as fixable only when FEMA also failed to verify ownership or occupancy.
OTHER_REASONS = {"7", "9"}
UNVERIFIED_TIER = "unverified_ownership_or_occupancy"

TIER_LABELS = {
    "missing_documents": "Denied for missing documents",
    "lost_contact": "Denied after FEMA lost contact",
    UNVERIFIED_TIER: "Ownership or occupancy never verified",
}


# OpenFEMA incidentTypeCode, from docs/data/ihp_fields.json
INCIDENT_NAMES = {
    "0": "Not applicable", "1": "Explosion", "2": "Straight-line winds", "3": "Tidal wave",
    "4": "Tropical storm", "5": "Winter storm", "8": "Tropical depression", "A": "Tsunami",
    "B": "Biological", "C": "Coastal storm", "D": "Drought", "E": "Earthquake", "F": "Flood",
    "G": "Freezing", "H": "Hurricane", "I": "Terrorist", "J": "Typhoon", "K": "Dam/levee break",
    "L": "Chemical", "M": "Mud/landslide", "N": "Nuclear", "O": "Severe ice storm",
    "P": "Fishing losses", "Q": "Crop losses", "R": "Fire", "S": "Snowstorm", "T": "Tornado",
    "U": "Civil unrest", "V": "Volcanic eruption", "W": "Severe storm", "X": "Toxic substances",
    "Y": "Human cause", "Z": "Other",
}


def reason_label(code):
    """Human-readable label for a reason code; unknown or missing codes get a neutral label."""
    if code is None:
        return "No reason recorded"
    return INELIGIBLE_REASONS.get(str(code), "Unknown code")
