from .models import MinimalSource, AnsweredQuestion, StudentSearchResults


def overlap_ratio(source_a: MinimalSource, source_b: MinimalSource) -> float:
    if source_a.file_path != source_b.file_path:
        return 0.0

    start_overlap = max(source_a.first_character_index,
                        source_b.first_character_index)
    end_overlap = min(source_a.last_character_index,
                      source_b.last_character_index)

    if start_overlap >= end_overlap:
        return 0.0
    overlap = end_overlap - start_overlap
    return float(overlap /
                 (source_a.last_character_index - (
                     source_a.first_character_index)))


def is_found(retrieved_sources: list[MinimalSource],
             correct_source: MinimalSource) -> bool:
    for source in retrieved_sources:
        if overlap_ratio(source, correct_source) >= 0.05:
            return True
    return False


def recall_at_k(questions: list[AnsweredQuestion],
                search_results: StudentSearchResults) -> float:
    scores = []
    for question in questions:
        found = 0
        for result in search_results.search_results:
            if question.question_id == result.question_id:
                for correct_source in question.sources:
                    if is_found(result.retrieved_sources, correct_source):
                        found += 1
                scores.append(found / len(question.sources))
    if not scores:
        return 0.0
    return sum(scores) / len(scores)
