import os
import tempfile
import docx
import chainlit as cl
from langchain_community.document_loaders import PyPDFLoader
from agent.graph import graph
from agent.llm import llm
from agent.prompts import QA_PROMPT

def extract_text_from_pdf(file_path: str) -> str:
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])

def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def format_report_html(report: dict) -> str:
    """Formats the structured report dict into a premium, beautiful HTML template."""
    contract_type = report.get("contract_type", "Unknown")
    risk_score = report.get("risk_score", "Low")
    summary = report.get("summary", "")
    findings = report.get("findings", [])
    missing_clauses = report.get("missing_clauses", [])
    positive_findings = report.get("positive_findings", [])
    disclaimer = report.get("disclaimer", "")
    
    # Severity color mapping
    risk_badges = {
        "High": '<span style="background-color: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 9999px; font-weight: 600; font-size: 14px;">🔴 High Risk</span>',
        "Medium": '<span style="background-color: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 9999px; font-weight: 600; font-size: 14px;">🟡 Medium Risk</span>',
        "Low": '<span style="background-color: #d1fae5; color: #065f46; padding: 4px 12px; border-radius: 9999px; font-weight: 600; font-size: 14px;">🟢 Low Risk</span>'
    }
    
    risk_badge = risk_badges.get(risk_score, risk_score)
    
    html = f"""
    <div style="font-family: 'Outfit', 'Inter', sans-serif; max-width: 800px; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); padding: 24px; border-left: 6px solid {'#ef4444' if risk_score == 'High' else '#f59e0b' if risk_score == 'Medium' else '#10b981'};">
        <!-- Header -->
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f3f4f6; padding-bottom: 16px; margin-bottom: 20px;">
            <div>
                <h1 style="margin: 0; font-size: 24px; color: #1f2937; font-weight: 700;">ContractLens Analysis Report</h1>
                <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 14px;">Contract Type: <strong>{contract_type}</strong></p>
            </div>
            <div>
                {risk_badge}
            </div>
        </div>
        
        <!-- Summary -->
        <div style="background: #f9fafb; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
            <h3 style="margin: 0 0 8px 0; color: #374151; font-size: 16px; font-weight: 600;">Executive Summary</h3>
            <p style="margin: 0; color: #4b5563; font-size: 14px; line-height: 1.6;">{summary}</p>
        </div>
    """
    
    # Findings
    if findings:
        html += '<h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 18px; font-weight: 700; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px;">Key Findings & Risks</h3>'
        for f in findings:
            sev = f.get("severity", "Low")
            badge_color = "#ef4444" if sev == "High" else "#f59e0b" if sev == "Medium" else "#10b981"
            bg_color = "#fef2f2" if sev == "High" else "#fffbeb" if sev == "Medium" else "#ecfdf5"
            text_color = "#991b1b" if sev == "High" else "#92400e" if sev == "Medium" else "#065f46"
            
            html += f"""
            <div style="background: {bg_color}; border: 1px solid {badge_color}40; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #374151; font-size: 15px;">{f.get("category", "General")} <span style="font-weight: 400; color: #6b7280; font-size: 13px;">({f.get("clause_location", "N/A")})</span></span>
                    <span style="font-size: 12px; font-weight: 600; text-transform: uppercase; background: {badge_color}20; color: {text_color}; padding: 2px 8px; border-radius: 4px;">{sev}</span>
                </div>
                <p style="margin: 0 0 8px 0; color: #1f2937; font-size: 14px; line-height: 1.5;"><strong>Issue:</strong> {f.get("issue")}</p>
                <p style="margin: 0 0 8px 0; color: #4b5563; font-size: 14px; line-height: 1.5;"><strong>What it means:</strong> {f.get("plain_english")}</p>
                <p style="margin: 0 0 8px 0; color: #047857; font-size: 14px; line-height: 1.5;"><strong>Recommendation:</strong> {f.get("recommendation")}</p>
                <p style="margin: 0; color: #6b7280; font-size: 12px;"><strong>Source reference:</strong> {f.get("source")}</p>
            </div>
            """
            
    # Missing Clauses
    if missing_clauses:
        html += f"""
        <div style="margin-top: 24px;">
            <h3 style="margin: 0 0 10px 0; color: #b91c1c; font-size: 16px; font-weight: 600;">⚠️ Missing Recommended Clauses</h3>
            <ul style="margin: 0; padding-left: 20px; color: #4b5563; font-size: 14px; line-height: 1.6;">
        """
        for c in missing_clauses:
            html += f"<li style='margin-bottom: 4px;'>{c}</li>"
        html += "</ul></div>"
        
    # Positive Findings
    if positive_findings:
        html += f"""
        <div style="margin-top: 24px;">
            <h3 style="margin: 0 0 10px 0; color: #047857; font-size: 16px; font-weight: 600;">✅ Positive / Fair Terms</h3>
            <ul style="margin: 0; padding-left: 20px; color: #4b5563; font-size: 14px; line-height: 1.6;">
        """
        for c in positive_findings:
            html += f"<li style='margin-bottom: 4px;'>{c}</li>"
        html += "</ul></div>"
        
    # Disclaimer
    if disclaimer:
        html += f"""
        <div style="margin-top: 28px; padding-top: 16px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 11px; line-height: 1.5; font-style: italic;">
            {disclaimer}
        </div>
        """
        
    html += "</div>"
    return html

@cl.on_chat_start
async def start():
    # Elegant landing welcome message
    welcome_text = """
    # Welcome to **ContractLens** 🔍
    
    Review your contracts instantly without requiring legal expertise.
    Upload your contract as a **PDF** or **DOCX** file to begin your structured risk report.
    """
    await cl.Message(content=welcome_text).send()
    
    # Prompt for file upload
    files = None
    while files is None:
        files = await cl.AskFileMessage(
            content="Please upload your legal contract file (PDF or DOCX) to get started:",
            accept={
                "application/pdf": [".pdf"],
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"]
            },
            max_size_mb=10
        ).send()
        
    file = files[0]
    
    # Process text extraction
    msg = cl.Message(content=f"Reading contract contents from **{file.name}**...")
    await msg.send()
    
    try:
        temp_file_path = file.path
        # Extract text based on file format
        ext = os.path.splitext(file.name)[1].lower()
        if ext == ".pdf":
            raw_text = extract_text_from_pdf(temp_file_path)
        elif ext == ".docx":
            raw_text = extract_text_from_docx(temp_file_path)
        else:
            raise ValueError("Unsupported file format.")
    except Exception as e:
        await cl.Message(content=f"❌ Error reading file: {e}").send()
        return
        
    cl.user_session.set("contract_text", raw_text)
    
    # Run the LangGraph agent
    msg.content = "Analyzing contract clauses using LangGraph and performing RAG lookup against standard templates and Malaysian laws..."
    await msg.update()
    
    try:
        # Trigger the workflow
        initial_state = {"raw_text": raw_text}
        
        # We run the agent synchronously in a separate thread so it doesn't block the async event loop
        final_state = await cl.make_async(graph.invoke)(initial_state)
        
        report = final_state.get("report", {})
        cl.user_session.set("contract_type", final_state.get("contract_type"))
        
        # Render html report
        html_report = format_report_html(report)
        
        msg.content = "Analysis complete!"
        await msg.update()
        
        # Send html card report to the chat
        await cl.Message(content=html_report).send()
        
        # Guide the user for follow up Q&A
        await cl.Message(
            content="You can now ask follow-up questions about the contract. E.g.:\n"
            "- *'What is the notice period for termination?'*\n"
            "- *'Are the payment terms fair?'*\n"
            "- *'Is the non-compete clause enforceable in Malaysia?'*"
        ).send()
        
    except Exception as e:
        await cl.Message(content=f"❌ Error during contract analysis: {e}").send()

@cl.on_message
async def main(message: cl.Message):
    # Check if contract has been uploaded
    raw_text = cl.user_session.get("contract_text")
    if not raw_text:
        await cl.Message(content="Please upload a contract file first using the file upload button.").send()
        return
        
    # Act as Q&A chat bot grounded on the uploaded contract
    question = message.content
    
    # Send processing status loader
    msg = cl.Message(content="Searching contract...")
    await msg.send()
    
    try:
        prompt = QA_PROMPT.format(contract_text=raw_text, question=question)
        answer = await cl.make_async(llm.invoke)(prompt)
        
        msg.content = answer
        await msg.update()
    except Exception as e:
        msg.content = f"❌ Error retrieving answer: {e}"
        await msg.update()
