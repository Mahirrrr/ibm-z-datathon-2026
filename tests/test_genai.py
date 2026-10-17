import json

import pytest

from pipeline import genai

PASSAGES = [
    {"id": "II.A.4#0", "section": "II.A.4", "title": "Occupancy", "page": 51,
     "text": "Applicants must prove they occupied the home. A utility bill dated within 3 months counts."},
    {"id": "II.C.1#0", "section": "II.C.1", "title": "Timeline for Appeal", "page": 65,
     "text": "Applicants have 60 days from the date of the decision letter to appeal."},
]

HOUSEHOLD = {
    "id": 42, "disasterNumber": 4559, "tier": "unverified_ownership_or_occupancy", "verified_loss": 21244.38,
    "habitabilityRepairsRequired": 1, "ownRent": "R", "factors": "renter, age 65+", "county": "Cameron (Parish)",
    "damagedStateAbbreviation": "LA", "declarationDate": "2020-08-28", "incidentTypeCode": "H",
}


def good_reply(**overrides):
    body = {
        "why_flagged": "FEMA verified $21,244 in damage but could not confirm the renter lived there [P1].",
        "callback_script": "Hello, an inspector confirmed $21,244 in damage. A utility bill can prove you lived "
                           "there [P1]. You can appeal within 60 days of the letter [P2].",
        "citations": ["P1", "P2"],
    }
    body.update(overrides)
    return json.dumps(body)


def test_prompt_contains_facts_and_numbered_passages():
    messages = genai.build_messages(HOUSEHOLD, PASSAGES)
    user = messages[-1]["content"]
    assert "$21,244" in user
    assert "renter" in user
    assert "Hurricane" in user and "2020" in user
    assert "[P1] IAPPG 1.1, Ch. 3 §II.A.4 Occupancy, p. 51" in user
    assert "[P2]" in user
    assert messages[0]["role"] == "system"


def test_valid_reply_maps_citations_to_policy_labels():
    note = genai.parse_reply(good_reply(), HOUSEHOLD, PASSAGES)
    assert note["status"] == "ok"
    assert [c["section"] for c in note["citations"]] == ["II.A.4", "II.C.1"]
    assert note["citations"][0]["label"] == "IAPPG 1.1, Ch. 3 §II.A.4 Occupancy, p. 51"
    assert note["why_flagged"].startswith("FEMA verified")


def test_citation_outside_retrieved_set_is_rejected():
    note = genai.parse_reply(good_reply(citations=["P1", "P7"]), HOUSEHOLD, PASSAGES)
    assert note["status"] == "rejected"
    assert "citation" in note["reason"]


def test_inline_marker_outside_retrieved_set_is_rejected():
    reply = good_reply(callback_script="See section [P9] for details on $21,244.")
    assert genai.parse_reply(reply, HOUSEHOLD, PASSAGES)["status"] == "rejected"


def test_no_citations_rejected():
    reply = good_reply(citations=[], why_flagged="Verified $21,244.", callback_script="Hello, please call FEMA.")
    assert genai.parse_reply(reply, HOUSEHOLD, PASSAGES)["status"] == "rejected"


def test_inline_markers_count_as_citations():
    note = genai.parse_reply(good_reply(citations=[]), HOUSEHOLD, PASSAGES)
    assert note["status"] == "ok"
    assert [c["ref"] for c in note["citations"]] == ["P1", "P2"]


def test_wrong_dollar_amount_rejected():
    reply = good_reply(why_flagged="FEMA verified $50,000 in damage [P1].")
    note = genai.parse_reply(reply, HOUSEHOLD, PASSAGES)
    assert note["status"] == "rejected"
    assert "amount" in note["reason"]


def test_rounded_dollar_amount_accepted():
    reply = good_reply(why_flagged="FEMA verified about $21,000 in damage [P1].")
    assert genai.parse_reply(reply, HOUSEHOLD, PASSAGES)["status"] == "ok"


def test_malformed_json_rejected():
    note = genai.parse_reply("not json at all", HOUSEHOLD, PASSAGES)
    assert note["status"] == "rejected"
    assert "json" in note["reason"]


def test_empty_fields_rejected():
    assert genai.parse_reply(good_reply(callback_script="  "), HOUSEHOLD, PASSAGES)["status"] == "rejected"


def test_promise_of_approval_rejected():
    reply = good_reply(callback_script="You will be approved for $21,244 [P1].")
    assert genai.parse_reply(reply, HOUSEHOLD, PASSAGES)["status"] == "rejected"


def test_done_ids_reads_existing_jsonl(tmp_path):
    path = tmp_path / "notes.jsonl"
    path.write_text(json.dumps({"id": 1, "status": "ok"}) + "\n" + json.dumps({"id": 2, "status": "rejected"}) + "\n")
    assert genai.done_ids(path) == {1, 2}
    assert genai.done_ids(tmp_path / "missing.jsonl") == set()


def test_done_ids_retries_llm_call_failures(tmp_path):
    path = tmp_path / "notes.jsonl"
    rows = [{"id": 1, "status": "ok"}, {"id": 2, "status": "rejected", "reason": "llm call failed: refused"},
            {"id": 3, "status": "rejected", "reason": "no citation"}]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert genai.done_ids(path) == {1, 3}


def test_load_notes_drops_llm_call_failures(tmp_path):
    path = tmp_path / "notes.jsonl"
    path.write_text(json.dumps({"id": 2, "status": "rejected", "reason": "llm call failed: refused"}) + "\n"
                    + json.dumps({"id": 3, "status": "rejected", "reason": "no citation"}) + "\n")
    assert list(genai.load_notes(path)["id"]) == [3]


def test_done_ids_skips_truncated_last_line(tmp_path):
    path = tmp_path / "notes.jsonl"
    path.write_text(json.dumps({"id": 1, "status": "ok"}) + "\n" + '{"id": 2, "sta')
    assert genai.done_ids(path) == {1}


def test_load_notes_keeps_latest_ok_per_id(tmp_path):
    path = tmp_path / "notes.jsonl"
    rows = [{"id": 1, "status": "rejected", "reason": "x"},
            {"id": 1, "status": "ok", "why_flagged": "a", "callback_script": "b", "citations": [], "model": "m",
             "seconds": 1.0, "completion_tokens": 10},
            {"id": 2, "status": "rejected", "reason": "y"}]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    df = genai.load_notes(path)
    assert sorted(df["id"]) == [1, 2]
    assert df.set_index("id").loc[1, "status"] == "ok"
    assert json.loads(df.set_index("id").loc[1, "citations"]) == []


@pytest.mark.parametrize("value,expected", [(21244.38, "$21,244"), (600.0, "$600"), (None, "an unknown amount")])
def test_money(value, expected):
    assert genai.money(value) == expected
