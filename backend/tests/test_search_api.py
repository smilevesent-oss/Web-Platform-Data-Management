"""API tests for Phase-2 ranked search and the search-engine admin workspace."""


def _search(client, **params):
    r = client.get("/api/documents", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def test_ranked_search_beats_like_on_natural_language(client):
    q = "what to do after clicking a suspicious link"
    like = _search(client, q=q, algo="like")
    assert like["total"] == 0  # every word must appear verbatim, so LIKE finds nothing

    res = _search(client, q=q)
    assert res["algorithm"] == "bm25"
    assert res["items"][0]["title"].startswith("Phishing Awareness")
    scores = [i["score"] for i in res["items"]]
    assert scores == sorted(scores, reverse=True)
    top = res["items"][0]["highlights"]
    assert top["snippet"] and top["snippet_ranges"]
    s, e = top["snippet_ranges"][0]
    assert top["snippet"][s:e].lower().startswith(("click", "link", "suspicious"))


def test_stemming_matches_inflections(client):
    titles = [i["title"] for i in _search(client, q="policies on working remotely")["items"][:3]]
    assert "Remote and Hybrid Work Policy 2026" in titles


def test_tfidf_algorithm_and_filters(client):
    res = _search(client, q="leave", algo="tfidf", category="human-resources")
    assert res["algorithm"] == "tfidf" and res["total"] >= 2
    assert all(i["category"]["slug"] == "human-resources" for i in res["items"])
    # sorting by date still only returns matching documents
    by_date = _search(client, q="leave", sort="latest", category="human-resources")
    assert {i["id"] for i in by_date["items"]} == {i["id"] for i in res["items"]}


def test_phrase_exclusion_and_suggestion(client):
    res = _search(client, q='"incident response" -postmortem')
    assert res["total"] >= 1
    assert all("Postmortem" not in i["title"] for i in res["items"])
    typo = _search(client, q="pasword polcy")
    assert typo["total"] == 0 and typo["suggestion"] == "password policy"


def test_search_is_logged_with_algorithm(client, auth):
    _search(client, q="kubernetes deployment", session_id="t-phase2")
    logs = client.get("/api/analytics/search-logs", params={"q": "kubernetes deployment"},
                      headers=auth("seo.analyst")).json()
    row = next(r for r in logs["items"] if r["session_id"] == "t-phase2")
    assert row["filters"]["algo"] == "bm25" and row["results_count"] >= 1


def test_index_updates_when_documents_change(client, auth):
    h = auth("content.manager")
    word = "zyxquartzwombat"
    assert _search(client, q=word)["total"] == 0
    doc = client.post("/api/admin/documents", headers=h, json={
        "title": f"Note on {word}", "content": f"The {word} procedure is described here in detail.",
        "status": "published", "tags": ["Test"], "doc_type": "Report",
    }).json()
    assert _search(client, q=word)["items"][0]["id"] == doc["id"]
    client.patch(f"/api/admin/documents/{doc['id']}/status", headers=h, json={"status": "draft"})
    assert _search(client, q=word)["total"] == 0
    client.delete(f"/api/admin/documents/{doc['id']}", headers=h)


def test_search_admin_requires_permission(client, auth):
    assert client.get("/api/admin/search/stats").status_code == 401
    assert client.get("/api/admin/search/stats", headers=auth("moderator")).status_code == 403
    stats = client.get("/api/admin/search/stats", headers=auth("seo.analyst")).json()
    assert stats["documents"] >= 50 and stats["vocabulary"] > 500


def test_search_admin_tools(client, auth):
    h = auth("seo.analyst")
    term = client.get("/api/admin/search/term", params={"word": "Policies"}, headers=h).json()
    assert term["term"] == "polici" and term["df"] == len(term["postings"]) > 0

    an = client.get("/api/admin/search/analyze", params={"text": "The policies"}, headers=h).json()
    assert an["tokens"][0]["removed"] == "stop word" and an["tokens"][1]["term"] == "polici"

    ex = client.get("/api/admin/search/explain", params={"q": "annual leave"}, headers=h).json()
    top = ex["results"][0]
    assert abs(sum(top["contributions"].values()) - top["score"]) < 1e-3

    ev = client.get("/api/admin/search/evaluate", headers=h).json()
    assert ev["queries"] >= 30 and not ev["missing_titles"]
    assert ev["summary"]["bm25"]["ndcg@10"] > ev["summary"]["like"]["ndcg@10"]


def test_search_config(client, auth):
    h = auth("superadmin")
    bad = client.put("/api/admin/search/config", headers=h, json={"algorithm": "bm25", "k1": 1.2, "b": 3})
    assert bad.status_code == 422
    cfg = client.put("/api/admin/search/config", headers=h, json={"algorithm": "tfidf", "k1": 1.5, "b": 0.5}).json()
    assert cfg["algorithm"] == "tfidf" and cfg["k1"] == 1.5
    assert _search(client, q="leave")["algorithm"] == "tfidf"
    client.put("/api/admin/search/config", headers=h, json={"algorithm": "bm25", "k1": 1.2, "b": 0.75})
    # search settings are not exposed on the generic settings page
    keys = {s["key"] for s in client.get("/api/admin/settings", headers=h).json()}
    assert "search_bm25_k1" not in keys
