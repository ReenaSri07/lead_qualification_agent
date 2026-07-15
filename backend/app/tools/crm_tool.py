"""
CRM Write Tool.
Records lead data, classification, score, email draft, and approval status.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from app.database import SessionLocal, Lead, LeadStatus


class CRMTool:
    """
    Tool for writing lead data to the CRM system.
    Records the full lead lifecycle including enrichment, scoring, classification,
    email drafts, and approval status.
    """

    def write_lead(
        self,
        lead_data: Dict[str, Any],
        classification: Optional[str] = None,
        reason: Optional[str] = None,
        score: Optional[float] = None,
        draft: Optional[Dict[str, Any]] = None,
        approval_status: str = "PENDING",
        lead_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Write lead data to CRM.

        Args:
            lead_data: Original lead information
            classification: HOT, NURTURE, or DISQUALIFY
            reason: Classification reason
            score: Total score
            draft: Email draft data
            approval_status: Approval status
            lead_id: Existing lead ID to update (optional)

        Returns:
            Dictionary with crm_id and status
        """
        db = SessionLocal()
        try:
            if lead_id:
                # Update existing lead
                lead = db.query(Lead).filter(Lead.id == lead_id).first()
                if not lead:
                    return {"success": False, "error": "Lead not found"}
            else:
                # Create new lead
                lead = Lead()
                lead.name = lead_data.get("name")
                lead.email = lead_data.get("email")
                lead.company = lead_data.get("company")
                lead.role = lead_data.get("role")
                lead.source = lead_data.get("source")
                lead.notes = lead_data.get("notes")
                lead.status = LeadStatus.PENDING.value
                db.add(lead)
                db.flush()

            # Update fields if provided
            if classification:
                lead.classification = classification
                lead.crm_status = classification
            if reason:
                lead.classification_reason = reason
            if score is not None:
                lead.total_score = score
            if draft:
                lead.email_subject = draft.get("subject")
                lead.email_body = draft.get("body")
            lead.approval_status = approval_status
            lead.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(lead)

            return {
                "success": True,
                "crm_id": str(lead.id),
                "status": lead.status,
                "classification": lead.classification,
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def update_status(
        self,
        lead_id: int,
        status: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Update lead status in CRM.

        Args:
            lead_id: ID of the lead to update
            status: New status
            **kwargs: Additional fields to update

        Returns:
            Dictionary with success status
        """
        db = SessionLocal()
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                return {"success": False, "error": "Lead not found"}

            lead.status = status
            lead.updated_at = datetime.utcnow()

            for key, value in kwargs.items():
                if hasattr(lead, key):
                    setattr(lead, key, value)

            db.commit()
            return {"success": True, "crm_id": str(lead.id), "status": status}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()