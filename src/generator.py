from transformers import (AutoTokenizer,
                          AutoModelForCausalLM,
                          PreTrainedModel,
                          PreTrainedTokenizer)

from .chunker import Chunk


def load_model(model_name: str) -> tuple[PreTrainedModel,
                                         PreTrainedTokenizer]:
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return (model, tokenizer)


def generate(question: str,
             chunks: list[Chunk],
             model: PreTrainedModel,
             tokenizer: PreTrainedTokenizer) -> str:
    context = "\n\n".join(chunk.content for chunk in chunks)
    context = context[:3000]

    prompt = f"""Given the following context, answer the question.
                Context: {context}
                Question: {question}
                Answer:
                """
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=200)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return answer
