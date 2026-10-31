"""Super Admin: users & roles, permissions, system logs, global settings."""
import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import client_ip, require_permissions
from ..models import Permission, Role, Setting, SystemLog, User
from ..permissions import DEFAULT_SETTINGS, ROLE_SUPER_ADMIN, SUPER_ADMIN_LOCKED
from ..schemas import (
    AdminUserCreate,
    AdminUserOut,
    AdminUserUpdate,
    Message,
    Page,
    PermissionOut,
    RoleOut,
    RolePermissionsUpdate,
    SettingOut,
    SettingUpdate,
    SystemLogOut,
)
from ..security import hash_password
from ..utils import audit

router = APIRouter(prefix="/admin", tags=["super admin"])


# --------------------------------------------------------------- users -----

@router.get("/users", response_model=Page[AdminUserOut])
def list_users(
    q: str | None = Query(default=None, max_length=100),
    role: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("users.manage")),
):
    stmt = select(User)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(func.lower(User.username).like(like), func.lower(User.email).like(like),
                func.lower(User.full_name).like(like))
        )
    if role:
        stmt = stmt.join(Role, Role.id == User.role_id).where(Role.name == role)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(User.id).offset((page - 1) * page_size).limit(page_size)).unique()
    return Page(
        items=[AdminUserOut.model_validate(u) for u in rows],
        total=total, page=page, page_size=page_size, pages=max(1, math.ceil(total / page_size)),
    )


@router.post("/users", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: AdminUserCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permissions("users.manage")),
):
    if db.scalar(select(User.id).where(func.lower(User.username) == data.username.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Username is already taken")
    if db.scalar(select(User.id).where(func.lower(User.email) == data.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail is already registered")
    if db.get(Role, data.role_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Role does not exist")
    user = User(
        username=data.username,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name.strip(),
        department=data.department.strip(),
        role_id=data.role_id,
    )
    db.add(user)
    db.flush()
    audit(db, "user.create", admin.id, "user", user.id, {"username": user.username, "role_id": data.role_id},
          client_ip(request))
    db.commit()
    db.refresh(user)
    return user


def _super_admin_count(db: Session, exclude_user_id: int | None = None) -> int:
    stmt = (
        select(func.count(User.id))
        .join(Role, Role.id == User.role_id)
        .where(Role.name == ROLE_SUPER_ADMIN, User.is_active.is_(True))
    )
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    return db.scalar(stmt) or 0


@router.put("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int,
    request: Request,
    data: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permissions("users.manage")),
):
    values = data.model_dump(exclude_unset=True)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")

    losing_admin = user.role.name == ROLE_SUPER_ADMIN and (
        ("role_id" in values and values["role_id"] != user.role_id) or values.get("is_active") is False
    )
    if losing_admin and _super_admin_count(db, exclude_user_id=user.id) == 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cannot remove the last active Super Admin")

    if values.get("email"):
        email = values["email"].lower()
        if db.scalar(select(User.id).where(func.lower(User.email) == email, User.id != user.id)):
            raise HTTPException(status.HTTP_409_CONFLICT, "E-mail is already registered")
        user.email = email
    if values.get("role_id") is not None:
        if db.get(Role, values["role_id"]) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Role does not exist")
        user.role_id = values["role_id"]
    if values.get("full_name") is not None:
        user.full_name = values["full_name"].strip()
    if values.get("department") is not None:
        user.department = values["department"].strip()
    if values.get("is_active") is not None:
        user.is_active = values["is_active"]
    if values.get("password"):
        user.password_hash = hash_password(values["password"])

    detail = {k: v for k, v in values.items() if k != "password"}
    if "password" in values:
        detail["password_reset"] = True
    audit(db, "user.update", admin.id, "user", user.id, detail, client_ip(request))
    db.commit()
    db.expire(user)  # reload role relationship
    return db.get(User, user_id)


@router.delete("/users/{user_id}", response_model=Message)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permissions("users.manage")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "You cannot delete your own account")
    if user.role.name == ROLE_SUPER_ADMIN and _super_admin_count(db, exclude_user_id=user.id) == 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cannot remove the last active Super Admin")
    audit(db, "user.delete", admin.id, "user", user.id, {"username": user.username}, client_ip(request))
    db.delete(user)
    db.commit()
    return Message(message="User deleted")


# ---------------------------------------------------- roles/permissions ----

@router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(db: Session = Depends(get_db), _: User = Depends(require_permissions("roles.manage"))):
    return list(db.scalars(select(Permission).order_by(Permission.code)))


@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("users.manage", "roles.manage", any_of=True)),
):
    counts = dict(db.execute(select(User.role_id, func.count(User.id)).group_by(User.role_id)).all())
    roles = db.scalars(select(Role).order_by(Role.id)).unique()
    out = []
    for r in roles:
        item = RoleOut.model_validate(r)
        item.user_count = counts.get(r.id, 0)
        out.append(item)
    return out


@router.put("/roles/{role_id}/permissions", response_model=RoleOut)
def set_role_permissions(
    role_id: int,
    data: RolePermissionsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permissions("roles.manage")),
):
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(404, "Role not found")
    codes = set(data.permission_codes)
    if role.name == ROLE_SUPER_ADMIN:
        codes |= SUPER_ADMIN_LOCKED
    perms = list(db.scalars(select(Permission).where(Permission.code.in_(codes))))
    unknown = codes - {p.code for p in perms}
    if unknown:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown permissions: {sorted(unknown)}")
    before = sorted(p.code for p in role.permissions)
    role.permissions = perms
    audit(db, "role.permissions_update", admin.id, "role", role.id,
          {"role": role.name, "before": before, "after": sorted(codes)}, client_ip(request))
    db.commit()
    db.refresh(role)
    item = RoleOut.model_validate(role)
    item.user_count = db.scalar(select(func.count(User.id)).where(User.role_id == role.id)) or 0
    return item


# ---------------------------------------------------------- system logs ----

@router.get("/system-logs", response_model=Page[SystemLogOut])
def system_logs(
    action: str | None = Query(default=None, max_length=100),
    user_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("logs.view")),
):
    stmt = select(SystemLog)
    if action:
        stmt = stmt.where(SystemLog.action.ilike(f"%{action}%"))
    if user_id:
        stmt = stmt.where(SystemLog.user_id == user_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(SystemLog.created_at.desc(), SystemLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).unique()
    return Page(
        items=[SystemLogOut.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size, pages=max(1, math.ceil(total / page_size)),
    )


# ------------------------------------------------------------- settings ----

@router.get("/settings", response_model=list[SettingOut])
def list_settings(db: Session = Depends(get_db), _: User = Depends(require_permissions("settings.manage"))):
    return list(db.scalars(select(Setting).order_by(Setting.key)))


@router.put("/settings/{key}", response_model=SettingOut)
def update_setting(
    key: str,
    data: SettingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_permissions("settings.manage")),
):
    if key not in DEFAULT_SETTINGS:
        raise HTTPException(404, "Unknown setting")
    default_value = DEFAULT_SETTINGS[key][0]
    value = data.value
    # Keep the type consistent with the default.
    if isinstance(default_value, bool):
        if not isinstance(value, bool):
            raise HTTPException(422, "Value must be true or false")
    elif isinstance(default_value, int):
        if isinstance(value, bool) or not isinstance(value, int) or not (1 <= value <= 100):
            raise HTTPException(422, "Value must be an integer between 1 and 100")
    elif isinstance(default_value, str):
        if not isinstance(value, str) or not value.strip() or len(value) > 200:
            raise HTTPException(422, "Value must be a non-empty string (max 200 chars)")
        value = value.strip()
    row = db.get(Setting, key)
    if row is None:
        row = Setting(key=key, value=value, description=DEFAULT_SETTINGS[key][1])
        db.add(row)
        old = None
    else:
        old = row.value
        row.value = value
    audit(db, "setting.update", admin.id, "setting", key, {"from": old, "to": value}, client_ip(request))
    db.commit()
    db.refresh(row)
    return row
