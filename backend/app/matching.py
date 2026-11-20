"""Pure matching rules (no I/O), so they can be unit-tested.

Reconnect is MUTUAL: A's request must fit how B says others knew them, AND B's request must fit A.
Meet New: both want overlapping activities in the same city.
"""
import math
import re

from .ai import MeetRecord, PersonRecord

WEIGHTS = {"name": 3, "nickname": 3, "phone": 5, "school": 2, "area": 2, "year": 1}
_GENERIC = {"school", "college", "high", "the", "of", "and", "st", "public", "convent", "academy",
            "west", "east", "north", "south", "road", "nagar", "colony", "sector", "near", "city"}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).strip()


def tokens(xs: list[str], min_len: int = 2) -> set[str]:
    return {t for x in xs for t in norm(x).split() if len(t) >= min_len}


def soundex(name: str) -> str:
    """Rough sound-alike code so 'Bunty' ~ 'Bunti', 'Chintu' ~ 'Chintoo'."""
    s = re.sub(r"[^a-z]", "", (name or "").lower())
    if not s:
        return ""
    codes = {**dict.fromkeys("bfpv", "1"), **dict.fromkeys("cgjkqsxz", "2"), **dict.fromkeys("dt", "3"),
             "l": "4", **dict.fromkeys("mn", "5"), "r": "6"}
    out, prev = s[0], codes.get(s[0], "")
    for ch in s[1:]:
        c = codes.get(ch, "")
        if c and c != prev:
            out += c
        if ch not in "hw":
            prev = c
    return (out + "000")[:4]


def _nick_match(xs: list[str], ys: list[str]) -> bool:
    a = {norm(x) for x in xs if norm(x)}
    b = {norm(y) for y in ys if norm(y)}
    if a & b:
        return True
    return bool({soundex(x) for x in a} & {soundex(y) for y in b} - {""})


def _school_match(xs: list[str], ys: list[str]) -> bool:
    a = [tokens([x]) - _GENERIC for x in xs]
    b = [tokens([y]) - _GENERIC for y in ys]
    return any(x and y and (x <= y or y <= x) for x in a for y in b)


def _year_match(a: PersonRecord, b: PersonRecord, slack: int = 1) -> bool:
    if not a.year_from or not b.year_from:
        return False
    a1, b1 = a.year_to or a.year_from, b.year_to or b.year_from
    return a.year_from - slack <= b1 and b.year_from - slack <= a1


def _area_match(a: PersonRecord, b: PersonRecord) -> bool:
    ta = tokens(a.places, 3) - _GENERIC
    tb = tokens(b.places, 3) - _GENERIC
    return bool(ta & tb)


def score_person(looking: PersonRecord, about: PersonRecord,
                 looking_phone: str | None = None, about_phone: str | None = None) -> tuple[int, list[str]]:
    """How well a 'looking for' description fits a person's 'about me'. Returns (points, reasons).

    Reasons are field names from the LOOKING side, so the searcher only ever sees their own words.
    """
    why = []
    if tokens(looking.names) & tokens(about.names):
        why.append("name")
    if _nick_match(looking.nicknames, about.nicknames) or _nick_match(looking.nicknames, about.names):
        why.append("nickname")
    if looking_phone and about_phone and looking_phone == about_phone:
        why.append("phone")
    if _school_match(looking.schools, about.schools):
        why.append("school")
    if _year_match(looking, about):
        why.append("year")
    if _area_match(looking, about):
        why.append("area")
    return sum(WEIGHTS[w] for w in why), why


IDENTITY = {"name", "nickname", "phone"}


def fits(points: int, why: list[str], threshold: int) -> bool:
    """A direction counts only with enough points AND at least one identity detail.

    Same school + year + area alone is too weak: two classmates looking for the same third friend
    would otherwise match each other.
    """
    return points >= threshold and bool(IDENTITY & set(why))


def city_match(a: MeetRecord, b: MeetRecord) -> bool:
    ca, cb = norm(a.city or ""), norm(b.city or "")
    if ca and cb and ca == cb:
        return True
    if tokens(a.areas, 3) & tokens(b.areas, 3):
        return True
    return not ca or not cb  # unknown city: don't block on it


def score_meet(a: MeetRecord, b: MeetRecord) -> list[str]:
    """Shared activities (in A's own words), or [] if they don't fit."""
    if not city_match(a, b):
        return []
    theirs = {x.lower() for x in b.activities}
    return [x for x in a.activities if x.lower() in theirs]


def cosine(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
