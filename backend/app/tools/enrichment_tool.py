"""
Lead Enrichment Tool.
Extracts and enriches lead information using LLM-based analysis.
Never hallucinates - returns "Unknown" for unavailable information.
"""
from typing import Dict, Any, Optional
from app.llm_client import LLMClient
from app.database import SessionLocal, AuditLog
from datetime import datetime


class LeadEnrichmentTool:
    """
    Tool for enriching lead data with company and contact information.
    Uses LLM to extract structured data from lead input.
    """

    def __init__(self):
        self.llm = LLMClient()

    def _build_enrichment_prompt(self, lead: Dict[str, Any]) -> str:
        """Build the prompt for lead enrichment."""
        return f"""
You are a lead enrichment specialist. Extract and enrich the following lead information.

LEAD INPUT:
- Name: {lead.get('name', 'Unknown')}
- Email: {lead.get('email', 'Unknown')}
- Company: {lead.get('company', 'Unknown')}
- Role: {lead.get('role', 'Unknown')}
- Source: {lead.get('source', 'Unknown')}
- Notes: {lead.get('notes', 'None')}

INSTRUCTIONS:
1. Extract as much information as possible from the lead input.
2. For any field where information is NOT available, return "Unknown".
3. NEVER hallucinate or invent information.
4. If the company is known, infer industry from company name if obvious (e.g., "Acme Corp" -> unknown, "Stripe" -> Fintech).
5. Be conservative - only state what can be reasonably inferred.

Return a JSON object with these fields:
{{
    "company": "extracted or Unknown",
    "industry": "extracted or Unknown",
    "company_size": "extracted or Unknown",
    "employee_count": "extracted or Unknown",
    "revenue": "extracted or Unknown",
    "role": "extracted or Unknown",
    "job_title": "extracted or Unknown",
    "location": "extracted or Unknown",
    "buying_signals": ["list of signals or empty array"],
    "website": "extracted or Unknown",
    "linkedin": "extracted or Unknown",
    "technology_stack": ["list or empty array"],
    "funding": "extracted or Unknown",
    "recent_news": "extracted or Unknown",
    "decision_maker_level": "C-Level / VP / Director / Manager / Individual / Unknown",
    "enrichment_confidence": "HIGH / MEDIUM / LOW"
}}
"""

    def enrich(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a lead with additional information.

        Args:
            lead: Dictionary containing lead information (name, email, company, role, etc.)

        Returns:
            Enriched profile dictionary
        """
        prompt = self._build_enrichment_prompt(lead)
        result = self.llm.call_json(
            system_prompt="You are a lead enrichment specialist. Extract structured data from lead information. Never hallucinate - return 'Unknown' for unavailable fields.",
            user_prompt=prompt,
            temperature=0.1,
        )

        if not result["success"]:
            # Return a safe default on error - include raw lead data for scoring
            return {
                "company": lead.get("company", "Unknown"),
                "industry": "Unknown",
                "company_size": "Unknown",
                "employee_count": "Unknown",
                "revenue": "Unknown",
                "role": lead.get("role", "Unknown"),
                "job_title": lead.get("role", "Unknown"),
                "location": "Unknown",
                "buying_signals": [lead.get("notes", "")] if lead.get("notes") else [],
                "website": lead.get("source", "Unknown"),
                "linkedin": "Unknown",
                "technology_stack": [],
                "funding": "Unknown",
                "recent_news": "Unknown",
                "decision_maker_level": "Unknown",
                "enrichment_confidence": "LOW",
                "notes": lead.get("notes", ""),
                "source": lead.get("source", ""),
                "_error": result.get("error"),
            }

        enriched = result["parsed"]

        # Ensure all required fields exist
        defaults = {
            "company": lead.get("company", "Unknown"),
            "industry": "Unknown",
            "company_size": "Unknown",
            "employee_count": "Unknown",
            "revenue": "Unknown",
            "role": lead.get("role", "Unknown"),
            "job_title": lead.get("role", "Unknown"),
            "location": "Unknown",
            "buying_signals": [],
            "website": "Unknown",
            "linkedin": "Unknown",
            "technology_stack": [],
            "funding": "Unknown",
            "recent_news": "Unknown",
            "decision_maker_level": "Unknown",
            "enrichment_confidence": "LOW",
        }

        for key, default_value in defaults.items():
            if key not in enriched or enriched[key] is None:
                enriched[key] = default_value

        return enriched