# test_retrieval.py
# WHAT: Standalone script to sanity-check retrieval quality BEFORE wiring
# it into the agent — same debugging philosophy as test_agent.py in Phase 2.
# WHY: If retrieval quality is bad, the bot will confidently answer with the
# WRONG policy chunk — a subtler, more dangerous failure than a crash, since
# it looks like a normal working answer. Always check this in isolation first.

import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_store")
collection = chroma_client.get_collection("store_policies")

test_queries = [
    "Do you ship internationally?",
    "What's your return policy?",
    "My shoes have a defect, what do I do?",
    "Can I return a final sale item?",
]

for query in test_queries:
    print(f"\n=== Query: {query} ===")
    results = collection.query(query_texts=[query], n_results=2)

    # WHY: Print BOTH the matched text and its source file + distance score —
    # distance tells you HOW confident the match is; source tells you WHICH
    # policy doc it pulled from, both critical for judging retrieval quality.
    for doc, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        print(f"[{meta['source']}] (distance: {distance:.3f})")
        print(doc[:150] + "...")
        print()