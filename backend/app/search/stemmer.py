"""Porter stemmer (M. F. Porter, "An algorithm for suffix stripping", 1980).

Implemented from the original paper so that the whole Phase-2 pipeline is
transparent and has no NLP library dependency. Stemming maps inflected forms
to a shared stem so that "policies", "policy" and "policy's" match:

    >>> stem("policies"), stem("connected"), stem("relational")
    ('polici', 'connect', 'relat')

A stem is an index key, not a word: it does not need to be a dictionary form.
"""
from __future__ import annotations

from functools import lru_cache

_VOWELS = frozenset("aeiou")


def _is_cons(w: str, i: int) -> bool:
    ch = w[i]
    if ch in _VOWELS:
        return False
    if ch == "y":
        return i == 0 or not _is_cons(w, i - 1)
    return True


def _measure(stem: str) -> int:
    """m in the paper: number of VC sequences in [C](VC)^m[V]."""
    m = 0
    i, n = 0, len(stem)
    while i < n and _is_cons(stem, i):
        i += 1
    while i < n:
        while i < n and not _is_cons(stem, i):
            i += 1
        if i >= n:
            break
        while i < n and _is_cons(stem, i):
            i += 1
        m += 1
    return m


def _has_vowel(stem: str) -> bool:
    return any(not _is_cons(stem, i) for i in range(len(stem)))


def _ends_double_cons(w: str) -> bool:
    return len(w) >= 2 and w[-1] == w[-2] and _is_cons(w, len(w) - 1)


def _cvc(w: str) -> bool:
    """*o: stem ends cvc where the final c is not w, x or y."""
    if len(w) < 3:
        return False
    return (
        _is_cons(w, len(w) - 3)
        and not _is_cons(w, len(w) - 2)
        and _is_cons(w, len(w) - 1)
        and w[-1] not in "wxy"
    )


def _replace(w: str, suffix: str, repl: str, min_m: int) -> str | None:
    """If w ends with suffix and measure(stem) > min_m, swap the suffix.

    Returns the new word, or None when the suffix does not match (so callers
    can stop at the first matching rule, as the paper prescribes).
    """
    if not w.endswith(suffix):
        return None
    stem = w[: len(w) - len(suffix)]
    return stem + repl if _measure(stem) > min_m else w


def _step1a(w: str) -> str:
    if w.endswith("sses"):
        return w[:-2]
    if w.endswith("ies"):
        return w[:-2]
    if w.endswith("ss"):
        return w
    if w.endswith("s"):
        return w[:-1]
    return w


def _step1b(w: str) -> str:
    if w.endswith("eed"):
        stem = w[:-3]
        return w[:-1] if _measure(stem) > 0 else w
    for suffix in ("ed", "ing"):
        if w.endswith(suffix):
            stem = w[: -len(suffix)]
            if not _has_vowel(stem):
                return w
            w = stem
            if w.endswith(("at", "bl", "iz")):
                return w + "e"
            if _ends_double_cons(w) and w[-1] not in "lsz":
                return w[:-1]
            if _measure(w) == 1 and _cvc(w):
                return w + "e"
            return w
    return w


def _step1c(w: str) -> str:
    if w.endswith("y") and _has_vowel(w[:-1]):
        return w[:-1] + "i"
    return w


_STEP2 = (
    ("ational", "ate"), ("tional", "tion"), ("enci", "ence"), ("anci", "ance"), ("izer", "ize"),
    ("abli", "able"), ("alli", "al"), ("entli", "ent"), ("eli", "e"), ("ousli", "ous"),
    ("ization", "ize"), ("ation", "ate"), ("ator", "ate"), ("alism", "al"), ("iveness", "ive"),
    ("fulness", "ful"), ("ousness", "ous"), ("aliti", "al"), ("iviti", "ive"), ("biliti", "ble"),
)
_STEP3 = (
    ("icate", "ic"), ("ative", ""), ("alize", "al"), ("iciti", "ic"), ("ical", "ic"),
    ("ful", ""), ("ness", ""),
)
_STEP4 = (
    "al", "ance", "ence", "er", "ic", "able", "ible", "ant", "ement", "ment", "ent",
    "ion", "ou", "ism", "ate", "iti", "ous", "ive", "ize",
)


def _rules(w: str, rules, min_m: int) -> str:
    # The longest matching suffix wins; table order handles the paper's cases.
    for suffix, repl in sorted(rules, key=lambda r: -len(r[0])):
        out = _replace(w, suffix, repl, min_m)
        if out is not None:
            return out
    return w


def _step4(w: str) -> str:
    for suffix in sorted(_STEP4, key=len, reverse=True):
        if w.endswith(suffix):
            stem = w[: -len(suffix)]
            if suffix == "ion" and not (stem.endswith(("s", "t"))):
                return w
            return stem if _measure(stem) > 1 else w
    return w


def _step5(w: str) -> str:
    if w.endswith("e"):
        stem = w[:-1]
        m = _measure(stem)
        if m > 1 or (m == 1 and not _cvc(stem)):
            w = stem
    if _measure(w) > 1 and _ends_double_cons(w) and w.endswith("l"):
        w = w[:-1]
    return w


@lru_cache(maxsize=50_000)
def stem(word: str) -> str:
    """Return the Porter stem of a lower-case word. Words of <= 2 letters are kept."""
    if len(word) <= 2 or not word.isalpha():
        return word
    w = _step1a(word)
    w = _step1b(w)
    w = _step1c(w)
    w = _rules(w, _STEP2, 0)
    w = _rules(w, _STEP3, 0)
    w = _step4(w)
    w = _step5(w)
    return w
