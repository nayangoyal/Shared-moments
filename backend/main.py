"""Shared Moments backend (FastAPI).

Flow:  /api/interview  ->  /api/finish (extract + save + match)  ->  /api/verify  ->  /api/consent
Run:   uvicorn main:app --reload --port 8000
"""
import json
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import gemini_client as gc
from matching import candidates
from models import ChatMessage, MemoryRecord

DATA = Path(__file__).parent / "data"
STORE = DATA / "records.json"
SEED = DATA / "seed.json"

app = FastAPI(title="Shared Moments")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# pending matches waiting for verification / consent (in memory is fine for a demo)
MATCHES: dict[str, dict] = {}


# ---------------- storage (a JSON file is enough for the demo) ----------------
def load_records() -> list[MemoryRecord]:
    if not STORE.exists():
        STORE.write_text(SEED.read_text())
    return [MemoryRecord(**r) for r in json.loads(STORE.read_text())]


def save_record(rec: MemoryRecord) -> None:
    recs = [r.model_dump() for r in load_records()]
    recs.append(rec.model_dump())
    STORE.write_text(json.dumps(recs, indent=2, ensure_ascii=False))


# ---------------- API ----------------
class ChatRequest(BaseModel):
    history: list[ChatMessage]


@app.get("/api/health")
def health():
    return {"ok": True, "records": len(load_records())}


@app.post("/api/interview")
def interview(req: ChatRequest):
    """Returns the interviewer's next question."""
    turn = gc.interview_turn(req.history)
    return turn.model_dump()


@app.post("/api/finish")
def finish(req: ChatRequest):
    """Interview done: extract a record, store it, and look for two-way matches."""
    rec = gc.extract_record(req.history)
    rec.id = f"user-{uuid.uuid4().hex[:8]}"
    pool = load_records()
    save_record(rec)

    results = []
    for other, scores in candidates(rec, pool):
        verdict = gc.judge_pair(rec, other)
        match_id = uuid.uuid4().hex[:10]
        MATCHES[match_id] = {"me": rec, "other": other, "verified": False}
        results.append({
            "match_id": match_id,
            "probability": verdict.probability,
            "scores": scores,
            "evidence": verdict.evidence,
            "conflicts": verdict.conflicts,
            "verification_questions": verdict.verification_questions,
            # Nothing that identifies the other person is sent before consent
        })
    results.sort(key=lambda r: r["probability"], reverse=True)

    record_view = rec.model_dump(exclude={"secret_detail"})
    return {"record": record_view, "matches": results}


class VerifyRequest(BaseModel):
    match_id: str
    secret_answer: str


@app.post("/api/verify")
def verify(req: VerifyRequest):
    """User types their secret detail; we check it against the other person's, privately."""
    m = MATCHES.get(req.match_id)
    if not m:
        raise HTTPException(404, "Match not found")
    check = gc.check_secret(req.secret_answer, m["other"].secret_detail)
    m["verified"] = check.same
    # The other person's secret is never returned
    return {"verified": check.same}


class ConsentRequest(BaseModel):
    match_id: str


@app.post("/api/consent")
def consent(req: ConsentRequest):
    """Demo: seeded profiles auto-consent. Real app: wait for the other side's yes."""
    m = MATCHES.get(req.match_id)
    if not m or not m["verified"]:
        raise HTTPException(400, "Verify the secret detail first")
    other = m["other"]
    return {
        "revealed": True,
        "name": other.owner_name,
        "known_as": other.my_nicknames,
        "message": f"{other.owner_name} was also looking for you. You can start chatting now.",
    }


@app.post("/api/reset")
def reset():
    """Restore the seed data (handy between demo runs)."""
    STORE.write_text(SEED.read_text())
    MATCHES.clear()
    return {"ok": True}
