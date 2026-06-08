import os
import sys
import json

# Ensure project root is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader
from agent.graph import graph

def extract_text_from_pdf(pdf_path: str) -> str:
    print(f"Extracting text from: {pdf_path}...")
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text = "\n".join([doc.page_content for doc in docs])
    return text

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_agent.py <path_to_contract_pdf>")
        sys.exit(1)
        
    contract_path = sys.argv[1]
    if not os.path.exists(contract_path):
        print(f"Error: File '{contract_path}' does not exist.")
        sys.exit(1)
        
    # Extract text from the contract PDF
    raw_text = extract_text_from_pdf(contract_path)
    
    print("\n[Start] Initializing LangGraph workflow...")
    initial_state = {
        "raw_text": raw_text
    }
    
    # Execute the graph synchronously
    print("Invoking graph...")
    try:
        final_state = graph.invoke(initial_state)
        
        print("\n=======================================")
        print("ContractLens Review Report Result")
        print("=======================================")
        
        print(f"Contract Type: {final_state.get('contract_type')}")
        print(f"Risk Score: {final_state.get('risk_score')}")
        print(f"Retry Count: {final_state.get('retry_count')}")
        print(f"Validation Errors: {final_state.get('validation_errors')}")
        
        print("\n[Report JSON Output]:")
        print(json.dumps(final_state.get("report"), indent=2))
        
    except Exception as e:
        print(f"\nExecution error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
