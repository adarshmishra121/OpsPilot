"""Build the FAISS vector index from runbook markdown files."""

import glob
import hashlib
import os

from opspilot.rag.chunking import simple_md_chunk
from opspilot.rag.index import FaissStore

RUNBOOKS_DIR = os.getenv("RUNBOOKS_DIR", "data/raw/runbooks")
OUT_INDEX = os.getenv("VECTOR_INDEX_PATH", "artifacts/vector_index")


def read_md(path: str) -> str:
    """Read a markdown file, returning its full text."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main() -> None:
    """Chunk all runbooks and build a FAISS index."""
    os.makedirs(OUT_INDEX, exist_ok=True)
    embed_model = os.getenv("EMBED_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

    store = FaissStore(OUT_INDEX, embed_model)
    docs = []

    md_files = glob.glob(os.path.join(RUNBOOKS_DIR, "**/*.md"), recursive=True)
    if not md_files:
        raise RuntimeError(f"No .md files found in {RUNBOOKS_DIR}")

    for path in sorted(md_files):
        text = read_md(path)
        title = os.path.splitext(os.path.basename(path))[0]
        chunks = simple_md_chunk(title=title, section="body", text=text)

        for i, chunk_text in enumerate(chunks):
            docs.append({
                "doc_id": f"runbook:{title}:{i}",
                "title": title,
                "section": "body",
                "text": chunk_text,
                "source": "prometheus-operator-runbooks",
                "checksum": hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
            })

    store.build(docs)
    print(f"Built FAISS index at {OUT_INDEX} — {len(docs)} chunks from {len(md_files)} files")


if __name__ == "__main__":
    main()
