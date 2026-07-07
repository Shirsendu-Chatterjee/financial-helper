from langchain_groq import ChatGroq
import os

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key="",
    temperature=0
)

response = llm.invoke("Explain RAG in simple terms")

print(response.content)