from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .core.database import Base

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(250), nullable=False)
    case_type = Column(String(120), default="غير محدد")
    jurisdiction = Column(String(200), nullable=True)
    summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    events = relationship("CaseEvent", cascade="all, delete-orphan")
    evidence = relationship("Evidence", cascade="all, delete-orphan")

class CaseEvent(Base):
    __tablename__ = "case_events"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    event_date = Column(Date, nullable=False)
    event_type = Column(String(120), nullable=False)
    description = Column(Text, default="")
    source_ref = Column(String(120), nullable=True)

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    title = Column(String(250), nullable=False)
    evidence_type = Column(String(100), default="document")
    status = Column(String(40), default="NEEDS_VERIFICATION")
    description = Column(Text, default="")
    document_ref = Column(String(120), nullable=True)

class LegalArticle(Base):
    __tablename__ = "legal_articles"
    id = Column(Integer, primary_key=True)
    system_name = Column(String(250), nullable=False)
    article_number = Column(String(40), nullable=False)
    version = Column(String(80), nullable=False)
    text = Column(Text, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    status = Column(String(30), default="ACTIVE")
    source_level = Column(String(30), default="UNVERIFIED")
    source_url = Column(Text, nullable=True)
    content_hash = Column(String(128), nullable=True)
    is_demo = Column(Boolean, default=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    action = Column(String(120), nullable=False)
    details = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
