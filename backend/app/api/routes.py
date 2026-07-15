"""
API Routes for the Lead Qualification & Outreach Agent.
Provides endpoints for submitting leads, checking status, approving/rejecting
emails, viewing audit logs, and running evaluations.
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr

from app.agents.workflow import run_workflow
from app.database import SessionLocal, Lead, AuditLog, EvaluationResult, get_db
from app.tools.audit_logger import AuditLogger
from app.tools.crm_tool import CRMTool
from app.tools.email_tool import EmailTool

router = APIRouter()


# =============================================================================
# Pydantic Models
# =============================================================================

class LeadInput(BaseModel):
    """Input model for submitting a new lead."""
    name: Optional[str] = Field(None, description="Lead's full name")
    email: Optional[str] = Field(None, description="Lead's email address")
    company: Optional[str] = Field(None, description="Lead's company name")
    role: Optional[str] = Field(None, description="Lead's job title or role")
    source: Optional[str] = Field(None, description="Lead source (e.g., website, referral, LinkedIn)")
    notes: Optional[str] = Field(None, description="Additional notes about the lead")


class ApprovalInput(BaseModel):
    """Input model for approving or rejecting an email."""
    lead_id: int = Field(..., description="ID of the lead to approve/reject")
    action: str = Field(..., description="Action: 'approve', 'reject', or 'edit'")
    edited_subject: Optional[str] = Field(None, description="Edited email subject (if action is 'edit')")
    edited_body: Optional[str] = Field(None, description="Edited email body (if action is 'edit')")
    reason: Optional[str] = Field(None, description="Reason for rejection")


class EvaluationInput(BaseModel):
    """Input model for running evaluations."""
    test_type: Optional[str] = Field(None, description="Specific test type to run, or 'all' for all tests")


# =============================================================================
# Lead Endpoints
# =============================================================================

@router.post("/leads", summary="Submit a new lead for qualification")
async def submit_lead(lead_input: LeadInput):
    """
    Submit a new lead to the qualification pipeline.
    The lead will be processed through the entire workflow:
    enrichment -> scoring -> classification -> routing -> email drafting -> approval gate.
    """
    lead_data = lead_input.model_dump()

    # Run the workflow
    result = run_workflow(lead_data)

    return {
        "lead_id": result.get("lead_id"),
        "status": "processing",
        "classification": result.get("classification"),
        "score": result.get("score"),
        "routing_action": result.get("routing_action"),
        "errors": result.get("errors", []),
        "message": "Lead submitted successfully. Check status via GET /leads/{id}",
    }


@router.get("/leads", summary="List all leads")
async def list_leads(
    status: Optional[str] = Query(None, description="Filter by lead status"),
    classification: Optional[str] = Query(None, description="Filter by classification (HOT, NURTURE, DISQUALIFY)"),
    limit: int = Query(50, description="Maximum number of leads to return"),
    offset: int = Query(0, description="Number of leads to skip"),
):
    """List all leads with optional filtering."""
    db = SessionLocal()
    try:
        query = db.query(Lead)
        if status:
            query = query.filter(Lead.status == status)
        if classification:
            query = query.filter(Lead.classification == classification)

        total = query.count()
        leads = query.order_by(Lead.created_at.desc()).offset(offset).limit(limit).all()

        result = []
        for lead in leads:
            result.append({
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "company": lead.company,
                "role": lead.role,
                "source": lead.source,
                "classification": lead.classification,
                "total_score": lead.total_score,
                "status": lead.status,
                "approval_status": lead.approval_status,
                "routing_action": lead.routing_action,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
            })

        return {"total": total, "leads": result, "limit": limit, "offset": offset}
    finally:
        db.close()


@router.get("/leads/{lead_id}", summary="Get lead details")
async def get_lead(lead_id: int):
    """Get detailed information about a specific lead."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        return {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "role": lead.role,
            "source": lead.source,
            "notes": lead.notes,
            "enriched_profile": lead.enriched_profile,
            "total_score": lead.total_score,
            "dimension_scores": lead.dimension_scores,
            "scoring_reasoning": lead.scoring_reasoning,
            "scoring_evidence": lead.scoring_evidence,
            "classification": lead.classification,
            "classification_reason": lead.classification_reason,
            "classification_confidence": lead.classification_confidence,
            "email_subject": lead.email_subject,
            "email_body": lead.email_body,
            "email_draft_version": lead.email_draft_version,
            "approval_status": lead.approval_status,
            "routing_action": lead.routing_action,
            "routing_reason": lead.routing_reason,
            "status": lead.status,
            "crm_status": lead.crm_status,
            "error_message": lead.error_message,
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
            "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
            "processed_at": lead.processed_at.isoformat() if lead.processed_at else None,
            "email_sent_at": lead.email_sent_at.isoformat() if lead.email_sent_at else None,
        }
    finally:
        db.close()


# =============================================================================
# Approval Endpoints
# =============================================================================

@router.post("/leads/{lead_id}/approve", summary="Approve email for sending")
async def approve_email(lead_id: int):
    """
    Approve the email draft for a HOT lead.
    This is the human approval gate - email cannot be sent without this.
    """
    db = SessionLocal()
    audit_logger = AuditLogger()
    crm_tool = CRMTool()

    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        if lead.classification != "HOT":
            raise HTTPException(
                status_code=400,
                detail=f"Lead is classified as {lead.classification}. Only HOT leads can be approved for email."
            )

        if lead.approval_status == "APPROVED":
            return {"message": "Email already approved", "lead_id": lead_id}

        # Update approval status
        lead.approval_status = "APPROVED"
        lead.approved_at = datetime.utcnow()
        lead.status = "APPROVED"
        db.commit()

        # Audit log
        audit_logger.log(
            action="EMAIL_APPROVED",
            lead_id=lead_id,
            approval_status="APPROVED",
            reason="Approved by human operator",
        )

        # Update CRM
        crm_tool.update_status(lead_id=lead_id, status="APPROVED", approval_status="APPROVED")

        return {
            "message": "Email approved successfully. It will be sent to the recipient.",
            "lead_id": lead_id,
            "email_subject": lead.email_subject,
            "email_body": lead.email_body,
        }
    finally:
        db.close()


@router.post("/leads/{lead_id}/reject", summary="Reject email for sending")
async def reject_email(lead_id: int, reason: Optional[str] = None):
    """
    Reject the email draft for a HOT lead.
    The lead will NOT receive any email.
    """
    db = SessionLocal()
    audit_logger = AuditLogger()
    crm_tool = CRMTool()

    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Update approval status
        lead.approval_status = "REJECTED"
        lead.status = "REJECTED"
        if reason:
            lead.error_message = reason
        db.commit()

        # Audit log
        audit_logger.log(
            action="EMAIL_REJECTED",
            lead_id=lead_id,
            approval_status="REJECTED",
            reason=reason or "Rejected by human operator",
        )

        crm_tool.update_status(lead_id=lead_id, status="REJECTED", approval_status="REJECTED")

        return {
            "message": "Email rejected. No email will be sent to this lead.",
            "lead_id": lead_id,
        }
    finally:
        db.close()


@router.post("/leads/{lead_id}/edit-email", summary="Edit and approve email draft")
async def edit_email_draft(
    lead_id: int,
    subject: str,
    body: str,
):
    """
    Edit the email draft and approve it simultaneously.
    This allows the human operator to customize the email before sending.
    """
    db = SessionLocal()
    audit_logger = AuditLogger()
    crm_tool = CRMTool()

    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Update email and approval
        lead.email_subject = subject
        lead.email_body = body
        lead.email_draft_version = (lead.email_draft_version or 0) + 1
        lead.approval_status = "APPROVED"
        lead.approved_at = datetime.utcnow()
        lead.status = "APPROVED"
        db.commit()

        # Audit log
        audit_logger.log(
            action="EMAIL_EDITED_AND_APPROVED",
            lead_id=lead_id,
            approval_status="APPROVED",
            email_draft=body,
            reason="Email edited and approved by human operator",
        )

        crm_tool.update_status(lead_id=lead_id, status="APPROVED", approval_status="APPROVED")

        return {
            "message": "Email edited and approved successfully.",
            "lead_id": lead_id,
            "email_subject": subject,
            "email_body": body,
        }
    finally:
        db.close()


# =============================================================================
# Evaluation Endpoints
# =============================================================================

@router.post("/evaluation/run", summary="Run automated evaluation tests")
async def run_evaluation_tests():
    """Run the complete evaluation test suite."""
    from app.evaluation.test_suite import run_evaluation
    result = run_evaluation()
    return result


@router.get("/evaluation/results", summary="Get evaluation results")
async def get_evaluation_results():
    """Get stored evaluation test results."""
    db = SessionLocal()
    try:
        results = db.query(EvaluationResult).order_by(EvaluationResult.timestamp.desc()).limit(50).all()
        return {
            "results": [
                {
                    "test_name": r.test_name,
                    "test_type": r.test_type,
                    "passed": r.passed,
                    "errors": r.errors,
                    "execution_time_ms": r.execution_time_ms,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                }
                for r in results
            ]
        }
    finally:
        db.close()


# =============================================================================
# Audit Log Endpoints
# =============================================================================

@router.get("/audit-logs", summary="Get audit logs")
async def get_audit_logs(
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    limit: int = Query(100, description="Maximum number of logs to return"),
):
    """Retrieve audit log entries with optional lead filtering."""
    audit_logger = AuditLogger()
    logs = audit_logger.get_audit_trail(lead_id=lead_id, limit=limit)
    return {"logs": logs, "total": len(logs)}


# =============================================================================
# Analytics Endpoints
# =============================================================================

@router.get("/analytics", summary="Get dashboard analytics")
async def get_analytics():
    """Get aggregate analytics for the dashboard."""
    db = SessionLocal()
    try:
        total_leads = db.query(Lead).count()
        hot_leads = db.query(Lead).filter(Lead.classification == "HOT").count()
        nurture_leads = db.query(Lead).filter(Lead.classification == "NURTURE").count()
        disqualified_leads = db.query(Lead).filter(Lead.classification == "DISQUALIFY").count()

        avg_score_result = db.query(Lead.total_score).filter(Lead.total_score.isnot(None)).all()
        avg_score = sum(s[0] for s in avg_score_result) / len(avg_score_result) if avg_score_result else 0

        emails_approved = db.query(Lead).filter(Lead.approval_status == "APPROVED").count()
        emails_sent = db.query(Lead).filter(Lead.status == "SENT").count()
        pending_approval = db.query(Lead).filter(Lead.approval_status == "AWAITING_APPROVAL").count()

        return {
            "total_leads": total_leads,
            "hot": hot_leads,
            "nurture": nurture_leads,
            "disqualified": disqualified_leads,
            "average_score": round(avg_score, 1),
            "emails_approved": emails_approved,
            "emails_sent": emails_sent,
            "pending_approval": pending_approval,
        }
    finally:
        db.close()


# =============================================================================
# Email Sending Endpoint (triggered after approval)
# =============================================================================

@router.post("/leads/{lead_id}/send", summary="Send approved email")
async def send_approved_email(lead_id: int):
    """
    Send the approved email for a lead.
    This endpoint enforces the human approval gate - email will only be sent
    if approval_status is APPROVED.
    """
    db = SessionLocal()
    audit_logger = AuditLogger()
    email_tool = EmailTool()

    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        if lead.approval_status != "APPROVED":
            raise HTTPException(
                status_code=400,
                detail=f"Email cannot be sent. Current approval status: {lead.approval_status}. "
                       f"Human approval is required before sending."
            )

        if lead.status == "SENT":
            return {"message": "Email already sent", "lead_id": lead_id}

        # Send the email
        send_result = email_tool.send_email(
            recipient=lead.email,
            subject=lead.email_subject,
            body=lead.email_body,
            approval_token="APPROVED",
        )

        if send_result.get("sent"):
            lead.status = "SENT"
            lead.email_sent_at = datetime.utcnow()
            db.commit()

            audit_logger.log(
                action="EMAIL_SENT",
                lead_id=lead_id,
                approval_status="APPROVED",
                email_draft=lead.email_body,
                response=json.dumps(send_result),
            )

            return {"message": "Email sent successfully", "lead_id": lead_id}
        else:
            lead.status = "ERROR"
            lead.error_message = send_result.get("message")
            db.commit()

            raise HTTPException(
                status_code=500,
                detail=f"Failed to send email: {send_result.get('message')}"
            )
    finally:
        db.close()