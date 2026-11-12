"""Ranking functions: TF-IDF (vector space, cosine) and BM25F.

Both functions return {doc_id: score}. With `explain=True` they also return
the per-term contribution so the admin "Explain" tool can show the maths.

Notation: N documents, df(t) documents containing t, tf_f(t,d) occurrences of
t in field f of d, |d|_f field length, avg_f average field length, w_f field
weight.

TF-IDF (lnc.ltc-style cosine)
    tf_w(t,d)  = sum_f w_f * tf_f(t,d)
    w(t,d)     = (1 + ln tf_w(t,d)) * idf(t),       idf(t) = ln(N / df(t))
    w(t,q)     = q_weight(t) * idf(t)
    score(d,q) = sum_t w(t,q) * w(t,d) / (|q| * |d|)

BM25F (BM25 with per-field length normalisation, Robertson & Zaragoza 2009)
    tf~(t,d)   = sum_f w_f * tf_f(t,d) / (1 - b + b * |d|_f / avg_f)
    idf(t)     = ln(1 + (N - df + 0.5) / (df + 0.5))
    score(d,q) = sum_t q_weight(t) * idf(t) * tf~ * (k1 + 1) / (k1 + tf~)
k1 controls term-frequency saturation, b how strongly long fields are penalised.
"""
from __future__ import annotations

import math
from collections import defaultdict

from .index import InvertedIndex

Contrib = dict[int, dict[str, float]]


def bm25_scores(
    index: InvertedIndex,
    query_terms: dict[str, float],
    k1: float = 1.2,
    b: float = 0.75,
    field_weights: dict[str, float] | None = None,
    explain: bool = False,
) -> tuple[dict[int, float], Contrib]:
    weights = field_weights or {}
    scores: dict[int, float] = defaultdict(float)
    contrib: Contrib = defaultdict(dict)
    for term, qw in query_terms.items():
        plist = index.postings.get(term)
        if not plist:
            continue
        idf = index.idf_bm25(term)
        for doc_id, fields in plist.items():
            lengths = index.docs[doc_id].lengths
            tf_tilde = 0.0
            for f, positions in fields.items():
                w = weights.get(f, 1.0)
                avg = index.avg_field_len.get(f) or 1.0
                norm = 1 - b + b * (lengths.get(f, 0) / avg)
                tf_tilde += w * len(positions) / norm
            s = qw * idf * tf_tilde * (k1 + 1) / (k1 + tf_tilde)
            scores[doc_id] += s
            if explain:
                contrib[doc_id][term] = s
    return dict(scores), contrib


def _weighted_tf(fields: dict[str, list[int]], weights: dict[str, float]) -> float:
    return sum(weights.get(f, 1.0) * len(p) for f, p in fields.items())


def doc_vector_norms(index: InvertedIndex, field_weights: dict[str, float]) -> dict[int, float]:
    """|d| for every document; cached on the index per weight setting."""
    key = tuple(sorted(field_weights.items()))
    cache = getattr(index, "_norm_cache", None)
    if cache and cache[0] == key:
        return cache[1]
    sq: dict[int, float] = defaultdict(float)
    for term, plist in index.postings.items():
        idf = index.idf_classic(term)
        if idf == 0:
            continue
        for doc_id, fields in plist.items():
            tfw = _weighted_tf(fields, field_weights)
            sq[doc_id] += ((1 + math.log(tfw)) * idf) ** 2
    norms = {d: math.sqrt(v) for d, v in sq.items()}
    index._norm_cache = (key, norms)
    return norms


def tfidf_scores(
    index: InvertedIndex,
    query_terms: dict[str, float],
    field_weights: dict[str, float] | None = None,
    explain: bool = False,
) -> tuple[dict[int, float], Contrib]:
    weights = field_weights or {}
    norms = doc_vector_norms(index, weights)
    q_vec = {t: qw * index.idf_classic(t) for t, qw in query_terms.items() if index.df(t)}
    q_norm = math.sqrt(sum(v * v for v in q_vec.values()))
    scores: dict[int, float] = defaultdict(float)
    contrib: Contrib = defaultdict(dict)
    if q_norm == 0:
        return {}, contrib
    for term, wq in q_vec.items():
        if wq == 0:
            continue
        idf = index.idf_classic(term)
        for doc_id, fields in index.postings[term].items():
            d_norm = norms.get(doc_id)
            if not d_norm:
                continue
            wd = (1 + math.log(_weighted_tf(fields, weights))) * idf
            s = wq * wd / (q_norm * d_norm)
            scores[doc_id] += s
            if explain:
                contrib[doc_id][term] = s
    return dict(scores), contrib
