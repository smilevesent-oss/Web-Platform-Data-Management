from sqlalchemy import text

from app.database import engine

ADMIN, CM, MOD, SEO, MEMBER, MEMBER2 = (
    "superadmin", "content.manager", "moderator", "seo.analyst", "sarah.lee", "john.carter",
)


# ----------------------------------------------------------- public ---------

def test_health_and_site(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    site = client.get("/api/site").json()
    assert site["site_name"] and site["registration_open"] is True


def test_home_listing_is_paginated_and_only_published(client):
    r = client.get("/api/documents", params={"page": 1, "page_size": 10})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 55 and body["pages"] == 6 and len(body["items"]) == 10
    assert all(d["status"] == "published" for d in body["items"])
    dates = [d["created_at"] for d in body["items"]]
    assert dates == sorted(dates, reverse=True)  # latest first
    assert body["items"][0]["summary"] and body["items"][0]["author"]["full_name"]
    page6 = client.get("/api/documents", params={"page": 6, "page_size": 10}).json()
    assert len(page6["items"]) == 5


def test_detail_increments_views_and_has_metadata(client):
    item = client.get("/api/documents").json()["items"][0]
    first = client.get(f"/api/documents/{item['slug']}").json()
    second = client.get(f"/api/documents/{item['id']}").json()
    assert second["views_count"] == first["views_count"] + 1
    for key in ("content", "author", "created_at", "category", "tags", "cover_image_url"):
        assert key in second
    assert len(second["content"]) > 500


def test_draft_hidden_from_public_but_visible_to_content_manager(client, auth):
    drafts = client.get("/api/admin/documents", params={"status": "draft"}, headers=auth(CM)).json()
    assert drafts["total"] == 4
    slug = drafts["items"][0]["slug"]
    assert client.get(f"/api/documents/{slug}").status_code == 404
    assert client.get(f"/api/documents/{slug}", headers=auth(CM)).status_code == 200


def test_keyword_search_filters_and_logging(client):
    with engine.connect() as c:
        before = c.execute(text("select count(*) from search_logs where event_type='search'")).scalar()
    r = client.get("/api/documents", params={"q": "password", "session_id": "test-session"}).json()
    titles = [d["title"] for d in r["items"]]
    assert "Password and Multi-Factor Authentication Standard" in titles
    # multi-word AND semantics + filter by category
    r2 = client.get("/api/documents", params={"q": "leave carry", "category": "human-resources"}).json()
    assert r2["total"] >= 1 and all(d["category"]["slug"] == "human-resources" for d in r2["items"])
    # LIKE wildcards are escaped
    assert client.get("/api/documents", params={"q": "%"}).json()["total"] == 0
    with engine.connect() as c:
        after = c.execute(text("select count(*) from search_logs where event_type='search'")).scalar()
        row = c.execute(text("select query_string, results_count, session_id from search_logs "
                             "where session_id='test-session'")).one()
    assert after == before + 3
    assert row.query_string == "password" and row.results_count == r["total"]


def test_tag_and_date_filters(client):
    tags = client.get("/api/tags").json()
    sec = next(t for t in tags if t["slug"] == "security")
    r = client.get("/api/documents", params={"tag": "security", "page_size": 50}).json()
    assert r["total"] == sec["document_count"]
    assert all(any(t["slug"] == "security" for t in d["tags"]) for d in r["items"])
    everything = client.get("/api/documents", params={"page_size": 50}).json()["items"]
    pivot = everything[10]["created_at"][:10]
    r = client.get("/api/documents", params={"date_from": pivot, "page_size": 50}).json()
    assert all(d["created_at"][:10] >= pivot for d in r["items"])
    r = client.get("/api/documents", params={"date_to": pivot, "page_size": 50}).json()
    assert all(d["created_at"][:10] <= pivot for d in r["items"])


def test_click_logging(client, auth):
    doc = client.get("/api/documents", params={"q": "bm25"}).json()["items"][0]
    r = client.post("/api/logs/click", json={"query_string": "bm25", "clicked_doc_id": doc["id"],
                                            "rank_position": 1, "session_id": "s1"}, headers=auth(MEMBER))
    assert r.status_code == 201
    with engine.connect() as c:
        row = c.execute(text("select user_id, clicked_doc_id, rank_position from search_logs "
                             "where event_type='click' and session_id='s1'")).one()
    assert row.clicked_doc_id == doc["id"] and row.rank_position == 1 and row.user_id is not None


def test_search_corpus_view_has_phase2_fields(client):
    with engine.connect() as c:
        cols = [r[0] for r in c.execute(text(
            "select column_name from information_schema.columns where table_name='search_corpus'"))]
    for f in ("id", "title", "content", "summary", "category_id", "tags", "author", "created_at", "views_count"):
        assert f in cols


# ------------------------------------------------------------ auth ----------

def test_register_login_profile_flow(client):
    r = client.post("/api/auth/register", json={"username": "new_reader", "email": "New@Example.com",
                                                "password": "s3cretpass", "full_name": "New Reader"})
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    assert r.json()["user"]["role"]["name"] == "user"
    dup = client.post("/api/auth/register", json={"username": "NEW_READER", "email": "x@example.com",
                                                  "password": "s3cretpass"})
    assert dup.status_code == 409
    bad = client.post("/api/auth/login", json={"username": "new_reader", "password": "wrong"})
    assert bad.status_code == 401
    ok = client.post("/api/auth/login", json={"username": "new@example.com", "password": "s3cretpass"})
    assert ok.status_code == 200
    h = {"Authorization": f"Bearer {token}"}
    me = client.put("/api/auth/me", json={"bio": "Hello", "department": "QA"}, headers=h).json()
    assert me["bio"] == "Hello" and me["department"] == "QA"
    assert client.post("/api/auth/change-password", json={"current_password": "nope", "new_password": "another123"},
                       headers=h).status_code == 400
    assert client.post("/api/auth/change-password", json={"current_password": "s3cretpass",
                                                          "new_password": "another123"}, headers=h).status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_validation_errors(client):
    r = client.post("/api/auth/register", json={"username": "a", "email": "nope", "password": "short"})
    assert r.status_code == 422


# ------------------------------------------------------------ RBAC ----------

def test_rbac_matrix(client, auth):
    cases = {
        "/api/admin/users": {ADMIN: 200, CM: 403, MOD: 403, SEO: 403, MEMBER: 403},
        "/api/admin/system-logs": {ADMIN: 200, CM: 403, MOD: 403, SEO: 403, MEMBER: 403},
        "/api/admin/settings": {ADMIN: 200, CM: 403, MOD: 403, SEO: 403, MEMBER: 403},
        "/api/admin/documents": {ADMIN: 200, CM: 200, MOD: 403, SEO: 200, MEMBER: 403},
        "/api/admin/categories": {ADMIN: 200, CM: 200, MOD: 403, SEO: 403, MEMBER: 403},
        "/api/moderation/comments": {ADMIN: 200, CM: 403, MOD: 200, SEO: 403, MEMBER: 403},
        "/api/moderation/reports": {ADMIN: 200, CM: 403, MOD: 200, SEO: 403, MEMBER: 403},
        "/api/seo/documents": {ADMIN: 200, CM: 403, MOD: 403, SEO: 200, MEMBER: 403},
        "/api/analytics/summary": {ADMIN: 200, CM: 403, MOD: 403, SEO: 200, MEMBER: 403},
    }
    for url, expected in cases.items():
        assert client.get(url).status_code == 401, url
        for user, code in expected.items():
            assert client.get(url, headers=auth(user)).status_code == code, (url, user)


# ---------------------------------------------------- content manager -------

def test_document_crud_and_publish(client, auth):
    cats = client.get("/api/admin/categories", headers=auth(CM)).json()
    payload = {"title": "Meeting Room Booking Guidelines", "content": "Rooms are booked through the calendar. "
               "Bookings longer than four hours need facilities approval.", "category_id": cats[0]["id"],
               "tags": ["Facilities", "facilities", "New Tag X"], "doc_type": "Guide", "status": "draft"}
    r = client.post("/api/admin/documents", json=payload, headers=auth(CM))
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["slug"] == "meeting-room-booking-guidelines" and doc["summary"]
    assert sorted(t["name"] for t in doc["tags"]) == ["Facilities", "New Tag X"]
    assert client.get(f"/api/documents/{doc['slug']}").status_code == 404

    # same title -> unique slug
    r2 = client.post("/api/admin/documents", json=payload, headers=auth(CM)).json()
    assert r2["slug"] == "meeting-room-booking-guidelines-2"

    up = client.put(f"/api/admin/documents/{doc['id']}", json={"summary": "Updated", "category_id": None},
                    headers=auth(CM)).json()
    assert up["summary"] == "Updated" and up["category"] is None

    pub = client.patch(f"/api/admin/documents/{doc['id']}/status", json={"status": "published"}, headers=auth(CM))
    assert pub.status_code == 200 and pub.json()["published_at"]
    assert client.get(f"/api/documents/{doc['slug']}").status_code == 200

    # SEO specialist can read drafts but cannot edit or publish
    assert client.put(f"/api/admin/documents/{doc['id']}", json={"summary": "x"}, headers=auth(SEO)).status_code == 403
    assert client.patch(f"/api/admin/documents/{doc['id']}/status", json={"status": "draft"},
                        headers=auth(SEO)).status_code == 403

    for d in (doc, r2):
        assert client.delete(f"/api/admin/documents/{d['id']}", headers=auth(CM)).status_code == 200
    assert client.get(f"/api/admin/documents/{doc['id']}", headers=auth(CM)).status_code == 404


def test_taxonomy_crud(client, auth):
    h = auth(CM)
    c = client.post("/api/admin/categories", json={"name": "Temporary Category"}, headers=h)
    assert c.status_code == 201
    assert client.post("/api/admin/categories", json={"name": "temporary category"}, headers=h).status_code == 409
    cid = c.json()["id"]
    assert client.put(f"/api/admin/categories/{cid}", json={"name": "Temp Renamed", "description": "d"},
                      headers=h).json()["slug"] == "temp-renamed"
    assert client.delete(f"/api/admin/categories/{cid}", headers=h).status_code == 200
    t = client.post("/api/admin/tags", json={"name": "Temporary Tag"}, headers=h)
    assert t.status_code == 201
    assert client.delete(f"/api/admin/tags/{t.json()['id']}", headers=h).status_code == 200


# --------------------------------------------------------- engagement -------

def test_comments_mentions_likes_ratings_reports(client, auth):
    doc = client.get("/api/documents").json()["items"][0]
    h = auth(MEMBER)
    c = client.post(f"/api/documents/{doc['id']}/comments", json={"body": "Useful! @john.carter please review."},
                    headers=h)
    assert c.status_code == 201
    assert c.json()["mentions"] == ["john.carter"] and c.json()["status"] == "visible"
    mentions = client.get("/api/me/mentions", headers=auth(MEMBER2)).json()
    assert any(m["comment_id"] == c.json()["id"] for m in mentions)

    reply = client.post(f"/api/documents/{doc['id']}/comments", json={"body": "Will do", "parent_id": c.json()["id"]},
                        headers=auth(MEMBER2))
    assert reply.status_code == 201 and reply.json()["parent_id"] == c.json()["id"]
    assert client.post(f"/api/documents/{doc['id']}/comments", json={"body": "x"}).status_code == 401

    # editing someone else's comment is not allowed
    assert client.put(f"/api/comments/{c.json()['id']}", json={"body": "hack"}, headers=auth(MEMBER2)).status_code == 404

    e = client.post(f"/api/documents/{doc['id']}/like", headers=h).json()
    e2 = client.post(f"/api/documents/{doc['id']}/like", headers=h).json()
    assert e["liked_by_me"] != e2["liked_by_me"] and abs(e["likes_count"] - e2["likes_count"]) == 1
    rt = client.put(f"/api/documents/{doc['id']}/rating", json={"score": 5}, headers=h).json()
    assert rt["my_rating"] == 5
    assert client.put(f"/api/documents/{doc['id']}/rating", json={"score": 6}, headers=h).status_code == 422

    rep = client.post("/api/reports", json={"target_type": "comment", "target_id": reply.json()["id"],
                                           "reason": "Off topic"}, headers=h)
    assert rep.status_code == 201
    assert client.delete(f"/api/comments/{c.json()['id']}", headers=h).status_code == 200


def test_spam_keyword_auto_flags(client, auth):
    doc = client.get("/api/documents").json()["items"][1]
    r = client.post(f"/api/documents/{doc['id']}/comments", json={"body": "Join our CASINO now"},
                    headers=auth(MEMBER))
    assert r.json()["status"] == "spam"
    visible = client.get(f"/api/documents/{doc['id']}/comments").json()
    assert all(c["id"] != r.json()["id"] for c in visible)


# --------------------------------------------------------- moderation -------

def test_moderation_flow(client, auth):
    h = auth(MOD)
    stats = client.get("/api/moderation/stats", headers=h).json()
    assert stats["open_reports"] >= 3
    reported = client.get("/api/moderation/comments", params={"status": "reported"}, headers=h).json()
    assert reported["total"] >= 1 and reported["items"][0]["report_count"] >= 1
    pending = client.get("/api/moderation/comments", params={"status": "pending"}, headers=h).json()["items"][0]
    assert client.patch(f"/api/moderation/comments/{pending['id']}", json={"status": "visible"},
                        headers=h).status_code == 200
    report = client.get("/api/moderation/reports", headers=h).json()[0]
    handled = client.patch(f"/api/moderation/reports/{report['id']}",
                           json={"status": "resolved", "note": "ok", "hide_target": report["target_type"] == "comment"},
                           headers=h)
    assert handled.status_code == 200 and handled.json()["status"] == "resolved"
    kw = client.post("/api/moderation/spam-keywords", json={"keyword": "Cheap Pills"}, headers=h)
    assert kw.status_code == 201 and kw.json()["keyword"] == "cheap pills"
    assert client.post("/api/moderation/spam-keywords", json={"keyword": "cheap pills"}, headers=h).status_code == 409
    assert client.delete(f"/api/moderation/spam-keywords/{kw.json()['id']}", headers=h).status_code == 200


# ---------------------------------------------------------- SEO / data ------

def test_seo_and_analytics(client, auth):
    h = auth(SEO)
    issues = client.get("/api/seo/documents", params={"only_issues": True, "page_size": 100}, headers=h).json()
    assert issues["total"] > 0 and all(i["issues"] for i in issues["items"])
    target = issues["items"][0]
    fixed = client.put(f"/api/seo/documents/{target['id']}", json={
        "seo_title": "Short title", "seo_description": "A meta description that is long enough to pass the check.",
        "seo_keywords": "a, b", "cover_image_alt": "Alt text"}, headers=h).json()
    assert fixed["issues"] == []
    a = client.get("/api/analytics/summary", headers=h).json()
    assert a["totals"]["searches_in_period"] > 0 and a["top_queries"] and a["views_by_day"]
    assert any(z["query"] == "parking reimbursement" for z in a["zero_result_queries"])
    logs = client.get("/api/analytics/search-logs", params={"event_type": "click"}, headers=h).json()
    assert logs["total"] > 0 and all(r["clicked_doc_id"] for r in logs["items"])
    csv = client.get("/api/analytics/search-logs.csv", headers=h)
    assert csv.status_code == 200 and csv.text.startswith("id,user_id,session_id,query_string,clicked_doc_id")


# --------------------------------------------------------- super admin ------

def test_super_admin_users_roles_settings_logs(client, auth):
    h = auth(ADMIN)
    roles = {r["name"]: r for r in client.get("/api/admin/roles", headers=h).json()}
    assert set(roles) == {"super_admin", "content_manager", "moderator", "seo_specialist", "user"}

    u = client.post("/api/admin/users", json={"username": "temp.mod", "email": "temp@example.com",
                                             "password": "Password123!", "role_id": roles["moderator"]["id"]},
                    headers=h)
    assert u.status_code == 201
    uid = u.json()["id"]
    login = client.post("/api/auth/login", json={"username": "temp.mod", "password": "Password123!"}).json()
    th = {"Authorization": f"Bearer {login['access_token']}"}
    assert client.get("/api/moderation/comments", headers=th).status_code == 200

    # promote to content manager -> permissions change immediately
    client.put(f"/api/admin/users/{uid}", json={"role_id": roles["content_manager"]["id"]}, headers=h)
    assert client.get("/api/moderation/comments", headers=th).status_code == 403
    assert client.get("/api/admin/documents", headers=th).status_code == 200

    # edit role permissions
    cm = roles["content_manager"]
    codes = [p["code"] for p in cm["permissions"]] + ["analytics.view"]
    r = client.put(f"/api/admin/roles/{cm['id']}/permissions", json={"permission_codes": codes}, headers=h)
    assert r.status_code == 200
    assert client.get("/api/analytics/summary", headers=th).status_code == 200
    client.put(f"/api/admin/roles/{cm['id']}/permissions",
               json={"permission_codes": [c for c in codes if c != "analytics.view"]}, headers=h)
    assert client.put(f"/api/admin/roles/{cm['id']}/permissions", json={"permission_codes": ["bogus"]},
                      headers=h).status_code == 422

    # deactivate -> token no longer works
    client.put(f"/api/admin/users/{uid}", json={"is_active": False}, headers=h)
    assert client.get("/api/auth/me", headers=th).status_code == 401

    # cannot demote the last super admin / delete yourself
    me = client.get("/api/auth/me", headers=h).json()
    assert client.put(f"/api/admin/users/{me['id']}", json={"role_id": roles["user"]["id"]},
                      headers=h).status_code == 409
    assert client.delete(f"/api/admin/users/{me['id']}", headers=h).status_code == 409
    assert client.delete(f"/api/admin/users/{uid}", headers=h).status_code == 200

    # settings
    assert client.put("/api/admin/settings/comments_require_approval", json={"value": True},
                      headers=h).status_code == 200
    doc = client.get("/api/documents").json()["items"][2]
    c = client.post(f"/api/documents/{doc['id']}/comments", json={"body": "Needs approval"}, headers=auth(MEMBER))
    assert c.json()["status"] == "pending"
    client.put("/api/admin/settings/comments_require_approval", json={"value": False}, headers=h)
    assert client.put("/api/admin/settings/default_page_size", json={"value": "ten"}, headers=h).status_code == 422
    assert client.put("/api/admin/settings/unknown", json={"value": 1}, headers=h).status_code == 404

    client.put("/api/admin/settings/registration_open", json={"value": False}, headers=h)
    assert client.post("/api/auth/register", json={"username": "blocked_user", "email": "b@example.com",
                                                   "password": "Password123!"}).status_code == 403
    client.put("/api/admin/settings/registration_open", json={"value": True}, headers=h)

    logs = client.get("/api/admin/system-logs", params={"action": "user."}, headers=h).json()
    actions = {l["action"] for l in logs["items"]}
    assert {"user.create", "user.update", "user.delete"} <= actions
