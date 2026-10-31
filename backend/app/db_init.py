"""Create tables, the Phase-2 corpus view, and the RBAC / settings baseline.

Safe to run repeatedly (idempotent).
"""
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .database import Base, engine
from .models import Permission, Role, Setting
from .permissions import DEFAULT_ROLES, DEFAULT_SETTINGS, PERMISSIONS

SEARCH_CORPUS_VIEW = """
CREATE OR REPLACE VIEW search_corpus AS
SELECT
    d.id,
    d.title,
    d.content,
    d.summary,
    d.category_id,
    ARRAY(
        SELECT t.name FROM document_tags dt
        JOIN tags t ON t.id = dt.tag_id
        WHERE dt.document_id = d.id
        ORDER BY t.name
    ) AS tags,
    COALESCE(NULLIF(u.full_name, ''), u.username) AS author,
    d.created_at,
    d.views_count,
    d.status
FROM documents d
LEFT JOIN users u ON u.id = d.author_id
"""


def create_schema() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text(SEARCH_CORPUS_VIEW))


def ensure_rbac_and_settings(db: Session) -> None:
    perms: dict[str, Permission] = {p.code: p for p in db.scalars(select(Permission))}
    for code, desc in PERMISSIONS.items():
        if code not in perms:
            p = Permission(code=code, description=desc)
            db.add(p)
            perms[code] = p
        else:
            perms[code].description = desc
    db.flush()

    for name, (display, desc, codes) in DEFAULT_ROLES.items():
        role = db.scalar(select(Role).where(Role.name == name))
        if role is None:
            role = Role(name=name, display_name=display, description=desc, is_system=True)
            role.permissions = [perms[c] for c in codes]
            db.add(role)

    for key, (value, desc) in DEFAULT_SETTINGS.items():
        if db.get(Setting, key) is None:
            db.add(Setting(key=key, value=value, description=desc))

    db.commit()


def init_db() -> None:
    from .database import SessionLocal

    create_schema()
    with SessionLocal() as db:
        ensure_rbac_and_settings(db)


if __name__ == "__main__":
    init_db()
    print("Database schema and RBAC baseline are ready.")
