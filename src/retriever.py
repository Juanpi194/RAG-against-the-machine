from .chunker import Chunk
import bm25s


def search(query: str, retriever: bm25s.BM25,
           chunks: list[Chunk], k: int) -> list[Chunk]:
    tokenized = bm25s.tokenize([query])
    results = retriever.retrieve(tokenized, k=k)
    result = [chunks[i] for i in results.documents[0]]
    return result
