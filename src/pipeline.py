import json

from .models import RagDataset
from .chunker import MAX_CHUNK_SIZE
from .indexer import index as index_repo, load_index
from .retriever import search as retriever_search


class Pipeline:

    @staticmethod
    def index(repo_path: str, save_dir: str,
              max_chunk_size: int = MAX_CHUNK_SIZE) -> None:
        index_repo(repo_path, save_dir, max_chunk_size)

    @staticmethod
    def search(query: str, k: int = 10,
               save_dir: str = "data/processed") -> None:
        retriever, chunks = load_index(save_dir)
        results = retriever_search(query, retriever, chunks, k)
        for result in results:
            print(result.file_path, result.first_character_index, result.last_character_index)

    @staticmethod
    def search_dataset(dataset_path: str, save_directory: str,
                       k: int = 10, index_dir: str = "data/processed") -> None:
        # TODO: Finish this function
        retriever, chunks = load_index(index_dir)
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        dataset = RagDataset(**data)

    @staticmethod
    def answer(query: str, k: int = 10) -> None:
        ...
    
    @staticmethod
    def answer_dataset(student_search_results_path: str,
                       save_directory: str) -> None:
        ...

    @staticmethod
    def evaluate(student_answer_path: str, dataset_path: str,
                 k: int = 10) -> None:
        ...
