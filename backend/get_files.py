import os
import re
from typing import Optional

from edgar import Company
from edgar.core import set_identity
from .section_chunker import SectionChunker
from .hybrid_index import HybridIndexer


def fetch_and_index(
    ticker: str,
    identity_email: Optional[str] = None,
    form: str = "10-K",
    batch_size: int = 32,
) -> dict:
    """Download the latest SEC filing for *ticker*, clean it,
    chunk it section-aware, and build both the BM25 + Chroma
    indexes. Raises on failure so callers can surface the error."""

    identity_email = (
        identity_email
        or os.environ.get("EDGAR_IDENTITY_EMAIL")
        or os.environ.get("EDGAR_IDENTITY")
        or ""
    )

    if identity_email:
        set_identity(identity_email)

    ticker = ticker.strip().upper()
    company = Company(ticker)

    # Get the latest filing of the requested form
    filings = company.get_filings(form=form)
    filing = filings.latest()
    text = filing.text()

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove trailing spaces
    text = re.sub(r"[ \t]+", " ", text)

    text = text.strip()
    chunker = SectionChunker()

    chunks = chunker.create_chunks(
        text=text,
        ticker=ticker,
        company=filing.company,
        filing_type=filing.form,
        filing_date=str(filing.filing_date),
        cik=company.cik,
    )

    indexer = HybridIndexer()

    indexer.build(
        ticker=ticker,
        chunks=chunks,
        batch_size=batch_size,
    )

    return {
        "ticker": ticker,
        "company": str(filing.company),
        "filing_type": filing.form,
        "filing_date": str(filing.filing_date),
        "chunks": len(chunks),
    }
