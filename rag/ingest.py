import os
import glob
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

PERSIST_DIRECTORY = "data/chromadb"

def load_document(file_path: str) -> List[Document]:
    """Loads a single PDF, TXT, or MD file."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
        return loader.load()
    elif ext in [".txt", ".md"]:
        loader = TextLoader(file_path, encoding="utf-8")
        return loader.load()
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

def chunk_documents(documents: List[Document]) -> List[Document]:
    """Chunks documents into chunks of 800 characters with 150 overlap."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        length_function=len,
        add_start_index=True
    )
    return text_splitter.split_documents(documents)

def ingest_directory(directory_path: str, collection_name: str):
    """Loads, chunks, and ingests all supported files in directory to ChromaDB."""
    # Find all PDF, TXT, MD files recursively
    files = []
    for ext in ["**/*.pdf", "**/*.txt", "**/*.md"]:
        pattern = os.path.join(directory_path, ext)
        files.extend(glob.glob(pattern, recursive=True))
    
    # Deduplicate and sort file paths
    files = list(sorted(set(os.path.abspath(f) for f in files)))
    
    if not files:
        print(f"No files found in {directory_path} matching pdf, txt, or md.")
        return
    
    all_docs = []
    for file_path in files:
        print(f"Loading {file_path}...")
        try:
            docs = load_document(file_path)
            for doc in docs:
                doc.metadata["source_file"] = os.path.basename(file_path)
                doc.metadata["file_path"] = file_path
            all_docs.extend(docs)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            
    if not all_docs:
        print("No documents loaded successfully.")
        return
        
    print(f"Loaded {len(all_docs)} pages/documents.")
    chunks = chunk_documents(all_docs)
    print(f"Split into {len(chunks)} chunks.")
    
    # Initialize embedding model
    print("Initializing HuggingFaceEmbeddings (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Initialize Chroma store
    print(f"Storing chunks to collection '{collection_name}' in {PERSIST_DIRECTORY}...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY,
        collection_name=collection_name
    )
    try:
        vectorstore.persist()
    except AttributeError:
        pass
    print(f"Collection '{collection_name}' successfully created and persisted.")
