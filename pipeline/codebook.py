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


def reason_label(code):
    """Human-readable label for a reason code; unknown or missing codes get a neutral label."""
    if code is None:
        return "No reason recorded"
    return INELIGIBLE_REASONS.get(str(code), "Unknown code")
