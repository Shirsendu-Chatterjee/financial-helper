from edgar import Company, set_identity
import re
from section_chunker import SectionChunker
from hybrid_index import HybridIndexer
from hybrid_retriever import HybridRetriever


# Required by SEC
set_identity("shirsendu chattshirsendu05@gmai.com")

ticker = input("Enter company ticker or CIK: ").upper()

company = Company(ticker)

# Get latest 10-K
filing = company.get_filings(form="10-K").latest()
text = filing.text()


# Save filing locally


# Remove excessive blank lines
text = re.sub(r"\n{3,}", "\n\n", text)

# Remove trailing spaces
text = re.sub(r"[ \t]+", " ", text)

text = text.strip()
print(text)

print("Done!\n\n\n")




chunker = SectionChunker()

chunks = chunker.create_chunks(
    text=text,
    ticker=ticker,
    company=filing.company,
    filing_type=filing.form,
    filing_date=str(filing.filing_date),
    cik=company.cik
)

print("Chunks:", len(chunks))

indexer = HybridIndexer()

indexer.build(
    ticker=ticker,
    chunks=chunks,
    batch_size=32
)
print("doneeee")





# retriever = HybridRetriever(chunks)

# while True:

#     query = input("\nAsk a question ('exit' to quit): ")

#     if query.lower() == "exit":
#         break

#     results = retriever.search(query)

#     print("\n" + "="*100)

#     for i, chunk in enumerate(results[:5], 1):

#         print(f"\nResult {i}")
#         print(f"Company : {chunk['company']}")
#         print(f"Section : {chunk['section']}")
#         print(f"Chunk ID: {chunk['chunk_id']}")
#         print("-"*100)
#         print(chunk["text"][:800])
#         print("-"*100)

