# Shared Moments

**Find anyone you remember, from 20 years ago or 20 minutes ago.** Startup Buildathon India 2026.

You describe *what you remember* about a lost friend (a nickname, a school, a year, a memory), not
who they are. Your description stays private. Gemini matches it **both ways**: you only match
someone who independently described you too, so nobody can be found unless they're also looking.
The same engine helps you meet new people who want the same moments (a walk, chai, music).

**Live:** https://shared-moments-894074329443.asia-south1.run.app

## Built on Google

| Product | What it does here |
|---|---|
| **Cloud Run** | Two services: `shared-moments` (web app) and `shared-moments-api` (FastAPI) |
| **Gemini on Vertex AI** (`gemini-3.5-flash`, Mumbai) | Turns forms into clean records (nickname spellings, year ranges, places, Hindi/Hinglish), judges "are these two people remembering each other?", and plays the demo people in chat |
| **Gemini Embeddings** (`gemini-embedding-001`) | Meaning-based matching of memories and descriptions |
| **Cloud Firestore** + vector search | Requests, matches, chats; nearest-neighbour search for Meet New |
| **Firebase Authentication** | Anonymous demo sessions (each judge gets a private sandbox); phone sign-in enabled |
| **Cloud Build** + GitHub | Push to `main` → tests → build → deploy, for both services |
| **Artifact Registry, Secret Manager, Cloud Logging, IAM** | Images, the GitHub connection, logs, a least-privilege API service account |

## How matching works

```
Reconnect form ──► POST /api/requests ──► Gemini: form → clean record   ──► Firestore (private)
                                          Gemini Embeddings: memory text
                         background ──►  1. fields, BOTH ways: your description fits how they say
                                            others knew them, AND theirs fits your "About me"
                                            (each way needs a name, nickname or old phone number)
                                         2. meaning: embedding similarity of the two memories
                                         3. Gemini judge: probability, evidence, conflicts
                                         ──► match for both people: "This might be your moment"
Meet New: shared activities in the same city + Firestore vector search on the descriptions.
```

Privacy: requests are only ever readable by their owner. A match shows the other person's name,
age and area, and *why it matched in your own words*. Phone numbers are stored only as a hash;
contact details are removed from free text; the database refuses all direct browser access.

## Try the demo

1. Open the live site. You start as a **returning user** with a match (Aarav), chats and requests.
   Say hi to Aarav: he answers in character (Gemini).
2. In *For the judges*, tap **A new user (empty)**. On Reconnect, tap **Fill an example** →
   **Start looking**. You're asked about you once: **Fill an example** again (you're Rahul, "Golu").
3. A few seconds later: *This might be your moment*. Aarav was looking for "Golu from
   St. Stanislaus, 2014", so you match both ways.
4. Type the name **Riya**: no match, the request waits for her to join.
5. Meet New → **Fill an example** → matches people who like music and sunsets.
6. **Two real people:** open the site in two different browsers. In each, tap the round avatar
   (top right) → **Profile**, replace the demo identity with your own details, then on Reconnect
   describe the other person. Both see the match within seconds and can chat.

Everyone starts as the demo identity (Rahul, "Golu"). Demo identities only match the demo people,
so judges using the examples never match each other; anyone with their own details is a real user.

## Run locally

```bash
# API (needs gcloud signed in to the project)
cd backend
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt pytest
.venv/bin/python -m pytest -q tests                       # matching unit tests
LOCAL_ACCESS_TOKEN=$(gcloud auth print-access-token) .venv/bin/uvicorn app.main:app --port 8000

# Web app (Vite forwards /api to :8000)
cd frontend && bun install && bun run dev                  # http://localhost:5173
```

## Code map

```
backend/app/
  main.py        API routes (all need a Firebase ID token)
  store.py       Firestore data + the matching engine
  matching.py    pure matching rules (sound-alike nicknames, two-way scoring) – unit-tested
  ai.py          Gemini: extraction, embeddings, judge, in-character replies (each with a fallback)
  prompts.py     every Gemini instruction in one place
  seed.py        demo people (each with a hidden About me + request) and the returning-user state
frontend/src/
  lib/api.js     Firebase anonymous sign-in + API client
  store/         app state from the API, polling, "This might be your moment", replies
  screens/       Reconnect, About you, Meet New, Reunited / New Friends (requests, matches, chat)
cloudbuild.yaml / cloudbuild.backend.yaml   auto-deploy on push to main
```

## Deploy

Pushing to `main` deploys automatically (Cloud Build triggers `deploy-frontend` and `deploy-backend`
in `asia-south1`, about 2–3 minutes; see Cloud Build → History). Manual deploys:

```bash
gcloud run deploy shared-moments-api --source backend --region asia-south1 \
  --service-account sm-api@PROJECT_ID.iam.gserviceaccount.com --allow-unauthenticated --no-cpu-throttling
gcloud run deploy shared-moments --source frontend --region asia-south1 --allow-unauthenticated
```

On a brand-new project the first build can fail with `PERMISSION_DENIED`: grant
`PROJECT_NUMBER-compute@developer.gserviceaccount.com` the `roles/run.builder` role once and retry.
