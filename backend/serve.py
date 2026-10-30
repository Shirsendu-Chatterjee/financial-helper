import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .state import GraphState
from .graph import app
from .get_files import fetch_and_index

logger = logging.getLogger(__name__)

INDEX_DIR = Path("indexes")
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AskRequest(BaseModel):
    question: str
    identity_email: Optional[str] = None


class Source(BaseModel):
    ticker: str
    company: Optional[str] = None
    section: str
    chunk_id: int
    text_preview: Optional[str] = None


class AskResponse(BaseModel):
    ticker: str
    answer: str
    sources: list[Source]


def _index_exists(ticker: str) -> bool:
    index_dir = INDEX_DIR / ticker
    return (index_dir / "chunks.pkl").exists()


def _run_ingest(ticker: str, identity_email: Optional[str]) -> dict:
    logger.info("Ingesting ticker=%s identity=%s", ticker, identity_email)
    return fetch_and_index(
        ticker=ticker,
        identity_email=identity_email,
    )


def _run_query(ticker: str, question: str) -> dict:
    logger.info("Querying ticker=%s question=%s", ticker, question)

    result = app.invoke(
        {
            "ticker": ticker,
            "question": question,
            "retrieved_docs": [],
            "context": "",
            "answer": "",
        }
    )

    # Ensure every invoke result carries ticker back (compat layer).
    result.setdefault("ticker", ticker)

    return result


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure working directories exist on startup.
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Working directories ready: %s", INDEX_DIR)
    yield


api = FastAPI(
    title="Financial Filing RAG Assistant",
    lifespan=lifespan,
)


@api.get("/health")
def health():
    return {"status": "ok"}


@api.get("/status/{ticker}")
def status(ticker: str):
    ticker = ticker.strip().upper()
    return {
        "ticker": ticker,
        "indexed": _index_exists(ticker),
    }


@api.post("/ingest/{ticker}", response_model=dict)
def ingest(ticker: str, body: AskRequest):
    ticker = ticker.strip().upper()
    try:
        result = _run_ingest(
            ticker=ticker,
            identity_email=body.identity_email,
        )
        return result
    except Exception as exc:
        logger.exception("Ingestion failed for ticker=%s", ticker)
        raise HTTPException(
            status_code=500, detail=f"Ingestion failed: {exc}"
        ) from None


@api.post("/ask/{ticker}", response_model=AskResponse)
def ask(ticker: str, body: AskRequest):
    ticker = ticker.strip().upper()

    if not body.question.strip():
        raise HTTPException(
            status_code=400, detail="question must not be empty"
        )

    # Ensure the index exists before querying. The graph's ensure_index node
    # also does this, but triggering it here keeps the HTTP flow explicit and
    # lets the UI wait on /status/{ticker} if it wants to.
    if not _index_exists(ticker):
        _run_ingest(
            ticker=ticker,
            identity_email=body.identity_email,
        )

    result = _run_query(ticker, body.question)

    answer = result.get("answer", "").strip()
    docs = result.get("retrieved_docs")
    if docs is None:
        docs = []

    sources: list[Source] = []
    for d in docs[:5]:
        sources.append(
            Source(
                ticker=d.get("ticker", ticker),
                company=d.get("company"),
                section=d.get("section", ""),
                chunk_id=d.get("chunk_id"),
                text_preview=(d.get("text") or "")[:500],
            )
        )

    return AskResponse(
        ticker=ticker,
        answer=answer,
        sources=sources,
    )


# Serve the static webpage (index.html / app.js) AFTER all API routes,
# so /, /index.html and /app.js come from this same server (same origin
# as the API -> no CORS needed). Override only for other routes.
api.mount(
    "/",
    StaticFiles(directory=PROJECT_ROOT, html=True),
    name="static",
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.serve:api",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        log_level=os.environ.get("LOG_LEVEL", "info"),
    )
