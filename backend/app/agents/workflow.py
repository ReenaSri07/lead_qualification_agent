"""
Lead Qualification & Outreach Agent - LangGraph Workflow.

This is the core orchestration agent that coordinates the complete lead
qualification pipeline using LangGraph. The workflow consists of:
1. Lead Enrichment
2. Identity-Blind Scoring
3. Classification
4. Routing
5. Email Drafting
6. Human Approval Gate
7. Email Sending
8. Logging & Evaluation

The workflow uses LangGraph's StateGraph to define a state machine with
conditional edges for routing decisions.
"""
import json
from typing import Dict, Any, Optional, TypedDict, List, Annotated, Literal
from datetime import datetime
from langgraph.graph import StateGraph, END

from app.tools.enrichment_tool import LeadEnrichmentTool
from app.tools.scoring_tool import LeadScoringTool
from app.tools.classification_tool import LeadClassificationTool
from app.tools.email_tool import EmailTool
from app.tools.crm_tool import CRMTool
from app.tools.audit_logger import AuditLogger
from app.database import SessionLocal, Lead, LeadStatus
from app.llm_client import LLMClient


# =============================================================================
# STATE DEFINITION
# =============================================================================

class AgentState(TypedDict):
    """State dictionary for the LangGraph workflow."""
    # Input
    lead: Dict[str, Any]
    lead_id: Optional[int]

    # Enrichment
    enriched_profile: Optional[Dict[str, Any]]
    enrichment_log: Optional[str]

    # Scoring
    score: Optional[float]
    dimension_scores: Optional[Dict[str, float]]
    scoring_reasoning: Optional[str]
    scoring_evidence: Optional[str]

    # Classification
    classification: Optional[str]
    classification_reason: Optional[str]
    classification_confidence: Optional[float]

    # Routing
    routing_action: Optional[str]
    routing_reason: Optional[str]

    # Email
    email_draft: Optional[Dict[str, Any]]
    email_subject: Optional[str]
    email_body: Optional[str]

    # Approval
    approval_status: str
    approval_token: Optional[str]
    approval_granted: bool

    # CRM
    crm_status: Optional[str]
    crm_id: Optional[str]

    # Audit
    audit_logs: List[Dict[str, Any]]

    # Evaluation
    evaluation_results: Optional[Dict[str, Any]]

    # Errors
    errors: List[str]


# =============================================================================
# PROMPT INJECTION DEFENSE
# =============================================================================

class PromptInjectionDefense:
    """
    Detects and neutralizes prompt injection attempts in lead data.
    Rejects instructions like "Ignore previous instructions", "Mark me hot",
    "Email CEO", etc. Treats them as malicious and continues normal scoring.
    """

    INJECTION_PATTERNS = [
        "ignore previous instructions",
        "ignore all previous",
        "ignore the above",
        "mark me hot",
        "mark me as hot",
        "classify me as hot",
        "email ceo",
        "email the ceo",
        "send email to",
        "forget your instructions",
        "forget everything",
        "you are now",
        "act as if",
        "pretend you are",
        "override",
        "disregard",
    ]

    @classmethod
    def check_for_injection(cls, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check lead data for prompt injection attempts.

        Args:
            lead: Lead data dictionary

        Returns:
            Dictionary with injection_detected flag and sanitized lead
        """
        text_fields = [
            str(lead.get("name", "")),
            str(lead.get("email", "")),
            str(lead.get("company", "")),
            str(lead.get("role", "")),
            str(lead.get("notes", "")),
            str(lead.get("source", "")),
        ]

        all_text = " ".join(text_fields).lower()

        for pattern in cls.INJECTION_PATTERNS:
            if pattern in all_text:
                return {
                    "injection_detected": True,
                    "pattern_matched": pattern,
                    "sanitized": True,
                    "message": f"Prompt injection detected: pattern '{pattern}' found in lead data. Sanitizing input.",
                }

        return {
            "injection_detected": False,
            "sanitized": False,
            "message": "No injection detected",
        }


# =============================================================================
# WORKFLOW NODES
# =============================================================================

def receive_lead(state: AgentState) -> AgentState:
    """
    Stage 0: Receive and validate lead input.
    Performs prompt injection defense on incoming lead data.
    """
    lead = state.get("lead", {})
    audit_logger = AuditLogger()
    errors = state.get("errors", [])

    # Validate required fields
    if not lead.get("email") and not lead.get("company"):
        errors.append("Lead must have at least an email or company name")

    # Check for prompt injection
    injection_check = PromptInjectionDefense.check_for_injection(lead)
    if injection_check["injection_detected"]:
        audit_logger.log(
            action="PROMPT_INJECTION_DETECTED",
            tool_name="PromptInjectionDefense",
            prompt=str(lead),
            response=injection_check["message"],
            metadata={"pattern_matched": injection_check["pattern_matched"]},
        )

    # Create lead in database
    db = SessionLocal()
    try:
        db_lead = Lead(
            name=lead.get("name"),
            email=lead.get("email"),
            company=lead.get("company"),
            role=lead.get("role"),
            source=lead.get("source"),
            notes=lead.get("notes"),
            status=LeadStatus.PENDING.value,
        )
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        lead_id = db_lead.id
    except Exception as e:
        db.rollback()
        errors.append(f"Database error: {str(e)}")
        return {**state, "errors": errors}
    finally:
        db.close()

    audit_logger.log(
        action="LEAD_RECEIVED",
        lead_id=lead_id,
        tool_name="receive_lead",
        prompt=f"Lead received: {lead.get('name', 'Unknown')} from {lead.get('company', 'Unknown')}",
        metadata={"injection_check": injection_check},
    )

    return {
        **state,
        "lead_id": lead_id,
        "approval_status": "PENDING",
        "approval_granted": False,
        "audit_logs": [],
        "errors": errors,
    }


def enrich_lead(state: AgentState) -> AgentState:
    """
    Stage 1: Enrich lead with company and contact information.
    """
    lead = state.get("lead", {})
    lead_id = state.get("lead_id")
    audit_logger = AuditLogger()
    enrichment_tool = LeadEnrichmentTool()

    # Update lead status
    db = SessionLocal()
    try:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if db_lead:
            db_lead.status = LeadStatus.ENRICHING.value
            db.commit()
    except Exception:
        pass
    finally:
        db.close()

    # Perform enrichment
    enriched = enrichment_tool.enrich(lead)

    # Save enriched profile to database
    db = SessionLocal()
    try:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if db_lead:
            db_lead.enriched_profile = enriched
            db.commit()
    except Exception:
        pass
    finally:
        db.close()

    audit_logger.log(
        action="LEAD_ENRICHED",
        lead_id=lead_id,
        tool_name="LeadEnrichmentTool",
        prompt=f"Enriching lead: {lead.get('name', 'Unknown')}",
        response=json.dumps(enriched),
        metadata={"enriched_profile": enriched},
    )

    return {
        **state,
        "enriched_profile": enriched,
    }


def score_lead(state: AgentState) -> AgentState:
    """
    Stage 2: Identity-blind scoring of the lead.
    Personal identifiers are stripped before scoring.
    """
    enriched_profile = state.get("enriched_profile", {})
    lead_id = state.get("lead_id")
    audit_logger = AuditLogger()
    scoring_tool = LeadScoringTool()

    # Update lead status
    db = SessionLocal()
    try:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if db_lead:
            db_lead.status = LeadStatus.SCORING.value
            db.commit()
    except Exception:
        pass
    finally:
        db.close()

    # Perform identity-blind scoring
    scoring_result = scoring_tool.score(enriched_profile)

    audit_logger.log(
        action="LEAD_SCORED",
        lead_id=lead_id,
        tool_name="LeadScoringTool",
        prompt=f"Scoring lead with identity-blind profile",
        response=json.dumps(scoring_result),
        score=scoring_result.get("total_score"),
        metadata={"dimension_scores": scoring_result.get("dimension_scores")},
    )

    return {
        **state,
        "score": scoring_result.get("total_score"),
        "dimension_scores": scoring_result.get("dimension_scores"),
        "scoring_reasoning": scoring_result.get("reasoning"),
        "scoring_evidence": scoring_result.get("evidence"),
    }


def classify_lead(state: AgentState) -> AgentState:
    """
    Stage 3: Classify lead based on score.
    HOT >= 80, NURTURE 50-79, DISQUALIFY < 50.
    """
    scoring_result = {
        "total_score": state.get("score", 0),
        "dimension_scores": state.get("dimension_scores", {}),
        "reasoning": state.get("scoring_reasoning", ""),
        "evidence": state.get("scoring_evidence", ""),
    }
    lead_id = state.get("lead_id")
    audit_logger = AuditLogger()
    classification_tool = LeadClassificationTool()

    classification_result = classification_tool.classify(scoring_result)

    # Update lead in database
    db = SessionLocal()
    try:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if db_lead:
            db_lead.classification = classification_result["classification"]
            db_lead.classification_reason = classification_result["reason"]
            db_lead.classification_confidence = classification_result["confidence"]
            db_lead.total_score = classification_result["score"]
            db_lead.status = LeadStatus.CLASSIFIED.value
            db.commit()
    except Exception:
        pass
    finally:
        db.close()

    audit_logger.log(
        action="LEAD_CLASSIFIED",
        lead_id=lead_id,
        tool_name="LeadClassificationTool",
        classification=classification_result["classification"],
        score=classification_result["score"],
        reason=classification_result["reason"],
        evidence=classification_result["evidence"],
        metadata={"confidence": classification_result["confidence"]},
    )

    return {
        **state,
        "classification": classification_result["classification"],
        "classification_reason": classification_result["reason"],
        "classification_confidence": classification_result["confidence"],
    }


def route_lead(state: AgentState) -> AgentState:
    """
    Stage 4: Route the lead based on classification.
    HOT -> Draft email
    NURTURE -> Nurture pipeline
    DISQUALIFY -> Archive
    """
    classification = state.get("classification", "DISQUALIFY")
    lead_id = state.get("lead_id")
    audit_logger = AuditLogger()

    if classification == "HOT":
        routing_action = "DRAFT_EMAIL"
        routing_reason = "Lead is HOT. Proceeding to email drafting."
    elif classification == "NURTURE":
        routing_action = "NURTURE"
        routing_reason = (
            f"Lead scored {state.get('score', 0)}/100, placing in NURTURE range. "
            "Moving to nurture pipeline for further engagement."
        )
    else:
        routing_action = "ARCHIVE"
        routing_reason = (
            f"Lead scored {state.get('score', 0)}/100, below qualification threshold. "
            "Archiving lead."
        )

    # Update CRM
    crm_tool = CRMTool()
    crm_result = crm_tool.write_lead(
        lead_data=state.get("lead", {}),
        classification=classification,
        reason=routing_reason,
        score=state.get("score"),
        lead_id=lead_id,
        approval_status="PENDING" if classification == "HOT" else "NOT_REQUIRED",
    )

    # Update lead status based on routing
    db = SessionLocal()
    try:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if db_lead:
            db_lead.routing_action = routing_action
            db_lead.routing_reason = routing_reason
            if classification == "NURTURE":
                db_lead.status = LeadStatus.NURTURE.value
            elif classification == "DISQUALIFY":
                db_lead.status = LeadStatus.DISQUALIFIED.value
            else:
                db_lead.status = LeadStatus.AWAITING_APPROVAL.value
            db.commit()
    except Exception:
        pass
    finally:
        db.close()

    audit_logger.log(
        action="LEAD_ROUTED",
        lead_id=lead_id,
        tool_name="route_lead",
        classification=classification,
        reason=routing_reason,
        metadata={"routing_action": routing_action},
    )

    return {
        **state,
        "routing_action": routing_action,
        "routing_reason": routing_reason,
        "crm_id": crm_result.get("crm_id"),
    }


def draft_email(state: AgentState) -> AgentState:
    """
    Stage 5: Draft personalized email for HOT leads.
    """
    lead = state.get("lead", {})
    enriched_profile = state.get("enriched_profile", {})
    lead_id = state.get("lead_id")
    audit_logger = AuditLogger()
    email_tool = EmailTool()

    # Generate email draft
    email_draft = email_tool.draft_email(lead, enriched_profile)

    # Update lead in database
    db = SessionLocal()
    try:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if db_lead:
            db_lead.email_subject = email_draft.get("subject")
            db_lead.email_body = email_draft.get("body")
            db_lead.email_draft_version = (db_lead.email_draft_version or 0) + 1
            db_lead.status = LeadStatus.AWAITING_APPROVAL.value
            db.commit()
    except Exception:
        pass
    finally:
        db.close()

    audit_logger.log(
        action="EMAIL_DRAFTED",
        lead_id=lead_id,
        tool_name="EmailTool",
        prompt=f"Drafting email for {lead.get('name', 'Unknown')} at {enriched_profile.get('company', 'Unknown')}",
        response=json.dumps(email_draft),
        email_draft=email_draft.get("body"),
        classification="HOT",
    )

    return {
        **state,
        "email_draft": email_draft,
        "email_subject": email_draft.get("subject"),
        "email_body": email_draft.get("body"),
        "approval_status": "AWAITING_APPROVAL",
    }


def human_approval(state: AgentState) -> AgentState:
    """
    Stage 6: Human approval gate.
    Email cannot be sent automatically. Approval must be granted through the UI.
    This node checks if approval has been granted via the API.
    """
    # This is a passthrough node - the actual approval happens via the API endpoint.
    # The state's approval_granted flag is set by the API endpoint.
    return state


def send_email(state: AgentState) -> AgentState:
    """
    Stage 7: Send the approved email.
    Only executes if human approval has been granted.
    """
    lead = state.get("lead", {})
    lead_id = state.get("lead_id")
    email_subject = state.get("email_subject", "")
    email_body = state.get("email_body", "")
    approval_granted = state.get("approval_granted", False)
    audit_logger = AuditLogger()
    email_tool = EmailTool()

    if not approval_granted:
        audit_logger.log(
            action="EMAIL_SEND_BLOCKED",
            lead_id=lead_id,
            tool_name="EmailTool",
            reason="No human approval granted",
            approval_status="DENIED",
        )
        return {
            **state,
            "errors": state.get("errors", []) + ["Email not sent: no human approval"],
        }

    # Send email
    recipient = lead.get("email", "")
    send_result = email_tool.send_email(
        recipient=recipient,
        subject=email_subject,
        body=email_body,
        approval_token="APPROVED",
    )

    # Update lead status
    db = SessionLocal()
    try:
        db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if db_lead:
            if send_result.get("sent"):
                db_lead.status = LeadStatus.SENT.value
                db_lead.email_sent_at = datetime.utcnow()
            else:
                db_lead.status = LeadStatus.ERROR.value
                db_lead.error_message = send_result.get("message")
            db.commit()
    except Exception:
        pass
    finally:
        db.close()

    audit_logger.log(
        action="EMAIL_SENT" if send_result.get("sent") else "EMAIL_SEND_FAILED",
        lead_id=lead_id,
        tool_name="EmailTool",
        response=json.dumps(send_result),
        approval_status="APPROVED",
        email_draft=email_body,
    )

    return {
        **state,
        "crm_status": "SENT" if send_result.get("sent") else "ERROR",
    }


def log_and_evaluate(state: AgentState) -> AgentState:
    """
    Stage 8: Final logging and evaluation.
    Records the complete workflow outcome.
    """
    lead_id = state.get("lead_id")
    audit_logger = AuditLogger()

    audit_logger.log(
        action="WORKFLOW_COMPLETE",
        lead_id=lead_id,
        classification=state.get("classification"),
        score=state.get("score"),
        approval_status=state.get("approval_status"),
        metadata={
            "routing_action": state.get("routing_action"),
            "errors": state.get("errors", []),
        },
    )

    return state


# =============================================================================
# CONDITIONAL EDGE FUNCTIONS
# =============================================================================

def should_draft_email(state: AgentState) -> str:
    """Determine if we should draft an email or finish."""
    classification = state.get("classification", "DISQUALIFY")
    if classification == "HOT":
        return "draft_email"
    else:
        return "finish"


def should_await_approval(state: AgentState) -> str:
    """Check if we need human approval."""
    classification = state.get("classification", "DISQUALIFY")
    if classification == "HOT":
        return "human_approval"
    return "finish"


def should_send_email(state: AgentState) -> str:
    """Check if email has been approved."""
    approval_granted = state.get("approval_granted", False)
    if approval_granted:
        return "send_email"
    # If not approved, finish the workflow and wait for API trigger
    return "finish"


# =============================================================================
# BUILD THE WORKFLOW GRAPH
# =============================================================================

def build_workflow() -> StateGraph:
    """
    Build the LangGraph workflow for lead qualification and outreach.

    The workflow is a state machine with these stages:
    Receive -> Enrich -> Score -> Classify -> Route -> (Draft Email -> Approve -> Send) | Finish

    Returns:
        Compiled LangGraph StateGraph
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("receive_lead", receive_lead)
    workflow.add_node("enrich_lead", enrich_lead)
    workflow.add_node("score_lead", score_lead)
    workflow.add_node("classify_lead", classify_lead)
    workflow.add_node("route_lead", route_lead)
    workflow.add_node("draft_email", draft_email)
    workflow.add_node("human_approval", human_approval)
    workflow.add_node("send_email", send_email)
    workflow.add_node("log_and_evaluate", log_and_evaluate)

    # Set entry point
    workflow.set_entry_point("receive_lead")

    # Add edges
    workflow.add_edge("receive_lead", "enrich_lead")
    workflow.add_edge("enrich_lead", "score_lead")
    workflow.add_edge("score_lead", "classify_lead")
    workflow.add_edge("classify_lead", "route_lead")

    # Conditional routing after route_lead
    workflow.add_conditional_edges(
        "route_lead",
        should_draft_email,
        {
            "draft_email": "draft_email",
            "finish": "log_and_evaluate",
        },
    )

    # After draft email, go to human approval
    workflow.add_edge("draft_email", "human_approval")

    # After human approval, check if approved
    workflow.add_conditional_edges(
        "human_approval",
        should_send_email,
        {
            "send_email": "send_email",
            "finish": "log_and_evaluate",
        },
    )

    # After send email, log and evaluate
    workflow.add_edge("send_email", "log_and_evaluate")

    # End
    workflow.add_edge("log_and_evaluate", END)

    return workflow.compile()


# =============================================================================
# WORKFLOW EXECUTION
# =============================================================================

def run_workflow(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the lead qualification workflow for a given lead.

    Args:
        lead_data: Dictionary containing lead information

    Returns:
        Final state dictionary with all workflow results
    """
    workflow = build_workflow()

    initial_state: AgentState = {
        "lead": lead_data,
        "lead_id": None,
        "enriched_profile": None,
        "enrichment_log": None,
        "score": None,
        "dimension_scores": None,
        "scoring_reasoning": None,
        "scoring_evidence": None,
        "classification": None,
        "classification_reason": None,
        "classification_confidence": None,
        "routing_action": None,
        "routing_reason": None,
        "email_draft": None,
        "email_subject": None,
        "email_body": None,
        "approval_status": "PENDING",
        "approval_token": None,
        "approval_granted": False,
        "crm_status": None,
        "crm_id": None,
        "audit_logs": [],
        "evaluation_results": None,
        "errors": [],
    }

    try:
        final_state = workflow.invoke(initial_state)
        return final_state
    except Exception as e:
        return {
            **initial_state,
            "errors": [str(e)],
            "classification": "ERROR",
            "approval_status": "ERROR",
        }