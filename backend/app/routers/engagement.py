from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import client_ip, get_current_user, get_current_user_optional
from ..models import Comment, CommentMention, Document, Like, Rating, Report, SpamKeyword, User
from ..schemas import (
    CommentIn,
    CommentOut,
    CommentUpdate,
    EngagementOut,
    Message,
    RatingIn,
    ReportIn,
    UserPublic,
)
from ..utils import audit, extract_mentions, get_setting

router = APIRouter(tags=["engagement"])


def to_comment_out(c: Comment) -> CommentOut:
    return CommentOut(
        id=c.id,
        document_id=c.document_id,
        parent_id=c.parent_id,
        body=c.body,
        status=c.status,
        created_at=c.created_at,
        updated_at=c.updated_at,
        user=UserPublic.model_validate(c.user),
        mentions=sorted(m.user.username for m in c.mentions),
    )


def _published_doc(db: Session, doc_id: int) -> Document:
    doc = db.get(Document, doc_id)
    if doc is None or doc.status != "published":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return doc


def _is_spam(db: Session, body: str) -> bool:
    text = body.lower()
    return any(k in text for k in db.scalars(select(func.lower(SpamKeyword.keyword))))


def _sync_mentions(db: Session, comment: Comment, author: User) -> None:
    names = {n.lower() for n in extract_mentions(comment.body)}
    users = (
        list(db.scalars(select(User).where(func.lower(User.username).in_(names), User.is_active.is_(True))))
        if names
        else []
    )
    wanted = {u.id for u in users if u.id != author.id}
    comment.mentions = [m for m in comment.mentions if m.user_id in wanted]
    have = {m.user_id for m in comment.mentions}
    for uid in wanted - have:
        comment.mentions.append(CommentMention(user_id=uid))


def engagement_for(db: Session, doc_id: int, user: User | None) -> EngagementOut:
    likes = db.scalar(select(func.count(Like.id)).where(Like.document_id == doc_id)) or 0
    avg, cnt = db.execute(
        select(func.avg(Rating.score), func.count(Rating.id)).where(Rating.document_id == doc_id)
    ).one()
    liked, mine = False, None
    if user:
        liked = db.scalar(select(Like.id).where(Like.document_id == doc_id, Like.user_id == user.id)) is not None
        mine = db.scalar(select(Rating.score).where(Rating.document_id == doc_id, Rating.user_id == user.id))
    return EngagementOut(
        likes_count=likes,
        liked_by_me=liked,
        rating_avg=round(float(avg), 2) if avg is not None else None,
        rating_count=cnt,
        my_rating=mine,
    )


# ------------------------------------------------------------ comments -----

@router.get("/documents/{doc_id}/comments", response_model=list[CommentOut])
def list_comments(
    doc_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)
):
    _published_doc(db, doc_id)
    cond = Comment.status == "visible"
    if user:
        cond = or_(cond, and_own(user.id))
    rows = db.scalars(
        select(Comment).where(Comment.document_id == doc_id, cond).order_by(Comment.created_at.asc())
    ).unique()
    return [to_comment_out(c) for c in rows]


def and_own(user_id: int):
    # A member also sees their own comments that are awaiting moderation.
    return (Comment.user_id == user_id) & (Comment.status == "pending")


@router.post("/documents/{doc_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    doc_id: int,
    data: CommentIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not get_setting(db, "comments_enabled"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Comments are currently disabled")
    _published_doc(db, doc_id)
    if data.parent_id is not None:
        parent = db.get(Comment, data.parent_id)
        if parent is None or parent.document_id != doc_id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Parent comment not found on this document")
    body = data.body.strip()
    if not body:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Comment cannot be empty")
    if _is_spam(db, body):
        state = "spam"
    elif get_setting(db, "comments_require_approval"):
        state = "pending"
    else:
        state = "visible"
    comment = Comment(document_id=doc_id, user_id=user.id, parent_id=data.parent_id, body=body, status=state)
    db.add(comment)
    db.flush()
    _sync_mentions(db, comment, user)
    if state == "spam":
        audit(db, "comment.auto_spam", user.id, "comment", comment.id, ip=client_ip(request))
    db.commit()
    db.refresh(comment)
    return to_comment_out(comment)


@router.put("/comments/{comment_id}", response_model=CommentOut)
def edit_comment(
    comment_id: int, data: CommentUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    comment = db.get(Comment, comment_id)
    if comment is None or comment.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    if comment.status in ("hidden", "spam"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This comment was moderated and can no longer be edited")
    comment.body = data.body.strip()
    if _is_spam(db, comment.body):
        comment.status = "spam"
    _sync_mentions(db, comment, user)
    db.commit()
    db.refresh(comment)
    return to_comment_out(comment)


@router.delete("/comments/{comment_id}", response_model=Message)
def delete_comment(
    comment_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    comment = db.get(Comment, comment_id)
    is_mod = "comments.moderate" in user.permission_codes
    if comment is None or (comment.user_id != user.id and not is_mod):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    if comment.user_id != user.id:
        audit(db, "comment.delete", user.id, "comment", comment.id, {"by_moderator": True}, client_ip(request))
    db.delete(comment)
    db.commit()
    return Message(message="Comment deleted")


# ------------------------------------------------------- likes / rating ----

@router.get("/documents/{doc_id}/engagement", response_model=EngagementOut)
def get_engagement(doc_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)):
    _published_doc(db, doc_id)
    return engagement_for(db, doc_id, user)


@router.post("/documents/{doc_id}/like", response_model=EngagementOut)
def toggle_like(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _published_doc(db, doc_id)
    existing = db.scalar(select(Like).where(Like.document_id == doc_id, Like.user_id == user.id))
    if existing:
        db.delete(existing)
    else:
        db.add(Like(document_id=doc_id, user_id=user.id))
    db.commit()
    return engagement_for(db, doc_id, user)


@router.put("/documents/{doc_id}/rating", response_model=EngagementOut)
def rate(doc_id: int, data: RatingIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _published_doc(db, doc_id)
    existing = db.scalar(select(Rating).where(Rating.document_id == doc_id, Rating.user_id == user.id))
    if existing:
        existing.score = data.score
    else:
        db.add(Rating(document_id=doc_id, user_id=user.id, score=data.score))
    db.commit()
    return engagement_for(db, doc_id, user)


@router.delete("/documents/{doc_id}/rating", response_model=EngagementOut)
def remove_rating(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _published_doc(db, doc_id)
    existing = db.scalar(select(Rating).where(Rating.document_id == doc_id, Rating.user_id == user.id))
    if existing:
        db.delete(existing)
        db.commit()
    return engagement_for(db, doc_id, user)


# ------------------------------------------------------------- reports -----

@router.post("/reports", response_model=Message, status_code=status.HTTP_201_CREATED)
def create_report(data: ReportIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    model = Comment if data.target_type == "comment" else Document
    if db.get(model, data.target_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{data.target_type.capitalize()} not found")
    dup = db.scalar(
        select(Report.id).where(
            Report.reporter_id == user.id,
            Report.target_type == data.target_type,
            Report.target_id == data.target_id,
            Report.status == "open",
        )
    )
    if dup:
        return Message(message="You have already reported this; a moderator will review it")
    db.add(Report(reporter_id=user.id, target_type=data.target_type, target_id=data.target_id,
                  reason=data.reason.strip()))
    db.commit()
    return Message(message="Thanks — a moderator will review your report")
