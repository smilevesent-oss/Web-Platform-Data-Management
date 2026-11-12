"""Offline evaluation of ranking quality against hand-judged queries.

    python -m app.search.evaluate            # compare LIKE, TF-IDF and BM25
    python -m app.search.evaluate --tune     # grid-search BM25 k1 and b

Metrics (averaged over queries):
  P@5     share of the top 5 results that are relevant
  R@10    share of all relevant documents found in the top 10
  MAP     mean average precision (precision at each relevant hit, averaged)
  MRR     1 / rank of the first relevant result
  nDCG@10 graded gain (2^rel - 1) discounted by log2(rank + 1), divided by the ideal ordering
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Document
from .engine import Params, engine

QRELS_PATH = Path(__file__).with_name("qrels.json")
METRICS = ("p@5", "r@10", "map", "mrr", "ndcg@10")


# ---------------------------------------------------------------- metrics --

def precision_at(ranked: list[int], rel: dict[int, int], k: int) -> float:
    return sum(1 for d in ranked[:k] if rel.get(d, 0) > 0) / k


def recall_at(ranked: list[int], rel: dict[int, int], k: int) -> float:
    total = sum(1 for g in rel.values() if g > 0)
    return sum(1 for d in ranked[:k] if rel.get(d, 0) > 0) / total if total else 0.0


def average_precision(ranked: list[int], rel: dict[int, int]) -> float:
    total = sum(1 for g in rel.values() if g > 0)
    hits, acc = 0, 0.0
    for i, d in enumerate(ranked, 1):
        if rel.get(d, 0) > 0:
            hits += 1
            acc += hits / i
    return acc / total if total else 0.0


def reciprocal_rank(ranked: list[int], rel: dict[int, int]) -> float:
    for i, d in enumerate(ranked, 1):
        if rel.get(d, 0) > 0:
            return 1 / i
    return 0.0


def ndcg_at(ranked: list[int], rel: dict[int, int], k: int) -> float:
    def dcg(grades):
        return sum((2 ** g - 1) / math.log2(i + 1) for i, g in enumerate(grades, 1))

    ideal = dcg(sorted(rel.values(), reverse=True)[:k])
    return dcg([rel.get(d, 0) for d in ranked[:k]]) / ideal if ideal else 0.0


def score_run(ranked: list[int], rel: dict[int, int]) -> dict[str, float]:
    return {
        "p@5": precision_at(ranked, rel, 5),
        "r@10": recall_at(ranked, rel, 10),
        "map": average_precision(ranked, rel),
        "mrr": reciprocal_rank(ranked, rel),
        "ndcg@10": ndcg_at(ranked, rel, 10),
    }


# ----------------------------------------------------------------- runners --

def load_qrels(db: Session) -> list[dict]:
    """Resolve titles in qrels.json to document ids (unknown titles are reported)."""
    data = json.loads(QRELS_PATH.read_text(encoding="utf-8"))
    ids = {t: i for i, t in db.execute(select(Document.id, Document.title).where(Document.status == "published"))}
    out = []
    for q in data["queries"]:
        rel = {ids[t]: g for t, g in q["relevant"].items() if t in ids}
        missing = [t for t in q["relevant"] if t not in ids]
        out.append({"query": q["query"], "rel": rel, "missing": missing})
    return out


def run_like(db: Session, query: str, k: int = 100) -> list[int]:
    """Phase-1 baseline: every word must appear (ILIKE), newest first."""
    from ..routers.documents import SORTS, apply_filters

    stmt = apply_filters(select(Document.id).where(Document.status == "published"), query, None, None, None, None, None)
    return list(db.scalars(stmt.order_by(*SORTS["latest"]).limit(k)))


def run_engine(db: Session, query: str, algorithm: str, params: Params | None = None) -> list[int]:
    res = engine.search(db, query, algorithm, params=params, suggest=False)
    return [h.doc_id for h in res.hits[:100]]


def evaluate(db: Session, systems: dict | None = None) -> dict:
    """Return per-system averages and per-query rows."""
    qrels = load_qrels(db)
    systems = systems or {
        "like": lambda q: run_like(db, q),
        "tfidf": lambda q: run_engine(db, q, "tfidf"),
        "bm25": lambda q: run_engine(db, q, "bm25"),
    }
    per_query = []
    totals: dict[str, list[dict]] = {name: [] for name in systems}
    for q in qrels:
        row = {"query": q["query"], "relevant": len(q["rel"]), "systems": {}}
        for name, fn in systems.items():
            ranked = fn(q["query"])
            m = score_run(ranked, q["rel"])
            m["returned"] = len(ranked)
            m["first_relevant_rank"] = next((i for i, d in enumerate(ranked, 1) if q["rel"].get(d)), None)
            totals[name].append(m)
            row["systems"][name] = m
        per_query.append(row)
    summary = {
        name: {m: round(mean(r[m] for r in rows), 4) for m in METRICS}
        | {"zero_result_queries": sum(1 for r in rows if r["returned"] == 0)}
        for name, rows in totals.items()
    }
    missing = sorted({t for q in qrels for t in q["missing"]})
    return {"queries": len(qrels), "summary": summary, "per_query": per_query, "missing_titles": missing}


def tune_bm25(db: Session, k1_values=(0.6, 0.9, 1.2, 1.5, 2.0), b_values=(0.3, 0.5, 0.75, 0.9)) -> list[dict]:
    qrels = load_qrels(db)
    grid = []
    for k1 in k1_values:
        for b in b_values:
            p = Params(k1=k1, b=b)
            rows = [score_run(run_engine(db, q["query"], "bm25", p), q["rel"]) for q in qrels]
            grid.append({"k1": k1, "b": b} | {m: round(mean(r[m] for r in rows), 4) for m in METRICS})
    grid.sort(key=lambda g: (-g["ndcg@10"], -g["map"]))
    return grid
