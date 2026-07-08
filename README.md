# Financial Filing RAG Assistant

A production-oriented Retrieval-Augmented Generation (RAG) system for querying SEC EDGAR filings using hybrid retrieval, LangGraph orchestration, and Large Language Models.

The application is designed for financial analysts and enterprise users who frequently work with SEC filings and need fast, accurate, and citation-backed answers without manually searching hundreds of pages of annual reports.

---

# Overview

Instead of asking an LLM directly, the system first retrieves the most relevant sections from SEC filings and then generates answers only from those retrieved documents.

This significantly reduces hallucinations while ensuring responses remain grounded in official SEC filings.

---

# Architecture

```
                   User
                     │
                     ▼
           Enter Company Ticker
                     │
                     ▼
          Check Local Company Index
             │                 │
         Exists            Doesn't Exist
             │                 │
             │          Download from EDGAR
             │                 │
             │         Parse & Clean Filing
             │                 │
             │      Section-aware Chunking
             │                 │
             │     Hybrid Index Construction
             │
             ▼
        Chat Interface Enabled
                     │
                     ▼
             Query Understanding
                     │
                     ▼
            Hybrid Retrieval Engine
         ┌────────────┴────────────┐
         │                         │
       BM25                  Dense Search
         │                         │
      Top-K                    Top-K
         └──────────┬──────────────┘
                    │
             Merge Results
                    │
              Cross Encoder
                Reranker
                    │
                 Top Chunks
                    │
                    ▼
            Large Language Model
                    │
                    ▼
        Citation + Confidence Score
                    │
                    ▼
                 Final Answer
```

---

# System Pipeline

## 1. EDGAR Ingestion

The user provides a company ticker.

The system automatically downloads the latest SEC filing directly from EDGAR using the `edgartools` library.

Supported filings include:

- 10-K
- 10-Q
- 8-K (future)
- DEF 14A (future)

---

## 2. Cleaning

Raw SEC filings contain:

- excessive whitespace
- formatting artifacts
- page separators
- duplicated blank lines
- inline XBRL noise

The cleaning pipeline removes unnecessary formatting while preserving tables and financial statements.

---

## 3. Section-aware Chunking

Unlike traditional RAG systems that split documents every *N* characters, this project preserves the logical structure of SEC filings.

Chunks are created according to filing sections such as:

```
Item 1. Business

Item 1A. Risk Factors

Item 7. Management Discussion

Item 8. Financial Statements
```

Each chunk stores metadata including:

- ticker
- company
- filing type
- filing date
- section
- chunk index

This allows precise retrieval and citation generation.

---

## 4. Hybrid Search

The system combines two retrieval methods.

### Sparse Retrieval (BM25)

Lexical search that excels at:

- exact financial terminology
- company-specific names
- accounting terminology
- legal language

Examples:

- deferred tax assets
- goodwill impairment
- inventory valuation

---

### Dense Vector Retrieval

Sentence embeddings generated using

```
BAAI/bge-small-en-v1.5
```

Stored in ChromaDB for semantic similarity search.

Dense retrieval excels at finding conceptually similar information even when wording differs.

---

### Hybrid Retrieval

```
Query

        │

 ┌──────┴───────┐
 │              │
BM25         Dense Search

 │              │
Top 20       Top 20

 └──────┬───────┘

   Merge Results

        │

 Remove Duplicates

        │

   Cross Encoder

        │

     Top Chunks

        │

       LLM
```

Combining sparse and dense retrieval improves recall while maintaining precision.

---

# LangGraph Workflow

The application uses LangGraph to orchestrate the retrieval pipeline.

```
START

   │

Query Understanding

   │

Retrieve

   │

Rerank

   │

Generate Answer

   │

Citation Builder

   │

Confidence Score

   │

END
```

Each stage is modular and independently replaceable.

---

# Technologies Used

## Retrieval

- BM25
- ChromaDB
- Sentence Transformers

---

## Embeddings

```
BAAI/bge-small-en-v1.5
```

---

## LLM

Supports any LangChain-compatible model.

Examples:

- Groq
- OpenAI
- Gemini
- Ollama

---

## Framework

- LangGraph
- LangChain

---

## Data Source

- SEC EDGAR

---

## Language

Python

---

# Features

- Automatic SEC filing download
- Section-aware document chunking
- Metadata-aware retrieval
- Hybrid search
- Persistent vector database
- Persistent BM25 index
- Company-specific indexes
- Semantic retrieval
- Citation-ready responses
- Modular LangGraph pipeline
- Batch embedding generation
- Production-oriented architecture

---

# Project Structure

```
backend/

│
├── get_files.py
├── section_chunker.py
├── hybrid_index.py
├── hybrid_retriever.py
├── graph.py
├── chat.py
├── prompts.py
├── llm.py
├── state.py
│
├── chroma_db/
│
└── indexes/
      ├── AAPL/
      ├── MSFT/
      └── ...
```

---

# Why Not a Traditional RAG?

Most tutorial RAG systems:

- split every 500–1000 characters
- use only vector search
- lose document structure
- retrieve irrelevant context
- cannot distinguish sections
- provide weak citations

This project instead:

- preserves SEC document hierarchy
- performs hybrid retrieval
- stores filing metadata
- separates ingestion from serving
- supports persistent indexing
- enables company-specific retrieval
- is designed for enterprise-scale financial document search

---

# Production Design

The ingestion pipeline is completely separated from the chat system.

## Ingestion

```
Download

↓

Clean

↓

Chunk

↓

BM25

↓

Dense Embeddings

↓

Persist Index
```

Runs only once per company.

---

## Serving

```
Load BM25

↓

Load Chroma

↓

Retrieve

↓

Generate

↓

Answer
```

The chatbot never re-downloads or re-embeds documents.

---

# Future Improvements

- Cross-Encoder reranking
- Multi-filing retrieval (10-K + 10-Q + 8-K)
- Financial table reasoning
- Streaming responses
- Conversation memory
- Multi-company comparison
- Incremental index updates
- PDF report generation
- SEC citation highlighting
- Real-time filing monitoring

---

# Motivation

Financial analysts often spend significant time locating information across lengthy SEC filings. This project aims to reduce that effort by combining modern retrieval techniques with LLMs to provide accurate, context-grounded answers backed by official filings.

The architecture is designed to be modular, scalable, and suitable as a foundation for enterprise document intelligence systems.
