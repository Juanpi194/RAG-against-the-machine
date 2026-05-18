*This project has been created as part of the 42 curriculum by jvizcain.*

## Description

This project implements a Retrieval-Augmented Generation (RAG) system capable of answering questions about the vLLM codebase. Given a question, the system retrieves the most relevant code snippets and documentation from the vLLM repository, then uses a language model (Qwen3-0.6B) to generate a grounded answer based on the retrieved context.

The system is evaluated using recall@k metrics, measuring how effectively it retrieves the correct source locations for a given question.

## Instructions

### Installation

This project uses `uv` as the package manager.

```bash
# Install dependencies
uv sync
```

### Setup

Place the vLLM repository under `data/raw/`:

```bash
mkdir -p data/raw
unzip vllm-0.10.1.zip -d data/raw/
```

### Execution

**Index the repository:**
```bash
uv run python -m src index data/raw/vllm-0.10.1 data/processed
```

**Search for a single query:**
```bash
uv run python -m src search "How to configure OpenAI server?" --k 5
```

**Search a dataset:**
```bash
uv run python -m src search_dataset data/datasets/UnansweredQuestions/dataset_docs_public.json data/output/search_results --k 10
```

**Answer a single query:**
```bash
uv run python -m src answer "How to configure OpenAI server?" --k 5
```

**Answer a dataset:**
```bash
uv run python -m src answer_dataset data/output/search_results/dataset_docs_public.json data/output/answers
```

**Evaluate search results:**
```bash
uv run python -m src evaluate data/output/search_results/dataset_docs_public.json data/datasets/AnsweredQuestions/dataset_docs_public.json
```

## System Architecture

The system is organized under `src/` and consists of the following modules:

- **`models.py`** — Pydantic models for type-safe data handling throughout the pipeline: `MinimalSource`, `UnansweredQuestion`, `AnsweredQuestion`, `RagDataset`, `MinimalSearchResults`, `MinimalAnswer`, `StudentSearchResults`, `StudentSearchResultsAndAnswer`.
- **`chunker.py`** — Splits repository files into chunks using different strategies depending on file type. Produces `Chunk` objects with character-level positions.
- **`indexer.py`** — Walks the repository, chunks all relevant files, builds a BM25 index, and saves it to disk. Also handles loading the saved index.
- **`retriever.py`** — Given a query and a loaded BM25 index, returns the top-k most relevant chunks.
- **`generator.py`** — Loads the Qwen3-0.6B model and generates natural language answers given a question and retrieved context chunks.
- **`evaluator.py`** — Implements the recall@k metric by computing character-level overlap between retrieved sources and ground truth sources.
- **`pipeline.py`** — Orchestrates all modules and exposes the CLI commands via Python Fire.
- **`__main__.py`** — Entry point, wires Fire to the Pipeline class.

```
Question → search → [chunk_1, chunk_2, ..., chunk_k] → generate → answer
                         ↑
                    BM25 index
                         ↑
               chunk_file × all repo files
```

## Chunking Strategy

Files are chunked differently depending on their type, with a maximum chunk size of 2000 characters (configurable via CLI).

**Python files (`.py`):** The file is parsed using Python's `ast` module. Top-level nodes (functions, classes, imports) are extracted and their character positions computed from line offsets. Consecutive nodes are grouped until the chunk size limit is reached. Oversized individual nodes are split using the size-based fallback.

**Markdown/text files (`.md`, `.rst`, `.txt`):** The file is split on heading lines (lines starting with `#`). Each heading marks the start of a new section. Consecutive sections are grouped until the chunk size limit is reached. Oversized sections fall back to size-based splitting.

**Fallback (`_split_by_size`):** A sliding window of `max_chunk_size` characters with an overlap of 200 characters between consecutive chunks, to avoid losing context at boundaries.

## Retrieval Method

The system uses **BM25** (Best Match 25) via the `bm25s` library. BM25 is a ranking function based on term frequency and inverse document frequency, with adjustments for document length. It scores each chunk against the query and returns the top-k highest-scoring chunks.

BM25 was chosen because it is fast, requires no GPU, and performs well on keyword-based queries over code and documentation. The index is built once and saved to disk for fast reuse.

## Performance Analysis

Evaluation was performed on the public datasets using k=10:

| Dataset | Recall@10 |
|---------|-----------|
| Docs    | 0.88      |
| Code    | 0.62      |

Both scores exceed the minimum thresholds required by the subject (0.80 for docs, 0.50 for code). The docs dataset benefits more from BM25 because documentation uses natural language that matches query terms directly. Code retrieval is harder because function names and variable names are less likely to appear verbatim in natural language queries.

## Design Decisions

**BM25 over TF-IDF:** Both are valid per the subject. BM25 was chosen because it handles varying document lengths better than TF-IDF, which is important given that chunks vary significantly in size.

**AST-based chunking for Python:** Cutting Python files at arbitrary character positions risks splitting in the middle of a function or class, which loses semantic coherence. Using AST boundaries ensures each chunk is a complete, meaningful unit.

**Heading-based chunking for Markdown:** Documentation is naturally organized by headings. Splitting at heading boundaries keeps related content together and avoids cutting mid-paragraph.

**Separate indexes per file type:** The same BM25 index covers all file types, which simplifies the retrieval pipeline while still benefiting from type-specific chunking.

## Challenges Faced

**Character index alignment:** The evaluation metric uses character-level overlap between retrieved and ground truth sources. Getting the exact character positions right required careful handling of line endings (`splitlines(keepends=True)`) and ensuring that sub-chunk positions were offset-corrected when falling back to size-based splitting.

**File path consistency:** The ground truth dataset uses paths prefixed with `data/raw/vllm-0.10.1/...`. The indexer must be pointed at the same root path to produce matching file paths, otherwise recall@k always returns 0.

**Empty corpus:** BM25 raises an error if the corpus is empty. This required ensuring that the file filter and chunking pipeline correctly produced at least one non-empty chunk before indexing.

## Example Usage

```bash
# Index the repository
uv run python -m src index data/raw/vllm-0.10.1 data/processed --max_chunk_size 2000

# Search for a single query
uv run python -m src search "What is PagedAttention?" --k 5

# Process a full dataset and save search results
uv run python -m src search_dataset datasets_public/public/UnansweredQuestions/dataset_docs_public.json data/output/search_results --k 10

# Evaluate recall@k against ground truth
uv run python -m src evaluate data/output/search_results/dataset_docs_public.json datasets_public/public/AnsweredQuestions/dataset_docs_public.json

# Generate answers for a dataset
uv run python -m src answer_dataset data/output/search_results/dataset_docs_public.json data/output/answers
```

## Resources

- [BM25 algorithm — Wikipedia](https://en.wikipedia.org/wiki/Okapi_BM25)
- [bm25s library documentation](https://github.com/xhluca/bm25s)
- [Python ast module documentation](https://docs.python.org/3/library/ast.html)
- [Pydantic documentation](https://docs.pydantic.dev/)
- [Qwen3 model — HuggingFace](https://huggingface.co/Qwen/Qwen3-0.6B)
- [RAG paper — Lewis et al. 2020](https://arxiv.org/abs/2005.11401)

**Use of AI:** Claude (Anthropic) was used as a learning assistant throughout this project. It was not used to generate code directly — instead, it explained concepts, reviewed implementations written by the student, and pointed out bugs. All code was written and understood by the student before being included in the project.