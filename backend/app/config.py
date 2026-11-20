"""Settings, read from environment variables (set on Cloud Run; defaults work for this project)."""
import os

PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "shared-moments-2026")

# Gemini on Vertex AI, as "location/model". Tried in order: the Mumbai endpoint first (reliable for this
# project and keeps users' memories in India), then the global endpoint as a backup.
# JUDGE_MODELS can list a Pro model first once the billing account is a full paid account.
FLASH_MODELS = os.getenv("GEMINI_FLASH_MODELS", "asia-south1/gemini-3.5-flash,global/gemini-3.8-flash").split(",")
JUDGE_MODELS = os.getenv("GEMINI_JUDGE_MODELS", "asia-south1/gemini-3.5-flash,global/gemini-3.1-pro-preview").split(",")
EMBED_LOCATION = os.getenv("EMBED_LOCATION", "asia-south1")             # keeps text in India
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = 768

# Matching
FIELD_THRESHOLD = 4          # points each direction must reach (name 3, nickname 3, phone 5, school 2, area 2, year 1)
JUDGE_MIN_PROBABILITY = 0.35  # the Gemini judge can veto a field match below this
MAX_ACTIVE_REQUESTS = 10     # anti-probing: one person can't describe dozens of people
MAX_MESSAGE_CHARS = 1000

# Demo people reply this many seconds after a message
REPLY_DELAY_S = float(os.getenv("REPLY_DELAY_S", "2"))

# Local development only: use a short-lived gcloud access token instead of a service account
LOCAL_ACCESS_TOKEN = os.getenv("LOCAL_ACCESS_TOKEN")
