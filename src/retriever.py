from .chunker import Chunk
import bm25s


def search(query: str, retriever: bm25s.BM25,
           chunks: list[Chunk], k: int) -> list[Chunk]:
    """
    Perform a BM25 similarity search for a query against an indexed corpus.

    Args:
        query: The natural language search query.
        retriever: A loaded and indexed BM25 retriever.
        chunks: The list of original Chunk objects corresponding to the index.
        k: The number of top-ranking results to return.

    Returns:
        A list of the k most relevant Chunk objects.
    """
    tokenized = bm25s.tokenize([query])
    results = retriever.retrieve(tokenized, k=k)
    result = [chunks[i] for i in results.documents[0]]
    return result
