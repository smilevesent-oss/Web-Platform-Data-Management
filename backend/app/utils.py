import re
import unicodedata
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Setting, SystemLog
from .permissions import DEFAULT_SETTINGS


def slugify(text: str, max_len: int = 300) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return (text[:max_len].strip("-")) or "item"


def unique_slug(db: Session, model: Any, base: str, exclude_id: int | None = None) -> str:
    slug = slugify(base)
    candidate, n = slug, 2
    while True:
        stmt = select(model.id).where(model.slug == candidate)
        existing = db.execute(stmt).scalar_one_or_none()
        if existing is None or existing == exclude_id:
            return candidate
        candidate = f"{slug}-{n}"
        n += 1


def make_summary(content: str, length: int = 240) -> str:
    text = re.sub(r"\s+", " ", content).strip()
    if len(text) <= length:
        return text
    cut = text[:length].rsplit(" ", 1)[0]
    return cut.rstrip(",.;:") + "…"


MENTION_RE = re.compile(r"(?<![\w@])@([A-Za-z0-9_.]{3,50})")


def extract_mentions(text: str) -> set[str]:
    return {m.rstrip(".") for m in MENTION_RE.findall(text)}


def get_setting(db: Session, key: str) -> Any:
    row = db.get(Setting, key)
    if row is not None:
        return row.value
    default = DEFAULT_SETTINGS.get(key)
    return default[0] if default else None


def audit(
    db: Session,
    action: str,
    user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: Any = None,
    detail: dict | None = None,
    ip: str | None = None,
) -> None:
    """Append an audit entry. Caller is responsible for committing."""
    db.add(
        SystemLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            detail=detail,
            ip_address=ip,
        )
    )
