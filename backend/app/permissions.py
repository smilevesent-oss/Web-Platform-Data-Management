"""Permission catalogue and default role → permission mapping (RBAC)."""

# code -> description
PERMISSIONS: dict[str, str] = {
    # Super Admin
    "users.manage": "Create/update/deactivate user accounts and assign roles",
    "roles.manage": "Edit the permissions granted to each role",
    "logs.view": "View system audit logs",
    "settings.manage": "Configure global settings",
    # Content Manager
    "documents.read_all": "See documents in any status (draft / archived)",
    "documents.create": "Create documents",
    "documents.update": "Edit documents",
    "documents.delete": "Delete documents",
    "documents.publish": "Publish / unpublish / archive documents",
    "taxonomy.manage": "Manage categories and tags",
    # Moderator
    "comments.moderate": "Approve, hide, mark spam or delete any comment",
    "reports.manage": "Review and resolve user flags/reports",
    "spam.manage": "Manage the spam keyword blocklist",
    # Data & SEO Specialist
    "seo.manage": "Edit SEO metadata (title, description, keywords, image alt text)",
    "analytics.view": "View analytics dashboards and search/click logs",
    # Phase 2 search engine
    "search.manage": "Inspect the search index, tune ranking (BM25 k1/b) and run relevance evaluation",
}

ROLE_SUPER_ADMIN = "super_admin"
ROLE_CONTENT_MANAGER = "content_manager"
ROLE_MODERATOR = "moderator"
ROLE_SEO = "seo_specialist"
ROLE_USER = "user"

# name -> (display name, description, permission codes)
DEFAULT_ROLES: dict[str, tuple[str, str, list[str]]] = {
    ROLE_SUPER_ADMIN: (
        "Super Admin",
        "Manages user accounts/roles, permissions, system logs and global settings.",
        list(PERMISSIONS.keys()),
    ),
    ROLE_CONTENT_MANAGER: (
        "Content Manager",
        "Full CRUD on documents, publication status and taxonomy.",
        [
            "documents.read_all",
            "documents.create",
            "documents.update",
            "documents.delete",
            "documents.publish",
            "taxonomy.manage",
        ],
    ),
    ROLE_MODERATOR: (
        "Moderator",
        "Reviews user comments, handles flags/reports and spam control.",
        ["comments.moderate", "reports.manage", "spam.manage"],
    ),
    ROLE_SEO: (
        "Data & SEO Specialist",
        "Configures SEO metadata and monitors analytics dashboards.",
        ["documents.read_all", "seo.manage", "analytics.view", "search.manage"],
    ),
    ROLE_USER: (
        "Member",
        "Registered reader: can comment, rate, like, tag users and report content.",
        [],
    ),
}

# Super Admin always keeps these, even if someone edits the role, so the
# system can never be locked out.
SUPER_ADMIN_LOCKED = {"users.manage", "roles.manage"}

DEFAULT_SETTINGS: dict[str, tuple[object, str]] = {
    "site_name": ("Enterprise Document & Research Repository", "Name shown in the header"),
    "site_tagline": ("Policies, research and know-how in one place", "Subtitle shown on the home page"),
    "registration_open": (True, "Allow new users to self-register"),
    "comments_enabled": (True, "Allow members to comment on documents"),
    "comments_require_approval": (False, "New comments are held as 'pending' until a moderator approves them"),
    "default_page_size": (10, "Default number of documents per page"),
    # Phase 2 ranking (edited on the admin "Search engine" page)
    "search_algorithm": ("bm25", "Default ranking algorithm for keyword search: bm25, tfidf or like"),
    "search_bm25_k1": (1.2, "BM25 k1: term-frequency saturation (typical 0.9-2.0)"),
    "search_bm25_b": (0.75, "BM25 b: document-length normalisation (0 = none, 1 = full)"),
}

# Settings shown on the Search engine page rather than the generic settings page.
SEARCH_SETTINGS = ("search_algorithm", "search_bm25_k1", "search_bm25_b")
