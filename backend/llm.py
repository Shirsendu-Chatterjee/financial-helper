import os

from langchain_groq import ChatGroq

# ------------------------------------------------------------------
# HARDCODED GROQ API KEY (DEV ONLY).
#
# For local dev you can paste your key here so the server runs without
# setting GROQ_API_KEY in the shell. This file is committed, so never
# leave a real key here in a shared / shipped checkout.
#
# Runtime already prefers the env var over this constant, so the Docker
# image simply needs -e GROQ_API_KEY=<key> and this can stay empty.
#
# Before pushing to GitHub or building the Docker image:
#   - leave this empty (as below), OR
#   - use a .env file that is gitignored.
# ------------------------------------------------------------------
HARDCODED_GROQ_API_KEY = ""


def get_llm():
    api_key = os.environ.get("GROQ_API_KEY") or HARDCODED_GROQ_API_KEY
    if not api_key:
        raise RuntimeError(
            "Set GROQ_API_KEY (env var) or HARDCODED_GROQ_API_KEY in backend/llm.py"
        )
    return ChatGroq(
        model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
        api_key=api_key,
        temperature=0,
    )


def _get_llm():
    """Lazily construct the LLM, only when needed."""
    global _llm
    if _llm is None:
        _llm = get_llm()
    return _llm


_llm = None


class _LazyLlm:
    def invoke(self, messages):
        return _get_llm().invoke(messages)


llm = _LazyLlm()
