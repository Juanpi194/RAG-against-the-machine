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
    """
    Main orchestration class for the RAG pipeline.

    Provides static methods exposed via the CLI for indexing, searching,
    answering, and evaluating the system.
    """

    @staticmethod
    def index(repo_path: str = "data/raw/vllm-0.10.1",
              save_dir: str = "data/processed",
              max_chunk_size: int = MAX_CHUNK_SIZE) -> None:
        """
        Ingest a repository and create a searchable BM25 index.

        Args:
            repo_path: Path to the repository files.
            save_dir: Directory to save the generated index and chunks.
            max_chunk_size: Configurable maximum size for each text chunk.
        """
        index_repo(repo_path, save_dir, max_chunk_size)
        print("Ingestion complete! Indices saved under data/processed/")

    @staticmethod
    def search(query: str, k: int = 10,
               save_dir: str = "data/processed") -> None:
        """
        Search the index for a single query and print top results.

        Args:
            query: The search string.
            k: Number of results to retrieve.
            save_dir: Directory where the index is stored.
        """
        retriever, chunks = load_index(save_dir)
        results = retriever_search(query, retriever, chunks, k)
        for result in results:
            print(f"{result.file_path}: "
                  f"{result.first_character_index}-"
                  f"{result.last_character_index}")

    @staticmethod
    def search_dataset(dataset_path: str, save_directory: str = "data/output",
                       k: int = 10, index_dir: str = "data/processed") -> None:
        """
        Process a batch of questions from a JSON dataset.

        Args:
            dataset_path: Path to the input JSON dataset.
            save_directory: Directory to save the output JSON results.
            k: Number of results to retrieve per question.
            index_dir: Directory where the index is stored.
        """
        retriever, chunks = load_index(index_dir)
        if not is_file_available(dataset_path):
            print_error(f"File '{dataset_path}' not found",
                        exit_program=False)
            return
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        dataset = RagDataset(**data)
        search_results: list[MinimalSearchResults] = []
        for question in tqdm(dataset.rag_questions,
                             desc="Searching questions"):
            result_chunks = retriever_search(question.question,
                                             retriever, chunks, k)

            sources = [
                MinimalSource(
                    file_path=chunk.file_path,
                    first_character_index=chunk.first_character_index,
                    last_character_index=chunk.last_character_index)
                for chunk in result_chunks]

            search_results.append(MinimalSearchResults(
                question_id=question.question_id,
                question_str=question.question,
                retrieved_sources=sources
            ))
        path = Path(save_directory)
        path.mkdir(parents=True, exist_ok=True)
        student_results = StudentSearchResults[MinimalSearchResults](
            search_results=search_results,
            k=k
        )
        output_path = path / Path(dataset_path).name
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(student_results.model_dump(), f)

    @staticmethod
    def answer(query: str, k: int = 10, index_dir: str = "data/processed",
               model_name: str = "Qwen/Qwen3-0.6B") -> None:
        """
        Retrieve context and generate an answer for a single query.

        Args:
            query: The natural language question.
            k: Number of context chunks to retrieve.
            index_dir: Directory where the index is stored.
            model_name: The identifier of the LLM to use.
        """
        retriever, chunks = load_index(index_dir)
        result_chunks = retriever_search(query, retriever, chunks, k)
        model, tokenizer = load_model(model_name)
        answer = generate(query, result_chunks, model, tokenizer)
        print(answer)

    @staticmethod
    def answer_dataset(student_search_results_path: str,
                       save_directory: str = "data/output",
                       model_name: str = "Qwen/Qwen3-0.6B",
                       index_dir: str = "data/processed") -> None:
        """
        Generate answers for a dataset of search results.

        Args:
            student_search_results_path: Path to the search results JSON.
            save_directory: Directory to save the final answers JSON.
            model_name: The identifier of the LLM to use.
            index_dir: Directory where the index is stored.
        """
        with open(student_search_results_path, "r") as f:
            raw_data = json.load(f)
            search_result = (
                StudentSearchResults[MinimalSearchResults]
                .model_validate(raw_data)
            )

        retriever, chunks = load_index(index_dir)
        chunks_map = {
            (c.file_path, c.first_character_index): c
            for c in chunks
        }

        model, tokenizer = load_model(model_name)
        answers: list[MinimalAnswer] = []
        for result in tqdm(search_result.search_results,
                           desc="Generating answers"):
            result_chunks: list[Chunk] = []
            for source in result.retrieved_sources:
                key = (source.file_path, source.first_character_index)
                if key in chunks_map:
                    result_chunks.append(chunks_map[key])

            answer = generate(result.question_str, result_chunks,
                              model, tokenizer)
            answers.append(MinimalAnswer(
                question_id=result.question_id,
                question_str=result.question_str,
                retrieved_sources=result.retrieved_sources,
                answer=answer
            ))

        search_result_and_answer = StudentSearchResultsAndAnswer(
            search_results=answers,
            k=search_result.k)

        path = Path(save_directory)
        path.mkdir(parents=True, exist_ok=True)
        output_path = path / Path(student_search_results_path).name
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(search_result_and_answer.model_dump(), f)

    @staticmethod
    def evaluate(student_answer_path: str, dataset_path: str,
                 k: int = 10) -> None:
        """
        Evaluate the recall@k performance.

        Args:
            student_answer_path: Path to the student's results JSON.
            dataset_path: Path to the ground truth dataset JSON.
            k: The k value for recall calculation.
        """
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
            student_answer = (
                StudentSearchResults[MinimalSearchResults]
                .model_validate(json.load(f))
            )

        result = recall_at_k(questions, student_answer)
        print(f"Recall@{k}: {result:.4f}")
