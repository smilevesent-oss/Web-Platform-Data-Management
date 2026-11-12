"""Search engine facade used by the API.

The index lives in memory (61-100 documents build in a few milliseconds).
Before every search we compare a cheap fingerprint of the published corpus
(count + hash of the indexed fields, computed by PostgreSQL) with the one the
index was built from. Any create / edit / publish / unpublish / delete changes
the fingerprint, so the next search rebuilds the index automatically. This
also keeps several API worker processes consistent without extra messaging.
View counts and SEO edits do not touch indexed fields, so they do not trigger
a rebuild.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.orm import Session

from .index import DEFAULT_FIELD_WEIGHTS, FIELDS, InvertedIndex
from .query import ParsedQuery, parse_query
from .ranking import bm25_scores, tfidf_scores
from .tokenizer import Token

ALGORITHMS = ("bm25", "tfidf")

CORPUS_SQL = text(
    "SELECT id, title, content, summary, tags, author FROM search_corpus WHERE status = 'published'"
)
FINGERPRINT_SQL = text(
    """
    SELECT count(*), coalesce(sum(hashtext(
        id::text || '|' || title || '|' || summary || '|' || content || '|' ||
        array_to_string(tags, '|') || '|' || coalesce(author, '')
    )::bigint), 0)
    FROM search_corpus WHERE status = 'published'
    """
)


@dataclass
class Hit:
    doc_id: int
    score: float


@dataclass
class SearchResult:
    hits: list[Hit]
    parsed: ParsedQuery
    algorithm: str
    took_ms: float
    suggestion: str | None = None
    contributions: dict[int, dict[str, float]] = field(default_factory=dict)


@dataclass
class Params:
    k1: float = 1.2
    b: float = 0.75
    field_weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_FIELD_WEIGHTS))


class SearchEngine:
    def __init__(self) -> None:
        self._index: InvertedIndex | None = None
        self._fingerprint: tuple | None = None
        self._lock = threading.Lock()
        self.rebuilds = 0

    # ------------------------------------------------------- lifecycle ----

    def index(self, db: Session, force: bool = False) -> InvertedIndex:
        fp = tuple(db.execute(FINGERPRINT_SQL).one())
        if not force and self._index is not None and fp == self._fingerprint:
            return self._index
        with self._lock:
            if force or self._index is None or fp != self._fingerprint:
                rows = [dict(r._mapping) for r in db.execute(CORPUS_SQL)]
                self._index = InvertedIndex.build(rows)
                self._fingerprint = fp
                self.rebuilds += 1
        return self._index

    # ---------------------------------------------------------- search ----

    def search(
        self,
        db: Session,
        query: str,
        algorithm: str = "bm25",
        params: Params | None = None,
        allowed_ids: set[int] | None = None,
        explain: bool = False,
        suggest: bool = True,
    ) -> SearchResult:
        t0 = time.perf_counter()
        idx = self.index(db)
        params = params or Params()
        pq = parse_query(query, idx)
        hits, contrib = self._rank(idx, pq, algorithm, params, allowed_ids, explain)
        suggestion = None
        if suggest and pq.unknown_words:
            suggestion = self.suggest(idx, query, pq)
        return SearchResult(
            hits=hits,
            parsed=pq,
            algorithm=algorithm,
            took_ms=(time.perf_counter() - t0) * 1000,
            suggestion=suggestion,
            contributions=contrib,
        )

    def _rank(self, idx, pq: ParsedQuery, algorithm, params: Params, allowed_ids, explain):
        if pq.empty:
            return [], {}
        qterms = pq.term_weights()
        if algorithm == "tfidf":
            scores, contrib = tfidf_scores(idx, qterms, params.field_weights, explain)
        else:
            scores, contrib = bm25_scores(idx, qterms, params.k1, params.b, params.field_weights, explain)

        def keep(doc_id: int) -> bool:
            if allowed_ids is not None and doc_id not in allowed_ids:
                return False
            if pq.excluded and any(doc_id in idx.postings.get(t, {}) for t in pq.excluded):
                return False
            return all(idx.phrase_match(doc_id, ph) for ph in pq.phrases)

        hits = [Hit(d, s) for d, s in scores.items() if s > 0 and keep(d)]
        hits.sort(key=lambda h: (-h.score, h.doc_id))
        return hits, contrib

    # ------------------------------------------------------ did you mean ---

    def suggest(self, idx: InvertedIndex, query: str, pq: ParsedQuery) -> str | None:
        fixed = query
        changed = False
        for word in dict.fromkeys(pq.unknown_words):
            best = closest_word(idx, word)
            if best and best != word:
                fixed = _replace_word(fixed, word, best)
                changed = True
        return fixed if changed else None

    # --------------------------------------------------------- snippets ----

    def highlights(self, db: Session, doc_id: int, pq: ParsedQuery, length: int = 240) -> dict:
        """Snippet from the body plus [start, end) ranges to highlight in title, summary, snippet."""
        idx = self.index(db)
        doc = idx.docs.get(doc_id)
        if doc is None:
            return {}
        wanted = {qt.term for qt in pq.terms}
        out = {
            "title": _ranges(doc.tokens["title"], wanted),
            "summary": _ranges(doc.tokens["summary"], wanted),
        }
        snippet, ranges = best_window(doc.texts["content"], doc.tokens["content"], wanted, length)
        out["snippet"] = snippet
        out["snippet_ranges"] = ranges
        out["matched_fields"] = [f for f in FIELDS if any(t.term in wanted for t in doc.tokens[f])]
        return out


def _ranges(tokens: list[Token], wanted: set[str]) -> list[list[int]]:
    return [[t.start, t.end] for t in tokens if t.term in wanted]


def best_window(text: str, tokens: list[Token], wanted: set[str], length: int) -> tuple[str, list[list[int]]]:
    """Pick the passage with the most distinct query terms (then most hits)."""
    hits = [t for t in tokens if t.term in wanted]
    if not hits:
        cut = text[:length]
        cut = cut.rsplit(" ", 1)[0] if len(text) > length else cut
        return " ".join(cut.split()) + ("…" if len(text) > length else ""), []
    best_key, best_start = (-1, -1), 0
    for i, h in enumerate(hits):
        start = max(0, h.start - 50)
        inside = [x for x in hits[i:] if x.end <= start + length]
        key = (len({x.term for x in inside}), len(inside))
        if key > best_key:
            best_key, best_start = key, start
    start = best_start
    if start > 0:  # snap to a word boundary
        space = text.rfind(" ", 0, start)
        start = space + 1 if space >= 0 and start - space < 20 else start
    end = min(len(text), start + length)
    if end < len(text):
        space = text.rfind(" ", start, end)
        end = space if space > start else end
    prefix = "…" if start > 0 else ""
    raw = text[start:end]
    # Collapse whitespace while keeping offsets valid: replace newlines 1:1.
    raw = raw.replace("\n", " ")
    ranges = [[len(prefix) + t.start - start, len(prefix) + t.end - start]
              for t in hits if t.start >= start and t.end <= end]
    return prefix + raw + ("…" if end < len(text) else ""), ranges


# ------------------------------------------------------------- spelling ----

def levenshtein(a: str, b: str, limit: int = 3) -> int:
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > limit:
            return limit + 1
        prev = cur
    return prev[-1]


def closest_word(idx: InvertedIndex, word: str) -> str | None:
    """Nearest vocabulary word by edit distance; ties go to the more frequent word."""
    if len(word) < 3 or word.isdigit():
        return None
    max_d = 1 if len(word) <= 4 else 2
    best: tuple[int, int, str] | None = None
    for cand, freq in idx.surface_counts.items():
        # Typos rarely hit the first letter; requiring it keeps this fast and precise.
        if abs(len(cand) - len(word)) > max_d or cand[0] != word[0]:
            continue
        d = levenshtein(word, cand, max_d)
        if d <= max_d:
            key = (d, -freq, cand)
            if best is None or key < best:
                best = key
    return best[2] if best else None


def _replace_word(query: str, word: str, repl: str) -> str:
    import re

    return re.sub(rf"(?i)\b{re.escape(word)}\b", repl, query, count=1)


engine = SearchEngine()
