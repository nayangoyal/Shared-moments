"""Demo people and the 'returning user' starting state.

Each demo person has a hidden About me and their own private requests, so matching is genuinely
two-way: e.g. Aarav is looking for "Golu from St. Stanislaus, 2014", which is the demo persona.
"""
import logging
import threading

from google.cloud.firestore_v1.vector import Vector

from . import ai
from .ai import MeetRecord, PersonRecord
from .clients import db
from .store import bump, matches_col, now, phone_hash, requests_col, users, wipe

log = logging.getLogger("seed")
SEED_VERSION = 3

C = ["#c2552d", "#3d6fb6", "#2f7a4f", "#8a5a9e", "#b5832a", "#4f7f86"]

# The person a judge "is" when they tap Fill an example on About me (and the returning user)
DEMO_ABOUT = {"name": "Rahul Sharma", "age": "24", "place": "Bandra, Mumbai", "nick": "Golu",
              "school": "St. Stanislaus School", "year": "2014", "area": "Pali Hill, Bandra; Kurla West"}
DEMO_ABOUT_REC = PersonRecord(names=["Rahul Sharma", "Rahul"], nicknames=["Golu", "Gollu"],
                              schools=["St. Stanislaus School"], year_from=2013, year_to=2015,
                              places=["Pali Hill", "Bandra", "Kurla West"], city="Mumbai",
                              summary="Grew up in Kurla West, then Pali Hill; St. Stanislaus School, class of 2014.")

OLD = [  # old friends (Reconnect)
    dict(id="seed-aarav", name="Aarav Mehta", age=24, place="Mumbai", color=C[1], phone="9820144120",
         about=PersonRecord(names=["Aarav Mehta", "Aarav"], nicknames=["Chintu", "Chintoo"], schools=["St. Stanislaus School"],
                            year_from=2008, year_to=2014, places=["Pali Hill", "Bandra"], city="Mumbai"),
         background="Grew up in Pali Hill, Bandra. St. Stanislaus School till 2014, everyone called you Chintu. Played gully cricket behind the chapel every recess. Moved to Andheri after 10th, now works in fintech.",
         looking=dict(data={"name": "Rahul", "nick": "Golu", "how": "Classmate", "school": "St. Stanislaus", "year": "2014", "area": "Pali Hill",
                            "memory": "Golu and I sat on the last bench in 7th standard and played gully cricket behind the chapel every recess. Lost touch after 10th."},
                      rec=PersonRecord(names=["Rahul"], nicknames=["Golu", "Gollu"], schools=["St. Stanislaus School"],
                                       year_from=2013, year_to=2014, places=["Pali Hill", "Bandra"], city="Mumbai"))),
    dict(id="seed-farah", name="Farah Sheikh", age=24, place="Thane", color=C[4], phone="9867022314",
         about=PersonRecord(names=["Farah Sheikh", "Farah"], nicknames=["Fizz"], schools=["St. Stanislaus School"],
                            year_from=2010, year_to=2014, places=["Bandra West"], city="Mumbai"),
         background="Went to St. Stanislaus School, friends called you Fizz. Shared tiffin on the school bus home. Lives in Thane now, teaches maths.",
         looking=dict(data={"name": "Tanya", "how": "Neighbour", "area": "Bandra West", "year": "2012",
                            "memory": "Tanya lived in the next building and we cycled around Carter Road every evening."},
                      rec=PersonRecord(names=["Tanya"], year_from=2011, year_to=2013, places=["Bandra West", "Carter Road"], city="Mumbai"))),
    dict(id="seed-zoya", name="Zoya Khan", age=23, place="Mumbai", color=C[3], phone="9930018877",
         about=PersonRecord(names=["Zoya Khan", "Zoya"], schools=["Holy Cross School"], year_from=2012, year_to=2015,
                            places=["Kurla West"], city="Mumbai"),
         background="Grew up in Building 4, Kurla West. Holy Cross School. Loves old Hindi film songs. Works as a nurse now.",
         looking=dict(data={"name": "Rahul", "how": "Neighbour", "area": "Kurla West", "year": "2015",
                            "memory": "Rahul lived in our building in Kurla West. We listened to old songs on the terrace."},
                      rec=PersonRecord(names=["Rahul"], year_from=2014, year_to=2015, places=["Kurla West"], city="Mumbai"))),
    dict(id="seed-meena", name="Meena Iyer", age=58, place="Chembur", color=C[5], phone="9820066710",
         about=PersonRecord(names=["Meena Iyer", "Meena"], nicknames=["Meenu"], schools=["SIES College"],
                            year_from=1984, year_to=1987, places=["Matunga"], city="Mumbai"),
         background="SIES College, Matunga, 1987. Friends called you Meenu. Loves filter coffee and Carnatic music. Retired teacher in Chembur.",
         looking=dict(data={"name": "Lakshmi", "school": "SIES College", "year": "1987", "area": "Matunga",
                            "memory": "Lakshmi and I had filter coffee on the Matunga terrace after college every day."},
                      rec=PersonRecord(names=["Lakshmi"], schools=["SIES College"], year_from=1986, year_to=1987, places=["Matunga"], city="Mumbai"))),
]

NEW = [  # new people nearby (Meet New)
    dict(id="seed-ishaan", name="Ishaan", age=23, place="Bandra · 1 km", color=C[0], acts=["Walks", "Chai or coffee", "Sunsets"],
         background="Moved to Bandra last year for a design job. Walks at Carter Road around 7 pm, loves cutting chai.",
         desc="Evening walks on Carter Road around 7, then a cutting chai. New in Bandra and looking for walking buddies."),
    dict(id="seed-sunita", name="Sunita", age=52, place="Santacruz · 3 km", color=C[4], acts=["Walks", "Cooking", "Music"],
         background="Homemaker in Santacruz, loves old Hindi songs and cooking Gujarati food. Walks every morning.",
         desc="A morning walk buddy who loves old Hindi songs. I also love cooking and would happily swap recipes."),
    dict(id="seed-meher", name="Meher", age=22, place="Khar · 2 km", color=C[3], acts=["Board games", "Chai or coffee", "Movies"],
         background="College student in Khar. Carrom champion of her building, loves card games and movies.",
         desc="Board games and carrom on weekends, chai, and a movie now and then. Teach me a card game and I'll teach you carrom."),
    dict(id="seed-desai", name="Mr. Desai", age=67, place="Bandra · 1 km", color=C[5], acts=["Walks", "Photography", "Chai or coffee"],
         background="Retired architect, has lived in Bandra for 60 years. Photographs old bungalows and leads a Sunday heritage walk.",
         desc="Sunday morning heritage walks around old Bandra bungalows with my camera, and chai after. All ages welcome."),
    dict(id="seed-rohan", name="Rohan", age=24, place="Juhu · 4 km", color=C[2], acts=["Cricket", "Treks", "Sunsets"],
         background="Software engineer in Juhu. Plays Sunday cricket on Juhu beach, treks in the monsoon.",
         desc="Sunday cricket on Juhu beach, then sunsets. Monsoon treks to Sahyadri forts with a small group."),
    dict(id="seed-dev", name="Dev", age=26, place="Mahim · 3 km", color=C[1], acts=["Music", "Sunsets", "Movies"],
         background="Plays guitar and tabla, goes to open mics in Bandra on Fridays. Works in advertising.",
         desc="Jamming on guitar, open mic nights on Fridays, and sitting by the sea at sunset with old songs."),
]

PERSONAS = {p["id"]: p for p in OLD + NEW}

_lock = threading.Lock()
_done = False


def ensure_seeded() -> None:
    """Create or refresh the demo people once per SEED_VERSION (safe to call often)."""
    global _done
    if _done:
        return
    with _lock:
        if _done:
            return
        meta = db().collection("meta").document("seed")
        snap = meta.get()
        if snap.exists and snap.get("version") == SEED_VERSION:
            _done = True
            return
        log.info("seeding demo people (v%s)", SEED_VERSION)
        for p in OLD:
            users().document(p["id"]).set({
                "name": p["name"], "age": p["age"], "place": p["place"], "color": p["color"], "seed": True,
                "about": p["about"].model_dump(), "phone_hash": phone_hash(p["phone"]),
                "persona": {"background": p["background"]}, "rev": 0})
            vec = ai.embed(p["looking"]["data"]["memory"])
            requests_col().document(p["id"] + "-re").set({
                "owner": p["id"], "kind": "re", "data": p["looking"]["data"], "rec": p["looking"]["rec"].model_dump(),
                "phone_hash": None, "embedding": Vector(vec) if vec else None, "status": "active", "created": now()})
        for p in NEW:
            users().document(p["id"]).set({
                "name": p["name"], "age": p["age"], "place": p["place"], "color": p["color"], "seed": True,
                "persona": {"background": p["background"]}, "rev": 0})
            vec = ai.embed(p["desc"] + " " + ", ".join(p["acts"]))
            requests_col().document(p["id"] + "-nw").set({
                "owner": p["id"], "kind": "nw", "data": {"acts": ", ".join(p["acts"]), "where": "Mumbai", "desc": p["desc"]},
                "rec": MeetRecord(activities=p["acts"], city="Mumbai", areas=[p["place"].split(" ·")[0]], summary=p["desc"]).model_dump(),
                "phone_hash": None, "embedding": Vector(vec) if vec else None, "status": "active", "created": now()})
        meta.set({"version": SEED_VERSION, "at": now()})
        _done = True


def reset_user(uid: str, persona: str) -> None:
    """'A new user' = empty. 'A returning user' = the same starting state the demo always had."""
    ensure_seeded()
    wipe(uid)
    if persona == "new":
        # merge keeps 'rev' increasing and the 'sandbox' flag; None clears a field
        users().document(uid).set({"name": "", "age": None, "place": "", "about": None, "about_raw": None,
                                   "phone_hash": None, "color": C[0], "updated": now()}, merge=True)
        bump(uid)
        return

    users().document(uid).set({"name": DEMO_ABOUT["name"], "age": 24, "place": DEMO_ABOUT["place"], "about_raw": DEMO_ABOUT,
                               "about": DEMO_ABOUT_REC.model_dump(), "phone_hash": None, "color": C[0], "updated": now()}, merge=True)
    t = now()

    def req(rid, kind, data, rec):
        requests_col().document(rid).set({"owner": uid, "kind": kind, "data": data, "rec": rec.model_dump(),
                                          "phone_hash": None, "embedding": None, "status": "active", "created": t})
        return rid

    r1 = req(f"{uid}-r1", "re", {"name": "Sonu", "how": "Classmate", "school": "Fergusson College", "year": "2017", "area": "Kothrud, Pune",
                                 "memory": "We cycled to Sinhagad every Sunday at 5 am in second year and shared vada pav at the top. He moved to Bangalore after college and we lost touch."},
             PersonRecord(names=["Sonu"], schools=["Fergusson College"], year_from=2016, year_to=2017, places=["Kothrud"], city="Pune"))
    r2 = req(f"{uid}-r2", "re", {"name": "Aarav", "nick": "Chintu", "how": "Classmate", "school": "St. Stanislaus", "year": "2014", "area": "Pali Hill",
                                 "memory": "We sat on the last bench in 7th standard and played gully cricket behind the chapel every recess."},
             PersonRecord(names=["Aarav"], nicknames=["Chintu"], schools=["St. Stanislaus School"], year_from=2014, year_to=2014, places=["Pali Hill"], city="Mumbai"))
    n1 = req(f"{uid}-n1", "nw", {"acts": "Walks, Chai or coffee", "when": "Weekday evenings", "where": "Bandra, Mumbai",
                                 "desc": "I've just moved to Bandra and walk at Carter Road most evenings around 7. Looking for a calm walking buddy, any age, who enjoys a cutting chai after."},
             MeetRecord(activities=["Walks", "Chai or coffee"], times=["Weekday evenings"], city="Mumbai", areas=["Bandra"]))
    del r1  # stays "waiting for a match", like the frontend demo

    def match(kind, other, my_req, other_req, why_me, why_them, state, msgs=()):
        ref = matches_col().document(f"{uid}-{other}")
        ref.set({"kind": kind, "users": [uid, other], "req": {uid: my_req, other: other_req},
                 "why": {uid: why_me, other: why_them}, "state": {uid: state, other: state},
                 "score": 0, "judge": None, "created": t, "updated": t})
        for i, (mine, text) in enumerate(msgs):  # fixed ids: running this twice can't duplicate messages
            ref.collection("messages").document(f"seed-{i}").set({"sender": uid if mine else other, "t": text, "at": t + i})

    match("re", "seed-aarav", r2, "seed-aarav-re", ["name", "nickname", "school", "year"], ["name", "nickname", "school", "year", "area"], "new")
    match("re", "seed-zoya", None, "seed-zoya-re", ["area"], ["name", "area", "year"], "chatting", [
        (True, "Zoya! Is this you from Kurla West? We were neighbours in Building 4!"),
        (False, "Yes it's me! Building 4!"), (False, "Do you still listen to those old songs?")])
    match("nw", "seed-sunita", n1, "seed-sunita-nw", ["Walks"], ["Walks"], "new")
    match("nw", "seed-ishaan", n1, "seed-ishaan-nw", ["Walks", "Chai or coffee"], ["Walks", "Chai or coffee"], "chatting", [
        (True, "Hi Ishaan! I walk at the sea face most evenings too. Chai sometime?"),
        (False, "Yes! Thursday 7 pm at Carter Road?")])
    bump(uid)
