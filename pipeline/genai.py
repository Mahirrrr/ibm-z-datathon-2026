"""Generative layer: IBM Granite writes a cited "why flagged" note and callback script per household.

Predictive + generative, like IBM's loan-approval lab run in reverse: the lab explains why a bank
approved or denied a loan; we explain why a household FEMA denied deserves a second look.

  1. Retrieve FEMA policy passages (IAPPG 1.1) for the household's denial tier (pipeline/policy.py).
  2. Ask Granite, served locally by llama.cpp on LinuxONE, for JSON: note, script, citations.
  3. Check the reply: every citation must be a retrieved passage, dollar amounts must match the
     verified loss, and the script must not promise approval. Anything else is rejected and the
     dashboard falls back to the template script.

Run on the VM with llama-server listening on 127.0.0.1:8081:
    python -m pipeline.genai --disasters 12 --per-disaster 8
Output is appended to data/processed/callback_notes.jsonl (resumable); pipeline.store loads it.
"""

import argparse
import json
import re
import time
import urllib.request

import pandas as pd

from pipeline import frames, policy
from pipeline.codebook import INCIDENT_NAMES, TIER_LABELS
from pipeline.config import CALLBACKS, LLM_URL, NOTES

MODEL_NAME = "IBM Granite 3.3 2B Instruct (Q4_0, big-endian GGUF) on llama.cpp"
MAX_TOKENS = 320
AMOUNT_TOLERANCE = 0.05  # "about $21,000" for $21,244 is fine; "$50,000" is not

SYSTEM = (
    "You help caseworkers at a local disaster-recovery nonprofit (not FEMA) call back households that FEMA "
    "denied even though an inspector verified their damage. Use only the FEMA policy passages you are given "
    "and cite them inline as [P1], [P2]. Write in plain language a stressed survivor can follow. Never promise "
    "that the household will be approved or receive money. Never invent dollar amounts, deadlines, or rules."
)

TIER_PLAIN = {
    "missing_documents": "FEMA denied the application because a required document was missing",
    "lost_contact": "FEMA denied the application after it could not reach the household or the household did not respond",
    "unverified_ownership_or_occupancy": "FEMA denied the application because it never verified that the household owned or lived in the home",
}

REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "why_flagged": {"type": "string"},
        "callback_script": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string", "pattern": "^P[0-9]+$"}},
    },
    "required": ["why_flagged", "callback_script", "citations"],
}

MARKER = re.compile(r"\[P(\d+)\]")
AMOUNT = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)")
PROMISE = re.compile(r"\b(guarantee\w*|will (?:be )?(?:approved|receive|get)|you(?:'ll| will) (?:be )?(?:approved|receive|get))\b",
                     re.IGNORECASE)


def money(value):
    if value is None or pd.isna(value):
        return "an unknown amount"
    return f"${value:,.0f}"


def facts(h):
    year = str(h.get("declarationDate") or "")[:4]
    incident = INCIDENT_NAMES.get(str(h.get("incidentTypeCode")), "disaster")
    lines = [
        f"Disaster: {incident} #{h['disasterNumber']}, {h.get('damagedStateAbbreviation')}, declared {year}",
        f"County: {h.get('county') or 'unknown'}",
        f"Inspector-verified damage: {money(h.get('verified_loss'))}",
        f"Housing: {'renter' if h.get('ownRent') == 'R' else 'owner'}",
        f"Home needs repairs to be livable: {'yes' if h.get('habitabilityRepairsRequired') == 1 else 'no'}",
        f"Denial: {TIER_PLAIN[h['tier']]} ({TIER_LABELS[h['tier']]})",
        f"Vulnerability factors: {h.get('factors') or 'none recorded'} (these do not change FEMA's rules; "
        "they are why the caseworker calls this household early)",
        "Not in the public data: which exact document FEMA wanted, and the date of FEMA's letter. "
        "Ask the household; do not guess.",
    ]
    return "\n".join(lines)


def build_messages(h, passages):
    numbered = "\n\n".join(f"[P{i}] {policy.label(p)}\n{p['text']}" for i, p in enumerate(passages, 1))
    user = (
        f"Household (from FEMA's public records, no names):\n{facts(h)}\n\n"
        f"FEMA policy passages:\n{numbered}\n\n"
        "Return JSON with three fields:\n"
        "- why_flagged: two sentences for the caseworker on why this denial looks fixable, citing passages.\n"
        "- callback_script: under 90 words the caseworker reads on the phone. Say what was verified, what "
        "FEMA still needs, which documents could help, and the appeal rule if a passage gives one. Cite passages "
        "inline as [P1].\n"
        "- citations: the passage ids you used, like [\"P1\"]."
    )
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def _reject(reason, raw=None):
    return {"status": "rejected", "reason": reason, "raw": raw}


def parse_reply(text, h, passages):
    """Validate Granite's JSON reply. Returns a note dict with status 'ok' or 'rejected'."""
    try:
        body = json.loads(text)
        why, script, cited = body["why_flagged"].strip(), body["callback_script"].strip(), list(body["citations"])
    except (ValueError, KeyError, TypeError, AttributeError):
        return _reject("reply is not valid json in the requested shape", text)
    if not why or not script:
        return _reject("empty note or script", text)

    refs = list(dict.fromkeys([str(c).strip("[] ") for c in cited] + [f"P{n}" for n in MARKER.findall(why + script)]))
    valid = {f"P{i}" for i in range(1, len(passages) + 1)}
    if not refs:
        return _reject("no citation", text)
    if not set(refs) <= valid:
        return _reject(f"citation outside retrieved passages: {sorted(set(refs) - valid)}", text)

    loss = h.get("verified_loss")
    for amount in AMOUNT.findall(why + " " + script):
        value = float(amount.replace(",", ""))
        if loss is None or abs(value - loss) > AMOUNT_TOLERANCE * loss:
            return _reject(f"dollar amount ${amount} does not match verified loss {money(loss)}", text)
    if PROMISE.search(why + " " + script):
        return _reject("promises an outcome", text)

    citations = []
    for ref in refs:
        p = passages[int(ref[1:]) - 1]
        citations.append({"ref": ref, "section": p["section"], "title": p["title"], "page": p["page"],
                          "label": policy.label(p), "quote": p["text"][:400]})
    return {"status": "ok", "why_flagged": why, "callback_script": script, "citations": citations}


def ask_granite(messages, url=LLM_URL, timeout=600):
    payload = {
        "messages": messages, "temperature": 0.2, "max_tokens": MAX_TOKENS,
        "response_format": {"type": "json_object", "schema": REPLY_SCHEMA},
    }
    req = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        body = json.loads(res.read())
    return body["choices"][0]["message"]["content"], body.get("usage", {}), body.get("timings", {})


LLM_FAILURE = "llm call failed"


def _results(path):
    """Parsed lines, minus transport failures (server down), which say nothing about Granite."""
    rows = []
    for line in path.read_text().splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue  # a run killed mid-write leaves a partial last line
        if "id" in row and not str(row.get("reason") or "").startswith(LLM_FAILURE):
            rows.append(row)
    return rows


def done_ids(path=NOTES):
    return {r["id"] for r in _results(path)} if path.exists() else set()


def load_notes(path=NOTES):
    """Latest result per household, with an 'ok' note preferred over a rejection."""
    df = pd.DataFrame(_results(path))
    df["ok"] = df["status"] == "ok"
    df = df.reset_index().sort_values(["ok", "index"]).drop_duplicates("id", keep="last")
    df["citations"] = df.get("citations", pd.Series(index=df.index, dtype=object)).apply(
        lambda c: json.dumps(c if isinstance(c, list) else []))
    keep = ["id", "status", "reason", "why_flagged", "callback_script", "citations", "model", "seconds",
            "prompt_tokens", "completion_tokens"]
    return df.reindex(columns=keep).sort_values("id").reset_index(drop=True)


def select_households(n_disasters, per_disaster):
    cb = frames.read(CALLBACKS)
    top = cb["disasterNumber"].value_counts().head(n_disasters).index
    picked = cb[cb["disasterNumber"].isin(top) & (cb["rank_in_disaster"] <= per_disaster)]
    order = {d: i for i, d in enumerate(top)}
    return picked.assign(_o=picked["disasterNumber"].map(order)).sort_values(["rank_in_disaster", "_o"]).drop(columns="_o")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--disasters", type=int, default=12)
    ap.add_argument("--per-disaster", type=int, default=8)
    ap.add_argument("--url", default=LLM_URL)
    args = ap.parse_args()

    index = policy.load_index()
    done = done_ids()
    todo = [h for h in select_households(args.disasters, args.per_disaster).to_dict("records") if h["id"] not in done]
    print(f"{len(todo)} households to write ({len(done)} already done)", flush=True)
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    for i, h in enumerate(todo, 1):
        passages = index.retrieve(h["tier"], h["ownRent"])
        start = time.perf_counter()
        try:
            text, usage, timings = ask_granite(build_messages(h, passages), args.url)
            note = parse_reply(text, h, passages)
        except OSError as e:
            note, usage, timings = _reject(f"{LLM_FAILURE}: {e}"), {}, {}
        note.update(id=h["id"], disasterNumber=h["disasterNumber"], model=MODEL_NAME,
                    seconds=round(time.perf_counter() - start, 1),
                    prompt_tokens=usage.get("prompt_tokens"), completion_tokens=usage.get("completion_tokens"),
                    tokens_per_second=timings.get("predicted_per_second"))
        with NOTES.open("a") as f:
            f.write(json.dumps(note) + "\n")
        print(f"[{i}/{len(todo)}] {h['disasterNumber']} rank {h['rank_in_disaster']}: {note['status']} "
              f"{note['seconds']}s {note.get('reason') or ''}", flush=True)


if __name__ == "__main__":
    main()
