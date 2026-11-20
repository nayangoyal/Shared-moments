# Shared Moments: Buildathon MVP

Find a lost friend from memory fragments. Gemini interviews you, turns the memory into a private
record, matches it **both ways** against other records, and reveals identities only after the
secret detail is verified and both say yes.

```
React chat ──► FastAPI ──► Gemini Flash  (interview + extract JSON + secret check)
                     └──► matching.py   (filter: year/city/age → score: nicknames both ways, places, school)
                     └──► Gemini Pro    (judge: probability + evidence + conflicts + verification Qs)
```

## Run it (2 terminals)

**1. Backend**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then paste your key from https://aistudio.google.com/apikey
uvicorn main:app --reload --port 8000
```

**2. Frontend**
```bash
cd frontend
bun install                 # or: npm install
bun run dev                 # or: npm run dev  → open http://localhost:5173
```

The frontend is the four-tab web app (Reconnect, Reunited, Meet New, New Friends). It runs on
sample data in the browser (saved in localStorage), so it works without the backend.

```
frontend/src/
  main.jsx, App.jsx          entry + page layout (header, screen, help panel, judges notes)
  styles.css                 all styles (light + dark, mobile layout)
  data/data.js               sample people, moments, seed state
  lib/utils.js               friend matching, Meet New queue, form scoring
  hooks/useHashRoute.js      #reconnect / #reunited / #meet / #newfriends
  store/StoreContext.jsx     saved state, toast, overlays, sending + "said yes" demo
  components/                Header, SidePanel, JudgesSection, ProfileCard, Overlays, Toast, ui, Icons
  screens/                   ReconnectScreen, FoundTab (Reunited + New Friends), MeetScreen
```

## Deploy the frontend to Cloud Run

`frontend/Dockerfile` builds the app with Bun and serves it with nginx on port 8080.
Cloud Build builds it in the cloud, so Docker isn't needed locally.

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud run deploy shared-moments \
  --source frontend --region asia-south1 \
  --allow-unauthenticated --port 8080 \
  --memory 256Mi --min-instances 0 --max-instances 3
```

The command prints the public URL. Run the last command again to redeploy after changes.

**Live:** https://shared-moments-894074329443.asia-south1.run.app
(project `shared-moments-2026`, service `shared-moments`, region `asia-south1`)

On a brand-new project the first build can fail with `PERMISSION_DENIED`. Grant the default
compute service account the build role once, wait a minute, then deploy again:
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" --role="roles/run.builder"
```

## Demo script (the story for the judges)

In the chat, describe this memory (Hinglish is fine):

> "2012 ke around Jaipur mein Shastri Nagar park mein, Hanuman mandir ke peeche, roz shaam ko
> cricket khelte the. Sharma Sir ki tuition bhi saath thi. Uska naam Bunty tha. Mujhe sab Golu
> bulate the. Hum dono 12 saal ke the. Chintu bhi saath khelta tha."

Secret detail when asked: *"we broke an uncle's window with a six and hid in the temple"*

What happens:
1. **Rohit ("Bunty")** comes back with a high probability. Evidence: same park, tuition, nicknames both ways.
2. **Ankit**, also called "Bunty" in Jaipur in 2012, shows up as a **near-miss** with a low score and
   conflicts listed (badminton, different school, different age). *This is the safety moment: same
   nickname and city is not enough.*
3. Click **Verify**, type the secret detail, and you get the reveal.
4. Try a wrong secret ("we went to a movie") and nothing is revealed.

`POST /api/reset` (or "Start over") restores the seed data between demo runs.

## Files

| File | What it does |
|---|---|
| `backend/prompts.py` | **All Gemini prompts.** Tune these first. |
| `backend/gemini_client.py` | Gemini calls with structured JSON output |
| `backend/matching.py` | Filter + two-way scoring (nickname sound-alikes, place/school overlap) |
| `backend/main.py` | API: `/interview`, `/finish`, `/verify`, `/consent`, `/reset` |
| `backend/data/seed.json` | 5 test profiles (1 true match, 1 near-miss, 3 unrelated) |
| `frontend/src/` | Four-tab web app (see the tree above) |

## Privacy rules already in the code
- The judge never sees the secret detail or real names.
- The other person's name is only returned by `/consent` after `/verify` passes.
- The other person's memory text is never sent to the frontend; only evidence summaries are.
