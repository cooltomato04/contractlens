import os
import sys

# Ensure the project root is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.ingest import ingest_directory

def main():
    print("=======================================")
    print("ContractLens — Vector Database Ingest")
    print("=======================================")
    
    # 1. Ingest templates collection
    templates_dir = "rag/templates"
    print(f"\n[Step 1] Ingesting standard templates from: {templates_dir}")
    if os.path.exists(templates_dir):
        ingest_directory(templates_dir, "templates")
    else:
        print(f"Error: Templates directory '{templates_dir}' not found.")
        
    # 2. Ingest knowledge collection
    knowledge_dir = "rag/knowledge"
    print(f"\n[Step 2] Ingesting knowledge files from: {knowledge_dir}")
    if os.path.exists(knowledge_dir):
        ingest_directory(knowledge_dir, "knowledge")
    else:
        print(f"Error: Knowledge directory '{knowledge_dir}' not found.")
        
    print("\nIngestion process complete!")

if __name__ == "__main__":
    main()
