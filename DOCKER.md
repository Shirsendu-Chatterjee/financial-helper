# Docker deployment for Financial Filing RAG Assistant

The server is a single FastAPI process that serves **both** the API and the
static webpage (`/`, `/index.html`, `/app.js`) from the same origin, so no
CORS setup is needed. Ports: **8000** (configurable via `PORT`).

## Prerequisites

- The two runtime env vars below. `GROQ_API_KEY` is required; `EDGAR_IDENTITY`
  is only needed when you actually run an `/ingest` (it's checked lazily).
- A working Docker installation.

## Build

```bash
# From the repository root:
docker build -t financial-helper:latest .

# Cross-platform (if you need a specific architecture for your target host):
DOCKER_BUILDKIT=1 docker buildx build --platform linux/amd64 -t financial-helper:latest .
```

## Run

```bash
docker run -d --name fh \
  -e GROQ_API_KEY="gsk_..." \
  -e EDGAR_IDENTITY="Morgana morgana@example.com" \
  -p 8000:8000 \
  -v fh_indexes:/app/indexes \
  -v fh_chroma:/app/chroma_db \
  financial-helper:latest
```

**What each flag does:**

- `-e GROQ_API_KEY` — required. Without it the container prints an error and
  exits (the entrypoint enforces this).
- `-e EDGAR_IDENTITY="Your Name your@email.com"` — required for the first
  `/ingest`. Format: `Name email@domain.com`. Optional at container start, but
  ingest won't work until it's set. You can pass it at run time, or stop and
  re-run with it added; the index, once built, doesn't need it again.
- `-p 8000:8000` — maps host port 8000 to the container.
- `-v fh_indexes:/app/indexes` and `-v fh_chroma:/app/chroma_db` — persist the
  indexes across container restarts so you don't rebuild on every restart.
  Without these, every restart loses the index and the first ingest runs again.

Open **http://localhost:8000** — the webpage is served directly by this
container.

### First use

1. Type a ticker (e.g. `AAPL`) → **Load / Index**. First ingest fetches from
   SEC EDGAR and embeds; the first run can take a few minutes, then the status
   pill turns green.
2. Type a question → **Ask**.

### Without pre-seeding env at run time

You can start the container without `EDGAR_IDENTITY`, then stop and re-run with
it when you're ready to ingest:

```bash
docker stop fh && docker rm fh
docker run -d --name fh \
  -e GROQ_API_KEY="gsk_..." \
  -e EDGAR_IDENTITY="Morgana morgana@example.com" \
  -p 8000:8000 \
  -v fh_indexes:/app/indexes \
  -v fh_chroma:/app/chroma_db \
  financial-helper:latest
```

## Verify the container is healthy

```bash
curl -s http://localhost:8000/health        # {"status":"ok"}
curl -s http://localhost:8000/status/AAPL   # {"ticker":"AAPL","indexed":false}
```

## Pushing to Docker Hub

1. **Log in** (one time per machine; it stores credentials in Docker's config):

   ```bash
   docker login
   ```

   You'll be prompted for your Docker Hub username and password (or a personal
   access token).

2. **Tag for your Hub account**:

   ```bash
   # Replace <hub-username> with your Docker Hub username;
   # replace <repo-name> with the Hub repo name you want (e.g. financial-helper).
   docker tag financial-helper:latest <hub-username>/<repo-name>:latest
   docker tag financial-helper:latest <hub-username>/<repo-name>:v0.1.0
   ```

3. **Push**:

   ```bash
   docker push <hub-username>/<repo-name>:latest
   docker push <hub-username>/<repo-name>:v0.1.0
   ```

After that, someone else can pull it with:

```bash
docker pull <hub-username>/<repo-name>:latest
```

## Environment reference

| Variable            | Required at start? | Purpose                                             |
|---------------------|--------------------|-----------------------------------------------------|
| `GROQ_API_KEY`      | **yes**            | LLM calls; missing -> container exits with a message|
| `EDGAR_IDENTITY`    | no (ingest needs)  | SEC EDGAR User-Agent: `Name email@domain.com`       |
| `GROQ_MODEL`        | no                 | LLM model name (default `openai/gpt-oss-120b`)      |
| `HOST` / `PORT`     | no                 | Bind address / port (defaults `0.0.0.0:8000`)       |

## Notes for the image author

- The hardcoded key in `backend/llm.py` (`HARDCODED_GROQ_API_KEY`) is left
  empty in this repo; the runtime prefers `GROQ_API_KEY` env, so the image
  depends on that env var and won't silently use a stale key.
- `indexes/` and `chroma_db/` are **not** baked into the image by default.
  They are created on first use and kept in named volumes. If you want to ship
  a pre-built index, `COPY indexes/ indexes/` and `COPY chroma_db/ chroma_db/`
  into the Dockerfile, but that makes the image larger and ties it to a single
  ticker.
- Indexes are per-ticker under `indexes/<TICKER>/`; chroma stores all tickers
  in one collection with ticker metadata filtering. The volume mounts keep both
  across restarts.
