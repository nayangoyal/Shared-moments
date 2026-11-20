"""Two-way matching: cheap filter -> score -> (Gemini judge happens in main.py).

This is basically reconciliation: compare two records and decide if they describe the same thing.
"""
from difflib import SequenceMatcher

from models import MemoryRecord


def _norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def soundex(name: str) -> str:
    """Rough sound-alike code so 'Bunty' ~ 'Bunti', 'Golu' ~ 'Gollu'."""
    name = _norm(name)
    if not name:
        return ""
    codes = {**dict.fromkeys("bfpv", "1"), **dict.fromkeys("cgjkqsxz", "2"),
             **dict.fromkeys("dt", "3"), "l": "4", **dict.fromkeys("mn", "5"), "r": "6"}
    out, prev = name[0], codes.get(name[0], "")
    for ch in name[1:]:
        c = codes.get(ch, "")
        if c and c != prev:
            out += c
        prev = c
    return (out + "000")[:4]


def names_match(xs: list[str], ys: list[str]) -> float:
    best = 0.0
    for x in xs:
        for y in ys:
            if _norm(x) == _norm(y):
                return 1.0
            if soundex(x) == soundex(y):
                best = max(best, 0.85)
            best = max(best, SequenceMatcher(None, _norm(x), _norm(y)).ratio() * 0.8)
    return best


def _overlap(xs: list[str], ys: list[str]) -> float:
    a, b = {_norm(x) for x in xs if x}, {_norm(y) for y in ys if y}
    if not a or not b:
        return 0.0
    hits = sum(1 for x in a for y in b if x in y or y in x)
    return min(1.0, hits / min(len(a), len(b)))


# ---------- Step a: hard filter (time, place, age must not contradict) ----------
def passes_filter(a: MemoryRecord, b: MemoryRecord, year_slack: int = 2, age_slack: int = 3) -> bool:
    if a.year_start and b.year_start:
        a_end, b_end = a.year_end or a.year_start, b.year_end or b.year_start
        if a.year_start - year_slack > b_end or b.year_start - year_slack > a_end:
            return False
    if a.city and b.city and _norm(a.city) != _norm(b.city):
        return False
    # A's guess of friend's age vs B's own age (and the reverse)
    if a.their_age_then and b.my_age_then and abs(a.their_age_then - b.my_age_then) > age_slack:
        return False
    if b.their_age_then and a.my_age_then and abs(b.their_age_then - a.my_age_then) > age_slack:
        return False
    return True


# ---------- Step b: score, checked BOTH ways ----------
def score_pair(a: MemoryRecord, b: MemoryRecord) -> dict:
    a_finds_b = names_match(a.their_nicknames, b.my_nicknames)   # A's memory of B vs B's self
    b_finds_a = names_match(b.their_nicknames, a.my_nicknames)   # B's memory of A vs A's self
    places = _overlap(a.places, b.places)
    inst = _overlap(a.institutions, b.institutions)
    acts = _overlap(a.shared_activities, b.shared_activities)
    people = _overlap(a.other_people, b.other_people)

    score = (0.25 * a_finds_b + 0.25 * b_finds_a + 0.15 * places
             + 0.15 * inst + 0.12 * acts + 0.08 * people)
    return {
        "score": round(score, 3),
        "a_finds_b": round(a_finds_b, 2), "b_finds_a": round(b_finds_a, 2),
        "places": round(places, 2), "institutions": round(inst, 2),
        "activities": round(acts, 2), "people": round(people, 2),
    }


def candidates(new: MemoryRecord, pool: list[MemoryRecord], top_k: int = 3, min_score: float = 0.15):
    out = []
    for other in pool:
        if other.id == new.id or not passes_filter(new, other):
            continue
        s = score_pair(new, other)
        if s["score"] >= min_score:
            out.append((other, s))
    out.sort(key=lambda t: t[1]["score"], reverse=True)
    return out[:top_k]
