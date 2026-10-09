# Thorkell

A local-first web app for recording workplace conversations, transcribing them,
and keeping track of ideas, notes, and action items.

- **Backend:** FastAPI + SQLAlchemy + SQLite (full-text search via FTS5)
- **Frontend:** React + Vite + TypeScript + Tailwind (white + violet theme, dark mode)
- **Transcription & summaries:** free cloud tier (Groq) now, swappable to paid providers later

## Features

- Record in the browser, or upload an existing audio file
- Transcribe to timestamped segments (Groq Whisper, or a local Whisper fallback)
- Click a timestamp to jump the audio player to that moment
- Label who said what (manual speakers), edit transcript text inline
- Tag conversations and full-text search across every transcript
- AI summary + extracted action items (via a swappable LLM provider)
- Export to Markdown or PDF

## Prerequisites

- Python 3.10+ (3.14 works with the current dependency floors; if a wheel is
  missing for your exact build, Python 3.12 or 3.13 is the smoothest option)
- Node.js 18+
- A free Groq API key (https://console.groq.com/keys) — optional if you run a
  local Whisper model instead

## Backend setup

```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend\.env` and set `GROQ_API_KEY=...` (get a free key at
https://console.groq.com/keys).

Run the API:

```bat
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health/config check: http://localhost:8000/api/health

## Frontend setup

```bat
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` to the backend on
port 8000, so both must be running.

## Switching providers (free now → paid later)

Everything routes through provider interfaces. To change a provider, edit
`backend\.env`:

| Setting | Values | Notes |
| --- | --- | --- |
| `TRANSCRIPTION_PROVIDER` | `groq`, `whisper_local` | Add a new class in `app/services/transcription/` and register it in `factory.py` for OpenAI/Deepgram/etc. |
| `SUMMARIZATION_PROVIDER` | `groq`, `none` | Add `app/services/summarization/openai.py` + register in `factory.py`. |
| `DIARIZATION_PROVIDER` | `manual` | Auto speaker detection drops in via `app/services/diarization/factory.py` (AssemblyAI/Deepgram/pyannote). |

### Fully-local transcription

```bat
pip install -r requirements-optional.txt
```

Then set `TRANSCRIPTION_PROVIDER=whisper_local` in `backend\.env`.

## Project layout

```
backend/
  app/
    main.py            # FastAPI app + CORS + startup
    config.py          # settings from .env
    db.py              # engine, session, schema + FTS5 init
    models.py          # SQLAlchemy models
    schemas.py         # Pydantic schemas
    api/routes/        # conversations, segments, speakers, action_items, search, tags, health
    services/
      transcription/   # base + groq + whisper_local + factory
      summarization/   # base + groq + factory
      diarization/     # base + manual + factory
      export/          # markdown + pdf
      search.py        # FTS5 indexing + query
      storage.py       # audio file storage
  storage/             # uploaded recordings (git-ignored)
  thorkell.db          # SQLite database (git-ignored)
frontend/
  src/
    components/         # Layout, RecordDialog, transcript/summary/action panels, ui primitives
    pages/              # Conversations, Conversation detail, Search
    theme/              # ThemeProvider (light / dark / system)
    hooks/              # useRecorder (MediaRecorder)
    lib/                # api client, types, formatting
```

## Data & privacy

- Recordings live in `backend/storage/`; the database is `backend/thorkell.db`.
- `.env`, the database, and recordings are git-ignored — never commit them.
- When using Groq, audio/transcripts are sent to their API. Use
  `TRANSCRIPTION_PROVIDER=whisper_local` for fully offline processing.
