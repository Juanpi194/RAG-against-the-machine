import json
from pathlib import Path
from tqdm import tqdm

from .models import RagDataset, MinimalSource, MinimalSearchResults
from .models import StudentSearchResults, MinimalAnswer
from .models import StudentSearchResultsAndAnswer, AnsweredQuestion
from .chunker import MAX_CHUNK_SIZE, Chunk
from .indexer import index as index_repo, load_index
from .retriever import search as retriever_search
from .generator import load_model, generate
from .evaluator import recall_at_k
from .utils import is_file_available, print_error


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
        retriever, chunks = load_index(index_dir)
        if not is_file_available(dataset_path):
            print_error(f"File '{dataset_path}' not found", exit_program=False)
            return
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        dataset = RagDataset(**data)
        search_results: list[MinimalSearchResults] = []
        for question in tqdm(dataset.rag_questions, desc="Searching questions"):
            result_chunks = retriever_search(question.question, retriever, chunks, k)

            sources = [MinimalSource(file_path=chunk.file_path,
                                    first_character_index=chunk.first_character_index,
                                    last_character_index=chunk.last_character_index)
                    for chunk in result_chunks]

            search_results.append(MinimalSearchResults(
                question_id=question.question_id,
                question=question.question,
                retrieved_sources=sources
            ))
        path = Path(save_directory)
        path.mkdir(parents=True, exist_ok=True)
        student_results = StudentSearchResults(search_results=search_results, k=k)
        output_path = path / Path(dataset_path).name
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(student_results.model_dump(), f)
            

    @staticmethod
    def answer(query: str, k: int = 10, index_dir: str = "data/processed",
               model_name: str = "Qwen/Qwen3-0.6B") -> None:
        retriever, chunks = load_index(index_dir)
        result_chunks = retriever_search(query, retriever, chunks, k)
        model, tokenizer = load_model(model_name)
        answer = generate(query, result_chunks, model, tokenizer)
        print(answer)

    @staticmethod
    def answer_dataset(student_search_results_path: str,
                       save_directory: str, model_name: str = "Qwen/Qwen3-0.6B",
                       index_dir: str = "data/processed") -> None:
        with open(student_search_results_path, "r") as f:
            search_result = StudentSearchResults.model_validate(json.load(f))
        retriever, chunks = load_index(index_dir)
        model, tokenizer = load_model(model_name)
        answers: list[MinimalAnswer] = []
        for result in tqdm(search_result.search_results, desc="Generating answers"):
            result_chunks: list[Chunk] = []
            for chunk in chunks:
                for source in result.retrieved_sources:
                    if (chunk.file_path == source.file_path and
                            chunk.first_character_index == source.first_character_index):
                        result_chunks.append(chunk)
                        break
            answer = generate(result.question, result_chunks, model, tokenizer)
            answers.append(MinimalAnswer(question_id=result.question_id,
                                        question=result.question,
                                        retrieved_sources=result.retrieved_sources,
                                        answer=answer
                                        ))
        search_result_and_answer = StudentSearchResultsAndAnswer(
            search_results=answers,
            k=search_result.k)
        path = Path(save_directory)
        output_path = path / Path(student_search_results_path).name
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(search_result_and_answer.model_dump(), f)

    @staticmethod
    def evaluate(student_answer_path: str, dataset_path: str,
                 k: int = 10) -> None:
        if not is_file_available(dataset_path):
            print_error(f"File '{dataset_path}' not found")
            return
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = RagDataset.model_validate(json.load(f))

        questions = [q for q in dataset.rag_questions 
                    if isinstance(q, AnsweredQuestion)]

        if not is_file_available(student_answer_path):
            print_error(f"File '{student_answer_path}' not found")
            return
        with open(student_answer_path, "r") as f:
            student_answer = StudentSearchResults.model_validate(json.load(f))

        result = recall_at_k(questions, student_answer)
        print(result)
