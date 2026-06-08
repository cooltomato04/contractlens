import logging
from langgraph.graph import StateGraph, END
from agent.state import ContractState
from agent.nodes import (
    ingest_node,
    classify_node,
    extract_node,
    rag_node,
    compile_node,
    guardrails_node
)

logger = logging.getLogger("contractlens.agent.graph")

def routing_edge(state: ContractState) -> str:
    """Routes the workflow to END or compiles again based on validation results."""
    errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    
    if not errors:
        logger.info("Routing to END (Validation Passed).")
        return "end"
        
    if retry_count < 2:
        logger.warning(f"Routing to retry compile (Errors found, retry count: {retry_count}).")
        return "retry"
        
    logger.error("Routing to END (Max retries reached). Appending warning to report.")
    # Append warning to report summary since validation is still failing after retries
    report = state.get("report", {})
    if isinstance(report, dict):
        summary = report.get("summary", "")
        report["summary"] = f"[WARNING: Guardrails check failed partially] {summary}"
    return "end"

# Initialize StateGraph with the ContractState schema
workflow = StateGraph(ContractState)

# Add all process nodes
workflow.add_node("ingest", ingest_node)
workflow.add_node("classify", classify_node)
workflow.add_node("extract", extract_node)
workflow.add_node("rag", rag_node)
workflow.add_node("compile", compile_node)
workflow.add_node("guardrails", guardrails_node)

# Set the entry point node
workflow.set_entry_point("ingest")

# Define the sequence edges
workflow.add_edge("ingest", "classify")
workflow.add_edge("classify", "extract")
workflow.add_edge("extract", "rag")
workflow.add_edge("rag", "compile")
workflow.add_edge("compile", "guardrails")

# Define validation check conditional edge routing from guardrails
workflow.add_conditional_edges(
    "guardrails",
    routing_edge,
    {
        "end": END,
        "retry": "compile"
    }
)

# Compile graph into a runnable agent
graph = workflow.compile()
