from .indexer import index

if __name__ == "__main__":
    index("vllm-0.10.1", "data/processed", max_chunk_size=2000)
