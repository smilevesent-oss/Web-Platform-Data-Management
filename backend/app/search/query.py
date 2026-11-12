"""Query language.

    remote work            ranked OR query: documents with more / rarer matches score higher
    "data protection"      phrase: the words must appear next to each other
    -contractor            exclusion: drop documents containing this word
    secur*                 prefix: expands to security, secure, secured, ...

Terms combine freely: `"incident response" -postmortem secur*`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .index import InvertedIndex
from .tokenizer import Token, analyze, normalize

_PART_RE = re.compile(r'(-?)"([^"]*)"|(\S+)')
MAX_QUERY_TERMS = 32


@dataclass
class QueryTerm:
    term: str            # index key (stem)
    surface: str         # what the user typed (normalised)
    weight: float = 1.0  # prefix expansions share one unit of weight
    origin: str = "word"  # word | phrase | prefix


@dataclass
class ParsedQuery:
    raw: str
    terms: list[QueryTerm] = field(default_factory=list)
    phrases: list[list[Token]] = field(default_factory=list)
    excluded: set[str] = field(default_factory=set)
    unknown_words: list[str] = field(default_factory=list)   # typed words not in the vocabulary

    @property
    def empty(self) -> bool:
        return not self.terms

    def term_weights(self) -> dict[str, float]:
        """Unique stems -> query weight (repeating a word in the query does not double it)."""
        out: dict[str, float] = {}
        for qt in self.terms:
            out[qt.term] = max(out.get(qt.term, 0.0), qt.weight)
        return out


def parse_query(raw: str, index: InvertedIndex) -> ParsedQuery:
    pq = ParsedQuery(raw=raw)
    for m in _PART_RE.finditer(raw or ""):
        negate, phrase, word = m.group(1), m.group(2), m.group(3)
        if phrase is not None:
            toks = analyze(phrase)
            if negate:
                pq.excluded.update(t.term for t in toks)
                continue
            if len(toks) > 1:
                pq.phrases.append(toks)
            pq.terms.extend(QueryTerm(t.term, t.surface, origin="phrase") for t in toks)
            continue

        if word.startswith("-") and len(word) > 1:
            pq.excluded.update(t.term for t in analyze(word[1:]))
            continue

        if word.endswith("*") and len(word.rstrip("*")) >= 2:
            prefix = normalize(word.rstrip("*"))
            surfaces = index.surfaces_with_prefix(prefix)
            stems: dict[str, str] = {}
            for s in surfaces:
                for t in analyze(s):
                    stems.setdefault(t.term, s)
            if not stems:
                pq.unknown_words.append(prefix)
            share = 1.0 / max(1, len(stems)) ** 0.5  # many expansions should not swamp other words
            pq.terms.extend(QueryTerm(stem_, s, weight=share, origin="prefix") for stem_, s in stems.items())
            continue

        for t in analyze(word):
            pq.terms.append(QueryTerm(t.term, t.surface))
            if index.df(t.term) == 0:
                pq.unknown_words.append(t.surface)

    pq.terms = pq.terms[:MAX_QUERY_TERMS]
    return pq
