# ingest_docs.py
# WHAT: Reads a CLIENT's policy documents, chunks them, and loads them into
# a client-specific, persistent Chroma collection.
# WHY (Phase 8 update): Collection creation moved INSIDE ingest_directory,
# named per-client (policies_<client_id>), instead of one shared global
# collection at import time — this is what makes policy RAG safe across
# multiple tenants. Client A's return policy text can never be retrieved
# by Client B's chatbot, because they live in entirely separate collections.

import os
import sys
import chromadb

# WHY: PersistentClient writes the vector index to disk at this path, so
# embeddings survive between server restarts — without this, Chroma would
# re-embed everything from scratch every time you run the app.
chroma_client = chromadb.PersistentClient(path="./chroma_store")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Simple sliding-window chunker, splitting on paragraph boundaries first.

    WHY paragraph-first: policy documents are naturally organized into
    self-contained paragraphs (one topic per paragraph). Splitting on blank
    lines keeps each chunk semantically coherent, rather than cutting a
    sentence in half at an arbitrary character count.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) <= chunk_size:
            current += ("\n\n" + para if current else para)
        else:
            if current:
                chunks.append(current)
            current = para

    if current:
        chunks.append(current)

    return chunks


def ingest_directory(directory: str, client_id: str):
    # WHY: Collection is now created HERE, per call, named after the client —
    # e.g. "policies_client_shoestore" — instead of one shared global
    # collection created at import time. delete-then-create guarantees a
    # clean re-ingest if this client's docs change and you re-run the script.
    collection_name = f"policies_{client_id}"
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass  # WHY: collection may not exist yet on first run — that's fine

    collection = chroma_client.create_collection(collection_name)

    doc_id_counter = 0

    for filename in os.listdir(directory):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(directory, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        print(f"{filename}: {len(chunks)} chunks")

        for chunk in chunks:
            # WHY: ids are scoped with client_id prefix too — avoids any
            # possibility of id collisions if this script is ever changed
            # to write into a shared space in the future.
            collection.add(
                documents=[chunk],
                metadatas=[{"source": filename, "client_id": client_id}],
                ids=[f"{client_id}_doc_{doc_id_counter}"],
            )
            doc_id_counter += 1

    print(f"\nTotal chunks in '{collection_name}': {collection.count()}")


if __name__ == "__main__":
    # WHY: client_id now comes from the command line, e.g.:
    #   uv run python ingest_docs.py client_shoestore
    # This lets you re-run ingestion for ONE specific client without
    # touching any other client's collection.
    if len(sys.argv) < 2:
        print("Usage: uv run python ingest_docs.py <client_id>")
        sys.exit(1)

    client_id = sys.argv[1]
    ingest_directory(f"store_docs/{client_id}", client_id)