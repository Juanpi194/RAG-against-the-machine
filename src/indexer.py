from pathlib import Path
import bm25s
import json
import dataclasses

from .chunker import chunk_file, Chunk


def index(repo_path: str, save_dir: str, max_chunk_size: int = 2000) -> None:
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    VALID_EXTENSIONS = {".py", ".md", ".rst", ".txt"}
    files = [f for f in Path(repo_path).rglob("*") if
             f.suffix in VALID_EXTENSIONS and f.is_file()]

    chunks: list[Chunk] = []
    for file in files:
        chunks.extend(chunk_file(str(file), max_chunk_size))

    corpus = [chunk.content for chunk in chunks]
    tokenized = bm25s.tokenize(corpus)
    retriever = bm25s.BM25()
    retriever.index(tokenized)
    retriever.save(save_dir)

    chunks_path = Path(save_dir) / "chunks.json"
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump([dataclasses.asdict(chunk) for chunk in chunks], f)


def load_index(save_dir: str) -> tuple[bm25s.BM25, list[Chunk]]:
    retriever = bm25s.BM25.load(save_dir)
    chunks_path = Path(save_dir) / "chunks.json"
    with open(chunks_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    chunks = [Chunk(**chunk) for chunk in data]
    return (retriever, chunks)
