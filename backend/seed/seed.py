"""Populate the database with realistic demo data.

Usage (from the backend/ folder):
    python -m seed.seed           # seed only if the database has no documents
    python -m seed.seed --reset   # drop everything and re-seed from scratch

Every value is deterministic (fixed random seed) so screenshots and tests are
reproducible.
"""
import argparse
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text

from app.database import Base, SessionLocal, engine
from app.db_init import create_schema, ensure_rbac_and_settings
from app.models import (
    Category,
    Comment,
    CommentMention,
    Document,
    DocumentView,
    Like,
    Rating,
    Report,
    Role,
    SearchLog,
    SpamKeyword,
    SystemLog,
    Tag,
    User,
)
from app.security import hash_password
from app.utils import slugify

from .docs_part1 import DOCS as P1
from .docs_part2 import DOCS as P2
from .docs_part3 import DOCS as P3
from .docs_part4 import DOCS as P4

ALL_DOCS = P1 + P2 + P3 + P4
DEMO_PASSWORD = "Password123!"
NOW = datetime.now(timezone.utc).replace(microsecond=0)
rng = random.Random(2026)

CATEGORIES = {
    "hr": ("Human Resources", "Employment policies, benefits, leave and people processes."),
    "security": ("Information Security", "Security policies, standards and incident response."),
    "engineering": ("Engineering & Architecture", "Architecture decisions, technical standards and runbooks."),
    "operations": ("Operations & SOPs", "Standard operating procedures, continuity and facilities."),
    "finance": ("Finance & Procurement", "Budgeting, purchasing, payments and financial controls."),
    "legal": ("Legal & Compliance", "Regulatory compliance, contracts, privacy and ethics."),
    "research": ("Research & Market Insights", "Market research, analytics studies and survey reports."),
    "product": ("Product & Customer Experience", "Product requirements, design standards and customer playbooks."),
}

# username, full name, role, department, bio
USERS = [
    ("superadmin", "Tran Thi Linh", "super_admin", "IT Services", "Platform owner and system administrator."),
    ("content.manager", "Nguyen Minh Anh", "content_manager", "Knowledge Management",
     "Leads the knowledge management team and curates the repository."),
    ("editor.hoang", "Hoang Gia Huy", "content_manager", "Knowledge Management",
     "Content editor focused on policies and procedures."),
    ("moderator", "Pham Thu Ha", "moderator", "Customer Operations", "Keeps discussions useful and respectful."),
    ("seo.analyst", "Le Quoc Bao", "seo_specialist", "Data & Analytics",
     "Search, findability and analytics specialist."),
    ("mai.nguyen", "Nguyen Thanh Mai", "user", "People & Culture", "HR business partner."),
    ("john.carter", "John Carter", "user", "Engineering", "Staff engineer, platform team."),
    ("david.kim", "David Kim", "user", "Finance", "Financial controller."),
    ("tuan.vo", "Vo Anh Tuan", "user", "Information Security", "Security engineer."),
    ("sarah.lee", "Sarah Lee", "user", "Product Management", "Senior product manager for internal tools."),
    ("khanh.dang", "Dang Bao Khanh", "user", "Legal", "Corporate counsel."),
    ("emily.chen", "Emily Chen", "user", "Strategy & Insights", "Market research analyst."),
    ("quang.pham", "Pham Minh Quang", "user", "Customer Operations", "Support team lead."),
]

# Which users author documents of each category (first = main author).
AUTHORS_BY_CATEGORY = {
    "hr": ["mai.nguyen", "content.manager"],
    "security": ["tuan.vo", "editor.hoang"],
    "engineering": ["john.carter", "editor.hoang"],
    "operations": ["quang.pham", "content.manager"],
    "finance": ["david.kim", "content.manager"],
    "legal": ["khanh.dang", "editor.hoang"],
    "research": ["emily.chen", "seo.analyst"],
    "product": ["sarah.lee", "content.manager"],
}

# Documents left as draft / archived (titles) to demonstrate publication status.
DRAFTS = {
    "FY2027 Budget Planning Guidelines",
    "Technical Debt Register: Q3 2026 Review",
    "Mobile App Release Process",
    "Sustainability Report: Scope 1 and 2 Emissions Baseline",
}
ARCHIVED = {"Corporate Card Usage Policy", "Office Health and Safety Induction"}

COMMENT_POOL = [
    "Thanks for the clear write-up. Is there a version of this for contractors as well?",
    "Could we add a short example for the most common case? It would make onboarding easier.",
    "We followed this last quarter and it worked well. One tip: involve finance earlier than step three.",
    "The section on approvals is really helpful. @{mention} you asked about this last week.",
    "Is this still current after the reorganisation in September? The owner listed has moved teams.",
    "Great summary. I shared it with my team during our weekly meeting.",
    "Small correction: the threshold mentioned in paragraph three changed at the start of the year.",
    "This answers the question we get most often on the support channel, thank you!",
    "@{mention} can you confirm whether this applies to the regional office too?",
    "It would help to link the related template directly from this page.",
    "Very practical. A checklist version we can print would be great.",
    "We are piloting this in our department; I will share lessons learned here in a month.",
]
REPLY_POOL = [
    "Good point, we will update the document in the next review cycle.",
    "Yes, it applies company-wide unless local law requires otherwise.",
    "Thanks for flagging — I have asked the owner to confirm.",
    "Agreed, I will add a template link this week.",
]

SEARCH_QUERIES = [
    "annual leave", "carry over leave", "remote work", "hybrid policy", "password", "mfa",
    "phishing", "incident response", "data classification", "personal data", "gdpr", "dpia",
    "procurement threshold", "invoice", "expense receipt", "travel booking", "budget",
    "capex", "bribery", "gifts hospitality", "whistleblowing", "sanctions screening",
    "open source license", "contract review", "api guidelines", "code review", "postgresql migration",
    "kubernetes", "observability", "postmortem", "checkout latency", "business continuity",
    "laptop refresh", "change freeze", "retention schedule", "churn", "nps", "bm25", "tf-idf",
    "search relevance", "e-commerce logistics", "payment preferences vietnam", "accessibility",
    "design system", "onboarding", "performance review", "parental leave", "engagement survey",
    "sla enterprise", "knowledge base", "generative ai", "vendor security",
    # queries that should return nothing (useful for zero-result analytics)
    "parking reimbursement", "vpn setup mac", "canteen menu", "stock options vesting",
]

SPAM_KEYWORDS = ["casino", "crypto giveaway", "buy followers", "free money", "click here to win"]


def reset_database() -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP VIEW IF EXISTS search_corpus"))
    Base.metadata.drop_all(bind=engine)


def matches(doc: dict, query: str) -> bool:
    blob = f"{doc['title']} {doc['summary']} {doc['content']}".lower()
    return all(w in blob for w in query.lower().split())


def run(reset: bool) -> None:
    if reset:
        reset_database()
    create_schema()
    db = SessionLocal()
    try:
        ensure_rbac_and_settings(db)
        if db.scalar(select(func.count(Document.id))):
            print("Database already contains documents; use --reset to re-seed.")
            return

        roles = {r.name: r for r in db.scalars(select(Role))}

        # ---- users -------------------------------------------------------
        pw_hash = hash_password(DEMO_PASSWORD)  # same demo password for all accounts
        users: dict[str, User] = {}
        for i, (username, name, role, dept, bio) in enumerate(USERS):
            u = User(
                username=username,
                email=f"{username.replace('.', '_')}@meridian.example.com",
                password_hash=pw_hash,
                full_name=name,
                department=dept,
                bio=bio,
                role_id=roles[role].id,
                created_at=NOW - timedelta(days=420 - i * 7),
            )
            db.add(u)
            users[username] = u
        db.flush()
        members = [u for u in users.values()]

        # ---- taxonomy ----------------------------------------------------
        cats: dict[str, Category] = {}
        for key, (name, desc) in CATEGORIES.items():
            c = Category(name=name, slug=slugify(name), description=desc, created_at=NOW - timedelta(days=430))
            db.add(c)
            cats[key] = c
        tags: dict[str, Tag] = {}
        for d in ALL_DOCS:
            for t in d["tags"]:
                if t not in tags:
                    tags[t] = Tag(name=t, slug=slugify(t))
                    db.add(tags[t])
        db.flush()

        # ---- documents ---------------------------------------------------
        # Spread creation dates over ~14 months; newest documents first in list order shuffled.
        order = list(range(len(ALL_DOCS)))
        rng.shuffle(order)
        documents: list[Document] = []
        for rank, idx in enumerate(order):
            d = ALL_DOCS[idx]
            created = NOW - timedelta(days=5 + rank * 7, hours=rng.randint(0, 20), minutes=rng.randint(0, 59))
            status = "draft" if d["title"] in DRAFTS else "archived" if d["title"] in ARCHIVED else "published"
            author_pool = AUTHORS_BY_CATEGORY[d["category"]]
            author = users[author_pool[0] if rng.random() < 0.7 else author_pool[1]]
            slug = slugify(d["title"])
            has_image = rng.random() < 0.85
            seo_done = rng.random() < 0.7
            doc = Document(
                title=d["title"],
                slug=slug,
                summary=d["summary"],
                content=d["content"].strip(),
                doc_type=d["doc_type"],
                department=d["department"],
                category_id=cats[d["category"]].id,
                author_id=author.id,
                status=status,
                cover_image_url=f"https://picsum.photos/seed/{slug[:40]}/1200/600" if has_image else None,
                cover_image_alt=(f"Illustration for {d['title']}" if has_image and seo_done else None),
                seo_title=(d["title"][:57] + "…" if len(d["title"]) > 60 else d["title"]) if seo_done else None,
                seo_description=d["summary"][:157] + ("…" if len(d["summary"]) > 157 else "") if seo_done else None,
                seo_keywords=", ".join(t.lower() for t in d["tags"]) if seo_done else None,
                created_at=created,
                updated_at=created + timedelta(days=rng.randint(0, 3)),
                published_at=created if status != "draft" else None,
                views_count=0,
            )
            doc.tags = [tags[t] for t in d["tags"]]
            db.add(doc)
            documents.append(doc)
        db.flush()
        published = [d for d in documents if d.status == "published"]

        # ---- views (raw events for the last 45 days + historical total) --
        for doc in published:
            popularity = rng.choice([1, 1, 2, 3, 5])
            recent = 0
            for day in range(45):
                for _ in range(rng.randint(0, popularity * 2)):
                    ts = NOW - timedelta(days=day, hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
                    if ts < doc.created_at:
                        continue
                    db.add(DocumentView(document_id=doc.id, user_id=rng.choice(members).id
                                        if rng.random() < 0.6 else None, viewed_at=ts))
                    recent += 1
            doc.views_count = recent + rng.randint(40, 260) * popularity

        # ---- likes & ratings ---------------------------------------------
        for doc in published:
            for u in rng.sample(members, rng.randint(0, 7)):
                db.add(Like(user_id=u.id, document_id=doc.id,
                            created_at=doc.created_at + timedelta(days=rng.randint(0, 20))))
            for u in rng.sample(members, rng.randint(0, 6)):
                db.add(Rating(user_id=u.id, document_id=doc.id, score=rng.choices([3, 4, 5, 2], [3, 5, 4, 1])[0],
                              created_at=doc.created_at + timedelta(days=rng.randint(0, 20))))

        # ---- comments with mentions and replies --------------------------
        all_comments: list[Comment] = []
        for doc in published:
            for _ in range(rng.randint(0, 3)):
                author = rng.choice(members)
                mention = rng.choice([u for u in members if u.id != author.id])
                body = rng.choice(COMMENT_POOL).format(mention=mention.username)
                c = Comment(document_id=doc.id, user_id=author.id, body=body, status="visible",
                            created_at=doc.created_at + timedelta(days=rng.randint(1, 30), hours=rng.randint(0, 12)))
                if f"@{mention.username}" in body:
                    c.mentions.append(CommentMention(user_id=mention.id, is_read=rng.random() < 0.5))
                db.add(c)
                db.flush()
                all_comments.append(c)
                if rng.random() < 0.35:
                    replier = users[AUTHORS_BY_CATEGORY[next(k for k, v in cats.items()
                                                             if v.id == doc.category_id)][0]]
                    r = Comment(document_id=doc.id, user_id=replier.id, parent_id=c.id,
                                body=rng.choice(REPLY_POOL), status="visible",
                                created_at=c.created_at + timedelta(hours=rng.randint(2, 30)))
                    db.add(r)
                    all_comments.append(r)
        db.flush()

        # Moderation queue examples: spam, pending, hidden + open reports.
        target = published[0]
        spam = Comment(document_id=target.id, user_id=users["david.kim"].id, status="spam",
                       body="Win big at our online casino, click here to win free money today!!!",
                       created_at=NOW - timedelta(days=2))
        pending = Comment(document_id=published[1].id, user_id=users["quang.pham"].id, status="pending",
                          body="I think the response targets in this document are unrealistic for weekend shifts.",
                          created_at=NOW - timedelta(days=1))
        rude = Comment(document_id=published[2].id, user_id=users["john.carter"].id, status="visible",
                       body="Whoever wrote this clearly never did the job themselves. Useless.",
                       created_at=NOW - timedelta(days=3))
        db.add_all([spam, pending, rude])
        db.flush()
        db.add_all([
            Report(reporter_id=users["sarah.lee"].id, target_type="comment", target_id=rude.id,
                   reason="Personal attack on the author; not constructive.", created_at=NOW - timedelta(days=2)),
            Report(reporter_id=users["emily.chen"].id, target_type="comment", target_id=rude.id,
                   reason="Disrespectful tone.", created_at=NOW - timedelta(days=2, hours=3)),
            Report(reporter_id=users["mai.nguyen"].id, target_type="document", target_id=published[3].id,
                   reason="The approval thresholds in this document look outdated.",
                   created_at=NOW - timedelta(days=4)),
            Report(reporter_id=users["tuan.vo"].id, target_type="comment", target_id=all_comments[0].id,
                   reason="Duplicate of another comment.", status="dismissed",
                   resolution_note="Not a duplicate; question is valid.", handled_by_id=users["moderator"].id,
                   created_at=NOW - timedelta(days=9), handled_at=NOW - timedelta(days=8)),
        ])
        for kw in SPAM_KEYWORDS:
            db.add(SpamKeyword(keyword=kw))

        # ---- search & click logs (Phase 2 data) --------------------------
        pub_sorted = sorted(published, key=lambda d: (d.created_at, d.id), reverse=True)  # = API "latest" order
        raw = {d["title"]: d for d in ALL_DOCS}
        for i in range(420):
            q = rng.choice(SEARCH_QUERIES)
            user = rng.choice(members) if rng.random() < 0.75 else None
            session = f"seed-{rng.randrange(16**8):08x}"
            ts = NOW - timedelta(days=rng.randint(0, 29), hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
            results = [d for d in pub_sorted if matches(raw[d.title], q)]
            db.add(SearchLog(user_id=user.id if user else None, session_id=session, query_string=q,
                             event_type="search", results_count=len(results), filters={"sort": "latest"},
                             timestamp=ts))
            if results and rng.random() < 0.72:
                top = results[:10]
                weights = [1 / (k + 1) for k in range(len(top))]  # position bias
                pos = rng.choices(range(len(top)), weights)[0]
                db.add(SearchLog(user_id=user.id if user else None, session_id=session, query_string=q,
                                 clicked_doc_id=top[pos].id, event_type="click", rank_position=pos + 1,
                                 timestamp=ts + timedelta(seconds=rng.randint(3, 40))))

        # ---- a few audit entries so the log page is not empty ------------
        for action, who, days in [("auth.login", "superadmin", 1), ("document.publish", "content.manager", 3),
                                  ("seo.update", "seo.analyst", 2), ("report.handle", "moderator", 8)]:
            db.add(SystemLog(user_id=users[who].id, action=action, detail={"seed": True},
                             created_at=NOW - timedelta(days=days)))

        db.commit()
        print(f"Seeded {len(users)} users, {len(cats)} categories, {len(tags)} tags, "
              f"{len(documents)} documents ({len(published)} published).")
        print(f"Demo password for every account: {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="drop all tables before seeding")
    run(parser.parse_args().reset)
