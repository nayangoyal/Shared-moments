"""Settings, read from environment variables (set on Cloud Run; defaults work for this project)."""
import os

PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "shared-moments-2026")

# Gemini, as "where/model", tried in order. where = "aistudio" (Gemini API key from Secret Manager) or a
# Vertex AI location ("asia-south1" keeps text in India, or "global").
# While the billing account is a free trial, Vertex AI mostly refuses calls ("eligible paid billing
# account"), so the API key goes first. After upgrading billing, put the Vertex entries first: env only.
# Measured 2026-11-20 on the API key: Flash-Lite answers every call in 1-3 s; the full Flash/Pro models
# mostly return "high demand" (503) on the free tier. Flash-Lite judged a true pair 0.99, a false pair 0.0.
FLASH_MODELS = os.getenv("GEMINI_FLASH_MODELS",
                         "aistudio/gemini-3.5-flash-lite,aistudio/gemini-3.1-flash-lite,asia-south1/gemini-3.5-flash").split(",")
JUDGE_MODELS = os.getenv("GEMINI_JUDGE_MODELS",
                         "aistudio/gemini-3.5-flash-lite,aistudio/gemini-3.1-flash-lite,asia-south1/gemini-3.5-flash").split(",")
EMBED_SOURCES = os.getenv("EMBED_SOURCES", "asia-south1,aistudio").split(",")  # embeddings work on Vertex today
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = 768
GEMINI_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", "25000"))

# Matching
FIELD_THRESHOLD = 4          # points each direction must reach (name 3, nickname 3, phone 5, school 2, area 2, year 1)
JUDGE_MIN_PROBABILITY = 0.35  # the Gemini judge can veto a field match below this
MAX_ACTIVE_REQUESTS = 10     # anti-probing: one person can't describe dozens of people
MAX_MESSAGE_CHARS = 1000

# Demo people reply this many seconds after a message
REPLY_DELAY_S = float(os.getenv("REPLY_DELAY_S", "2"))

# Local development only: use a short-lived gcloud access token instead of a service account
LOCAL_ACCESS_TOKEN = os.getenv("LOCAL_ACCESS_TOKEN")
