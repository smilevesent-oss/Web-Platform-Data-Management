from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import client_ip, get_current_user
from ..models import Comment, CommentMention, Role, User
from ..permissions import ROLE_USER
from ..schemas import (
    LoginIn,
    MentionOut,
    Message,
    PasswordChange,
    ProfileUpdate,
    RegisterIn,
    RoleBrief,
    TokenOut,
    UserMe,
    UserPublic,
)
from ..security import create_access_token, hash_password, verify_password
from ..utils import audit, get_setting

router = APIRouter(tags=["auth & profile"])


def to_me(user: User) -> UserMe:
    return UserMe(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        department=user.department,
        bio=user.bio,
        avatar_url=user.avatar_url,
        email=user.email,
        role=RoleBrief.model_validate(user.role),
        permissions=sorted(user.permission_codes),
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.post("/auth/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, request: Request, db: Session = Depends(get_db)):
    if not get_setting(db, "registration_open"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Registration is currently closed")
    email = data.email.lower()
    if db.scalar(select(User.id).where(func.lower(User.username) == data.username.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Username is already taken")
    if db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail is already registered")
    role = db.scalar(select(Role).where(Role.name == ROLE_USER))
    if role is None:
        raise HTTPException(500, "Default role missing; run the database initialisation")
    user = User(
        username=data.username,
        email=email,
        password_hash=hash_password(data.password),
        full_name=data.full_name.strip(),
        role_id=role.id,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.flush()
    audit(db, "user.register", user.id, "user", user.id, ip=client_ip(request))
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id, user.role.name), user=to_me(user))


@router.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    ident = data.username.strip().lower()
    user = db.scalar(
        select(User).where(or_(func.lower(User.username) == ident, func.lower(User.email) == ident))
    )
    if user is None or not verify_password(data.password, user.password_hash):
        audit(db, "auth.login_failed", None, "user", None, {"username": ident}, client_ip(request))
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated")
    user.last_login_at = datetime.now(timezone.utc)
    audit(db, "auth.login", user.id, "user", user.id, ip=client_ip(request))
    db.commit()
    return TokenOut(access_token=create_access_token(user.id, user.role.name), user=to_me(user))


@router.get("/auth/me", response_model=UserMe)
def me(user: User = Depends(get_current_user)):
    return to_me(user)


@router.put("/auth/me", response_model=UserMe)
def update_profile(data: ProfileUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    values = data.model_dump(exclude_unset=True)
    if "email" in values and values["email"] is not None:
        email = values["email"].lower()
        clash = db.scalar(select(User.id).where(func.lower(User.email) == email, User.id != user.id))
        if clash:
            raise HTTPException(status.HTTP_409_CONFLICT, "E-mail is already registered")
        user.email = email
    for field in ("full_name", "bio", "department", "avatar_url"):
        if field in values and values[field] is not None:
            setattr(user, field, values[field].strip() if isinstance(values[field], str) else values[field])
    db.commit()
    db.refresh(user)
    return to_me(user)


@router.post("/auth/change-password", response_model=Message)
def change_password(
    data: PasswordChange, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    audit(db, "user.change_password", user.id, "user", user.id, ip=client_ip(request))
    db.commit()
    return Message(message="Password updated")


@router.get("/users/search", response_model=list[UserPublic])
def search_users(q: str = Query(min_length=1, max_length=50), db: Session = Depends(get_db)):
    """Autocomplete for @mentions."""
    like = f"{q.lower()}%"
    rows = db.scalars(
        select(User)
        .where(User.is_active.is_(True))
        .where(or_(func.lower(User.username).like(like), func.lower(User.full_name).like(f"%{q.lower()}%")))
        .order_by(User.username)
        .limit(8)
    )
    return list(rows)


@router.get("/users/{username}", response_model=UserPublic)
def public_profile(username: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.username) == username.lower(), User.is_active.is_(True)))
    if user is None:
        raise HTTPException(404, "User not found")
    return user


@router.get("/me/mentions", response_model=list[MentionOut])
def my_mentions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(CommentMention, Comment)
        .join(Comment, Comment.id == CommentMention.comment_id)
        .where(CommentMention.user_id == user.id, Comment.status == "visible")
        .order_by(Comment.created_at.desc())
        .limit(50)
    ).all()
    return [
        MentionOut(
            comment_id=c.id,
            document_id=c.document_id,
            document_title=c.document.title,
            document_slug=c.document.slug,
            by=UserPublic.model_validate(c.user),
            body=c.body,
            created_at=c.created_at,
            is_read=m.is_read,
        )
        for m, c in rows
    ]


@router.post("/me/mentions/read", response_model=Message)
def mark_mentions_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(update(CommentMention).where(CommentMention.user_id == user.id).values(is_read=True))
    db.commit()
    return Message(message="ok")
