"""Simple markdown chunker with configurable size and overlap."""

from typing import List


def simple_md_chunk(
    title: str,
    section: str,
    text: str,
    chunk_size: int = 900,
    overlap: int = 150,
) -> List[str]:
    """Split text into overlapping word-boundary chunks.

    Each chunk is prefixed with the document title and section name
    so the embedding captures the source context.
    """
    prefix = f"{title} | {section}\n"
    words = text.split()
    chunks: List[str] = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text = prefix + " ".join(chunk_words)
        chunks.append(chunk_text)
        start += chunk_size - overlap

    return chunks if chunks else [prefix + text]
