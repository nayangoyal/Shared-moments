"""Everything that talks to Gemini on Vertex AI.

Each call has a plain-code fallback, so the app keeps working if a model is slow or unavailable.
"""
import json
import logging
import re
import time

from google.genai import types
from pydantic import BaseModel, Field

from . import config, prompts
from .clients import embedder, vertex

log = logging.getLogger("ai")

FAST = types.ThinkingConfig(thinking_level="minimal")  # quick, complete answers for chat + extraction


def _generate(models: list[str], contents: str, cfg: types.GenerateContentConfig):
    """Try each 'location/model' in order; retry once on 403/429/5xx (seen intermittently on new projects)."""
    last = None
    for spec in models:
        loc, model = spec.strip().split("/", 1)
        this_cfg = cfg
        for attempt in range(2):
            try:
                return vertex(loc).models.generate_content(model=model, contents=contents, config=this_cfg)
            except Exception as e:  # noqa: BLE001
                last = e
                if "Thinking level is unsupported" in str(e) and this_cfg.thinking_config is not None:
                    this_cfg = this_cfg.model_copy(update={"thinking_config": None})  # model doesn't take it
                    continue
                retryable = any(code in str(e)[:12] for code in ("403", "429", "500", "503"))
                log.info("gemini %s attempt %d failed: %s", spec, attempt + 1, str(e)[:80])
                if not retryable:
                    break
                time.sleep(0.4 * (attempt + 1))
    raise last


# ---------- structured records ----------
class PersonRecord(BaseModel):
    """A person as remembered by someone: either "who I'm looking for" or "how others knew me"."""
    names: list[str] = Field(default_factory=list, description="Real names and partial names, with common spelling variants")
    nicknames: list[str] = Field(default_factory=list, description="Nicknames, with common spelling variants")
    schools: list[str] = Field(default_factory=list, description="Schools, colleges, tuition classes, offices: short canonical names")
    year_from: int | None = Field(default=None, description="Earliest year of the shared time")
    year_to: int | None = Field(default=None, description="Latest year of the shared time")
    places: list[str] = Field(default_factory=list, description="Areas, colonies, streets, landmarks (no house numbers)")
    city: str | None = Field(default=None, description="City, normalised (e.g. Mumbai, Pune)")
    summary: str = Field(default="", description="One neutral sentence about the shared past")


class MeetRecord(BaseModel):
    activities: list[str] = Field(default_factory=list, description="Activities from the allowed list")
    times: list[str] = Field(default_factory=list)
    city: str | None = None
    areas: list[str] = Field(default_factory=list)
    summary: str = ""


class JudgeVerdict(BaseModel):
    probability: float = Field(description="0 to 1: chance both people are remembering each other")
    evidence: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)


# ---------- privacy: strip contact details from free text ----------
_PHONE = re.compile(r"(?:\+?\d[\d\s-]{7,}\d)")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_URL = re.compile(r"https?://\S+|www\.\S+")


def scrub(text: str) -> str:
    text = _EMAIL.sub("[email removed]", text or "")
    text = _URL.sub("[link removed]", text)
    return _PHONE.sub("[number removed]", text)


# ---------- Gemini calls ----------
def _json(models: list[str], system: str, text: str, schema: type[BaseModel], fast: bool = True) -> BaseModel:
    resp = _generate(models, text, types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.2,
        thinking_config=FAST if fast else None,
    ))
    if resp.parsed is not None:
        return resp.parsed
    return schema.model_validate(json.loads(resp.text))


def _years(text: str) -> tuple[int | None, int | None]:
    ys = [int(y) for y in re.findall(r"\b(19[4-9]\d|20[0-4]\d)\b", text or "")]
    return (min(ys), max(ys)) if ys else (None, None)


def _split(s: str) -> list[str]:
    return [p.strip() for p in re.split(r"[,/;]", s or "") if p.strip()]


def fallback_person(d: dict) -> PersonRecord:
    y0, y1 = _years(d.get("year", ""))
    places = _split(d.get("area", ""))
    return PersonRecord(
        names=[d["name"].strip()] if d.get("name", "").strip() else [],
        nicknames=[n for n in _split(d.get("nick", ""))],
        schools=_split(d.get("school", "")),
        year_from=y0, year_to=y1, places=places,
        city=d.get("city") or (places[-1] if places else None),
        summary=(d.get("memory") or "")[:200],
    )


def extract_person(d: dict, purpose: str) -> PersonRecord:
    """purpose: 'looking_for' (a Reconnect request) or 'about_me' (how others knew this user)."""
    text = "\n".join(f"{k}: {v}" for k, v in d.items() if v and k != "phone")
    try:
        rec = _json(config.FLASH_MODELS, prompts.EXTRACT_PERSON[purpose], text, PersonRecord)
        base = fallback_person(d)  # never lose what the user literally typed
        rec.names = _uniq(base.names + rec.names)
        rec.nicknames = _uniq(base.nicknames + rec.nicknames)
        rec.schools = _uniq(base.schools + rec.schools)
        rec.places = _uniq(base.places + rec.places)
        rec.year_from = rec.year_from or base.year_from
        rec.year_to = rec.year_to or base.year_to or rec.year_from
        return rec
    except Exception as e:  # noqa: BLE001
        log.warning("extract_person fallback: %s", e)
        return fallback_person(d)


def extract_meet(d: dict, allowed: list[str]) -> MeetRecord:
    base = MeetRecord(activities=_split(d.get("acts", "")), times=[d["when"]] if d.get("when") else [],
                      city=(_split(d.get("where", "")) or [None])[-1], areas=_split(d.get("where", "")),
                      summary=(d.get("desc") or "")[:200])
    try:
        text = "\n".join(f"{k}: {v}" for k, v in d.items() if v)
        rec = _json(config.FLASH_MODELS, prompts.EXTRACT_MEET.format(allowed=", ".join(allowed)), text, MeetRecord)
        rec.activities = _uniq(base.activities + [a for a in rec.activities if a in allowed])
        rec.city = rec.city or base.city
        rec.areas = _uniq(base.areas + rec.areas)
        return rec
    except Exception as e:  # noqa: BLE001
        log.warning("extract_meet fallback: %s", e)
        return base


def embed(text: str) -> list[float] | None:
    if not (text or "").strip():
        return None
    try:
        resp = embedder().models.embed_content(
            model=config.EMBED_MODEL, contents=text[:4000],
            config=types.EmbedContentConfig(output_dimensionality=config.EMBED_DIM, task_type="SEMANTIC_SIMILARITY"),
        )
        return list(resp.embeddings[0].values)
    except Exception as e:  # noqa: BLE001
        log.warning("embed failed: %s", e)
        return None


def judge(a_looking: PersonRecord, b_about: PersonRecord, b_looking: PersonRecord, a_about: PersonRecord,
          a_memory: str, b_memory: str) -> JudgeVerdict | None:
    """Gemini decides if A and B are remembering EACH OTHER. Returns None if the model is unavailable."""
    text = json.dumps({
        "A_is_looking_for": a_looking.model_dump(), "A_memory": a_memory[:1500],
        "B_says_others_knew_them_as": b_about.model_dump(),
        "B_is_looking_for": b_looking.model_dump(), "B_memory": b_memory[:1500],
        "A_says_others_knew_them_as": a_about.model_dump(),
    }, ensure_ascii=False)
    try:
        return _json(config.JUDGE_MODELS, prompts.JUDGE, text, JudgeVerdict, fast=False)  # the judge thinks
    except Exception as e:  # noqa: BLE001
        log.warning("judge unavailable: %s", e)
        return None


def persona_reply(persona: dict, history: list[dict]) -> str | None:
    """A demo person answers in character."""
    convo = "\n".join(f"{'THEM' if m['me'] else 'YOU'}: {m['t']}" for m in history[-12:])
    try:
        resp = _generate(config.FLASH_MODELS, convo, types.GenerateContentConfig(
            system_instruction=prompts.PERSONA.format(**persona),
            temperature=0.8, max_output_tokens=1500, thinking_config=FAST,  # room for models that still think
        ))
        text = (resp.text or "").strip()
        return scrub(text)[:400] or None
    except Exception as e:  # noqa: BLE001
        log.warning("persona_reply fallback: %s", e)
        return None


def _uniq(xs: list[str]) -> list[str]:
    seen, out = set(), []
    for x in xs:
        k = x.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(x.strip())
    return out
