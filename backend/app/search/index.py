"""Positional, multi-field inverted index.

    postings[term][doc_id][field] = [position, position, ...]

From the postings we can read every statistic the ranking functions need:
  * tf(t, d, f)  = len(postings[t][d][f])
  * df(t)        = len(postings[t])            (number of documents)
  * |d|_f        = field_len[d][f]             (tokens in that field)
  * avg |d|_f    = avg_field_len[f]
Positions let us answer phrase queries ("data protection officer").
"""
from __future__ import annotations

import math
import time
from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .tokenizer import Token, analyze

FIELDS = ("title", "tags", "summary", "content", "author")

# How much a match in each field counts (used by both BM25F and TF-IDF).
# A word in the title says far more about the topic than one in the body.
DEFAULT_FIELD_WEIGHTS = {"title": 3.0, "tags": 2.0, "summary": 1.5, "content": 1.0, "author": 0.5}


@dataclass
class IndexedDoc:
    id: int
    texts: dict[str, str]                       # original field text (for snippets)
    tokens: dict[str, list[Token]]              # analysed tokens per field (for highlighting)
    lengths: dict[str, int] = field(default_factory=dict)


class InvertedIndex:
    def __init__(self) -> None:
        self.postings: dict[str, dict[int, dict[str, list[int]]]] = defaultdict(dict)
        self.docs: dict[int, IndexedDoc] = {}
        self.avg_field_len: dict[str, float] = {f: 0.0 for f in FIELDS}
        self.surface_counts: Counter[str] = Counter()       # word -> collection frequency
        self.stem_surfaces: dict[str, Counter[str]] = defaultdict(Counter)  # stem -> words
        self._sorted_surfaces: list[str] = []
        self.built_at: float | None = None
        self.build_ms: float = 0.0

    # ------------------------------------------------------------ build ----

    @classmethod
    def build(cls, rows) -> "InvertedIndex":
        """rows: iterable of dicts with id + the FIELDS (tags may be a list)."""
        t0 = time.perf_counter()
        idx = cls()
        for row in rows:
            idx._add(row)
        idx._finalise()
        idx.build_ms = (time.perf_counter() - t0) * 1000
        idx.built_at = time.time()
        return idx

    def _add(self, row: dict) -> None:
        texts: dict[str, str] = {}
        for f in FIELDS:
            value = row.get(f) or ""
            if isinstance(value, (list, tuple)):
                value = " | ".join(value)  # separator keeps tag phrases from joining up
            texts[f] = value
        doc = IndexedDoc(id=row["id"], texts=texts, tokens={})
        for f, text in texts.items():
            toks = analyze(text)
            doc.tokens[f] = toks
            doc.lengths[f] = len(toks)
            for tok in toks:
                self.postings[tok.term].setdefault(doc.id, {}).setdefault(f, []).append(tok.position)
                self.surface_counts[tok.surface] += 1
                self.stem_surfaces[tok.term][tok.surface] += 1
        self.docs[doc.id] = doc

    def _finalise(self) -> None:
        n = len(self.docs) or 1
        for f in FIELDS:
            self.avg_field_len[f] = sum(d.lengths.get(f, 0) for d in self.docs.values()) / n
        self.postings = dict(self.postings)
        self._sorted_surfaces = sorted(self.surface_counts)

    # ------------------------------------------------------------ stats ----

    @property
    def n_docs(self) -> int:
        return len(self.docs)

    def df(self, term: str) -> int:
        return len(self.postings.get(term, ()))

    def tf(self, term: str, doc_id: int, f: str) -> int:
        return len(self.postings.get(term, {}).get(doc_id, {}).get(f, ()))

    def idf_bm25(self, term: str) -> float:
        """Robertson-Sparck Jones IDF with +1 inside the log so it never goes negative."""
        n, df = self.n_docs, self.df(term)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def idf_classic(self, term: str) -> float:
        """idf = ln(N / df), the textbook TF-IDF weight."""
        df = self.df(term)
        return math.log(self.n_docs / df) if df else 0.0

    def stats(self) -> dict:
        n_postings = sum(len(p) for p in self.postings.values())
        return {
            "documents": self.n_docs,
            "vocabulary": len(self.postings),
            "distinct_words": len(self.surface_counts),
            "postings": n_postings,
            "tokens": sum(sum(d.lengths.values()) for d in self.docs.values()),
            "avg_field_length": {f: round(v, 1) for f, v in self.avg_field_len.items()},
            "build_ms": round(self.build_ms, 1),
            "built_at": self.built_at,
        }

    # ---------------------------------------------------------- lookups ----

    def surfaces_with_prefix(self, prefix: str, limit: int = 30) -> list[str]:
        """Words in the vocabulary starting with prefix (for `secur*` queries)."""
        out: list[str] = []
        i = bisect_left(self._sorted_surfaces, prefix)
        while i < len(self._sorted_surfaces) and self._sorted_surfaces[i].startswith(prefix):
            out.append(self._sorted_surfaces[i])
            i += 1
        out.sort(key=lambda w: -self.surface_counts[w])
        return out[:limit]

    def phrase_match(self, doc_id: int, phrase: list[Token]) -> bool:
        """True if the tokens appear in this order (with the same gaps) in one field."""
        if not phrase:
            return True
        first, rest = phrase[0], phrase[1:]
        by_term = [self.postings.get(t.term, {}).get(doc_id) for t in phrase]
        if any(p is None for p in by_term):
            return False
        for f in FIELDS:
            starts = by_term[0].get(f)
            if not starts:
                continue
            others = []
            for tok, p in zip(rest, by_term[1:]):
                pos = p.get(f)
                if not pos:
                    break
                others.append((tok.position - first.position, set(pos)))
            else:
                if any(all(s + gap in pos for gap, pos in others) for s in starts):
                    return True
        return False
