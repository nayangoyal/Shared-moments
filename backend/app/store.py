"""Firestore data + the matching engine.

Collections
  users/{uid}            name, age, place, color, about_raw, about (PersonRecord), phone_hash, rev, seed, persona
  requests/{id}          owner, kind ('re'|'nw'), data (what the owner typed, phone masked), rec, phone_hash,
                         embedding (vector), status ('active'|'removed'), created
  matches/{id}           kind, users [a, b], req {uid: request id}, why {uid: [...]}, state {uid: 'new'|'dismissed'|'chatting'},
                         score, judge, created, updated
  matches/{id}/messages  sender, t, at

Privacy: a user only ever receives their own requests, and for a match only the other person's
public card (name, age, place) plus the reasons built from their OWN words.
"""
import hashlib
import logging
import os
import time
import zlib

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector

from . import ai, config
from .ai import MeetRecord, PersonRecord
from .clients import db
from .matching import cosine, fits, score_meet, score_person

log = logging.getLogger("store")

COLORS = ["#c2552d", "#3d6fb6", "#2f7a4f", "#8a5a9e", "#b5832a", "#4f7f86"]
ACTS = ["Walks", "Chai or coffee", "Sunsets", "Board games", "Music", "Cooking", "Cricket", "Photography", "Treks", "Movies"]
_SALT = os.getenv("PHONE_SALT", "shared-moments-demo-salt")


def now() -> float:
    return time.time()


def color_for(uid: str) -> str:
    return COLORS[zlib.crc32(uid.encode()) % len(COLORS)]


def phone_hash(phone: str | None) -> str | None:
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())[-10:]
    return hashlib.sha256((_SALT + digits).encode()).hexdigest() if len(digits) >= 8 else None


def mask_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"{digits[:2]}••• ••{digits[-2:]}" if len(digits) >= 6 else ""


# ---------- users ----------
def users():
    return db().collection("users")


def requests_col():
    return db().collection("requests")


def matches_col():
    return db().collection("matches")


def get_user(uid: str) -> dict:
    snap = users().document(uid).get()
    return snap.to_dict() if snap.exists else {}


def bump(*uids: str) -> None:
    """Tell these users' apps that something changed (cheap polling)."""
    for uid in uids:
        users().document(uid).set({"rev": firestore.Increment(1)}, merge=True)


def public_card(uid: str, u: dict) -> dict:
    return {"n": u.get("name") or "Someone", "a": u.get("age") or "", "place": u.get("place") or "",
            "c": u.get("color") or color_for(uid), "verified": True}


def save_about(uid: str, raw: dict) -> dict:
    raw = {k: str(v).strip()[:300] for k, v in raw.items() if k in
           {"name", "age", "place", "nick", "school", "year", "area"}}
    rec = ai.extract_person({"name": raw.get("name", ""), "nick": raw.get("nick", ""), "school": raw.get("school", ""),
                             "year": raw.get("year", ""), "area": raw.get("area", "")}, "about_me")
    age = "".join(ch for ch in raw.get("age", "") if ch.isdigit())[:3]
    doc = {"name": raw.get("name", ""), "age": int(age) if age else None, "place": raw.get("place", ""),
           "about_raw": raw, "about": rec.model_dump(), "color": color_for(uid), "updated": now()}
    users().document(uid).set(doc, merge=True)
    bump(uid)
    return doc


# ---------- requests ----------
def active_requests(uid: str) -> list[firestore.DocumentSnapshot]:
    snaps = requests_col().where(filter=FieldFilter("owner", "==", uid)).get()
    return [s for s in snaps if s.get("status") == "active"]


def create_request(uid: str, kind: str, data: dict) -> str:
    data = {k: str(v).strip()[:2000] for k, v in data.items() if v is not None and str(v).strip()}
    phone = data.pop("phone", "")
    for k in ("memory", "desc"):
        if k in data:
            data[k] = ai.scrub(data[k])
    if phone:
        data["phone"] = mask_phone(phone)
    ref = requests_col().document()
    ref.set({"owner": uid, "kind": kind, "data": data, "phone_hash": phone_hash(phone),
             "status": "active", "rec": None, "embedding": None, "created": now()})
    bump(uid)
    return ref.id


def remove_request(uid: str, rid: str) -> bool:
    ref = requests_col().document(rid)
    snap = ref.get()
    if not snap.exists or snap.get("owner") != uid:
        return False
    ref.update({"status": "removed", "data": {}, "rec": None, "embedding": None, "phone_hash": None})
    # pending matches made from this request disappear for both people; chats stay
    for m in matches_col().where(filter=FieldFilter("users", "array_contains", uid)).get():
        d = m.to_dict()
        if d["req"].get(uid) == rid and d["state"].get(uid) == "new":
            m.reference.delete()
            bump(*d["users"])
    bump(uid)
    return True


def prepare_request(rid: str) -> dict | None:
    """Gemini: tidy the form into a record and embed the free text."""
    ref = requests_col().document(rid)
    snap = ref.get()
    if not snap.exists or snap.get("status") != "active":
        return None
    r = snap.to_dict()
    d = r["data"]
    if r["kind"] == "re":
        rec = ai.extract_person(d, "looking_for")
        text = " ".join(filter(None, [d.get("memory"), rec.summary, ", ".join(rec.places)]))
    else:
        rec = ai.extract_meet(d, ACTS)
        text = " ".join(filter(None, [d.get("desc"), d.get("acts"), d.get("where")]))
    vec = ai.embed(text)
    ref.update({"rec": rec.model_dump(), "embedding": Vector(vec) if vec else None})
    r.update(rec=rec.model_dump(), embedding=vec, id=rid)
    return r


# ---------- matching ----------
def _existing_pairs(uid: str, kind: str) -> set[str]:
    return {o for m in matches_col().where(filter=FieldFilter("users", "array_contains", uid)).get()
            for o in m.get("users") if m.get("kind") == kind and o != uid}


def _vec(x) -> list[float] | None:
    if x is None:
        return None
    return list(x.to_map_value()["value"]) if hasattr(x, "to_map_value") else list(x)


def run_matching(rid: str) -> int:
    """Find two-way matches for one request. Returns how many matches were created."""
    r = prepare_request(rid)
    if not r:
        return 0
    uid = r["owner"]
    me = get_user(uid)
    taken = _existing_pairs(uid, r["kind"])
    found = _match_reconnect(r, uid, me, taken) if r["kind"] == "re" else _match_meet(r, uid, me, taken)
    t = now()
    for i, c in enumerate(found[:3]):  # best match gets the newest timestamp, so it's listed first
        ref = matches_col().document()
        ref.set({"kind": r["kind"], "users": [uid, c["uid"]], "req": {uid: rid, c["uid"]: c["rid"]},
                 "why": {uid: c["why_me"], c["uid"]: c["why_them"]},
                 "state": {uid: "new", c["uid"]: "new"}, "score": c["score"], "judge": c.get("judge"),
                 "created": t - i * 0.001, "updated": t - i * 0.001})
        bump(uid, c["uid"])
    log.info("request %s (%s): %d match(es)", rid, r["kind"], len(found[:3]))
    return len(found[:3])


def _match_reconnect(r: dict, uid: str, me: dict, taken: set[str]) -> list[dict]:
    if not me.get("about"):
        return []  # mutual matching needs to know how others knew this user
    my_about = PersonRecord(**me["about"])
    looking = PersonRecord(**r["rec"])
    owners: dict[str, dict] = {}
    out = []
    for s in requests_col().where(filter=FieldFilter("kind", "==", "re")).where(filter=FieldFilter("status", "==", "active")).limit(500).get():
        o = s.to_dict()
        other = o["owner"]
        if other == uid or other in taken or not o.get("rec"):
            continue
        if other not in owners:
            owners[other] = get_user(other)
        them = owners[other]
        if not them.get("about") or (me.get("sandbox") and them.get("sandbox")):
            continue  # demo sandboxes (anonymous judges) don't match each other
        p1, why_me = score_person(looking, PersonRecord(**them["about"]), r.get("phone_hash"), them.get("phone_hash"))
        p2, why_them = score_person(PersonRecord(**o["rec"]), my_about, o.get("phone_hash"), me.get("phone_hash"))
        if not (fits(p1, why_me, config.FIELD_THRESHOLD) and fits(p2, why_them, config.FIELD_THRESHOLD)):
            continue
        sim = cosine(r.get("embedding"), _vec(o.get("embedding")))
        out.append({"uid": other, "rid": s.id, "why_me": why_me, "why_them": why_them,
                    "score": round(p1 + p2 + 4 * sim, 2), "o": o, "them": them, "sim": sim})
    out.sort(key=lambda c: c["score"], reverse=True)
    best = {}
    for c in out:  # one match per person
        best.setdefault(c["uid"], c)
    confirmed = []
    for c in list(best.values())[:3]:
        verdict = ai.judge(looking, PersonRecord(**c["them"]["about"]), PersonRecord(**c["o"]["rec"]), my_about,
                           r["data"].get("memory", ""), c["o"]["data"].get("memory", ""))
        if verdict is not None:
            c["judge"] = verdict.model_dump()
            if verdict.probability < config.JUDGE_MIN_PROBABILITY:
                log.info("judge vetoed %s (p=%.2f)", c["uid"], verdict.probability)
                continue
        if c["sim"] >= 0.75 and "memory" not in c["why_me"]:
            c["why_me"] = c["why_me"] + ["memory"]
            c["why_them"] = c["why_them"] + ["memory"]
        confirmed.append({k: c[k] for k in ("uid", "rid", "why_me", "why_them", "score")} | {"judge": c.get("judge")})
    return confirmed


def _match_meet(r: dict, uid: str, me: dict, taken: set[str]) -> list[dict]:
    mine = MeetRecord(**r["rec"])
    owners: dict[str, dict] = {}
    q = requests_col().where(filter=FieldFilter("kind", "==", "nw")).where(filter=FieldFilter("status", "==", "active"))
    if r.get("embedding"):
        try:  # Firestore vector search: nearest descriptions first
            snaps = q.find_nearest(vector_field="embedding", query_vector=Vector(r["embedding"]),
                                   distance_measure=DistanceMeasure.COSINE, limit=50).get()
        except Exception as e:  # noqa: BLE001  (index still building, etc.)
            log.warning("vector search unavailable, scanning: %s", e)
            snaps = q.limit(500).get()
    else:
        snaps = q.limit(500).get()
    best: dict[str, dict] = {}
    for s in snaps:
        o = s.to_dict()
        other = o["owner"]
        if other == uid or other in taken or not o.get("rec"):
            continue
        if me.get("sandbox"):
            if other not in owners:
                owners[other] = get_user(other)
            if owners[other].get("sandbox"):
                continue  # demo sandboxes (anonymous judges) don't match each other
        theirs = MeetRecord(**o["rec"])
        why_me, why_them = score_meet(mine, theirs), score_meet(theirs, mine)
        if not why_me:
            continue
        sim = cosine(r.get("embedding"), _vec(o.get("embedding")))
        c = {"uid": other, "rid": s.id, "why_me": why_me, "why_them": why_them, "score": round(len(why_me) + 2 * sim, 2)}
        if other not in best or c["score"] > best[other]["score"]:
            best[other] = c
    return sorted(best.values(), key=lambda c: c["score"], reverse=True)


# ---------- matches and messages ----------
def get_match(uid: str, mid: str):
    snap = matches_col().document(mid).get()
    if not snap.exists or uid not in snap.get("users"):
        return None, None
    return snap.reference, snap.to_dict()


def dismiss(uid: str, mid: str) -> bool:
    ref, m = get_match(uid, mid)
    if not m:
        return False
    ref.update({f"state.`{uid}`": "dismissed", "updated": now()})
    bump(uid)
    return True


def add_message(uid: str, mid: str, text: str) -> dict | None:
    ref, m = get_match(uid, mid)
    if not m or m["state"].get(uid) == "dismissed":
        return None
    ref.collection("messages").add({"sender": uid, "t": text, "at": now()})
    ref.update({**{f"state.`{u}`": "chatting" for u in m["users"]}, "updated": now()})
    bump(*m["users"])
    return m


def messages(ref, uid: str) -> list[dict]:
    return [{"me": d.get("sender") == uid, "t": d.get("t", "")}
            for d in (s.to_dict() for s in ref.collection("messages").order_by("at").get())]


# ---------- the whole app state for one user (the frontend's store shape) ----------
def state(uid: str) -> dict:
    me = get_user(uid)
    out = {"rev": me.get("rev", 0), "me": {"hasAbout": bool(me.get("about")), "about": me.get("about_raw") or {}},
           "re": {"reqs": [], "moments": [], "chats": []}, "nw": {"reqs": [], "moments": [], "chats": []},
           "msgs": {}, "people": {}}
    reqs = sorted(active_requests(uid), key=lambda s: s.get("created"), reverse=True)
    for s in reqs:
        out[s.get("kind")]["reqs"].append({"id": s.id, "data": s.get("data")})
    ms = sorted((m for m in matches_col().where(filter=FieldFilter("users", "array_contains", uid)).get()),
                key=lambda m: m.get("updated"), reverse=True)
    for m in ms:
        d = m.to_dict()
        st = d["state"].get(uid)
        if st == "dismissed":
            continue
        other = next(u for u in d["users"] if u != uid)
        if other not in out["people"]:
            out["people"][other] = public_card(other, get_user(other))
        box = out[d["kind"]]
        if st == "new":
            box["moments"].append({"id": m.id, "pid": other, "req": d["req"].get(uid), "why": d["why"].get(uid, [])})
        else:
            box["chats"].append({"id": m.id, "pid": other})
            out["msgs"][m.id] = messages(m.reference, uid)
    return out


def wipe(uid: str) -> None:
    """Delete everything a user owns (used by the demo 'try it as' buttons)."""
    for s in requests_col().where(filter=FieldFilter("owner", "==", uid)).get():
        s.reference.delete()
    for m in matches_col().where(filter=FieldFilter("users", "array_contains", uid)).get():
        for msg in m.reference.collection("messages").get():
            msg.reference.delete()
        others = [u for u in m.get("users") if u != uid]
        m.reference.delete()
        bump(*others)
