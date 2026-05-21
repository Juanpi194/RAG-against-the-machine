from pathlib import Path
import bm25s
import json
from tqdm import tqdm

from .chunker import chunk_file, Chunk


def index(repo_path: str, save_dir: str, max_chunk_size: int = 2000) -> None:
    """
    Index a repository by chunking files and building a BM25 index.

    The indexer processes Python and Markdown files, creates an optimized
    BM25 retriever, and saves both the index and the chunk metadata to disk.

    Args:
        repo_path: The root directory of the repository to index.
        save_dir: The directory where the index and chunks will be saved.
        max_chunk_size: The maximum character count for each chunk.
    """
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    VALID_EXTENSIONS = {".py", ".md", ".rst", ".txt"}
    files = [f for f in Path(repo_path).rglob("*") if
             f.suffix in VALID_EXTENSIONS and f.is_file()]

    chunks: list[Chunk] = []
    for file in tqdm(files, desc="Indexing files"):
        chunks.extend(chunk_file(str(file), max_chunk_size))

    corpus = [chunk.content for chunk in chunks]
    tokenized = bm25s.tokenize(corpus)
    retriever = bm25s.BM25()
    retriever.index(tokenized)
    retriever.save(save_dir)

    chunks_path = Path(save_dir) / "chunks.json"
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump([chunk.model_dump() for chunk in chunks], f)


def load_index(save_dir: str) -> tuple[bm25s.BM25, list[Chunk]]:
    """
    Load a previously saved BM25 index and its corresponding chunks.

    Args:
        save_dir: The directory containing 'chunks.json' and BM25 index files.

    Returns:
        A tuple containing (BM25 retriever instance, list of Chunk objects).
    """
    retriever = bm25s.BM25.load(save_dir)
    chunks_path = Path(save_dir) / "chunks.json"
    with open(chunks_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    chunks = [Chunk(**chunk) for chunk in data]
    return (retriever, chunks)
