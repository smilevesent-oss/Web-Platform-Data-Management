"""Phase 2 search-engine workspace: index inspection, query explain, tuning and evaluation.

All routes require the `search.manage` permission (Super Admin and Data & SEO Specialist by default).
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import client_ip, require_permissions
from ..models import Document, Setting
from ..permissions import DEFAULT_SETTINGS
from ..search import engine
from ..search.evaluation import evaluate, tune_bm25
from ..search.index import DEFAULT_FIELD_WEIGHTS
from ..search.tokenizer import STOP_WORDS, analyze
from ..utils import audit
from .documents import default_algorithm, search_params

router = APIRouter(prefix="/admin/search", tags=["search engine"])
perm = require_permissions("search.manage")


class SearchConfig(BaseModel):
    algorithm: Literal["bm25", "tfidf", "like"]
    k1: float = Field(ge=0.0, le=5.0)
    b: float = Field(ge=0.0, le=1.0)


def _config(db: Session) -> dict:
    p = search_params(db)
    return {"algorithm": default_algorithm(db), "k1": p.k1, "b": p.b, "field_weights": DEFAULT_FIELD_WEIGHTS}


def _titles(db: Session, ids) -> dict[int, str]:
    ids = list(ids)
    if not ids:
        return {}
    return dict(db.execute(select(Document.id, Document.title).where(Document.id.in_(ids))).all())


@router.get("/stats")
def index_stats(db: Session = Depends(get_db), _=Depends(perm)):
    idx = engine.index(db)
    top = sorted(idx.postings, key=lambda t: -idx.df(t))[:25]
    return {
        **idx.stats(),
        "rebuilds": engine.rebuilds,
        "config": _config(db),
        "top_terms": [
            {"term": t, "df": idx.df(t), "idf": round(idx.idf_bm25(t), 3),
             "words": [w for w, _ in idx.stem_surfaces[t].most_common(3)]}
            for t in top
        ],
    }


@router.post("/rebuild")
def rebuild(request: Request, db: Session = Depends(get_db), user=Depends(perm)):
    idx = engine.index(db, force=True)
    audit(db, "search.rebuild", user.id, "search_index", None, {"documents": idx.n_docs}, client_ip(request))
    db.commit()
    return idx.stats()


@router.get("/analyze")
def analyze_text(text: str = Query(max_length=2000), _=Depends(perm)):
    """Show every step of the analysis pipeline for a piece of text."""
    kept = {(t.start, t.end): t for t in analyze(text)}
    out = []
    for t in analyze(text, keep_stop_words=True):
        k = kept.get((t.start, t.end))
        out.append({
            "original": text[t.start:t.end],
            "normalised": t.surface,
            "term": k.term if k else None,
            "position": t.position,
            "removed": None if k else ("stop word" if t.surface in STOP_WORDS else "too short"),
        })
    return {"tokens": out}


@router.get("/term")
def term_lookup(word: str = Query(min_length=1, max_length=100), db: Session = Depends(get_db), _=Depends(perm)):
    """Postings list for a word: which documents contain it, where and how often."""
    idx = engine.index(db)
    toks = analyze(word)
    if not toks:
        return {"word": word, "term": None, "df": 0, "postings": [], "note": "Removed by the analyser (stop word)"}
    term = toks[0].term
    plist = idx.postings.get(term, {})
    titles = _titles(db, plist)
    rows = [
        {"doc_id": d, "title": titles.get(d, ""), "tf": sum(len(p) for p in fields.values()),
         "fields": {f: p[:20] for f, p in fields.items()}}
        for d, fields in plist.items()
    ]
    rows.sort(key=lambda r: -r["tf"])
    return {
        "word": word,
        "term": term,
        "df": idx.df(term),
        "idf_bm25": round(idx.idf_bm25(term), 4),
        "idf_tfidf": round(idx.idf_classic(term), 4),
        "words": [w for w, _ in idx.stem_surfaces.get(term, {}).most_common(10)] if term in idx.stem_surfaces else [],
        "postings": rows,
    }


@router.get("/explain")
def explain(
    q: str = Query(min_length=1, max_length=200),
    algo: Literal["bm25", "tfidf"] = "bm25",
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    _=Depends(perm),
):
    """Score breakdown: how much each query term contributed to each top document."""
    res = engine.search(db, q, algo, params=search_params(db), explain=True)
    idx = engine.index(db)
    terms = list(res.parsed.term_weights())
    top = res.hits[:limit]
    titles = _titles(db, [h.doc_id for h in top])
    return {
        "query": q,
        "algorithm": algo,
        "took_ms": round(res.took_ms, 2),
        "suggestion": res.suggestion,
        "parsed": {
            "terms": [{"term": t.term, "word": t.surface, "weight": round(t.weight, 3), "origin": t.origin}
                      for t in res.parsed.terms],
            "phrases": [" ".join(tok.surface for tok in ph) for ph in res.parsed.phrases],
            "excluded": sorted(res.parsed.excluded),
            "unknown": res.parsed.unknown_words,
        },
        "term_stats": [
            {"term": t, "df": idx.df(t),
             "idf": round(idx.idf_bm25(t) if algo == "bm25" else idx.idf_classic(t), 4)}
            for t in terms
        ],
        "total": len(res.hits),
        "results": [
            {"rank": i, "doc_id": h.doc_id, "title": titles.get(h.doc_id, ""), "score": round(h.score, 4),
             "contributions": {t: round(res.contributions.get(h.doc_id, {}).get(t, 0.0), 4) for t in terms}}
            for i, h in enumerate(top, 1)
        ],
    }


@router.get("/config")
def get_config(db: Session = Depends(get_db), _=Depends(perm)):
    return _config(db)


@router.put("/config")
def set_config(data: SearchConfig, request: Request, db: Session = Depends(get_db), user=Depends(perm)):
    new = {"search_algorithm": data.algorithm, "search_bm25_k1": data.k1, "search_bm25_b": data.b}
    old = {}
    for key, value in new.items():
        row = db.get(Setting, key)
        if row is None:
            db.add(Setting(key=key, value=value, description=DEFAULT_SETTINGS[key][1]))
        else:
            old[key] = row.value
            row.value = value
    audit(db, "search.config", user.id, "setting", "search", {"from": old, "to": new}, client_ip(request))
    db.commit()
    return _config(db)


@router.get("/evaluate")
def run_evaluation(db: Session = Depends(get_db), _=Depends(perm)):
    """Compare LIKE, TF-IDF and BM25 on the judged queries in app/search/qrels.json."""
    return evaluate(db)


@router.get("/evaluate/tune")
def run_tuning(db: Session = Depends(get_db), _=Depends(perm)):
    """Grid search over BM25 k1 and b (best nDCG@10 first)."""
    return {"grid": tune_bm25(db)}
