from pipeline import policy

SAMPLE = """II. Individuals and Households Program Eligibility
Intro text about eligibility.
A. General IHP Eligibility
These general conditions must be met.
4. Occupancy
Applicants (both owners and renters) must be able to prove they occupied the home.
51
Chapter 3: Individuals and Households Program
Utility bills must be dated within 3 months prior to the incident period.
5. Ownership
FEMA will accept a written self-declarative statement as proof of ownership as a last resort.
52
Chapter 3: Individuals and Households Program
C. Appeal Process
1. Timeline for Appeal
Applicants have 60 days from the date of the decision letter to appeal.
III. Delivering Individuals and Households Program Assistance
C. Applicant Communication
FEMA attempts to contact applicants by phone and letter.
A. Lodging Expense Reimbursement
Not part of the corpus.
"""


def chunks():
    return policy.build_chunks(SAMPLE.splitlines(), first_page=51)


def test_sections_carry_hierarchy_title_and_page():
    by_section = {c["section"]: c for c in chunks()}
    occ = by_section["II.A.4"]
    assert occ["title"] == "Occupancy"
    assert occ["page"] == 51
    assert "Utility bills" in occ["text"]
    assert by_section["II.A.5"]["page"] == 52
    assert by_section["II.C.1"]["page"] == 53
    assert by_section["III.C"]["title"] == "Applicant Communication"


def test_page_headers_and_footers_are_stripped():
    text = " ".join(c["text"] for c in chunks())
    assert "Chapter 3:" not in text
    assert " 51 " not in f" {text} "


def test_stops_before_housing_assistance():
    assert all("Not part of the corpus" not in c["text"] for c in chunks())


def test_footnote_markers_removed_but_quantities_kept():
    lines = ["II. Individuals and Households Program Eligibility", "C. Appeal Process", "1. Timeline for Appeal",
             "Applicants must appeal determinations 81 within 60 days of the letter. 82"]
    text = policy.build_chunks(lines, first_page=66)[0]["text"]
    assert text == "Applicants must appeal determinations within 60 days of the letter."


def test_long_sections_split_into_passages_with_same_label():
    long_text = ["II. Individuals and Households Program Eligibility", "A. General IHP Eligibility",
                 "4. Occupancy"] + [f"Sentence number {i} about occupancy documents." for i in range(200)]
    parts = [c for c in policy.build_chunks(long_text, first_page=51) if c["section"] == "II.A.4"]
    assert len(parts) > 1
    assert all(len(p["text"]) <= policy.MAX_CHARS for p in parts)
    assert len({p["id"] for p in parts}) == len(parts)


def test_citation_label():
    c = {"section": "II.A.4", "title": "Occupancy", "page": 51}
    assert policy.label(c) == "IAPPG 1.1, Ch. 3 §II.A.4 Occupancy, p. 51"


def test_retrieval_stays_inside_tier_sections():
    index = policy.PolicyIndex(chunks())
    hits = index.retrieve("lost_contact", own_rent="R")
    assert {h["section"] for h in hits} <= {"III.C", "II.C.1"}
    assert any(h["section"] == "II.C.1" for h in hits), "appeal timeline always included"


def test_retrieval_for_unverified_renter_uses_occupancy_not_ownership():
    hits = policy.PolicyIndex(chunks()).retrieve("unverified_ownership_or_occupancy", own_rent="R")
    sections = {h["section"] for h in hits}
    assert "II.A.4" in sections
    assert "II.A.5" not in sections


def test_retrieval_for_unverified_owner_includes_ownership():
    hits = policy.PolicyIndex(chunks()).retrieve("unverified_ownership_or_occupancy", own_rent="O")
    assert "II.A.5" in {h["section"] for h in hits}


def test_retrieval_unknown_tier_raises():
    try:
        policy.PolicyIndex(chunks()).retrieve("nope", own_rent="O")
    except KeyError:
        return
    raise AssertionError("expected KeyError")
