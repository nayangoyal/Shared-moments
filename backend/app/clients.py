"""Google Cloud clients, created once. On Cloud Run they use the service's own identity (no keys)."""
from functools import lru_cache

from google import genai
from google.cloud import firestore

from . import config


def _credentials():
    if config.LOCAL_ACCESS_TOKEN:
        from google.oauth2.credentials import Credentials
        return Credentials(token=config.LOCAL_ACCESS_TOKEN)
    return None  # Application Default Credentials (the Cloud Run service account)


@lru_cache
def db() -> firestore.Client:
    return firestore.Client(project=config.PROJECT, credentials=_credentials())


@lru_cache
def vertex(location: str) -> genai.Client:
    """Gemini on Vertex AI for one location (e.g. 'asia-south1' or 'global')."""
    return genai.Client(vertexai=True, project=config.PROJECT, location=location, credentials=_credentials())


def embedder() -> genai.Client:
    return vertex(config.EMBED_LOCATION)
