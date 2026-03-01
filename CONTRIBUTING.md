# Contributing to Studia

Thanks for your interest in contributing. Studia is a local, self-hosted interview prep coach. These guidelines will help you get set up and submit changes. We also follow the [Contributor Covenant](CODE_OF_CONDUCT.md) code of conduct.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) (for the LLM; run `ollama pull qwen3`)

## Running locally

1. Clone the repo and go to the backend:

   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Optional: copy `.env.example` to `.env` and adjust (e.g. `OLLAMA_BASE_URL` if Ollama runs elsewhere).

3. Start the backend:

   ```bash
   uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. Open http://127.0.0.1:8000 in your browser. The web UI is served by the backend. On first run you can create a profile via the onboarding form (resumes and/or LinkedIn export).

To run Ollama and the backend together from the repo root, use `./start.sh` (see README).

## Running tests

From the backend directory with your venv activated:

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

See `backend/tests/` for the test suite.

## Submitting changes

1. Open an issue or pick an existing one to discuss the change if it's non-trivial.
2. Fork the repo and create a branch from `main`.
3. Make your changes. Keep the scope focused; add or update tests where relevant.
4. Run tests and ensure the app still runs (e.g. health endpoint, profile status).
5. Submit a pull request with a clear description of what changed and why. Link any related issue.

## Code and design

- Backend: Python 3.10+, FastAPI, SQLite by default. Config via environment variables; no secrets in code.
- Frontend: Vanilla HTML/CSS/JS in `web/`; no build step. Message content is rendered with `textContent` to avoid XSS.
- The app is single-user and local; no authentication. Do not expose it to untrusted networks.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT).
