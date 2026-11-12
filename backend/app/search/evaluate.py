"""CLI: python -m app.search.evaluate [--tune] [--per-query]"""
from __future__ import annotations

import argparse

from ..database import SessionLocal
from .evaluation import METRICS, evaluate, tune_bm25


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate search ranking against qrels.json")
    ap.add_argument("--tune", action="store_true", help="grid-search BM25 k1 and b")
    ap.add_argument("--per-query", action="store_true", help="show nDCG@10 for every query")
    args = ap.parse_args()
    with SessionLocal() as db:
        res = evaluate(db)
        print(f"{res['queries']} judged queries\n")
        print(f"{'system':8}" + "".join(f"{m:>9}" for m in METRICS) + f"{'0-result':>10}")
        for name, s in res["summary"].items():
            print(f"{name:8}" + "".join(f"{s[m]:9.3f}" for m in METRICS) + f"{s['zero_result_queries']:10d}")
        if args.per_query:
            print("\nnDCG@10 per query")
            for row in res["per_query"]:
                vals = "  ".join(f"{n}={m['ndcg@10']:.2f}" for n, m in row["systems"].items())
                print(f"  {row['query'][:48]:48} {vals}")
        if res["missing_titles"]:
            print("\nWARNING: titles in qrels.json not found:", res["missing_titles"])
        if args.tune:
            print("\nBM25 grid search (best first)")
            for g in tune_bm25(db)[:10]:
                print(f"  k1={g['k1']:<4} b={g['b']:<5}" + "".join(f" {m}={g[m]:.3f}" for m in METRICS))


if __name__ == "__main__":
    main()
