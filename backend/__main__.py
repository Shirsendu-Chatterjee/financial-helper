import os
import sys


def _interactive_get_files() -> None:
    from backend.get_files import fetch_and_index

    ticker = input("Enter company ticker or CIK: ").upper()
    result = fetch_and_index(
        ticker=ticker,
        identity_email=os.environ.get("EDGAR_IDENTITY_EMAIL"),
    )
    print(
        f"Indexed {result['company']} "
        f"({result['filing_type']} "
        f"{result['filing_date']}): "
        f"{result['chunks']} chunks"
    )


def _interactive_graph() -> None:
    from backend.graph import app

    ticker = input("Ticker: ").strip().upper()
    question = input("\nQuestion: ")

    while True:
        if question == "exit":
            break

        result = app.invoke(
            {
                "ticker": ticker,
                "question": question,
                "retrieved_docs": [],
                "context": "",
                "answer": "",
            }
        )
        result.setdefault("ticker", ticker)

        print("\nANSWER:")
        print(result["answer"])
        print("\nSOURCES:")
        for d in result["retrieved_docs"][:5]:
            print(d["ticker"], d["section"], d["chunk_id"])

        question = input("\nQuestion: ")


def _interactive_cli() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "get_files"

    if mode == "get_files":
        _interactive_get_files()
    elif mode == "graph":
        _interactive_graph()
    else:
        print("Usage: python -m backend <get_files|graph>")


if __name__ == "__main__":
    _interactive_cli()
