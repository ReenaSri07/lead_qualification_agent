"""
Audit Logger Tool.
Logs every tool call, prompt, response, classification, reason, approval, email draft, and timestamp.
Provides a complete audit trail for governance and compliance.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from app.database import SessionLocal, AuditLog


class AuditLogger:
    """
    Logs all operations for complete audit trail and governance compliance.
    Every tool call, LLM prompt, response, decision, and action is logged.
    """

    def log(
        self,
        action: str,
        lead_id: Optional[int] = None,
        tool_name: Optional[str] = None,
        prompt: Optional[str] = None,
        response: Optional[str] = None,
        classification: Optional[str] = None,
        score: Optional[float] = None,
        reason: Optional[str] = None,
        evidence: Optional[str] = None,
        approval_status: Optional[str] = None,
        email_draft: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log an audit entry.

        Args:
            action: Description of the action being logged
            lead_id: ID of the associated lead (if any)
            tool_name: Name of the tool being called
            prompt: LLM prompt text
            response: LLM response text
            classification: Lead classification (HOT/NURTURE/DISQUALIFY)
            score: Lead score
            reason: Decision reason
            evidence: Supporting evidence
            approval_status: Current approval status
            email_draft: Email draft content
            metadata: Additional metadata

        Returns:
            Dictionary with log entry id and status
        """
        db = SessionLocal()
        try:
            log_entry = AuditLog(
                lead_id=lead_id,
                action=action,
                tool_name=tool_name,
                prompt=prompt,
                response=response,
                classification=classification,
                score=score,
                reason=reason,
                evidence=evidence,
                approval_status=approval_status,
                email_draft=email_draft,
                metadata=metadata,
                timestamp=datetime.utcnow(),
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            return {
                "success": True,
                "log_id": log_entry.id,
                "timestamp": log_entry.timestamp.isoformat(),
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def get_audit_trail(self, lead_id: Optional[int] = None, limit: int = 100) -> list:
        """
        Retrieve audit log entries, optionally filtered by lead_id.

        Args:
            lead_id: Optional lead ID filter
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries
        """
        db = SessionLocal()
        try:
            query = db.query(AuditLog)
            if lead_id:
                query = query.filter(AuditLog.lead_id == lead_id)
            entries = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

            result = []
            for entry in entries:
                result.append({
                    "id": entry.id,
                    "lead_id": entry.lead_id,
                    "action": entry.action,
                    "tool_name": entry.tool_name,
                    "classification": entry.classification,
                    "score": entry.score,
                    "reason": entry.reason,
                    "approval_status": entry.approval_status,
                    "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                })
            return result
        finally:
            db.close()