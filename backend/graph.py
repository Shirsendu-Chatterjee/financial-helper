from pathlib import Path
import subprocess

from langgraph.graph import StateGraph, END

from hybrid_retriever import HybridRetriever
from prompt import SYSTEM_PROMPT
from llm import llm

from state import GraphState



# -----------------------------
# NODE 1
# -----------------------------

def ensure_index_node(state: GraphState):

    ticker = state["ticker"]

    index_dir = Path("indexes") / ticker


    if (index_dir / "chunks.pkl").exists():

        print("Index exists")

        return state


    print("Creating index...")


    proc = subprocess.run(
        [
            "python",
            "backend/get_files.py"
        ],
        input=ticker+"\n",
        text=True
    )


    if proc.returncode != 0:
        raise Exception(
            "Index creation failed"
        )


    return state




# -----------------------------
# NODE 2
# -----------------------------

def retrieve_node(state: GraphState):

    ticker = state["ticker"]

    query = state["question"]


    retriever = HybridRetriever(ticker)


    docs = retriever.search(query)


    return {

        "retrieved_docs": docs

    }




# -----------------------------
# NODE 3
# -----------------------------

def context_node(state: GraphState):

    docs = state["retrieved_docs"]


    parts=[]


    for d in docs[:5]:

        parts.append(
            f"""
Section:
{d.get('section')}

Text:
{d.get('text')}

Source:
{d.get('ticker')}
chunk_id:
{d.get('chunk_id')}
"""
        )


    return {

        "context":"\n\n".join(parts)

    }




# -----------------------------
# NODE 4
# -----------------------------

def llm_node(state: GraphState):


    messages=[

        (
            "system",
            SYSTEM_PROMPT
        ),

        (
            "human",
            f"""
CONTEXT:

{state['context']}


QUESTION:

{state['question']}


Answer:
"""
        )

    ]


    response = llm.invoke(messages)


    return {

        "answer":response.content

    }



# -----------------------------
# BUILD GRAPH
# -----------------------------


workflow = StateGraph(GraphState)



workflow.add_node(
    "ensure_index",
    ensure_index_node
)


workflow.add_node(
    "retrieve",
    retrieve_node
)


workflow.add_node(
    "context",
    context_node
)


workflow.add_node(
    "generate",
    llm_node
)



workflow.set_entry_point(
    "ensure_index"
)


workflow.add_edge(
    "ensure_index",
    "retrieve"
)


workflow.add_edge(
    "retrieve",
    "context"
)


workflow.add_edge(
    "context",
    "generate"
)


workflow.add_edge(
    "generate",
    END
)



app = workflow.compile()




# -----------------------------
# RUN
# -----------------------------


if __name__=="__main__":


    ticker=input(
        "Ticker: "
    ).strip().upper()


    while True:


        question=input(
            "\nQuestion: "
        )


        if question=="exit":
            break



        result=app.invoke(
            {

                "ticker":ticker,

                "question":question,

                "retrieved_docs":[],

                "context":"",

                "answer":""

            }
        )


        print("\nANSWER:")
        print(
            result["answer"]
        )


        print("\nSOURCES:")

        for d in result["retrieved_docs"][:5]:

            print(
                d["ticker"],
                d["section"],
                d["chunk_id"]
            )