# Architecture Overview

- **FastAPI Web app** exposes REST and WebSocket endpoints for Twilio media streaming.
- **Twilio** streams call audio to the app via Media Streams (WebSocket).
- **STT (Deepgram)** converts audio to text.
- **Agents** (LLM-driven) process transcripts and call tools for side-effects.
- **TTS (ElevenLabs)** synthesizes spoken responses streamed back to Twilio.
- **Redis** stores session state (fast ephemeral store).
- **Postgres** stores persistent orders, users (SQLAlchemy).
- **Qdrant** used for vector search (optional).
- **Prometheus** scrapes metrics; Alerts configured via rules.
