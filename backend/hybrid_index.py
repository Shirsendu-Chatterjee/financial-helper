from pathlib import Path
import pickle

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


class HybridIndexer:

    def __init__(self):

        self.embedding_model = SentenceTransformer(
            "BAAI/bge-small-en-v1.5"
        )

        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name="edgar_filings"
        )

    def build(self, ticker, chunks, batch_size=32):

        # ------------------------------------------------ #
        # Create folder for this company's indexes
        # ------------------------------------------------ #

        index_dir = Path("indexes") / ticker
        index_dir.mkdir(parents=True, exist_ok=True)

        # ------------------------------------------------ #
        # BM25
        # ------------------------------------------------ #

        corpus = [
            chunk["text"].split()
            for chunk in chunks
        ]

        with open(index_dir / "bm25_corpus.pkl", "wb") as f:
            pickle.dump(corpus, f)

        with open(index_dir / "chunks.pkl", "wb") as f:
            pickle.dump(chunks, f)

        print("✓ BM25 Saved")

        # ------------------------------------------------ #
        # Dense Embeddings
        # ------------------------------------------------ #

        total = len(chunks)

        for start in range(0, total, batch_size):

            end = min(start + batch_size, total)

            batch = chunks[start:end]

            print(f"Embedding {start}-{end} / {total}")

            embeddings = self.embedding_model.encode(
                [c["text"] for c in batch],
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=False
            )

            ids = [

                f"{c['ticker']}_"
                f"{c['filing_type']}_"
                f"{c['filing_date']}_"
                f"{c['chunk_id']}"

                for c in batch
            ]

            self.collection.upsert(

                ids=ids,

                documents=[
                    c["text"]
                    for c in batch
                ],

                embeddings=embeddings.tolist(),

                metadatas=[

                    {

                        "ticker": c["ticker"],

                        "company": c["company"],

                        "cik": c["cik"],

                        "section": c["section"],

                        "filing_type": c["filing_type"],

                        "filing_date": c["filing_date"],

                        "chunk_id": c["chunk_id"],

                        "chunk_index": c["chunk_index"]

                    }

                    for c in batch

                ]

            )

        print("✓ Chroma Updated")
        print("✓ Indexing Finished")