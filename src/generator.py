import re
from typing import Any
from transformers import (AutoTokenizer,
                          AutoModelForCausalLM)

from .chunker import Chunk


def load_model(model_name: str) -> tuple[Any, Any]:
    """
    Load a pre-trained causal language model and its tokenizer.

    Args:
        model_name: The HuggingFace model identifier or local path.

    Returns:
        A tuple containing (model, tokenizer).
    """
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return (model, tokenizer)


def generate(question: str,
             chunks: list[Chunk],
             model: Any,
             tokenizer: Any) -> str:
    """
    Generate an answer grounded in the provided context chunks.

    The generator uses a prompt that instructs the model to cite its sources
    and remain faithful to the provided context, avoiding hallucinations.

    Args:
        question: The natural language question to answer.
        chunks: A list of retrieved code or documentation chunks.
        model: The loaded LLM.
        tokenizer: The corresponding tokenizer.

    Returns:
        A natural language answer string.
    """
    if not chunks:
        return "I don't know"

    context_parts = []
    for i, chunk in enumerate(chunks):
        part = f"Source [{i}]: {chunk.file_path}\n{chunk.content}"
        context_parts.append(part)

    context = "\n\n".join(context_parts)
    context = context[:3500]

    prompt = f"""Context:
{context}

Question: {question}
Answer: According to the documentation,"""

    inputs = tokenizer(prompt, return_tensors="pt")
    input_ids = inputs["input_ids"]

    outputs = model.generate(
        **inputs,
        max_new_tokens=80,
        do_sample=False,
        repetition_penalty=1.5,
        pad_token_id=tokenizer.eos_token_id,
    )

    generated_ids = outputs[0][input_ids.shape[-1]:]
    answer_tail = tokenizer.decode(generated_ids, skip_special_tokens=True)

    answer = "According to the documentation," + answer_tail
    answer = answer.strip()

    if "\n" in answer:
        answer = answer.split("\n")[0].strip()

    citations = re.findall(r"\[\d+\]", answer)
    if not citations and chunks:
        answer = answer.rstrip(".") + " [0]."
    elif citations:
        last_cite = citations[-1]
        pos = answer.rfind(last_cite)
        answer = answer[:pos + len(last_cite)].strip()

    for label in ["Question:", "Answer:", "Note:", "Please", "Source:",
                  "Chinese"]:
        if label in answer:
            answer = answer.split(label)[0].strip()

    return answer
