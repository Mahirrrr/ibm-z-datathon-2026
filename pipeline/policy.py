"""FEMA policy corpus for the generative layer: IAPPG 1.1 chunks plus a TF-IDF retriever.

Source: FEMA Individual Assistance Program and Policy Guide (IAPPG) v1.1, May 2021,
https://www.fema.gov/sites/default/files/documents/fema_iappg-1.1.pdf (a U.S. government work).
We use Chapter 3, sections II (IHP eligibility, verification, appeals) and III (applying,
verifying losses, applicant communication).

    pdftotext data/policy/iappg-1.1.pdf data/policy/iappg-1.1.txt
    python -m pipeline.policy          # writes docs/data/iappg_chunks.json
"""

import json
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from pipeline.config import POLICY_CHUNKS, POLICY_TEXT

SOURCE = "IAPPG 1.1"
START = "II. Individuals and Households Program Eligibility"
STOP = "A. Lodging Expense Reimbursement"  # first heading of Section IV, Housing Assistance
FIRST_PAGE = 46  # printed page number of START in the PDF
MAX_CHARS = 1100

HEADING = re.compile(r"^(?:(?P<roman>II|III)|(?P<letter>[A-H])|(?P<number>\d{1,2}))\.\s+(?P<title>[A-Z].{2,80})$")
FOOTER = re.compile(r"^\d{2,3}$")
RUNNING_HEADER = "Chapter 3: Individuals and Households Program"
# Inline footnote markers ("determinations 81 within"), but not quantities ("within 60 days").
FOOTNOTE = re.compile(r"(?<=[A-Za-z.,;:)”])\s\d{2,3}(?=\s|$)(?!\s+(?:days?|months?|years?|hours?|percent|calendar|business|or|to|and)\b)")

# Sections each denial tier may cite. Pinned so grounding is auditable, not left to retrieval.
TIER_SECTIONS = {
    "missing_documents": {
        "O": ["II.A.2", "II.A.3", "II.A.4", "II.A.5", "III.B.3"],
        "R": ["II.A.2", "II.A.3", "II.A.4", "III.B.3"],
    },
    "unverified_ownership_or_occupancy": {
        "O": ["II.A.4", "II.A.5"],
        "R": ["II.A.4"],
    },
    "lost_contact": {
        "O": ["III.C"],
        "R": ["III.C"],
    },
}
APPEAL_SECTIONS = ["II.C"]

TIER_QUERIES = {
    "missing_documents": "submit missing documents verify identity insurance settlement occupancy ownership proof",
    "unverified_ownership_or_occupancy": "verify occupancy ownership documents utility bill lease deed declarative statement",
    "lost_contact": "contact applicant phone letters communication unable to reach",
}
APPEAL_QUERY = "appeal within 60 days decision letter submit documents"


def label(chunk):
    return f"{SOURCE}, Ch. 3 §{chunk['section']} {chunk['title']}, p. {chunk['page']}"


def _split(text):
    """Split a section into passages of at most MAX_CHARS, on sentence boundaries."""
    passages, current = [], ""
    for sentence in re.split(r"(?<=[.;:])\s+", text):
        while len(sentence) > MAX_CHARS:
            passages.append(sentence[:MAX_CHARS])
            sentence = sentence[MAX_CHARS:]
        if current and len(current) + 1 + len(sentence) > MAX_CHARS:
            passages.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        passages.append(current)
    return passages


def build_chunks(lines, first_page=FIRST_PAGE):
    """Turn pdftotext lines into section passages with a citable section id, title and page."""
    started = False
    page = first_page
    path = {}  # level -> (key, title)
    sections = []  # [section, title, page, [lines]]
    for raw in lines:
        line = raw.replace("\f", "").strip()
        if not started:
            started = line == START
            if not started:
                continue
        if line == STOP:
            break
        if FOOTER.match(line):
            page += 1
            continue
        if not line or line == RUNNING_HEADER:
            continue
        m = HEADING.match(line)
        if m:
            level = 0 if m["roman"] else 1 if m["letter"] else 2
            key = m["roman"] or m["letter"] or m["number"]
            path = {k: v for k, v in path.items() if k < level}
            path[level] = key
            section = ".".join(path[k] for k in sorted(path))
            sections.append([section, m["title"].strip(), page, []])
            continue
        if sections:
            sections[-1][3].append(line)

    chunks = []
    for section, title, pg, body in sections:
        text = FOOTNOTE.sub("", re.sub(r"\s+", " ", " ".join(body))).strip()
        for i, passage in enumerate(_split(text)):
            chunks.append({"id": f"{section}#{i}", "section": section, "title": title, "page": pg, "text": passage})
    return chunks


def _in(section, prefixes):
    return any(section == p or section.startswith(p + ".") for p in prefixes)


class PolicyIndex:
    """TF-IDF vector index over policy passages, restricted per denial tier."""

    def __init__(self, chunks):
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(stop_words="english", sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform([f"{c['title']} {c['text']}" for c in chunks])

    def _top(self, query, prefixes, k):
        allowed = [i for i, c in enumerate(self.chunks) if _in(c["section"], prefixes)]
        if not allowed:
            return []
        scores = linear_kernel(self.vectorizer.transform([query]), self.matrix[allowed]).ravel()
        order = sorted(range(len(allowed)), key=lambda j: -scores[j])[:k]
        return [self.chunks[allowed[j]] for j in order]

    def retrieve(self, tier, own_rent, k=2):
        sections = TIER_SECTIONS[tier]["R" if own_rent == "R" else "O"]
        query = TIER_QUERIES[tier] + (" renter lease" if own_rent == "R" else " owner deed")
        hits = []
        # One passage per section first so each allowed rule gets a chance, then fill by score.
        for chunk in self._top(query, sections, k=len(self.chunks)):
            if len(hits) < k and all(h["section"] != chunk["section"] for h in hits):
                hits.append(chunk)
        return hits + self._top(APPEAL_QUERY, APPEAL_SECTIONS, k=1)


def load_index(path=POLICY_CHUNKS):
    return PolicyIndex(json.loads(path.read_text()))


def main():
    chunks = build_chunks(POLICY_TEXT.read_text().splitlines())
    POLICY_CHUNKS.write_text(json.dumps(chunks, indent=1))
    print(f"wrote {POLICY_CHUNKS}: {len(chunks)} passages from {len({c['section'] for c in chunks})} sections")


if __name__ == "__main__":
    main()
