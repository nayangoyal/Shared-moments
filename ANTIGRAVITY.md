# Using this project in Antigravity

Open the `shared-moments` folder in Antigravity (File → Open Folder). Get the base running first
(see README), then paste these prompts into the Antigravity agent one at a time, testing in
between. They're ordered by demo impact.

---

### 1. Get it running
```
Read README.md. Create a Python venv in backend/, install requirements, and start the FastAPI
server on port 8000. In another terminal, run npm install and npm run dev in frontend/.
Then open http://localhost:5173 in the browser and confirm the interviewer's first message appears.
```

### 2. Run the demo once end to end
```
Using the browser, run the demo script in README.md: chat the Hinglish memory, give the secret
detail when asked, click "Find my match", check that Rohit scores high and Ankit low, then verify.
Report anything that breaks and fix it.
```

### 3. Better match card (high demo value)
```
In frontend/src/App.jsx, make the match card more visual: a coloured probability ring, the
evidence as green ticks, conflicts as red crosses, and a small "checked both ways ✓✓" badge when
scores.a_finds_b and scores.b_finds_a are both above 0.7. Keep the existing styles.css look.
```

### 4. "Memory card" share image (shows the cold-start fix)
```
After a search with no strong match, show a shareable "memory card" with NO names, e.g.
"Someone remembers cricket near Shastri Nagar park, Jaipur, 2012. Was it you?". Generate the
one-line text with Gemini in backend (new endpoint /api/memory-card using the record, never
nicknames or secret_detail) and add a "Copy for WhatsApp" button.
```

### 5. Voice input (optional, only if time allows)
```
Add a mic button to the chat composer that uses the browser Web Speech API (lang hi-IN, fallback
en-IN) to fill the text input. No backend changes.
```

### 6. Deploy (only at the end, if the event wants a live link)
```
Add a Dockerfile for the backend and deploy it to Cloud Run with GEMINI_API_KEY as a secret.
Build the frontend and serve frontend/dist from FastAPI as static files, so it's one service.
```

---

**Don't change** `matching.py` thresholds or `prompts.py` right before the demo without re-running
step 2. Those decide whether the near-miss is rejected.
