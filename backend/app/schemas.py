from datetime import date, datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

T = TypeVar("T")

USERNAME_PATTERN = r"^[A-Za-z0-9_.]{3,50}$"


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class Message(BaseModel):
    message: str


# ------------------------------------------------------------- Users -------

class RoleBrief(ORM):
    id: int
    name: str
    display_name: str


class UserPublic(ORM):
    id: int
    username: str
    full_name: str
    department: str = ""
    bio: str = ""
    avatar_url: str | None = None


class UserMe(UserPublic):
    email: str
    role: RoleBrief
    permissions: list[str]
    created_at: datetime
    last_login_at: datetime | None = None


class RegisterIn(BaseModel):
    username: str = Field(pattern=USERNAME_PATTERN)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=120)


class LoginIn(BaseModel):
    username: str = Field(min_length=1, description="Username or e-mail")
    password: str = Field(min_length=1)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserMe


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    bio: str | None = Field(default=None, max_length=2000)
    department: str | None = Field(default=None, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=500)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


# ----------------------------------------------------------- Taxonomy ------

class CategoryIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=2000)


class CategoryOut(ORM):
    id: int
    name: str
    slug: str
    description: str = ""
    document_count: int = 0


class CategoryBrief(ORM):
    id: int
    name: str
    slug: str


class TagIn(BaseModel):
    name: str = Field(min_length=2, max_length=60)


class TagOut(ORM):
    id: int
    name: str
    slug: str
    document_count: int = 0


class TagBrief(ORM):
    id: int
    name: str
    slug: str


# ---------------------------------------------------------- Documents ------

DocStatus = Literal["draft", "published", "archived"]


def _clean_tags(v: list[str]) -> list[str]:
    seen: dict[str, str] = {}
    for t in v:
        t = t.strip()
        if t and t.lower() not in seen:
            seen[t.lower()] = t[:60]
    return list(seen.values())


class AuthorBrief(ORM):
    id: int
    username: str
    full_name: str


class DocumentListItem(ORM):
    id: int
    title: str
    slug: str
    summary: str
    doc_type: str
    department: str
    status: str
    category: CategoryBrief | None = None
    tags: list[TagBrief] = []
    author: AuthorBrief | None = None
    cover_image_url: str | None = None
    cover_image_alt: str | None = None
    views_count: int
    created_at: datetime
    published_at: datetime | None = None
    updated_at: datetime


class DocumentDetail(DocumentListItem):
    content: str
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    likes_count: int = 0
    rating_avg: float | None = None
    rating_count: int = 0
    comments_count: int = 0
    liked_by_me: bool = False
    my_rating: int | None = None


class DocumentIn(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    content: str = Field(min_length=10)
    summary: str = Field(default="", max_length=2000)
    doc_type: str = Field(default="Report", max_length=50)
    department: str = Field(default="", max_length=100)
    category_id: int | None = None
    tags: list[str] = Field(default_factory=list, description="Tag names; unknown tags are created")
    status: DocStatus = "draft"
    cover_image_url: str | None = Field(default=None, max_length=500)
    cover_image_alt: str | None = Field(default=None, max_length=300)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, v: list[str]) -> list[str]:
        return _clean_tags(v)


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=300)
    content: str | None = Field(default=None, min_length=10)
    summary: str | None = Field(default=None, max_length=2000)
    doc_type: str | None = Field(default=None, max_length=50)
    department: str | None = Field(default=None, max_length=100)
    category_id: int | None = None
    tags: list[str] | None = None
    status: DocStatus | None = None
    cover_image_url: str | None = Field(default=None, max_length=500)
    cover_image_alt: str | None = Field(default=None, max_length=300)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, v: list[str] | None) -> list[str] | None:
        return None if v is None else _clean_tags(v)


class StatusUpdate(BaseModel):
    status: DocStatus


class SEOUpdate(BaseModel):
    seo_title: str | None = Field(default=None, max_length=300)
    seo_description: str | None = Field(default=None, max_length=500)
    seo_keywords: str | None = Field(default=None, max_length=500)
    cover_image_alt: str | None = Field(default=None, max_length=300)


class SEOItem(ORM):
    id: int
    title: str
    slug: str
    status: str
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    cover_image_url: str | None = None
    cover_image_alt: str | None = None
    issues: list[str] = []


# --------------------------------------------------------- Engagement ------

class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    parent_id: int | None = None


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class CommentOut(ORM):
    id: int
    document_id: int
    parent_id: int | None = None
    body: str
    status: str
    created_at: datetime
    updated_at: datetime
    user: UserPublic
    mentions: list[str] = []


class CommentModerationOut(CommentOut):
    document_title: str
    report_count: int = 0


class CommentStatusUpdate(BaseModel):
    status: Literal["visible", "pending", "hidden", "spam"]


class RatingIn(BaseModel):
    score: int = Field(ge=1, le=5)


class EngagementOut(BaseModel):
    likes_count: int
    liked_by_me: bool
    rating_avg: float | None
    rating_count: int
    my_rating: int | None


class MentionOut(BaseModel):
    comment_id: int
    document_id: int
    document_title: str
    document_slug: str
    by: UserPublic
    body: str
    created_at: datetime
    is_read: bool


class ReportIn(BaseModel):
    target_type: Literal["comment", "document"]
    target_id: int
    reason: str = Field(min_length=3, max_length=1000)


class ReportOut(ORM):
    id: int
    target_type: str
    target_id: int
    reason: str
    status: str
    resolution_note: str
    created_at: datetime
    handled_at: datetime | None = None
    reporter: UserPublic | None = None
    handled_by: UserPublic | None = None
    target_preview: str | None = None
    target_link: str | None = None


class ReportHandle(BaseModel):
    status: Literal["resolved", "dismissed"]
    note: str = Field(default="", max_length=1000)
    hide_target: bool = Field(default=False, description="Also hide the reported comment / unpublish the document")


class SpamKeywordIn(BaseModel):
    keyword: str = Field(min_length=2, max_length=100)


class SpamKeywordOut(ORM):
    id: int
    keyword: str
    created_at: datetime


# -------------------------------------------------------- Logs/analytics ----

class SearchClickIn(BaseModel):
    query_string: str = Field(min_length=1, max_length=500)
    clicked_doc_id: int
    rank_position: int | None = Field(default=None, ge=1)
    session_id: str | None = Field(default=None, max_length=64)


class SearchLogOut(ORM):
    id: int
    user_id: int | None
    session_id: str | None
    query_string: str
    clicked_doc_id: int | None
    event_type: str
    rank_position: int | None
    results_count: int | None
    filters: dict | None
    timestamp: datetime


class SystemLogOut(ORM):
    id: int
    action: str
    entity_type: str | None
    entity_id: str | None
    detail: dict | None
    ip_address: str | None
    created_at: datetime
    user: UserPublic | None = None


# --------------------------------------------------------- Super admin -----

class AdminUserOut(ORM):
    id: int
    username: str
    email: str
    full_name: str
    department: str
    is_active: bool
    role: RoleBrief
    created_at: datetime
    last_login_at: datetime | None = None


class AdminUserCreate(BaseModel):
    username: str = Field(pattern=USERNAME_PATTERN)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=120)
    department: str = Field(default="", max_length=100)
    role_id: int


class AdminUserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=100)
    role_id: int | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class PermissionOut(ORM):
    id: int
    code: str
    description: str


class RoleOut(ORM):
    id: int
    name: str
    display_name: str
    description: str
    is_system: bool
    permissions: list[PermissionOut]
    user_count: int = 0


class RolePermissionsUpdate(BaseModel):
    permission_codes: list[str]


class SettingOut(ORM):
    key: str
    value: Any
    description: str
    updated_at: datetime | None = None


class SettingUpdate(BaseModel):
    value: Any


class DateRange(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
