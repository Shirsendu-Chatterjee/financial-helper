from langchain_groq import ChatGroq
import os

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key="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",
    temperature=0
)

response = llm.invoke("Explain RAG in simple terms")

print(response.content)
