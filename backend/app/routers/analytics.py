"""Data & SEO Specialist: SEO metadata, analytics dashboard, search/click logs."""
import csv
import io
import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import Date, case, cast, func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import client_ip, get_current_user_optional, require_permissions
from ..models import Category, Comment, Document, DocumentView, Like, SearchLog, User
from ..schemas import Message, Page, SearchClickIn, SearchLogOut, SEOItem, SEOUpdate
from ..utils import audit

router = APIRouter(tags=["seo & analytics"])


# ------------------------------------------------------ click logging ------

@router.post("/logs/click", response_model=Message, status_code=status.HTTP_201_CREATED)
def log_click(data: SearchClickIn, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    """Record that a search result was clicked (Phase-2 relevance feedback)."""
    if db.get(Document, data.clicked_doc_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    db.add(
        SearchLog(
            user_id=user.id if user else None,
            session_id=data.session_id,
            query_string=data.query_string.strip()[:500],
            clicked_doc_id=data.clicked_doc_id,
            event_type="click",
            rank_position=data.rank_position,
        )
    )
    db.commit()
    return Message(message="logged")


# ---------------------------------------------------------------- SEO ------

def seo_issues(d: Document) -> list[str]:
    issues = []
    if not d.seo_title:
        issues.append("Missing SEO title")
    elif len(d.seo_title) > 60:
        issues.append("SEO title longer than 60 characters")
    if not d.seo_description:
        issues.append("Missing meta description")
    elif not 50 <= len(d.seo_description) <= 160:
        issues.append("Meta description should be 50–160 characters")
    if not d.seo_keywords:
        issues.append("Missing keywords")
    if d.cover_image_url and not d.cover_image_alt:
        issues.append("Image has no alt text")
    return issues


def _seo_item(d: Document) -> SEOItem:
    item = SEOItem.model_validate(d)
    item.issues = seo_issues(d)
    return item


@router.get("/seo/documents", response_model=Page[SEOItem])
def seo_documents(
    q: str | None = Query(default=None, max_length=200),
    only_issues: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("seo.manage")),
):
    stmt = select(Document)
    if q:
        stmt = stmt.where(Document.title.ilike(f"%{q.strip()}%"))
    if only_issues:
        stmt = stmt.where(
            or_(
                Document.seo_title.is_(None), Document.seo_title == "", func.length(Document.seo_title) > 60,
                Document.seo_description.is_(None), Document.seo_description == "",
                func.length(Document.seo_description) < 50, func.length(Document.seo_description) > 160,
                Document.seo_keywords.is_(None), Document.seo_keywords == "",
                (Document.cover_image_url.is_not(None)) & (or_(Document.cover_image_alt.is_(None),
                                                                Document.cover_image_alt == "")),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Document.id).offset((page - 1) * page_size).limit(page_size)).unique()
    return Page(items=[_seo_item(d) for d in rows], total=total, page=page, page_size=page_size,
                pages=max(1, math.ceil(total / page_size)))


@router.put("/seo/documents/{doc_id}", response_model=SEOItem)
def update_seo(
    doc_id: int,
    data: SEOUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("seo.manage")),
):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    values = data.model_dump(exclude_unset=True)
    for k, v in values.items():
        setattr(doc, k, (v.strip() or None) if isinstance(v, str) else v)
    audit(db, "seo.update", user.id, "document", doc.id, {"fields": sorted(values)}, client_ip(request))
    db.commit()
    db.refresh(doc)
    return _seo_item(doc)


# ---------------------------------------------------------- analytics ------

@router.get("/analytics/summary")
def analytics_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("analytics.view")),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    doc_status = dict(db.execute(select(Document.status, func.count(Document.id)).group_by(Document.status)).all())
    searches = db.scalar(select(func.count(SearchLog.id)).where(SearchLog.event_type == "search",
                                                               SearchLog.timestamp >= since)) or 0
    clicks = db.scalar(select(func.count(SearchLog.id)).where(SearchLog.event_type == "click",
                                                             SearchLog.timestamp >= since)) or 0
    views_period = db.scalar(select(func.count(DocumentView.id)).where(DocumentView.viewed_at >= since)) or 0

    day = cast(DocumentView.viewed_at, Date)
    views_by_day = [
        {"date": d.isoformat(), "views": n}
        for d, n in db.execute(
            select(day, func.count(DocumentView.id)).where(DocumentView.viewed_at >= since).group_by(day).order_by(day)
        ).all()
    ]
    sday = cast(SearchLog.timestamp, Date)
    searches_by_day = [
        {"date": d.isoformat(), "searches": s, "clicks": c}
        for d, s, c in db.execute(
            select(
                sday,
                func.sum(case((SearchLog.event_type == "search", 1), else_=0)),
                func.sum(case((SearchLog.event_type == "click", 1), else_=0)),
            ).where(SearchLog.timestamp >= since).group_by(sday).order_by(sday)
        ).all()
    ]

    top_docs = [
        {"id": i, "title": t, "slug": s, "views": v}
        for i, t, s, v in db.execute(
            select(Document.id, Document.title, Document.slug, Document.views_count)
            .where(Document.status == "published").order_by(Document.views_count.desc()).limit(10)
        ).all()
    ]

    q_norm = func.lower(SearchLog.query_string)
    top_queries = [
        {"query": q, "searches": s, "clicks": c, "avg_results": round(float(r), 1) if r is not None else None,
         "ctr": round(c / s, 3) if s else None}
        for q, s, c, r in db.execute(
            select(
                q_norm,
                func.sum(case((SearchLog.event_type == "search", 1), else_=0)).label("s"),
                func.sum(case((SearchLog.event_type == "click", 1), else_=0)),
                func.avg(SearchLog.results_count),
            )
            .where(SearchLog.timestamp >= since)
            .group_by(q_norm)
            .order_by(func.sum(case((SearchLog.event_type == "search", 1), else_=0)).desc())
            .limit(15)
        ).all()
    ]
    zero_results = [
        {"query": q, "count": n}
        for q, n in db.execute(
            select(q_norm, func.count(SearchLog.id))
            .where(SearchLog.event_type == "search", SearchLog.results_count == 0, SearchLog.timestamp >= since)
            .group_by(q_norm).order_by(func.count(SearchLog.id).desc()).limit(10)
        ).all()
    ]
    by_category = [
        {"category": name or "Uncategorised", "documents": n, "views": int(v or 0)}
        for name, n, v in db.execute(
            select(Category.name, func.count(Document.id), func.sum(Document.views_count))
            .select_from(Document).outerjoin(Category, Category.id == Document.category_id)
            .where(Document.status == "published")
            .group_by(Category.name).order_by(func.sum(Document.views_count).desc())
        ).all()
    ]
    avg_click_rank = db.scalar(
        select(func.avg(SearchLog.rank_position)).where(SearchLog.event_type == "click", SearchLog.timestamp >= since)
    )

    return {
        "period_days": days,
        "totals": {
            "documents": sum(doc_status.values()),
            "published": doc_status.get("published", 0),
            "drafts": doc_status.get("draft", 0),
            "archived": doc_status.get("archived", 0),
            "users": db.scalar(select(func.count(User.id))) or 0,
            "comments": db.scalar(select(func.count(Comment.id))) or 0,
            "likes": db.scalar(select(func.count(Like.id))) or 0,
            "all_time_views": int(db.scalar(select(func.coalesce(func.sum(Document.views_count), 0))) or 0),
            "views_in_period": views_period,
            "searches_in_period": searches,
            "clicks_in_period": clicks,
            "search_ctr": round(clicks / searches, 3) if searches else None,
            "avg_click_rank": round(float(avg_click_rank), 2) if avg_click_rank is not None else None,
        },
        "views_by_day": views_by_day,
        "searches_by_day": searches_by_day,
        "top_documents": top_docs,
        "top_queries": top_queries,
        "zero_result_queries": zero_results,
        "by_category": by_category,
    }


@router.get("/analytics/search-logs", response_model=Page[SearchLogOut])
def search_logs(
    q: str | None = Query(default=None, max_length=200),
    event_type: str | None = Query(default=None, pattern="^(search|click)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("analytics.view")),
):
    stmt = select(SearchLog)
    if q:
        stmt = stmt.where(SearchLog.query_string.ilike(f"%{q}%"))
    if event_type:
        stmt = stmt.where(SearchLog.event_type == event_type)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(SearchLog.timestamp.desc(), SearchLog.id.desc())
                      .offset((page - 1) * page_size).limit(page_size))
    return Page(items=[SearchLogOut.model_validate(r) for r in rows], total=total, page=page, page_size=page_size,
                pages=max(1, math.ceil(total / page_size)))


@router.get("/analytics/search-logs.csv")
def export_search_logs(db: Session = Depends(get_db), _: User = Depends(require_permissions("analytics.view"))):
    """CSV export for offline Phase-2 experiments (click models, evaluation)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "user_id", "session_id", "query_string", "clicked_doc_id", "event_type",
                "rank_position", "results_count", "timestamp"])
    for r in db.scalars(select(SearchLog).order_by(SearchLog.timestamp, SearchLog.id)):
        w.writerow([r.id, r.user_id, r.session_id, r.query_string, r.clicked_doc_id, r.event_type,
                    r.rank_position, r.results_count, r.timestamp.isoformat()])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=search_logs.csv"})
