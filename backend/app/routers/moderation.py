import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import client_ip, require_permissions
from ..models import Comment, Document, Report, SpamKeyword, User
from ..schemas import (
    CommentModerationOut,
    CommentStatusUpdate,
    Message,
    Page,
    ReportHandle,
    ReportOut,
    SpamKeywordIn,
    SpamKeywordOut,
    UserPublic,
)
from ..utils import audit
from .engagement import to_comment_out

router = APIRouter(prefix="/moderation", tags=["moderation"])


def _report_counts(db: Session, comment_ids: list[int]) -> dict[int, int]:
    if not comment_ids:
        return {}
    rows = db.execute(
        select(Report.target_id, func.count(Report.id))
        .where(Report.target_type == "comment", Report.target_id.in_(comment_ids), Report.status == "open")
        .group_by(Report.target_id)
    ).all()
    return {tid: n for tid, n in rows}


@router.get("/stats")
def stats(db: Session = Depends(get_db), _: User = Depends(require_permissions("comments.moderate"))):
    by_status = dict(db.execute(select(Comment.status, func.count(Comment.id)).group_by(Comment.status)).all())
    open_reports = db.scalar(select(func.count(Report.id)).where(Report.status == "open")) or 0
    return {
        "comments": {s: by_status.get(s, 0) for s in ("visible", "pending", "hidden", "spam")},
        "open_reports": open_reports,
        "spam_keywords": db.scalar(select(func.count(SpamKeyword.id))) or 0,
    }


@router.get("/comments", response_model=Page[CommentModerationOut])
def list_comments(
    status_: str | None = Query(default=None, alias="status", pattern="^(visible|pending|hidden|spam|reported)$"),
    q: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("comments.moderate")),
):
    stmt = select(Comment)
    if status_ == "reported":
        reported = select(Report.target_id).where(Report.target_type == "comment", Report.status == "open")
        stmt = stmt.where(Comment.id.in_(reported))
    elif status_:
        stmt = stmt.where(Comment.status == status_)
    if q:
        stmt = stmt.where(Comment.body.ilike(f"%{q.strip()}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = list(
        db.scalars(stmt.order_by(Comment.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).unique()
    )
    counts = _report_counts(db, [c.id for c in rows])
    items = [
        CommentModerationOut(
            **to_comment_out(c).model_dump(),
            document_title=c.document.title,
            report_count=counts.get(c.id, 0),
        )
        for c in rows
    ]
    return Page(items=items, total=total, page=page, page_size=page_size, pages=max(1, math.ceil(total / page_size)))


@router.patch("/comments/{comment_id}", response_model=Message)
def set_comment_status(
    comment_id: int,
    data: CommentStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("comments.moderate")),
):
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(404, "Comment not found")
    old = comment.status
    comment.status = data.status
    audit(db, "comment.moderate", user.id, "comment", comment.id, {"from": old, "to": data.status},
          client_ip(request))
    db.commit()
    return Message(message=f"Comment marked as {data.status}")


@router.delete("/comments/{comment_id}", response_model=Message)
def delete_comment(
    comment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("comments.moderate")),
):
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(404, "Comment not found")
    audit(db, "comment.delete", user.id, "comment", comment.id, {"body": comment.body[:200]}, client_ip(request))
    db.delete(comment)
    db.commit()
    return Message(message="Comment deleted")


# ------------------------------------------------------------- reports -----

def _report_out(db: Session, r: Report) -> ReportOut:
    preview = link = None
    if r.target_type == "comment":
        c = db.get(Comment, r.target_id)
        if c:
            preview = f'{c.user.username}: "{c.body[:200]}" (status: {c.status})'
            link = f"/documents/{c.document.slug}#comment-{c.id}"
        else:
            preview = "[comment deleted]"
    else:
        d = db.get(Document, r.target_id)
        if d:
            preview = f"{d.title} (status: {d.status})"
            link = f"/documents/{d.slug}"
        else:
            preview = "[document deleted]"
    return ReportOut(
        id=r.id,
        target_type=r.target_type,
        target_id=r.target_id,
        reason=r.reason,
        status=r.status,
        resolution_note=r.resolution_note,
        created_at=r.created_at,
        handled_at=r.handled_at,
        reporter=UserPublic.model_validate(r.reporter) if r.reporter else None,
        handled_by=UserPublic.model_validate(r.handled_by) if r.handled_by else None,
        target_preview=preview,
        target_link=link,
    )


@router.get("/reports", response_model=list[ReportOut])
def list_reports(
    status_: str | None = Query(default="open", alias="status", pattern="^(open|resolved|dismissed|all)$"),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("reports.manage")),
):
    stmt = select(Report).order_by(Report.created_at.desc()).limit(200)
    if status_ and status_ != "all":
        stmt = stmt.where(Report.status == status_)
    return [_report_out(db, r) for r in db.scalars(stmt).unique()]


@router.patch("/reports/{report_id}", response_model=ReportOut)
def handle_report(
    report_id: int,
    data: ReportHandle,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("reports.manage")),
):
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(404, "Report not found")
    report.status = data.status
    report.resolution_note = data.note
    report.handled_by_id = user.id
    report.handled_at = datetime.now(timezone.utc)
    if data.hide_target:
        if report.target_type == "comment":
            c = db.get(Comment, report.target_id)
            if c:
                c.status = "hidden"
        else:
            if "documents.publish" not in user.permission_codes:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Unpublishing a document requires documents.publish")
            d = db.get(Document, report.target_id)
            if d:
                d.status = "draft"
    audit(db, "report.handle", user.id, "report", report.id,
          {"status": data.status, "hide_target": data.hide_target}, client_ip(request))
    db.commit()
    db.refresh(report)
    return _report_out(db, report)


# -------------------------------------------------------- spam keywords ----

@router.get("/spam-keywords", response_model=list[SpamKeywordOut])
def list_spam_keywords(db: Session = Depends(get_db), _: User = Depends(require_permissions("spam.manage"))):
    return list(db.scalars(select(SpamKeyword).order_by(SpamKeyword.keyword)))


@router.post("/spam-keywords", response_model=SpamKeywordOut, status_code=201)
def add_spam_keyword(
    data: SpamKeywordIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("spam.manage")),
):
    kw = SpamKeyword(keyword=data.keyword.strip().lower())
    db.add(kw)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Keyword already exists")
    audit(db, "spam.keyword_add", user.id, "spam_keyword", kw.id, {"keyword": kw.keyword}, client_ip(request))
    db.commit()
    db.refresh(kw)
    return kw


@router.delete("/spam-keywords/{kw_id}", response_model=Message)
def delete_spam_keyword(
    kw_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("spam.manage")),
):
    kw = db.get(SpamKeyword, kw_id)
    if kw is None:
        raise HTTPException(404, "Keyword not found")
    audit(db, "spam.keyword_delete", user.id, "spam_keyword", kw.id, {"keyword": kw.keyword}, client_ip(request))
    db.delete(kw)
    db.commit()
    return Message(message="Keyword removed")
