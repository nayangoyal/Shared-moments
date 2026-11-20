"""Shared Moments API (FastAPI on Cloud Run).

Every route needs a Firebase ID token. The frontend polls GET /api/state?rev=N, which costs one
database read when nothing changed.
"""
import logging
import threading
import time
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import ai, config, seed, store
from .auth import current_user, identity

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("api")

CANNED = {
    "seed-aarav": "Chintu here! I can't believe it. How have you been all these years?",
    "seed-farah": "Oh my god, hi!! It's been more than 10 years!",
    "seed-zoya": "Yes it's me! Building 4!",
    "seed-meena": "What a lovely surprise! Come over for filter coffee, like old times.",
    "seed-ishaan": "Hey! Yes, let's do it. Carter Road at 7?",
    "seed-sunita": "Hello! I'd love a walking buddy. Mornings suit me best.",
    "seed-meher": "Hi! Carrom this weekend?",
    "seed-desai": "Hello young friend! Join me for the Sunday morning walk.",
    "seed-rohan": "Hey! Sunday match at Juhu?",
    "seed-dev": "Hi! There's an open mic on Friday, come along.",
}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    threading.Thread(target=_safe_seed, daemon=True).start()  # don't block startup
    yield


def _safe_seed():
    try:
        seed.ensure_seeded()
    except Exception:  # noqa: BLE001
        log.exception("seeding failed (will retry on next session)")


app = FastAPI(title="Shared Moments API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])


# ---------- models ----------
class About(BaseModel):
    name: str = Field("", max_length=80)
    age: str = Field("", max_length=3)
    place: str = Field("", max_length=120)
    nick: str = Field("", max_length=120)
    school: str = Field("", max_length=200)
    year: str = Field("", max_length=20)
    area: str = Field("", max_length=200)


class NewRequest(BaseModel):
    kind: Literal["re", "nw"]
    data: dict[str, str]


class Message(BaseModel):
    text: str = Field(min_length=1, max_length=config.MAX_MESSAGE_CHARS)


class Reset(BaseModel):
    persona: Literal["new", "returning"]


# ---------- routes ----------
@app.get("/api/health")
def health():
    return {"ok": True, "models": {"flash": config.FLASH_MODELS, "judge": config.JUDGE_MODELS, "embed": config.EMBED_MODEL}}


@app.post("/api/session")
def session(who: dict = Depends(identity)):
    """First visit gets the 'returning user' demo state (as Rahul, "Golu"), like the original prototype.
    The app says so and links to Profile, where people enter their own details to match real friends."""
    uid = who["uid"]
    seed.ensure_seeded()
    if not store.get_user(uid):
        seed.reset_user(uid, "returning")
    store.users().document(uid).set({"anonymous": who["anonymous"]}, merge=True)
    return store.state(uid)


@app.get("/api/state")
def get_state(rev: int | None = None, uid: str = Depends(current_user)):
    if rev is not None and store.get_user(uid).get("rev", 0) == rev:
        return {"unchanged": True, "rev": rev}
    return store.state(uid)


@app.put("/api/me")
def put_me(about: About, bg: BackgroundTasks, uid: str = Depends(current_user)):
    if not about.name.strip():
        raise HTTPException(422, "Please add your name")
    store.save_about(uid, about.model_dump())
    for s in store.active_requests(uid):  # requests waiting on "About me" can match now
        if s.get("kind") == "re":
            bg.add_task(_match, s.id)
    return store.state(uid)


@app.delete("/api/me")
def delete_me(uid: str = Depends(current_user)):
    """Delete all my data: requests, matches, chats and About me (the deck's "delete at any time")."""
    seed.reset_user(uid, "new")
    return store.state(uid)


@app.post("/api/requests", status_code=201)
def create_request(body: NewRequest, bg: BackgroundTasks, uid: str = Depends(current_user)):
    me = store.get_user(uid)
    if not me.get("about"):
        raise HTTPException(409, {"code": "about_required", "message": "Tell us about you first"})
    if len(store.active_requests(uid)) >= config.MAX_ACTIVE_REQUESTS:
        raise HTTPException(429, f"You can have up to {config.MAX_ACTIVE_REQUESTS} active requests. Remove one first.")
    data = {k: v for k, v in body.data.items() if isinstance(v, str)}
    if body.kind == "re" and not any(v.strip() for v in data.values()):
        raise HTTPException(422, "Fill in at least one thing you remember")
    if body.kind == "nw":
        if not data.get("acts", "").strip():
            raise HTTPException(422, "Pick at least one thing you'd like to do")
        if len(data.get("desc", "").split()) < 20:
            raise HTTPException(422, "Please describe it in more detail (at least 20 words)")
    rid = store.create_request(uid, body.kind, data)
    bg.add_task(_match, rid)
    return {"id": rid}


@app.delete("/api/requests/{rid}")
def delete_request(rid: str, uid: str = Depends(current_user)):
    if not store.remove_request(uid, rid):
        raise HTTPException(404, "Request not found")
    return {"ok": True}


@app.post("/api/matches/{mid}/dismiss")
def dismiss(mid: str, uid: str = Depends(current_user)):
    if not store.dismiss(uid, mid):
        raise HTTPException(404, "Match not found")
    return {"ok": True}


@app.post("/api/matches/{mid}/messages", status_code=201)
def send_message(mid: str, body: Message, bg: BackgroundTasks, uid: str = Depends(current_user)):
    text = ai.scrub(body.text.strip())
    m = store.add_message(uid, mid, text)
    if not m:
        raise HTTPException(404, "Chat not found")
    other = next(u for u in m["users"] if u != uid)
    if other in seed.PERSONAS:
        bg.add_task(_persona_reply, mid, uid, other)
    return {"ok": True}


@app.post("/api/demo/reset")
def demo_reset(body: Reset, uid: str = Depends(current_user)):
    seed.reset_user(uid, body.persona)
    return store.state(uid)


# ---------- background work ----------
def _match(rid: str):
    try:
        store.run_matching(rid)
    except Exception:  # noqa: BLE001
        log.exception("matching failed for %s", rid)


def _persona_reply(mid: str, uid: str, persona_id: str):
    try:
        time.sleep(config.REPLY_DELAY_S)
        ref, m = store.get_match(uid, mid)
        if not m:
            return
        history = store.messages(ref, uid)
        if not history or not history[-1]["me"]:
            return  # already answered
        p = seed.PERSONAS[persona_id]
        persona = {"name": p["name"], "first": p["name"].split()[0].replace("Mr.", "Mr"), "age": p["age"], "background": p["background"]}
        text = ai.persona_reply(persona, history) or CANNED.get(persona_id, "Hi! Nice to hear from you.")
        ref.collection("messages").add({"sender": persona_id, "t": text, "at": time.time()})
        ref.update({"updated": time.time()})
        store.bump(uid)
    except Exception:  # noqa: BLE001
        log.exception("persona reply failed")
