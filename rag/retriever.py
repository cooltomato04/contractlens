import os
from typing import List
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

PERSIST_DIRECTORY = "data/chromadb"

_embeddings = None
_templates_store = None
_knowledge_store = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings

def get_templates_store():
    global _templates_store
    if _templates_store is None:
        _templates_store = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=get_embeddings(),
            collection_name="templates"
        )
    return _templates_store

def get_knowledge_store():
    global _knowledge_store
    if _knowledge_store is None:
        _knowledge_store = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=get_embeddings(),
            collection_name="knowledge"
        )
    return _knowledge_store

def query_templates(text: str, n: int = 5) -> List[Document]:
    """Retrieve n similar standard clauses from the templates collection."""
    store = get_templates_store()
    return store.similarity_search(text, k=n)

def query_knowledge(text: str, n: int = 5) -> List[Document]:
    """Retrieve n similar law/guideline sections from the knowledge collection."""
    store = get_knowledge_store()
    return store.similarity_search(text, k=n)
