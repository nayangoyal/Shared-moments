"""Google Cloud clients, created once. On Cloud Run they use the service's own identity (no keys),
except the optional Gemini API key (AI Studio), which comes from Secret Manager as GEMINI_API_KEY."""
import os
from functools import lru_cache

from google import genai
from google.cloud import firestore
from google.genai import types

from . import config

# Every Gemini call gives up after this long, so a stuck call can't stall matching or a reply
_HTTP = types.HttpOptions(timeout=config.GEMINI_TIMEOUT_MS)


def _credentials():
    if config.LOCAL_ACCESS_TOKEN:
        from google.oauth2.credentials import Credentials
        return Credentials(token=config.LOCAL_ACCESS_TOKEN)
    return None  # Application Default Credentials (the Cloud Run service account)


@lru_cache
def db() -> firestore.Client:
    return firestore.Client(project=config.PROJECT, credentials=_credentials())


@lru_cache
def gemini_client(where: str) -> genai.Client:
    """'aistudio' = Gemini API with the key from Secret Manager; anything else = a Vertex AI location."""
    if where == "aistudio":
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        return genai.Client(api_key=key, http_options=_HTTP)
    return genai.Client(vertexai=True, project=config.PROJECT, location=where, credentials=_credentials(), http_options=_HTTP)


def vertex(where: str) -> genai.Client:  # kept for callers that name a location
    return gemini_client(where)
