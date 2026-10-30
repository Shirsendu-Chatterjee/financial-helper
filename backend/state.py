from typing import TypedDict, List


class GraphState(TypedDict):
    ticker: str
    question: str
    retrieved_docs: List[dict]
    context: str
    answer: str