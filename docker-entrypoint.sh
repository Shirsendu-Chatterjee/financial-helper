#!/bin/sh
set -e

if [ -z "${GROQ_API_KEY}" ]; then
  echo "ERROR: GROQ_API_KEY is not set."
  echo "Pass it at runtime, e.g.:"
  echo "  docker run -e GROQ_API_KEY=<key> ..."
  exit 1
fi

# EDGAR_IDENTITY is optional at startup (only required when an ingest runs).
if [ -n "${EDGAR_IDENTITY}" ]; then
  echo "Using EDGAR_IDENTITY supplied at runtime."
else
  echo "NOTE: EDGAR_IDENTITY is not set. Ingest will fail until you supply it."
fi

# Run the server. PORT defaults to 8000 inside the app.
exec .venv/bin/python -m backend.serve
