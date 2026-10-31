import math
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import client_ip, get_current_user_optional, require_permissions
from ..models import Category, Comment, Document, DocumentView, Like, Rating, SearchLog, Tag, User, document_tags
from ..schemas import (
    DocumentDetail,
    DocumentIn,
    DocumentListItem,
    DocumentUpdate,
    Message,
    Page,
    StatusUpdate,
)
from ..utils import audit, get_setting, make_summary, unique_slug

router = APIRouter(tags=["documents"])

SORTS = {
    "latest": (Document.created_at.desc(), Document.id.desc()),
    "oldest": (Document.created_at.asc(), Document.id.asc()),
    "views": (Document.views_count.desc(), Document.id.desc()),
    "title": (Document.title.asc(), Document.id.asc()),
}


# ------------------------------------------------------------ helpers ------

def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def apply_filters(
    stmt: Select,
    q: str | None,
    category: str | None,
    tag: str | None,
    doc_type: str | None,
    date_from: date | None,
    date_to: date | None,
) -> Select:
    if q:
        # Basic keyword search (Phase-2 placeholder): every word must appear
        # (case-insensitive LIKE) in the title, summary or content.
        for word in q.split()[:10]:
            pattern = f"%{_escape_like(word)}%"
            stmt = stmt.where(
                or_(
                    Document.title.ilike(pattern, escape="\\"),
                    Document.summary.ilike(pattern, escape="\\"),
                    Document.content.ilike(pattern, escape="\\"),
                )
            )
    if category:
        cat_cond = Category.slug == category
        if category.isdigit():
            cat_cond = or_(cat_cond, Category.id == int(category))
        stmt = stmt.where(Document.category_id.in_(select(Category.id).where(cat_cond)))
    if tag:
        stmt = stmt.where(
            Document.id.in_(
                select(document_tags.c.document_id)
                .join(Tag, Tag.id == document_tags.c.tag_id)
                .where(Tag.slug == tag)
            )
        )
    if doc_type:
        stmt = stmt.where(Document.doc_type == doc_type)
    if date_from:
        stmt = stmt.where(Document.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
        stmt = stmt.where(Document.created_at < end)
    return stmt


def paginate(db: Session, stmt: Select, page: int, page_size: int, order_by) -> Page:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(stmt.order_by(*order_by).offset((page - 1) * page_size).limit(page_size)).unique().all()
    return Page(
        items=[DocumentListItem.model_validate(d) for d in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)) if page_size else 1,
    )


def resolve_tags(db: Session, names: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    for name in names:
        tag = db.scalar(select(Tag).where(func.lower(Tag.name) == name.lower()))
        if tag is None:
            tag = Tag(name=name, slug=unique_slug(db, Tag, name))
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


def get_doc_by_ref(db: Session, ref: str) -> Document | None:
    if ref.isdigit():
        doc = db.get(Document, int(ref))
        if doc:
            return doc
    return db.scalar(select(Document).where(Document.slug == ref))


def build_detail(db: Session, doc: Document, user: User | None) -> DocumentDetail:
    likes = db.scalar(select(func.count(Like.id)).where(Like.document_id == doc.id)) or 0
    r_avg, r_cnt = db.execute(
        select(func.avg(Rating.score), func.count(Rating.id)).where(Rating.document_id == doc.id)
    ).one()
    comments = (
        db.scalar(select(func.count(Comment.id)).where(Comment.document_id == doc.id, Comment.status == "visible"))
        or 0
    )
    liked = my_rating = None
    if user:
        liked = db.scalar(select(Like.id).where(Like.document_id == doc.id, Like.user_id == user.id)) is not None
        my_rating = db.scalar(select(Rating.score).where(Rating.document_id == doc.id, Rating.user_id == user.id))
    detail = DocumentDetail.model_validate(doc)
    detail.likes_count = likes
    detail.rating_avg = round(float(r_avg), 2) if r_avg is not None else None
    detail.rating_count = r_cnt
    detail.comments_count = comments
    detail.liked_by_me = bool(liked)
    detail.my_rating = my_rating
    return detail


# ------------------------------------------------------ public routes ------

@router.get("/documents", response_model=Page[DocumentListItem])
def list_documents(
    request: Request,
    q: str | None = Query(default=None, max_length=200, description="Keyword search (LIKE)"),
    category: str | None = Query(default=None, description="Category slug or id"),
    tag: str | None = Query(default=None, description="Tag slug"),
    doc_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort: str = Query(default="latest", pattern="^(latest|oldest|views|title)$"),
    page: int = Query(default=1, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=50),
    session_id: str | None = Query(default=None, max_length=64),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    q = q.strip() if q else None
    size = page_size or int(get_setting(db, "default_page_size") or 10)
    stmt = select(Document).where(Document.status == "published")
    stmt = apply_filters(stmt, q, category, tag, doc_type, date_from, date_to)
    result = paginate(db, stmt, page, size, SORTS[sort])

    if q and page == 1:
        # Search log for Phase 2 (one row per executed query).
        db.add(
            SearchLog(
                user_id=user.id if user else None,
                session_id=session_id,
                query_string=q[:500],
                event_type="search",
                results_count=result.total,
                filters={
                    k: v
                    for k, v in {
                        "category": category,
                        "tag": tag,
                        "doc_type": doc_type,
                        "date_from": date_from.isoformat() if date_from else None,
                        "date_to": date_to.isoformat() if date_to else None,
                        "sort": sort,
                    }.items()
                    if v
                },
            )
        )
        db.commit()
    return result


@router.get("/documents/doc-types", response_model=list[str])
def list_doc_types(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Document.doc_type).where(Document.status == "published").distinct().order_by(Document.doc_type)
    )
    return [r for r in rows if r]


@router.get("/documents/popular", response_model=list[DocumentListItem])
def popular_documents(limit: int = Query(default=5, ge=1, le=20), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Document).where(Document.status == "published").order_by(Document.views_count.desc()).limit(limit)
    ).unique()
    return [DocumentListItem.model_validate(d) for d in rows]


@router.get("/documents/{ref}", response_model=DocumentDetail)
def get_document(
    ref: str,
    track: bool = Query(default=True, description="Count this request as a view"),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    doc = get_doc_by_ref(db, ref)
    can_see_all = bool(user and "documents.read_all" in user.permission_codes)
    if doc is None or (doc.status != "published" and not can_see_all):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if track and doc.status == "published":
        doc.views_count = (doc.views_count or 0) + 1
        db.add(DocumentView(document_id=doc.id, user_id=user.id if user else None))
        db.commit()
        db.refresh(doc)
    return build_detail(db, doc, user)


@router.get("/documents/{doc_id}/related", response_model=list[DocumentListItem])
def related_documents(doc_id: int, limit: int = Query(default=4, ge=1, le=12), db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    tag_ids = [t.id for t in doc.tags]
    shared = (
        select(func.count())
        .select_from(document_tags)
        .where(and_(document_tags.c.document_id == Document.id, document_tags.c.tag_id.in_(tag_ids or [-1])))
        .scalar_subquery()
    )
    rows = db.scalars(
        select(Document)
        .where(Document.status == "published", Document.id != doc.id)
        .where(or_(Document.category_id == doc.category_id, shared > 0))
        .order_by(shared.desc(), Document.views_count.desc())
        .limit(limit)
    ).unique()
    return [DocumentListItem.model_validate(d) for d in rows]


# ------------------------------------------------------- admin routes ------

@router.get("/admin/documents", response_model=Page[DocumentListItem])
def admin_list_documents(
    q: str | None = Query(default=None, max_length=200),
    status_: str | None = Query(default=None, alias="status", pattern="^(draft|published|archived)$"),
    category: str | None = None,
    tag: str | None = None,
    sort: str = Query(default="latest", pattern="^(latest|oldest|views|title)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("documents.read_all")),
):
    stmt = select(Document)
    if status_:
        stmt = stmt.where(Document.status == status_)
    stmt = apply_filters(stmt, q.strip() if q else None, category, tag, None, None, None)
    return paginate(db, stmt, page, page_size, SORTS[sort])


@router.get("/admin/documents/{doc_id}", response_model=DocumentDetail)
def admin_get_document(
    doc_id: int, db: Session = Depends(get_db), user: User = Depends(require_permissions("documents.read_all"))
):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    return build_detail(db, doc, user)


def _check_category(db: Session, category_id: int | None) -> None:
    if category_id is not None and db.get(Category, category_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Category does not exist")


@router.post("/admin/documents", response_model=DocumentDetail, status_code=status.HTTP_201_CREATED)
def create_document(
    data: DocumentIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("documents.create")),
):
    if data.status != "draft" and "documents.publish" not in user.permission_codes:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Missing permission: documents.publish")
    _check_category(db, data.category_id)
    now = datetime.now(timezone.utc)
    doc = Document(
        title=data.title.strip(),
        slug=unique_slug(db, Document, data.title),
        summary=data.summary.strip() or make_summary(data.content),
        content=data.content,
        doc_type=data.doc_type,
        department=data.department,
        category_id=data.category_id,
        author_id=user.id,
        status=data.status,
        cover_image_url=data.cover_image_url or None,
        cover_image_alt=data.cover_image_alt or None,
        created_at=now,
        updated_at=now,
        published_at=now if data.status == "published" else None,
    )
    doc.tags = resolve_tags(db, data.tags)
    db.add(doc)
    db.flush()
    audit(db, "document.create", user.id, "document", doc.id, {"title": doc.title, "status": doc.status},
          client_ip(request))
    db.commit()
    db.refresh(doc)
    return build_detail(db, doc, user)


@router.put("/admin/documents/{doc_id}", response_model=DocumentDetail)
def update_document(
    doc_id: int,
    data: DocumentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("documents.update")),
):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    values = data.model_dump(exclude_unset=True)
    if "status" in values and values["status"] != doc.status and "documents.publish" not in user.permission_codes:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Missing permission: documents.publish")
    if "category_id" in values:
        _check_category(db, values["category_id"])
    if "title" in values and values["title"] and values["title"].strip() != doc.title:
        doc.title = values["title"].strip()
        doc.slug = unique_slug(db, Document, doc.title, exclude_id=doc.id)
    for field in ("content", "doc_type", "department", "category_id", "cover_image_url", "cover_image_alt"):
        if field in values and (values[field] is not None or field in ("category_id", "cover_image_url",
                                                                        "cover_image_alt")):
            setattr(doc, field, values[field])
    if "summary" in values and values["summary"] is not None:
        doc.summary = values["summary"].strip() or make_summary(doc.content)
    if "tags" in values and values["tags"] is not None:
        doc.tags = resolve_tags(db, values["tags"])
    if "status" in values and values["status"]:
        _set_status(doc, values["status"])
    doc.updated_at = datetime.now(timezone.utc)
    audit(db, "document.update", user.id, "document", doc.id, {"fields": sorted(values.keys())}, client_ip(request))
    db.commit()
    db.refresh(doc)
    return build_detail(db, doc, user)


def _set_status(doc: Document, new_status: str) -> None:
    if new_status == "published" and doc.published_at is None:
        doc.published_at = datetime.now(timezone.utc)
    doc.status = new_status


@router.patch("/admin/documents/{doc_id}/status", response_model=DocumentDetail)
def change_status(
    doc_id: int,
    data: StatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("documents.publish")),
):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    old = doc.status
    _set_status(doc, data.status)
    doc.updated_at = datetime.now(timezone.utc)
    audit(db, f"document.{'publish' if data.status == 'published' else 'unpublish'}", user.id, "document", doc.id,
          {"from": old, "to": data.status}, client_ip(request))
    db.commit()
    db.refresh(doc)
    return build_detail(db, doc, user)


@router.delete("/admin/documents/{doc_id}", response_model=Message)
def delete_document(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("documents.delete")),
):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    audit(db, "document.delete", user.id, "document", doc.id, {"title": doc.title}, client_ip(request))
    db.delete(doc)
    db.commit()
    return Message(message="Document deleted")
