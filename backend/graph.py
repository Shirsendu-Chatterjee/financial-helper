import subprocess
from pathlib import Path
from hybrid_retriever import HybridRetriever
from prompt import SYSTEM_PROMPT
from llm import llm


def ensure_indexed(ticker: str):

    index_dir = Path("indexes") / ticker

    if (index_dir / "chunks.pkl").exists():
        print(f"Index for {ticker} found, skipping fetch.")
        return True

    print(f"Index for {ticker} not found. Running get_files.py to fetch and index.")

    # Run the existing script which prompts for the ticker
    proc = subprocess.run(
        ["python", "backend/get_files.py"],
        input=ticker + "\n",
        text=True
    )

    return proc.returncode == 0


def build_context(retrieved_docs, max_chunks=5):

    parts = []

    for d in retrieved_docs[:max_chunks]:
        parts.append(f"Section: {d.get('section')}\nText:\n{d.get('text')}\n---\nSource: {d.get('ticker')} | chunk_id={d.get('chunk_id')}")

    return "\n\n".join(parts)


def ask_llm(system_prompt: str, context: str, question: str):

    user_msg = f"CONTEXT:\n{context}\n\nQuestion: {question}\nAnswer:" 

    try:
        # ChatGroq expects a list of messages; use `invoke` as documented
        messages = [
            ("system", system_prompt),
            ("human", user_msg),
        ]

        resp = llm.invoke(messages)

        # `invoke` returns an AIMessage-like object; try to get `.content`
        try:
            return resp.content
        except Exception:
            return str(resp)

    except Exception as e:
        return f"LLM invocation failed: {e}"


def main():

    ticker = input("Enter company ticker or CIK: ").strip().upper()

    ok = ensure_indexed(ticker)

    if not ok:
        print("Failed to fetch/index filings. Exiting.")
        return

    retriever = HybridRetriever(ticker)

    print("\nReady. Ask questions (type 'exit' to quit). Answers will be produced using RAG + LLM.")

    while True:

        q = input("\nQuestion: ")

        if q.lower() in ("exit", "quit"):
            break

        docs = retriever.search(q)

        context = build_context(docs, max_chunks=5)

        answer = ask_llm(SYSTEM_PROMPT, context, q)

        print("\n" + "="*80)
        print("Answer:\n")
        print(answer)
        print("\nSources:")

        for d in docs[:5]:
            print(f"- {d.get('ticker')} | section={d.get('section')} | chunk_id={d.get('chunk_id')}")


if __name__ == "__main__":
    main()
