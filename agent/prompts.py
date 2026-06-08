from langchain_core.prompts import PromptTemplate

# Prompt to classify the type of contract
CLASSIFY_PROMPT = PromptTemplate.from_template(
    "You are a legal document classifier. Classify the following contract into exactly one of "
    "these categories: NDA, Employment, Vendor, Freelance, Unknown.\n\n"
    "Respond with ONLY the category name and nothing else.\n\n"
    "Contract text:\n{contract_text}\n\n"
    "Category:"
)

# Prompt to extract clauses for a specific category
EXTRACT_CLAUSE_PROMPT = PromptTemplate.from_template(
    "You are an expert legal assistant. Extract all clauses related to the category '{category}' from the contract below.\n"
    "Category Description: {description}\n\n"
    "Instructions:\n"
    "1. Extract the exact text of the relevant clauses including their section/clause numbers (e.g., 'Section 4.1').\n"
    "2. If no clauses relate to this category, respond with 'None'.\n"
    "3. Respond with only the extracted clauses. Do not add conversational comments.\n\n"
    "Contract text:\n{contract_text}\n\n"
    "Extracted clauses:"
)

# Prompt to compile the structured report using the extracted clauses and RAG context
COMPILE_REPORT_PROMPT = PromptTemplate.from_template(
    "You are a senior Malaysian legal risk analyst. Compile a structured contract review report in JSON format "
    "based on the contract details and the RAG context retrieved from standard templates and Malaysian laws.\n\n"
    "Contract Type: {contract_type}\n"
    "Extracted Clauses:\n{extracted_clauses}\n"
    "RAG Context:\n{rag_context}\n"
    "Previous Validation Errors (if any): {validation_errors}\n\n"
    "You MUST output a single valid JSON object conforming exactly to this schema:\n"
    "{{\n"
    "  \"contract_type\": \"{contract_type}\",\n"
    "  \"risk_score\": \"Low\" | \"Medium\" | \"High\",\n"
    "  \"summary\": \"plain English summary of findings (50-500 characters)\",\n"
    "  \"findings\": [\n"
    "    {{\n"
    "      \"category\": \"clause category name\",\n"
    "      \"clause_location\": \"exact section (e.g. Section 4.2)\",\n"
    "      \"issue\": \"description of what is wrong or risky\",\n"
    "      \"plain_english\": \"what this means for the user in simple terms\",\n"
    "      \"severity\": \"Low\" | \"Medium\" | \"High\",\n"
    "      \"recommendation\": \"what the user should ask to change\",\n"
    "      \"source\": \"the law or standard template this finding is based on\"\n"
    "    }}\n"
    "  ],\n"
    "  \"missing_clauses\": [\"list of important standard clauses that are missing (e.g., no PDPA clause, no termination clause)\"],\n"
    "  \"positive_findings\": [\"list of fair or correct clauses found in the contract (e.g., correct governing law)\"],\n"
    "  \"disclaimer\": \"This analysis is for informational purposes only and does not constitute legal advice. Consult a qualified Malaysian lawyer before signing.\"\n"
    "}}\n\n"
    "Rules:\n"
    "1. Respond ONLY with valid JSON. Do not wrap it in markdown code blocks or add text before/after.\n"
    "2. Ground every finding in the contract details and RAG context.\n"
    "3. Do not use vague or uncertain language like 'I think', 'probably', or 'I believe' in the findings.\n"
    "4. Ensure 'clause_location' is never empty. Every finding must point to a specific section.\n"
    "5. Ensure minimum 1 finding, maximum 20 findings.\n"
    "6. Address any previous validation errors explicitly in your corrections.\n\n"
    "JSON Report:"
)

# Prompt for follow-up QA based on the contract
QA_PROMPT = PromptTemplate.from_template(
    "You are a helpful legal assistant for ContractLens. Answer the user's question about the uploaded contract "
    "using ONLY the contract text provided below.\n\n"
    "If the answer cannot be found in the contract, say: 'I cannot find the answer to this question in the contract text.'\n"
    "Do not assume or make up legal facts.\n\n"
    "Contract text:\n{contract_text}\n\n"
    "User Question: {question}\n\n"
    "Answer:"
)
