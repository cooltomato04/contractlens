from typing import TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage

class ContractState(TypedDict):
    raw_text: str
    contract_type: str                   # NDA / Employment / Vendor / Freelance / Unknown
    clauses: Dict[str, str]              # extracted clause text by category
    rag_context: Dict[str, List[str]]    # retrieved templates/knowledge chunks by category
    findings: List[Dict[str, Any]]       # list of flagged issues
    risk_score: str                      # Low / Medium / High
    report: Dict[str, Any]               # final validated report object
    validation_errors: List[str]         # list of guardrails errors triggers retry
    messages: List[BaseMessage]          # conversation/reasoning history
    retry_count: int                     # guardrails loop counter (max 2 retries)
