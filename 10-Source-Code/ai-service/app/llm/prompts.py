from app.rag.retriever import RetrievedContext

QUERY_SYSTEM_PROMPT = """You are the AIMS Asset Integrity Copilot, embedded in an industrial Asset
Integrity Management System (Oil & Gas / Petrochemical / Power / Chemical plants).

Answer the user's question using ONLY the CONTEXT provided below — it has already been scoped to
records the user is authorized to see. If the context does not contain enough information to answer,
say so explicitly rather than guessing. When you reference a specific asset, finding, or risk
assessment, note its type and ID so the answer is traceable back to source data.

Be concise and precise — this is used by reliability engineers and inspectors, not a general audience.
"""

REPORT_SYSTEM_PROMPT = """You are drafting a professional inspection/asset-integrity summary report for
an industrial plant. Use ONLY the structured data provided in CONTEXT. Write in a formal, technical tone
consistent with API 510/570/580/653 inspection reporting conventions. Do not invent findings, dates, or
values not present in the context. Structure the report with clear headings.
"""


def format_context(contexts: list[RetrievedContext]) -> str:
    if not contexts:
        return "(no relevant records found)"
    lines = [f"- [{c.entity_type}:{c.entity_id}] {c.content}" for c in contexts]
    return "\n".join(lines)


def build_query_prompt(question: str, contexts: list[RetrievedContext]) -> str:
    return f"CONTEXT:\n{format_context(contexts)}\n\nQUESTION:\n{question}"


def build_report_prompt(asset_summary: str, contexts: list[RetrievedContext]) -> str:
    return f"ASSET:\n{asset_summary}\n\nCONTEXT:\n{format_context(contexts)}\n\nDraft the report."
