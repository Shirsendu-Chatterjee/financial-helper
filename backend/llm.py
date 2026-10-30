import os

from langchain_groq import ChatGroq

# ------------------------------------------------------------------
# HARDCODED GROQ API KEY (temporary — remove this and use the
# GROQ_API_KEY environment variable before committing/sharing).
# ------------------------------------------------------------------
HARDCODED_GROQ_API_KEY = "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"


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
