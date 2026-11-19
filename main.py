from datetime import date
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.orm import Session
from .core.database import Base, engine, get_db
from . import models
from .schemas.api import CaseCreate, EventCreate, EvidenceCreate, ArticleCreate, ResearchRequest, DraftRequest
from .services.timeline import build_timeline
from .services.evidence import evidence_matrix
from .services.retrieval import hybrid_search
from .services.drafting import build_draft
from .services.official_sources import OFFICIAL_SOURCES
from .services.knowledge_graph import build_graph

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Saudi Legal AI v1.0 Starter API", version="1.0.0")

def log(db, action, case_id=None, details=""):
    db.add(models.AuditLog(case_id=case_id, action=action, details=details))
    db.commit()

@app.get("/health")
def health():
    return {"status": "ok", "service": "Saudi Legal AI", "version": "1.0.0"}

@app.post("/cases", status_code=201)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    case = models.Case(**payload.model_dump())
    db.add(case); db.commit(); db.refresh(case)
    log(db, "CASE_CREATED", case.id, case.title)
    return {"id": case.id, "title": case.title, "case_type": case.case_type}

@app.get("/cases/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.get(models.Case, case_id)
    if not case: raise HTTPException(404, "Case not found")
    return {"id": case.id, "title": case.title, "case_type": case.case_type,
            "jurisdiction": case.jurisdiction, "summary": case.summary}

@app.post("/cases/{case_id}/events", status_code=201)
def add_event(case_id: int, payload: EventCreate, db: Session = Depends(get_db)):
    if not db.get(models.Case, case_id): raise HTTPException(404, "Case not found")
    item = models.CaseEvent(case_id=case_id, **payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    log(db, "EVENT_ADDED", case_id, str(item.event_date))
    return {"id": item.id, **payload.model_dump()}

@app.get("/cases/{case_id}/timeline")
def get_timeline(case_id: int, db: Session = Depends(get_db)):
    case = db.get(models.Case, case_id)
    if not case: raise HTTPException(404, "Case not found")
    return [{"id": e.id, "date": e.event_date, "type": e.event_type,
             "description": e.description, "source_ref": e.source_ref}
            for e in build_timeline(case.events)]

@app.post("/cases/{case_id}/evidence", status_code=201)
def add_evidence(case_id: int, payload: EvidenceCreate, db: Session = Depends(get_db)):
    if not db.get(models.Case, case_id): raise HTTPException(404, "Case not found")
    item = models.Evidence(case_id=case_id, **payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    log(db, "EVIDENCE_ADDED", case_id, item.title)
    return {"id": item.id, **payload.model_dump()}

@app.get("/cases/{case_id}/evidence-matrix")
def get_evidence(case_id: int, db: Session = Depends(get_db)):
    case = db.get(models.Case, case_id)
    if not case: raise HTTPException(404, "Case not found")
    return evidence_matrix(case.evidence)

@app.post("/legal-articles", status_code=201)
def create_article(payload: ArticleCreate, db: Session = Depends(get_db)):
    item = models.LegalArticle(**payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return {"id": item.id, "system_name": item.system_name,
            "article_number": item.article_number, "version": item.version}

@app.post("/research")
def research(payload: ResearchRequest, db: Session = Depends(get_db)):
    articles = db.query(models.LegalArticle).all()
    results = hybrid_search(payload.query, articles, payload.as_of, payload.system_name)
    return [{"score": r["score"], "article": {
        "id": r["article"].id, "system_name": r["article"].system_name,
        "article_number": r["article"].article_number, "version": r["article"].version,
        "text": r["article"].text, "effective_from": r["article"].effective_from,
        "effective_to": r["article"].effective_to, "source_level": r["article"].source_level,
        "is_demo": r["article"].is_demo
    }} for r in results]

@app.post("/drafts/{case_id}")
def generate_draft(case_id: int, payload: DraftRequest, db: Session = Depends(get_db)):
    case = db.get(models.Case, case_id)
    if not case: raise HTTPException(404, "Case not found")
    result = build_draft(case, case.events, case.evidence)
    log(db, "DRAFT_GENERATED", case_id, payload.draft_type)
    return result

@app.get("/audit/{case_id}")
def get_audit(case_id: int, db: Session = Depends(get_db)):
    if not db.get(models.Case, case_id): raise HTTPException(404, "Case not found")
    rows = db.query(models.AuditLog).filter_by(case_id=case_id).order_by(models.AuditLog.created_at).all()
    return [{"id": r.id, "action": r.action, "details": r.details, "created_at": r.created_at}
            for r in rows]


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(Path(__file__).parent / "static" / "index.html")

@app.get("/sources")
def official_sources():
    return OFFICIAL_SOURCES

@app.get("/knowledge-graph")
def knowledge_graph(db: Session = Depends(get_db)):
    articles = db.query(models.LegalArticle).filter(models.LegalArticle.is_demo == False).all()
    return build_graph(articles)

@app.post("/articles/{article_id}/validate")
def validate_article(article_id: int, event_date: date, db: Session = Depends(get_db)):
    from .services.citation_guard import validate_article_for_date, CitationBlocked
    article = db.get(models.LegalArticle, article_id)
    try:
        validate_article_for_date(article, event_date)
        return {"valid": True, "article_id": article_id, "event_date": event_date}
    except CitationBlocked as exc:
        raise HTTPException(status_code=422, detail=str(exc))
