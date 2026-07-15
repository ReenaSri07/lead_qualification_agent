"""
Database models and connection management for the Lead Qualification Agent.
Uses SQLAlchemy with SQLite for persistence.
"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text,
    DateTime, JSON, Boolean, Enum as SAEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import enum

# Create engine and session
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class LeadStatus(str, enum.Enum):
    """Enumeration of possible lead statuses."""
    PENDING = "PENDING"
    ENRICHING = "ENRICHING"
    SCORING = "SCORING"
    CLASSIFIED = "CLASSIFIED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENT = "SENT"
    ARCHIVED = "ARCHIVED"
    NURTURE = "NURTURE"
    DISQUALIFIED = "DISQUALIFIED"
    ERROR = "ERROR"


class Classification(str, enum.Enum):
    """Lead classification categories."""
    HOT = "HOT"
    NURTURE = "NURTURE"
    DISQUALIFY = "DISQUALIFY"


class Lead(Base):
    """Main lead record storing all lead information and processing results."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Original lead input
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    role = Column(String(255), nullable=True)
    source = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Enriched profile (stored as JSON)
    enriched_profile = Column(JSON, nullable=True)

    # Scoring
    total_score = Column(Float, nullable=True)
    dimension_scores = Column(JSON, nullable=True)
    scoring_reasoning = Column(Text, nullable=True)
    scoring_evidence = Column(Text, nullable=True)

    # Classification
    classification = Column(String(50), nullable=True)
    classification_reason = Column(Text, nullable=True)
    classification_evidence = Column(Text, nullable=True)
    classification_confidence = Column(Float, nullable=True)

    # Email
    email_subject = Column(String(500), nullable=True)
    email_body = Column(Text, nullable=True)
    email_draft_version = Column(Integer, default=0)

    # Approval
    approval_status = Column(String(50), default="PENDING")
    approval_token = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)

    # CRM
    crm_status = Column(String(50), nullable=True)
    crm_id = Column(String(255), nullable=True)

    # Routing
    routing_action = Column(String(50), nullable=True)
    routing_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    email_sent_at = Column(DateTime, nullable=True)

    # Status
    status = Column(String(50), default=LeadStatus.PENDING.value)
    error_message = Column(Text, nullable=True)

    # Identity-blind fields (stripped for fairness)
    has_identity_stripped = Column(Boolean, default=False)


class AuditLog(Base):
    """Audit log for tracking all operations, decisions, and tool calls."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lead_id = Column(Integer, nullable=True)
    action = Column(String(255), nullable=False)
    tool_name = Column(String(255), nullable=True)
    prompt = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    classification = Column(String(50), nullable=True)
    score = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)
    approval_status = Column(String(50), nullable=True)
    email_draft = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class EvaluationResult(Base):
    """Stores evaluation test results."""
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_name = Column(String(255), nullable=False)
    test_type = Column(String(100), nullable=False)
    passed = Column(Boolean, default=False)
    input_data = Column(JSON, nullable=True)
    expected_output = Column(JSON, nullable=True)
    actual_output = Column(JSON, nullable=True)
    errors = Column(Text, nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency injection for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()