from pydantic import BaseModel
import ast

from .utils import is_file_available


MAX_CHUNK_SIZE = 2000


class Chunk(BaseModel):
    """
    Represents a discrete segment of a file.

    Attributes:
        file_path: The relative path to the original file.
        first_character_index: The global character offset of the chunk start.
        last_character_index: The global character offset of the chunk end.
        content: The actual text content of the chunk.
    """
    file_path: str
    first_character_index: int
    last_character_index: int
    content: str


def _split_by_size(text: str, file_path: str,
                   max_chunk_size: int, overlap: int = 200) -> list[Chunk]:
    """
    Split text into fixed-size chunks with a sliding window.

    Args:
        text: The raw string to be split.
        file_path: The source file path for metadata.
        max_chunk_size: Maximum characters per chunk.
        overlap: Number of characters to overlap between chunks.

    Returns:
        A list of Chunk objects.
    """
    chunk_list: list[Chunk] = []
    text_len = len(text)
    if text_len == 0:
        return []

    start = 0
    while start < text_len:
        end = min(start + max_chunk_size, text_len)
        chunk_list.append(Chunk(file_path=file_path,
                                first_character_index=start,
                                last_character_index=end,
                                content=text[start:end]))
        if end == text_len:
            break
        start = end - overlap
        if start >= text_len or start < 0:
            break
        if start <= chunk_list[-1].first_character_index:
            start = end
    return chunk_list


def _chunk_python(text: str, file_path: str,
                  max_chunk_size: int) -> list[Chunk]:
    """
    Chunk Python code using its Abstract Syntax Tree (AST).
    """
    chunk_list: list[Chunk] = []

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _split_by_size(text, file_path, max_chunk_size)

    lines = text.splitlines(keepends=True)
    line_offsets = [0]
    for line in lines:
        line_offsets.append(line_offsets[-1] + len(line))

    segments: list[tuple[int, int]] = []
    for node in ast.iter_child_nodes(tree):
        lineno = getattr(node, "lineno", None)
        end_lineno = getattr(node, "end_lineno", None)
        if lineno is None or end_lineno is None:
            continue
        start = line_offsets[lineno - 1]
        end = min(line_offsets[end_lineno], len(text))
        segments.append((start, end))

    if not segments:
        return _split_by_size(text, file_path, max_chunk_size)

    group_start, group_end = segments[0]
    for sec_start, sec_end in segments[1:]:
        if (sec_end - group_start) > max_chunk_size:
            content = text[group_start:group_end]
            if len(content) > max_chunk_size:
                sub_chunks = _split_by_size(content, file_path, max_chunk_size)
                for sc in sub_chunks:
                    sc.first_character_index += group_start
                    sc.last_character_index += group_start
                chunk_list.extend(sub_chunks)
            else:
                chunk_list.append(Chunk(file_path=file_path,
                                        first_character_index=group_start,
                                        last_character_index=group_end,
                                        content=content))
            group_start, group_end = sec_start, sec_end
        else:
            group_end = sec_end

    content = text[group_start:group_end]
    if len(content) > max_chunk_size:
        sub_chunks = _split_by_size(content, file_path, max_chunk_size)
        for sc in sub_chunks:
            sc.first_character_index += group_start
            sc.last_character_index += group_start
        chunk_list.extend(sub_chunks)
    else:
        chunk_list.append(Chunk(file_path=file_path,
                                first_character_index=group_start,
                                last_character_index=group_end,
                                content=content))
    return chunk_list


def _chunk_markdown(text: str, file_path: str,
                    max_chunk_size: int) -> list[Chunk]:
    """
    Chunk Markdown files based on header sections.
    """
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
        sec_end = hash_lines[i + 1] if i + 1 < len(hash_lines) else len(text)
        sections.append((sec_start, sec_end))

    chunk_list: list[Chunk] = []
    group_start, group_end = sections[0]
    for sec_start, sec_end in sections[1:]:
        if (sec_end - group_start) > max_chunk_size:
            content = text[group_start:group_end]
            if len(content) > max_chunk_size:
                sub_chunks = _split_by_size(content, file_path, max_chunk_size)
                for sc in sub_chunks:
                    sc.first_character_index += group_start
                    sc.last_character_index += group_start
                chunk_list.extend(sub_chunks)
            else:
                chunk_list.append(Chunk(file_path=file_path,
                                        first_character_index=group_start,
                                        last_character_index=group_end,
                                        content=content))
            group_start, group_end = sec_start, sec_end
        else:
            group_end = sec_end

    content = text[group_start:group_end]
    if len(content) > max_chunk_size:
        sub_chunks = _split_by_size(content, file_path, max_chunk_size)
        for sc in sub_chunks:
            sc.first_character_index += group_start
            sc.last_character_index += group_start
        chunk_list.extend(sub_chunks)
    else:
        chunk_list.append(Chunk(file_path=file_path,
                                first_character_index=group_start,
                                last_character_index=group_end,
                                content=content))
    return chunk_list


def chunk_file(file_path: str, max_chunk_size: int) -> list[Chunk]:
    """
    Apply type-specific chunking strategies to a file.
    """
    if not is_file_available(file_path):
        raise Exception(f"File {file_path} is not available")

    effective_max = min(max_chunk_size, MAX_CHUNK_SIZE)
    if effective_max <= 0:
        raise ValueError("Chunk size must be positive")

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    if not text.strip():
        return []

    if file_path.endswith(".py"):
        return _chunk_python(text, file_path, effective_max)
    if file_path.endswith(".md"):
        return _chunk_markdown(text, file_path, effective_max)
    return _split_by_size(text, file_path, effective_max)
