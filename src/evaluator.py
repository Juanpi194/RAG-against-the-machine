from .models import MinimalSource, AnsweredQuestion, StudentSearchResults


def overlap_ratio(source_a: MinimalSource, source_b: MinimalSource) -> float:
    """
    Calculate the character-level overlap ratio between two sources.

    The ratio is computed as (overlap_length / source_a_length).

    Args:
        source_a: The retrieved source.
        source_b: The ground truth source.

    Returns:
        A float representing the overlap ratio (0.0 to 1.0).
    """
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
    """
    Determine if a correct source is present in the retrieved sources.

    A source is considered 'found' if there is at least a 5% overlap
    with any of the retrieved sources.

    Args:
        retrieved_sources: A list of sources returned by the retriever.
        correct_source: A single ground truth source.

    Returns:
        True if the source is found, False otherwise.
    """
    for source in retrieved_sources:
        if overlap_ratio(source, correct_source) >= 0.05:
            return True
    return False


def recall_at_k(questions: list[AnsweredQuestion],
                search_results: StudentSearchResults) -> float:
    """
    Calculate the Recall@k metric for a dataset.

    Recall@k = (number of correct sources found) / (total correct sources).

    Args:
        questions: The list of answered questions (ground truth).
        search_results: The results produced by the student system.

    Returns:
        The average recall across all questions.
    """
    results_map = {
        res.question_id: res.retrieved_sources
        for res in search_results.search_results
    }

    scores = []
    for question in questions:
        if question.question_id not in results_map:
            scores.append(0.0)
            continue

        retrieved = results_map[question.question_id]
        found = 0
        for correct_source in question.sources:
            if is_found(retrieved, correct_source):
                found += 1
        scores.append(found / len(question.sources))

    if not scores:
        return 0.0
    return sum(scores) / len(scores)
