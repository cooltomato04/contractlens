# ContractLens — Project Specification

**Version:** 1.0  
**Author:** Houng Nai Zhe (Zac)  
**Stack:** LangGraph · LangChain · MCP · ChromaDB · Guardrails AI · Chainlit  
**Target Deploy:** Hugging Face Spaces  

---

## 1. Objective

ContractLens is a deployed AI agent that reviews legal contracts and produces structured, plain-English risk reports — without requiring legal expertise from the user.

A user uploads any contract (PDF or DOCX). The agent reads it, extracts key clauses, compares them against standard templates, flags risks, and returns a structured report with an overall risk score and source citations. Every output is validated before the user sees it.

The target users are Malaysian SMEs, freelancers, startup founders, and employees who need a fast first-pass review before engaging a lawyer.

---

## 2. Problem Being Solved

Most people sign contracts without fully understanding them. Hiring a lawyer for a first-pass review costs RM500–2,000 and takes days. Online tools either give generic advice or hallucinate legal conclusions without sources.

ContractLens solves this by:
- Grounding every finding in the actual uploaded contract
- Comparing against real standard contract templates
- Applying Malaysian legal context (PDPA, Employment Act, Contracts Act)
- Validating every output against a strict schema before showing it
- Being usable by anyone with a browser — no setup, no account

---

## 3. Use Cases

### 3.1 Employee reviewing a job offer
**Input:** Upload employment_offer.pdf  
**Output:** Flags below-minimum annual leave, overbroad non-compete, missing termination notice period. Compares against Employment Act 1955 minimums.

### 3.2 Freelancer reviewing a client contract
**Input:** Upload client_service_agreement.pdf  
**Output:** Flags one-sided indemnification, auto-renewal trap, payment terms beyond 60 days, no IP ownership clarity.

### 3.3 Startup founder reviewing a vendor agreement
**Input:** Upload saas_vendor_agreement.pdf  
**Output:** Flags no data protection clause (PDPA risk), governing law set to foreign jurisdiction, unlimited liability exposure, no SLA penalties.

### 3.4 Business owner reviewing an NDA
**Input:** Upload nda.pdf  
**Output:** Flags overly broad confidentiality scope, no mutual reciprocity, excessive duration (10 years), no carve-outs for publicly available information.

### 3.5 Follow-up Q&A
After the report is generated, the user can ask follow-up questions:
- "What does the indemnification clause actually mean?"
- "Is the non-compete enforceable in Malaysia?"
- "Which clause should I ask them to change first?"

The agent answers from the uploaded contract using RAG.

---

## 4. System Architecture

```
User (Chainlit UI)
        │
        ▼
  File Upload Handler
  (PDF/DOCX → raw text)
        │
        ▼
┌─────────────────────────────────────────┐
│           LangGraph Agent               │
│                                         │
│  Node 1: Ingest & Chunk Contract        │
│      ↓                                  │
│  Node 2: Classify Contract Type         │
│      ↓                                  │
│  Node 3: Extract Clauses (parallel)     │
│    ├── Payment & commercial terms       │
│    ├── Termination & notice             │
│    ├── Liability & indemnification      │
│    ├── IP ownership                     │
│    ├── Data protection                  │
│    ├── Non-compete / restraint          │
│    ├── Governing law & disputes         │
│    └── Missing standard clauses         │
│      ↓                                  │
│  Node 4: RAG Retrieval                  │
│    ├── Query templates collection       │
│    │   (compare against standard)       │
│    └── Query knowledge collection       │
│        (apply Malaysian legal context)  │
│      ↓                                  │
│  Node 5: Score & Compile Report         │
│      ↓                                  │
│  Node 6: Guardrails Validation          │
│    ├── PASS → return report to user     │
│    └── FAIL → loop back to Node 5       │
└─────────────────────────────────────────┘
        │
        ▼
  Structured Report (Chainlit UI)
  + Follow-up Q&A (RAG over contract)
```

---

## 5. Components

### 5.1 `app.py` — Chainlit UI
- File upload handler (PDF, DOCX)
- Chat interface for follow-up Q&A
- Renders the structured report with risk colour coding
- Download button for the report as PDF

### 5.2 `agent/state.py` — Shared State Schema
Defines the LangGraph state object passed between all nodes:
```
ContractState:
  - raw_text: str               # full contract text
  - contract_type: str          # NDA / Employment / Vendor / Freelance / Unknown
  - clauses: dict               # extracted clause content by category
  - rag_context: dict           # retrieved template and knowledge chunks
  - findings: list[Finding]     # list of flagged issues
  - risk_score: str             # Low / Medium / High
  - report: Report              # final validated report object
  - validation_errors: list     # guardrails failures, triggers loop
  - messages: list              # LangChain message history
```

### 5.3 `agent/graph.py` — LangGraph State Machine
Defines the directed graph connecting all nodes:
- Entry point: `ingest_node`
- Conditional edge after `guardrails_node`: pass → END, fail → `compile_node`
- Max retry loop: 2 iterations before returning partial report with warning

### 5.4 `agent/nodes.py` — Node Logic
Each function takes `ContractState` and returns updated `ContractState`:

| Node | Function | What it does |
|---|---|---|
| Node 1 | `ingest_node` | Extracts text from PDF/DOCX, stores in state |
| Node 2 | `classify_node` | Identifies contract type using LLM |
| Node 3 | `extract_node` | Parallel LLM calls to extract each clause category |
| Node 4 | `rag_node` | Queries ChromaDB for relevant template and knowledge chunks |
| Node 5 | `compile_node` | Scores risk, compiles structured report |
| Node 6 | `guardrails_node` | Validates report against schema, routes pass/fail |

### 5.5 `agent/prompts.py` — Prompt Templates
All LangChain `ChatPromptTemplate` objects:
- `CLASSIFY_PROMPT` — identify contract type
- `EXTRACT_CLAUSE_PROMPT` — extract a specific clause category
- `RISK_SCORE_PROMPT` — assess risk level with reasoning
- `COMPILE_REPORT_PROMPT` — generate final structured report
- `QA_PROMPT` — answer follow-up questions from contract text

### 5.6 `rag/ingest.py` — Knowledge Base Builder
- Reads all PDFs, markdown, and txt files from `rag/templates/` and `rag/knowledge/`
- Chunks text (800 chars, 150 overlap)
- Embeds using `all-MiniLM-L6-v2` (local, no API cost)
- Stores into two ChromaDB collections: `templates` and `knowledge`
- Run once before deployment: `python3 scripts/ingest_all.py`

### 5.7 `rag/retriever.py` — Knowledge Retrieval
- `query_templates(text, n=5)` — find similar standard clauses
- `query_knowledge(text, n=5)` — find relevant law and legal context
- Returns chunks with source metadata for citations

### 5.8 `guardrails/validators.py` — Output Validation
Rules every report must pass before being shown to the user:
- Every `Finding` must have a `clause_location` (not empty)
- Every `Finding` must have a `severity` of Low / Medium / High
- `risk_score` must be one of: Low / Medium / High
- `summary` must be between 50–500 characters
- `disclaimer` field must be present and non-empty
- No finding can contain the phrases "I think", "probably", "I believe" (hallucination signals)
- Minimum 1 finding, maximum 20 findings per report

### 5.9 `guardrails/schemas/report_schema.json` — Report Schema
Defines the exact JSON structure the agent must produce:
```json
{
  "contract_type": "string",
  "risk_score": "Low | Medium | High",
  "summary": "string (plain English, 50-500 chars)",
  "findings": [
    {
      "category": "string",
      "clause_location": "string (e.g. Section 4.2)",
      "issue": "string (what is wrong)",
      "plain_english": "string (what it means for the user)",
      "severity": "Low | Medium | High",
      "recommendation": "string (what to ask the other party to change)",
      "source": "string (which template or law this is based on)"
    }
  ],
  "missing_clauses": ["string"],
  "positive_findings": ["string"],
  "disclaimer": "string"
}
```

### 5.10 `mcp/tools.py` — MCP Tool Definitions
Tools the agent can invoke during clause analysis:
- `web_search_tool` — search for context on unusual clause patterns
- `malaysia_law_tool` — return jurisdiction-specific legal context by topic

### 5.11 `mcp/servers/malaysia_law.py` — Malaysia Law MCP Server
Lightweight MCP server that maps legal topics to context from the knowledge base:
- Input: topic string (e.g. "non-compete", "PDPA", "termination")
- Output: relevant Malaysian legal context + applicable statute

### 5.12 `scripts/ingest_all.py` — One-Shot Ingest Script
Run once to populate ChromaDB before starting the app:
```bash
python3 scripts/ingest_all.py
```

### 5.13 `scripts/test_agent.py` — Development Test Script
Runs the full agent against a test contract and prints the report:
```bash
python3 scripts/test_agent.py data/test_contracts/nda_sample_1.pdf
```

---

## 6. RAG Knowledge Base

### Collection: `templates`
Standard, well-drafted contract examples for comparison.

| File | Purpose |
|---|---|
| `employment1-3.pdf` | Standard employment agreement references |
| `NDA1-3.pdf` | Standard NDA references |
| `vendor1-2.pdf` | Standard vendor/service agreement references |

### Collection: `knowledge`
Legal rules, context, and clause definitions.

| File | Purpose |
|---|---|
| `laws/pdpa_2010.pdf` | Data protection obligations |
| `laws/employment_act.pdf` | Statutory employment minimums |
| `laws/contracts_act_1950.pdf` | What makes a contract valid |
| `laws/limitation_act_1953.pdf` | Time limits for legal claims |
| `laws/stamp_act_1949.pdf` | Stamping requirements |
| `guides/business_agreement_guide.txt` | Practical contract reading guide |
| `guides/pdpa_compliance_guide.txt` | PDPA compliance checklist |
| `guides/rulesandrulings_barconcil.pdf` | Malaysian Bar Council guidance |
| `written/malaysia_context.md` | Malaysian jurisdiction context (custom) |
| `written/predatory_clauses.md` | Known predatory clause patterns (custom) |
| `written/clause_explanations.md` | Plain English clause definitions (custom) |

---

## 7. Tech Stack

| Layer | Technology | Why |
|---|---|---|
| UI | Chainlit | Built for chat + file upload, deploys easily |
| LLM | Claude API (claude-sonnet) | Best reasoning for legal analysis |
| Agent orchestration | LangGraph | Multi-node stateful workflow with loops |
| LLM framework | LangChain | Prompt templates, LLM wrappers, document loaders |
| Vector database | ChromaDB | Local, persistent, no external service needed |
| Embeddings | all-MiniLM-L6-v2 | Free, runs locally, good for legal text |
| Guardrails | Guardrails AI | Schema validation, hallucination detection |
| Tool integration | MCP | Structured external tool calls |
| PDF reading | PyMuPDF (fitz) | Fast, reliable text extraction |
| DOCX reading | python-docx | Native DOCX parsing |
| Deployment | Hugging Face Spaces | Free, public URL, no server management |

---

## 8. Data Flow (End to End)

```
1. User uploads contract.pdf via Chainlit
2. app.py extracts text using PyMuPDF
3. LangGraph starts: state initialised with raw_text
4. classify_node: LLM identifies contract type (e.g. "Employment")
5. extract_node: parallel LLM calls extract 8 clause categories
6. rag_node:
   - For each finding, query templates collection for comparison
   - Query knowledge collection for Malaysian legal context
   - Attach retrieved chunks to state as rag_context
7. compile_node:
   - LLM scores risk (Low/Medium/High) with reasoning
   - Compiles full report JSON using rag_context as grounding
8. guardrails_node:
   - Validates report against report_schema.json
   - Checks no empty clause locations, no hallucination phrases
   - PASS: returns report to app.py
   - FAIL: loops back to compile_node (max 2 retries)
9. app.py renders report in Chainlit:
   - Risk score badge (green/amber/red)
   - Findings table with severity colours
   - Missing clauses list
   - Download report button
10. User can ask follow-up questions
    - RAG over uploaded contract answers from source text
```

---

## 9. Report Output Example

```
CONTRACT TYPE: Employment Agreement
RISK SCORE: 🔴 HIGH

SUMMARY
This employment contract contains several terms below Malaysian statutory 
minimums and an overbroad non-compete clause that may not be enforceable.
Review findings below before signing.

FINDINGS

🔴 HIGH — Non-Compete Clause (Section 8.1)
Issue: Non-compete duration is 3 years, scope is nationwide.
Plain English: You cannot work in the same industry anywhere in Malaysia 
for 3 years after leaving.
Recommendation: Negotiate down to 12 months, limited to Klang Valley.
Based on: malaysia_context.md — Non-compete enforceability in Malaysia

🟡 MEDIUM — Annual Leave (Section 5.2)  
Issue: Contract states 7 days annual leave per year.
Plain English: This is below the legal minimum of 8 days for employees 
under 2 years of service.
Recommendation: Request amendment to minimum 8 days as per Employment Act 1955.
Based on: employment_act.pdf — Section 60E

🟢 LOW — Governing Law (Section 12)
Issue: Governing law is Malaysia — this is correct for a local employer.
Plain English: Disputes will be handled in Malaysian courts.
No action needed.

MISSING CLAUSES
- No data protection / PDPA clause (required if employer handles personal data)
- No grievance procedure mentioned

⚠️ DISCLAIMER
This analysis is for informational purposes only and does not constitute 
legal advice. Consult a qualified Malaysian lawyer before signing.
```

---

## 10. Deployment

### Local development
```bash
source venv/bin/activate
python3 scripts/ingest_all.py    # one-time setup
chainlit run app.py              # start the app
```

### Hugging Face Spaces
- Create a new Space (Chainlit template)
- Push code via Git
- Add `ANTHROPIC_API_KEY` as a Space secret
- Run `ingest_all.py` as part of the startup script
- Public URL auto-generated: `huggingface.co/spaces/yourname/contractlens`

---

## 11. Build Order

| Step | File | Status |
|---|---|---|
| 1 | RAG knowledge base (all files in `rag/`) | ✅ Done |
| 2 | `rag/ingest.py` | 🔄 In progress |
| 3 | `rag/retriever.py` | ⬜ Next |
| 4 | `agent/state.py` | ⬜ |
| 5 | `agent/prompts.py` | ⬜ |
| 6 | `agent/nodes.py` | ⬜ |
| 7 | `agent/graph.py` | ⬜ |
| 8 | `guardrails/schemas/report_schema.json` | ⬜ |
| 9 | `guardrails/validators.py` | ⬜ |
| 10 | `mcp/tools.py` + `mcp/servers/` | ⬜ |
| 11 | `app.py` | ⬜ |
| 12 | `scripts/ingest_all.py` + `test_agent.py` | ⬜ |
| 13 | Deploy to Hugging Face Spaces | ⬜ |