import os
import sys

# Ensure the project root is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.retriever import query_templates, query_knowledge

def test_retrieval():
    print("=======================================")
    print("ContractLens — Testing RAG Retrieval")
    print("=======================================")
    
    # 1. Test query templates
    print("\n--- Testing 'templates' collection retrieval ---")
    template_query = "non-compete clause duration and geographic scope"
    print(f"Query: '{template_query}'")
    try:
        template_results = query_templates(template_query, n=2)
        print(f"Retrieved {len(template_results)} results:")
        for idx, doc in enumerate(template_results, 1):
            print(f"\n[{idx}] Source: {doc.metadata.get('source_file')}")
            snippet = doc.page_content.replace('\n', ' ')[:150]
            print(f"    Snippet: {snippet}...")
    except Exception as e:
        print(f"Error querying templates: {e}")
        
    # 2. Test query knowledge
    print("\n--- Testing 'knowledge' collection retrieval ---")
    knowledge_query = "Employment Act minimum annual leave entitlement"
    print(f"Query: '{knowledge_query}'")
    try:
        knowledge_results = query_knowledge(knowledge_query, n=2)
        print(f"Retrieved {len(knowledge_results)} results:")
        for idx, doc in enumerate(knowledge_results, 1):
            print(f"\n[{idx}] Source: {doc.metadata.get('source_file')}")
            snippet = doc.page_content.replace('\n', ' ')[:150]
            print(f"    Snippet: {snippet}...")
    except Exception as e:
        print(f"Error querying knowledge: {e}")

if __name__ == "__main__":
    test_retrieval()
