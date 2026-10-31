from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import client_ip, require_permissions
from ..models import Category, Document, Tag, User, document_tags
from ..schemas import CategoryIn, CategoryOut, Message, TagIn, TagOut
from ..utils import audit, unique_slug

router = APIRouter(tags=["taxonomy"])


def _category_rows(db: Session, published_only: bool) -> list[CategoryOut]:
    cond = Document.category_id == Category.id
    if published_only:
        cond = cond & (Document.status == "published")
    count = select(func.count(Document.id)).where(cond).correlate(Category).scalar_subquery()
    rows = db.execute(select(Category, count).order_by(Category.name)).all()
    return [
        CategoryOut(id=c.id, name=c.name, slug=c.slug, description=c.description, document_count=n)
        for c, n in rows
    ]


def _tag_rows(db: Session, published_only: bool, limit: int | None = None) -> list[TagOut]:
    join_cond = (Document.id == document_tags.c.document_id)
    if published_only:
        join_cond = join_cond & (Document.status == "published")
    count = (
        select(func.count(document_tags.c.document_id))
        .join(Document, join_cond)
        .where(document_tags.c.tag_id == Tag.id)
        .correlate(Tag)
        .scalar_subquery()
    )
    stmt = select(Tag, count.label("n")).order_by(count.desc(), Tag.name)
    if limit:
        stmt = stmt.limit(limit)
    return [TagOut(id=t.id, name=t.name, slug=t.slug, document_count=n) for t, n in db.execute(stmt).all()]


# ----------------------------------------------------------- public --------

@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return _category_rows(db, published_only=True)


@router.get("/tags", response_model=list[TagOut])
def list_tags(limit: int | None = Query(default=None, ge=1, le=500), db: Session = Depends(get_db)):
    return [t for t in _tag_rows(db, published_only=True, limit=limit) if t.document_count > 0]


# ------------------------------------------------------------ admin --------

@router.get("/admin/categories", response_model=list[CategoryOut])
def admin_list_categories(db: Session = Depends(get_db), _: User = Depends(require_permissions("taxonomy.manage"))):
    return _category_rows(db, published_only=False)


@router.post("/admin/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("taxonomy.manage")),
):
    name = data.name.strip()
    if db.scalar(select(Category.id).where(func.lower(Category.name) == name.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Category already exists")
    cat = Category(name=name, slug=unique_slug(db, Category, name), description=data.description.strip())
    db.add(cat)
    db.flush()
    audit(db, "category.create", user.id, "category", cat.id, {"name": name}, client_ip(request))
    db.commit()
    return CategoryOut(id=cat.id, name=cat.name, slug=cat.slug, description=cat.description, document_count=0)


@router.put("/admin/categories/{cat_id}", response_model=CategoryOut)
def update_category(
    cat_id: int,
    data: CategoryIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("taxonomy.manage")),
):
    cat = db.get(Category, cat_id)
    if cat is None:
        raise HTTPException(404, "Category not found")
    name = data.name.strip()
    clash = db.scalar(select(Category.id).where(func.lower(Category.name) == name.lower(), Category.id != cat_id))
    if clash:
        raise HTTPException(status.HTTP_409_CONFLICT, "Category already exists")
    if name != cat.name:
        cat.name = name
        cat.slug = unique_slug(db, Category, name, exclude_id=cat.id)
    cat.description = data.description.strip()
    audit(db, "category.update", user.id, "category", cat.id, {"name": name}, client_ip(request))
    db.commit()
    return next(c for c in _category_rows(db, False) if c.id == cat_id)


@router.delete("/admin/categories/{cat_id}", response_model=Message)
def delete_category(
    cat_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("taxonomy.manage")),
):
    cat = db.get(Category, cat_id)
    if cat is None:
        raise HTTPException(404, "Category not found")
    audit(db, "category.delete", user.id, "category", cat.id, {"name": cat.name}, client_ip(request))
    db.delete(cat)  # documents keep existing; their category_id becomes NULL
    db.commit()
    return Message(message="Category deleted")


@router.get("/admin/tags", response_model=list[TagOut])
def admin_list_tags(db: Session = Depends(get_db), _: User = Depends(require_permissions("taxonomy.manage"))):
    return _tag_rows(db, published_only=False)


@router.post("/admin/tags", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(
    data: TagIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("taxonomy.manage")),
):
    name = data.name.strip()
    if db.scalar(select(Tag.id).where(func.lower(Tag.name) == name.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Tag already exists")
    tag = Tag(name=name, slug=unique_slug(db, Tag, name))
    db.add(tag)
    db.flush()
    audit(db, "tag.create", user.id, "tag", tag.id, {"name": name}, client_ip(request))
    db.commit()
    return TagOut(id=tag.id, name=tag.name, slug=tag.slug, document_count=0)


@router.put("/admin/tags/{tag_id}", response_model=TagOut)
def update_tag(
    tag_id: int,
    data: TagIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("taxonomy.manage")),
):
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(404, "Tag not found")
    name = data.name.strip()
    if db.scalar(select(Tag.id).where(func.lower(Tag.name) == name.lower(), Tag.id != tag_id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Tag already exists")
    if name != tag.name:
        tag.name = name
        tag.slug = unique_slug(db, Tag, name, exclude_id=tag.id)
    audit(db, "tag.update", user.id, "tag", tag.id, {"name": name}, client_ip(request))
    db.commit()
    return next(t for t in _tag_rows(db, False) if t.id == tag_id)


@router.delete("/admin/tags/{tag_id}", response_model=Message)
def delete_tag(
    tag_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permissions("taxonomy.manage")),
):
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(404, "Tag not found")
    audit(db, "tag.delete", user.id, "tag", tag.id, {"name": tag.name}, client_ip(request))
    db.delete(tag)
    db.commit()
    return Message(message="Tag deleted")
