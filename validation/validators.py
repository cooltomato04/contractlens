from typing import List, Dict, Any

def validate_report(report: Dict[str, Any]) -> List[str]:
    """
    Validates a compiled contract review report against strict guidelines.
    Returns a list of validation error strings. If list is empty, report is valid.
    """
    errors = []
    
    if not isinstance(report, dict):
        return ["Report is not a valid JSON dictionary."]
        
    # 1. Validate contract_type
    contract_type = report.get("contract_type")
    if not contract_type or not isinstance(contract_type, str):
        errors.append("contract_type is missing or not a string.")
        
    # 2. Validate risk_score
    risk_score = report.get("risk_score")
    if risk_score not in ["Low", "Medium", "High"]:
        errors.append(f"risk_score must be 'Low', 'Medium', or 'High'. Got: '{risk_score}'")
        
    # 3. Validate summary length (50-500 chars)
    summary = report.get("summary", "")
    if not isinstance(summary, str):
        errors.append("summary must be a string.")
    elif len(summary) < 50 or len(summary) > 500:
        errors.append(f"summary must be between 50 and 500 characters. Current length: {len(summary)}")
        
    # 4. Validate disclaimer presence
    disclaimer = report.get("disclaimer", "")
    if not disclaimer or not isinstance(disclaimer, str) or len(disclaimer.strip()) == 0:
        errors.append("disclaimer field must be present and non-empty.")
        
    # 5. Validate findings count (1 to 20)
    findings = report.get("findings", [])
    if not isinstance(findings, list):
        errors.append("findings must be a list of objects.")
        findings = []
        
    if len(findings) < 1 or len(findings) > 20:
        errors.append(f"findings list must contain between 1 and 20 findings. Current count: {len(findings)}")
        
    # 6. Validate each individual finding
    forbidden_phrases = ["i think", "probably", "i believe"]
    for idx, finding in enumerate(findings):
        if not isinstance(finding, dict):
            errors.append(f"Finding at index {idx} is not a dictionary.")
            continue
            
        category = finding.get("category", "")
        location = finding.get("clause_location", "")
        issue = finding.get("issue", "")
        severity = finding.get("severity", "")
        plain_english = finding.get("plain_english", "")
        recommendation = finding.get("recommendation", "")
        
        # Locations must not be empty
        if not location or not str(location).strip():
            errors.append(f"Finding at index {idx} is missing a valid 'clause_location'.")
            
        if not category:
            errors.append(f"Finding at index {idx} is missing 'category'.")
            
        if not issue:
            errors.append(f"Finding at index {idx} is missing 'issue'.")
            
        if severity not in ["Low", "Medium", "High"]:
            errors.append(f"Finding at index {idx} severity must be 'Low', 'Medium', or 'High'. Got: '{severity}'")
            
        # Check for hallucination/uncertainty signals
        all_text = f"{issue} {plain_english} {recommendation}".lower()
        for phrase in forbidden_phrases:
            if phrase in all_text:
                errors.append(f"Finding at index {idx} contains uncertain/hallucinated phrase: '{phrase}'.")
                
    return errors
