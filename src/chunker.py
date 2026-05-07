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


def _chunk_python(text: str, file_path: str, max_chunk_size: int) -> list[Chunk]:
    chunk_list: list[Chunk] = []

    try:
        tree = ast.parse(text)
    except SyntaxError:
        chunk_list.extend(_split_by_size(text, file_path,
                                         max_chunk_size))
        return chunk_list

    lines = text.splitlines(keepends=True)
    line_offsets = [0]
    for line in lines:
        line_offsets.append(line_offsets[-1] + len(line))

    segments: list[tuple[int, int]] = []
    for node in ast.iter_child_nodes(tree):
        start = line_offsets[node.lineno - 1]
        end = line_offsets[node.end_lineno]
        if end - start > max_chunk_size:
            sub_chunks = _split_by_size(text[start:end], file_path, max_chunk_size)
            for chunk in sub_chunks:
                chunk.first_character_index += start
                chunk.last_character_index += start
            chunk_list.extend(sub_chunks)
        else:
            segments.append((start, end))

    if not segments:
        return chunk_list

    group_start, group_end = segments[0]
    for sec_start, sec_end in segments[1:]:
        if (sec_end - group_start) > max_chunk_size:
            chunk_list.append(Chunk(file_path, group_start, group_end,
                                    text[group_start:group_end]))
            group_start = sec_start
            group_end = sec_end
        else:
            group_end = sec_end
    chunk_list.append(Chunk(file_path, group_start, group_end,
                            text[group_start:group_end]))
    return chunk_list


def _chunk_markdown(text: str, file_path: str, max_chunk_size: int) -> list[Chunk]:
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
    for sec_start, sec_end in sections[1:]:
        if sec_end - sec_start > max_chunk_size:
            if group_end > group_start:
                chunk_list.append(Chunk(file_path, group_start, group_end,
                                        text[group_start:group_end]))
            sub_chunks = _split_by_size(text[sec_start:sec_end], file_path, max_chunk_size)
            for chunk in sub_chunks:
                chunk.first_character_index += sec_start
                chunk.last_character_index += sec_start
            chunk_list.extend(sub_chunks)
            group_start = sec_end
            group_end = sec_end
        elif (sec_end - group_start) > max_chunk_size:
            chunk_list.append(Chunk(file_path, group_start, group_end,
                                    text[group_start:group_end]))
            group_start = sec_start
            group_end = sec_end
        else:
            group_end = sec_end
    chunk_list.append(Chunk(file_path, group_start, group_end,
                            text[group_start:group_end]))
    return chunk_list


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
        chunk_list = _chunk_python(text, file_path, max_chunk_size)
    elif file_path.endswith(".md"):
        chunk_list = _chunk_markdown(text, file_path, max_chunk_size)
    else:
        chunk_list = _split_by_size(text, file_path, max_chunk_size)
    return chunk_list
