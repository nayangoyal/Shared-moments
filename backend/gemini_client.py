"""Thin wrapper around the Gemini API (google-genai library)."""
import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from models import ChatMessage, InterviewTurn, JudgeResult, MemoryRecord, SecretCheck
import prompts

load_dotenv()

FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
JUDGE_MODEL = os.getenv("GEMINI_JUDGE_MODEL", "gemini-2.5-pro")

_client = None


def client() -> genai.Client:
    global _client
    if _client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set. Put it in backend/.env")
        _client = genai.Client(api_key=key)
    return _client


def _to_contents(history: list[ChatMessage]) -> list[types.Content]:
    contents = [
        types.Content(role=m.role if m.role in ("user", "model") else "user",
                      parts=[types.Part(text=m.text)])
        for m in history
    ]
    if not contents:
        # Gemini needs at least one user turn to start the interview
        contents = [types.Content(role="user", parts=[types.Part(text="Hi, I want to find someone.")])]
    return contents


def _json_call(model: str, system: str, contents, schema):
    resp = client().models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.3,
        ),
    )
    if resp.parsed is not None:
        return resp.parsed
    return schema.model_validate(json.loads(resp.text))


def interview_turn(history: list[ChatMessage]) -> InterviewTurn:
    return _json_call(FLASH_MODEL, prompts.INTERVIEW_SYSTEM, _to_contents(history), InterviewTurn)


def extract_record(history: list[ChatMessage]) -> MemoryRecord:
    transcript = "\n".join(f"{'USER' if m.role == 'user' else 'INTERVIEWER'}: {m.text}" for m in history)
    return _json_call(FLASH_MODEL, prompts.EXTRACT_SYSTEM, transcript, MemoryRecord)


def _public_view(r: MemoryRecord) -> dict:
    # The judge never needs the secret detail
    return r.model_dump(exclude={"secret_detail", "id", "owner_name"})


def judge_pair(a: MemoryRecord, b: MemoryRecord) -> JudgeResult:
    text = f"RECORD A:\n{json.dumps(_public_view(a), indent=2)}\n\nRECORD B:\n{json.dumps(_public_view(b), indent=2)}"
    return _json_call(JUDGE_MODEL, prompts.JUDGE_SYSTEM, text, JudgeResult)


def check_secret(answer: str, stored_secret: str) -> SecretCheck:
    text = f"DETAIL 1: {answer}\nDETAIL 2: {stored_secret}"
    return _json_call(FLASH_MODEL, prompts.SECRET_SYSTEM, text, SecretCheck)
