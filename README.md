# ContractLens — AI Contract Review System

ContractLens is a deployed AI agent that reviews legal contracts and produces structured, plain-English risk reports — without requiring legal expertise from the user. It applies Malaysian legal context (PDPA, Employment Act, Contracts Act) and compares findings against standard contract templates.

## Architecture

- **UI**: Chainlit UI for file upload and chat interaction
- **Agent Orchestration**: LangGraph
- **Database (RAG)**: ChromaDB with local `all-MiniLM-L6-v2` embeddings
- **Validation**: Guardrails-based output validation rules

## Getting Started

### Local Setup

1. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Populate vector database (RAG)**:
   ```bash
   python scripts/ingest_all.py
   ```
4. **Test the agent**:
   ```bash
   python scripts/test_agent.py data/test_contracts/test_contract1.pdf
   ```
