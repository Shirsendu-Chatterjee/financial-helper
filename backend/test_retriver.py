from hybrid_retriever import HybridRetriever

ticker = input("Ticker: ").strip().upper()

retriever = HybridRetriever(ticker)

while True:

	query = input("\nQuery ('exit' to quit): ")

	if query.lower() == "exit":
		break

	results = retriever.search(query)

	print("\n" + "="*100)

	for i, chunk in enumerate(results[:5], 1):

		print(f"\nResult {i}")
		print(f"Company : {chunk.get('company')}")
		print(f"Section : {chunk.get('section')}")
		print(f"Chunk ID: {chunk.get('chunk_id')}")
		print("-"*100)
		print(chunk["text"][:800])
		print("-"*100)