"""Text analysis: normalisation -> tokenisation -> stop-word removal -> stemming.

The same `analyze()` function is used for documents (at index time) and for
queries (at search time). Using one pipeline for both is what makes a query
word and a document word land on the same index key.

Each token keeps:
  * term     - the index key (Porter stem of the normalised word)
  * surface  - the normalised word before stemming (used for "did you mean")
  * position - word position in the field, counting stop words too, so that
               phrase queries such as "terms of use" keep their gaps
  * start/end- character offsets in the original text (used for highlighting)
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .stemmer import stem

# A standard English stop-word list (function words that carry no topic).
STOP_WORDS = frozenset(
    """
    a about above after again against all am an and any are as at be because been before being below
    between both but by can could did do does doing down during each few for from further had has have
    having he her here hers herself him himself his how i if in into is it its itself just me more most
    my myself no nor not now of off on once only or other our ours ourselves out over own same she
    should so some such than that the their theirs them themselves then there these they this those
    through to too under until up very was we were what when where which while who whom why will with
    would you your yours yourself yourselves also may must shall within per via etc
    """.split()
)

# Word characters after normalisation. Apostrophes inside a word are kept so
# that "employee's" can be reduced to "employee" below.
_WORD_RE = re.compile(r"[a-z0-9]+(?:['’][a-z0-9]+)*")


@dataclass(frozen=True, slots=True)
class Token:
    term: str
    surface: str
    position: int
    start: int
    end: int


def _fold_char(ch: str) -> str:
    """Lower-case and strip accents from one character (é -> e, đ -> d)."""
    if ch in "đĐ":
        return "d"
    decomposed = unicodedata.normalize("NFKD", ch)
    base = "".join(c for c in decomposed if not unicodedata.combining(c))
    return base.lower() if len(base) == 1 else ch.lower()


def normalize(text: str) -> str:
    """Character-by-character folding that keeps offsets aligned with the input."""
    return "".join(_fold_char(c) for c in text)


def _clean(word: str) -> str:
    word = word.replace("’", "'")
    if word.endswith("'s"):
        word = word[:-2]
    return word.replace("'", "")


def analyze(text: str | None, keep_stop_words: bool = False) -> list[Token]:
    """Turn text into index tokens."""
    if not text:
        return []
    folded = normalize(text)
    tokens: list[Token] = []
    position = -1
    for m in _WORD_RE.finditer(folded):
        word = _clean(m.group())
        if not word:
            continue
        position += 1
        if not keep_stop_words and word in STOP_WORDS:
            continue
        if len(word) == 1 and not word.isdigit():
            continue  # stray letters, e.g. the "e" of "e-commerce"
        tokens.append(Token(term=stem(word), surface=word, position=position, start=m.start(), end=m.end()))
    return tokens


def terms(text: str | None) -> list[str]:
    """Convenience: just the index keys, in order."""
    return [t.term for t in analyze(text)]
