"""
Email Drafting and Sending Tool.
Generates personalized first-touch emails based on enriched lead data.
Requires human approval token before sending.
"""
from typing import Dict, Any, Optional
from app.llm_client import LLMClient


class EmailTool:
    """
    Handles email draft generation and sending with human approval gate.
    Never sends email without a valid approval token.
    """

    def __init__(self):
        self.llm = LLMClient()

    def _build_email_prompt(self, lead: Dict[str, Any], enriched: Dict[str, Any]) -> str:
        """Build the prompt for generating a personalized email."""
        return f"""
You are a sales email specialist. Draft a personalized first-touch outreach email for a lead.

LEAD INFORMATION:
- Name: {lead.get('name', 'There')}
- Company: {enriched.get('company', lead.get('company', 'their company'))}
- Role: {enriched.get('role', lead.get('role', 'Unknown'))}
- Industry: {enriched.get('industry', 'Unknown')}
- Company Size: {enriched.get('company_size', 'Unknown')}
- Location: {enriched.get('location', 'Unknown')}
- Technology Stack: {enriched.get('technology_stack', [])}
- Recent News: {enriched.get('recent_news', 'Unknown')}
- Buying Signals: {enriched.get('buying_signals', [])}

INSTRUCTIONS:
1. Write a concise, professional first-touch email.
2. Ground every statement in the enrichment data provided above.
3. NEVER invent company facts or make claims not supported by the data.
4. Structure: Subject line, greeting, personalization sentence, pain point, value proposition, CTA, signature.
5. Keep it to 3-4 short paragraphs maximum.
6. Use a warm but professional tone.
7. Personalize based on their specific industry, role, and company.

Return a JSON object:
{{
    "subject": "Email subject line",
    "body": "Full email body with proper line breaks",
    "personalization_summary": "Brief explanation of what was personalized and why",
    "cta": "The call to action used"
}}
"""

    def draft_email(self, lead: Dict[str, Any], enriched_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a personalized email draft based on lead and enrichment data.

        Args:
            lead: Original lead data
            enriched_profile: Enriched lead profile data

        Returns:
            Dictionary with subject, body, personalization_summary, and cta
        """
        prompt = self._build_email_prompt(lead, enriched_profile)
        result = self.llm.call_json(
            system_prompt="You are a sales email specialist. Generate personalized, professional outreach emails. Never invent company facts - ground every statement in provided data.",
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=1500,
        )

        if not result["success"]:
            return {
                "subject": f"Introduction - {enriched_profile.get('company', '')}",
                "body": f"Hi {lead.get('name', 'there')},\n\nI'd love to connect and explore how we can help {enriched_profile.get('company', 'your company')} achieve better results.\n\nBest regards,\nSales Team",
                "personalization_summary": "Generic fallback due to generation error",
                "cta": "Reply to schedule a call",
                "_error": result.get("error"),
            }

        email = result["parsed"]

        # Ensure required fields
        if "subject" not in email:
            email["subject"] = f"Introduction - {enriched_profile.get('company', '')}"
        if "body" not in email:
            email["body"] = f"Hi {lead.get('name', 'there')},\n\nI'd love to connect.\n\nBest regards,\nSales Team"
        if "personalization_summary" not in email:
            email["personalization_summary"] = "Standard outreach"
        if "cta" not in email:
            email["cta"] = "Reply to schedule a call"

        return email

    def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        approval_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email. Requires a valid approval token.
        Without approval token, the email will NOT be sent.

        Args:
            recipient: Email address of the recipient
            subject: Email subject line
            body: Email body content
            approval_token: Token proving human approval was given

        Returns:
            Dictionary with success status and message
        """
        # Validate approval token
        if not approval_token or approval_token != "APPROVED":
            return {
                "success": False,
                "message": "Email cannot be sent without human approval. "
                          "Approval token is missing or invalid.",
                "sent": False,
            }

        # In production, this would integrate with an email service (SendGrid, SES, etc.)
        # For now, log the email as "sent" for demonstration
        return {
            "success": True,
            "message": f"Email approved and queued for delivery to {recipient}",
            "sent": True,
            "recipient": recipient,
            "subject": subject,
        }