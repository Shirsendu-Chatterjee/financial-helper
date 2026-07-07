import pickle
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


class HybridRetriever:

    def __init__(self, ticker):

        self.ticker = ticker

        # ---------------- Load BM25 ---------------- #

        index_dir = Path("indexes") / ticker

        with open(index_dir / "bm25_corpus.pkl", "rb") as f:
            corpus = pickle.load(f)

        with open(index_dir / "chunks.pkl", "rb") as f:
            self.documents = pickle.load(f)

        self.bm25 = BM25Okapi(corpus)

        print("✓ BM25 Loaded")

        # ---------------- Chroma ---------------- #

        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        self.collection = self.client.get_collection(
            "edgar_filings"
        )

        # ---------------- Embedding Model ---------------- #

        self.embedding_model = SentenceTransformer(
            "BAAI/bge-small-en-v1.5"
        )

        print("✓ Retriever Ready")

    def bm25_search(self, query, k=20):

        scores = self.bm25.get_scores(query.split())

        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            self.documents[idx]
            for idx, _ in ranked[:k]
        ]

    def dense_search(self, query, k=20):

        embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True
        ).tolist()

        results = self.collection.query(

            query_embeddings=[embedding],

            n_results=k,

            where={
                "ticker": self.ticker
            }

        )

        docs = []

        for document, metadata in zip(
            results["documents"][0],
            results["metadatas"][0]
        ):

            docs.append({
                "text": document,
                **metadata
            })

        return docs

    def search(self, query):

        bm25_results = self.bm25_search(query)

        dense_results = self.dense_search(query)

        merged = {}

        # BM25 first
        for doc in bm25_results:

            key = (
                doc["ticker"],
                doc["chunk_id"]
            )

            merged[key] = doc

        # Dense next
        for doc in dense_results:

            key = (
                doc["ticker"],
                doc["chunk_id"]
            )

            if key not in merged:
                merged[key] = doc

        return list(merged.values())