import json
import logging
from typing import Dict, Any, List

from agent.llm import llm
from agent.state import ContractState
from agent.prompts import (
    CLASSIFY_PROMPT,
    EXTRACT_CLAUSE_PROMPT,
    COMPILE_REPORT_PROMPT
)
from rag.retriever import query_templates, query_knowledge
from validation.validators import validate_report

# Configure logger
logger = logging.getLogger("contractlens.agent.nodes")
logging.basicConfig(level=logging.INFO)

# 8 clause categories requested by system specifications
CLAUSE_CATEGORIES = {
    "Payment & commercial terms": "Payment terms, invoicing, rates, late payment interest, deposits.",
    "Termination & notice": "How the contract can be terminated, notice period required, immediate termination triggers.",
    "Liability & indemnification": "Limits of liability, caps on damage claims, who indemnifies whom for what losses.",
    "IP ownership": "Who owns intellectual property created during the contract, transfer of IP, license grants.",
    "Data protection": "Compliance with PDPA, personal data handling, security measures, data breach notifications.",
    "Non-compete / restraint": "Restrictions on working for competitors, duration of restraint, geographic scope, non-solicitation of clients/staff.",
    "Governing law & disputes": "Which country's laws govern, which courts have jurisdiction, arbitration rules (e.g. AIAC).",
    "Missing standard clauses": "Checking if standard boilerplate clauses like mutual NDAs, force majeure, severability, entire agreement are absent."
}

def parse_json_response(text: str) -> Dict[str, Any]:
    """Cleans markdown blocks and parses JSON output from LLM."""
    clean_text = text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    elif clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()
    return json.loads(clean_text)

# 1. Ingest Node
def ingest_node(state: ContractState) -> Dict[str, Any]:
    """Prepares and validates raw contract text in the state."""
    logger.info("Ingesting contract...")
    text = state.get("raw_text", "")
    if not text:
        raise ValueError("No raw contract text provided in the state.")
        
    return {
        "raw_text": text.strip(),
        "clauses": {},
        "rag_context": {},
        "findings": [],
        "risk_score": "Low",
        "report": {},
        "validation_errors": [],
        "retry_count": 0,
        "messages": []
    }

# 2. Classify Node
def classify_node(state: ContractState) -> Dict[str, Any]:
    """Classifies the contract type (NDA / Employment / Vendor / Freelance / Unknown)."""
    logger.info("Classifying contract type...")
    prompt = CLASSIFY_PROMPT.format(contract_text=state["raw_text"][:4000]) # Limit input size for classification
    category = llm.invoke(prompt).strip()
    
    # Sanitize category response
    valid_categories = ["NDA", "Employment", "Vendor", "Freelance", "Unknown"]
    matched_category = "Unknown"
    for cat in valid_categories:
        if cat.lower() in category.lower():
            matched_category = cat
            break
            
    logger.info(f"Classified as: {matched_category}")
    return {"contract_type": matched_category}

# 3. Extract Node
def extract_node(state: ContractState) -> Dict[str, Any]:
    """Parallel/batch extracts the 8 standard clause categories from the contract."""
    logger.info("Extracting contract clauses...")
    prompts = [
        EXTRACT_CLAUSE_PROMPT.format(
            contract_text=state["raw_text"],
            category=category,
            description=desc
        )
        for category, desc in CLAUSE_CATEGORIES.items()
    ]
    
    # Run batch LLM invocation
    outputs = llm.batch(prompts)
    
    clauses = {
        category: output.strip()
        for category, output in zip(CLAUSE_CATEGORIES.keys(), outputs)
    }
    
    return {"clauses": clauses}

# 4. RAG Node
def rag_node(state: ContractState) -> Dict[str, Any]:
    """Queries vector database to fetch relevant law guidelines and templates."""
    logger.info("Querying vector database for RAG context...")
    rag_context = {}
    
    for category, text in state["clauses"].items():
        if text and text.strip().lower() != "none":
            # Search standard templates (similarity matching)
            template_docs = query_templates(text, n=2)
            # Search laws and regulations guidelines
            knowledge_docs = query_knowledge(text, n=2)
            
            rag_context[category] = {
                "templates": [
                    {"source": doc.metadata.get("source_file"), "content": doc.page_content}
                    for doc in template_docs
                ],
                "knowledge": [
                    {"source": doc.metadata.get("source_file"), "content": doc.page_content}
                    for doc in knowledge_docs
                ]
            }
            
    return {"rag_context": rag_context}

# 5. Compile Node
def compile_node(state: ContractState) -> Dict[str, Any]:
    """Compiles the structured legal findings and risk report using context."""
    logger.info(f"Compiling structured report (Retry count: {state.get('retry_count', 0)})...")
    
    # Format clauses and RAG context into prompt text
    extracted_clauses_str = ""
    for category, text in state["clauses"].items():
        extracted_clauses_str += f"### {category}\n{text}\n\n"
        
    rag_context_str = ""
    for category, context in state["rag_context"].items():
        rag_context_str += f"### {category}\n"
        if context.get("templates"):
            rag_context_str += "Standard templates details:\n"
            for item in context["templates"]:
                rag_context_str += f"- Source [{item['source']}]: {item['content']}\n"
        if context.get("knowledge"):
            rag_context_str += "Malaysian Law details:\n"
            for item in context["knowledge"]:
                rag_context_str += f"- Source [{item['source']}]: {item['content']}\n"
        rag_context_str += "\n"

    errors_str = "None"
    if state.get("validation_errors"):
        errors_str = "\n".join([f"- {err}" for err in state["validation_errors"]])
        
    prompt = COMPILE_REPORT_PROMPT.format(
        contract_type=state["contract_type"],
        extracted_clauses=extracted_clauses_str,
        rag_context=rag_context_str,
        validation_errors=errors_str
    )
    
    response = llm.invoke(prompt)
    
    try:
        report = parse_json_response(response)
        risk_score = report.get("risk_score", "Low")
        findings = report.get("findings", [])
    except Exception as e:
        logger.error(f"Failed to parse compiled JSON report: {e}")
        # Build a fallback dict if LLM outputs malformed JSON
        report = {
            "contract_type": state["contract_type"],
            "risk_score": "High",
            "summary": "Error: Failed to compile JSON report from the LLM.",
            "findings": [
                {
                    "category": "System Error",
                    "clause_location": "N/A",
                    "issue": "The AI produced an unparseable JSON report.",
                    "plain_english": "The review could not complete cleanly.",
                    "severity": "High",
                    "recommendation": "Try running the analysis again.",
                    "source": "System"
                }
            ],
            "missing_clauses": [],
            "positive_findings": [],
            "disclaimer": "This analysis failed to generate successfully due to JSON parsing error."
        }
        risk_score = "High"
        findings = report["findings"]
        
    return {
        "report": report,
        "risk_score": risk_score,
        "findings": findings
    }

# 6. Guardrails Node
def guardrails_node(state: ContractState) -> Dict[str, Any]:
    """Validates compiled report schema, constraints, and contents."""
    logger.info("Executing output validation guardrails...")
    report = state.get("report", {})
    errors = validate_report(report)
    
    retry_count = state.get("retry_count", 0)
    if errors:
        logger.warning(f"Validation failed with {len(errors)} errors: {errors}")
        return {"validation_errors": errors, "retry_count": retry_count + 1}
    else:
        logger.info("Validation passed successfully.")
        return {"validation_errors": errors}
