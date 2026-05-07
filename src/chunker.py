from dataclasses import dataclass
import ast

from .utils import is_file_available


MAX_CHUNK_SIZE = 2000


@dataclass
class Chunk:
    file_path: str
    first_character_index: int
    last_character_index: int
    content: str


def _split_by_size(text: str, file_path: str, max_chunk_size: int, overlap: int = 200) -> list[Chunk]:
    chunk_list: list[Chunk] = []
    start = 0
    end = min(start + max_chunk_size, len(text))
    while end != len(text):
        chunk_list.append(Chunk(file_path, start, end, text[start:end]))
        start = end - overlap
        end = min(start + max_chunk_size, len(text))
    chunk_list.append(Chunk(file_path, start, end, text[start:end]))
    return chunk_list


def chunk_python(text: str, file_path: str, max_chunk_size: int) -> list[Chunk]:
    ...


def chunk_markdown(text: str, file_path: str, max_chunk_size: int) -> list[Chunk]:
    # TODO: Finish this function
    chunk_list: list[Chunk] = []

    lines = text.splitlines(keepends=True)
    offset = 0
    hash_lines: list[int] = []
    for line in lines:
        if line.startswith("#"):
            hash_lines.append(offset)
        offset += len(line)

    if not hash_lines:
        return _split_by_size(text, file_path, max_chunk_size)
    
    sections: list[tuple[int, int]] = []
    for i in range(len(hash_lines)):
        sec_start = hash_lines[i]
        if i + 1 < len(hash_lines):
            sec_end = hash_lines[i + 1]
        else:
            sec_end = len(text)
        sections.append((sec_start, sec_end))

    group_start, group_end = sections[0]
    i = 0
    while group_end != len(text):
        i += 1
        if group_end - group_start <= max_chunk_size:
            group_end = sections[i][1]
            # Making bigger chunk
        else:
            chunk_list.append(Chunk(file_path, group_start,
                                    group_end,
                                    text[group_start:group_end]))
            group_start, group_end = sections[i]
            # Chunk finished
    chunk_list.append(Chunk(file_path, group_start,
                            group_end,
                            text[group_start:group_end]))


def chunk_file(file_path: str, max_chunk_size: int) -> list[Chunk]:
    if not is_file_available(file_path):
        raise Exception(f"File {file_path} is not available")
    if max_chunk_size > MAX_CHUNK_SIZE:
        raise ValueError(f"Chunk size '{max_chunk_size}' is greater than maxi allowed. "
                         f"Maximum size is '{MAX_CHUNK_SIZE}'")
    elif max_chunk_size <= 0:
        raise ValueError(f"Chunk size must be a positive number ('{max_chunk_size}' given)")

    # It will not fail because we already checked if the file is available
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    if not text.strip():
        return []

    if file_path.endswith(".py"):
        chunk_list = chunk_python(text, file_path, max_chunk_size)
    elif file_path.endswith(".md"):
        chunk_list = chunk_markdown(text, file_path, max_chunk_size)
    else:
        chunk_list = _split_by_size(text, file_path, max_chunk_size)
    return chunk_list
