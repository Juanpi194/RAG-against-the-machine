import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

DEFAULT_PATH = "./datasets_public/public/"

texto = DEFAULT_PATH + "AnsweredQuestions/dataset_code_public.json"

with open(texto, "r", encoding="utf-8") as f:
    data = json.load(f)

# Convertir a string
text = json.dumps(data)

# Crear Document
doc = Document(page_content=text)

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base",
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", " ", ""]
)

chunks = text_splitter.split_documents([doc])

for chunk in chunks:
    print(chunk)
    print("=====")
