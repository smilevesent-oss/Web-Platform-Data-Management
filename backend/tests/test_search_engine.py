"""Unit tests for the Phase-2 search engine (no database needed)."""
import math

import pytest

from app.search.evaluation import average_precision, ndcg_at, precision_at, reciprocal_rank
from app.search.index import InvertedIndex
from app.search.query import parse_query
from app.search.ranking import bm25_scores, tfidf_scores
from app.search.stemmer import stem
from app.search.tokenizer import analyze, terms


@pytest.mark.parametrize("word,expected", [
    ("caresses", "caress"), ("ponies", "poni"), ("cats", "cat"), ("agreed", "agre"),
    ("plastered", "plaster"), ("motoring", "motor"), ("hopping", "hop"), ("happy", "happi"),
    ("relational", "relat"), ("conditional", "condit"), ("electrical", "electr"),
    ("generalizations", "gener"), ("policies", "polici"), ("policy", "polici"),
])
def test_porter_stemmer(word, expected):
    assert stem(word) == expected


def test_tokenizer_pipeline():
    toks = analyze("The Employee's NEW policies, café-style!")
    assert [t.term for t in toks] == ["employe", "new", "polici", "cafe", "style"]
    assert [t.surface for t in toks] == ["employee", "new", "policies", "cafe", "style"]
    # positions count stop words ("the" is position 0) so phrases keep their gaps
    assert toks[0].position == 1
    # offsets point back into the original text for highlighting
    text = "Data PROTECTION officer"
    t = analyze(text)[1]
    assert text[t.start:t.end] == "PROTECTION"


def test_accents_are_folded():
    assert terms("Thanh toán điện tử") == terms("thanh toan dien tu")


CORPUS = [
    {"id": 1, "title": "Annual leave policy", "content": "Employees accrue annual leave every month. Leave carries over."},
    {"id": 2, "title": "Parental leave", "content": "Parents receive paid leave after the birth of a child."},
    {"id": 3, "title": "Password standard", "content": "Use a password manager and multi factor authentication."},
    {"id": 4, "title": "Travel expenses", "content": "Book flights early. Keep every receipt for expense claims."},
]


@pytest.fixture(scope="module")
def idx():
    return InvertedIndex.build(CORPUS)


def test_index_statistics(idx):
    assert idx.n_docs == 4
    assert idx.df("leav") == 2
    assert idx.tf("leav", 1, "content") == 2
    assert idx.tf("leav", 1, "title") == 1
    assert idx.idf_classic("leav") == pytest.approx(math.log(4 / 2))
    assert idx.idf_bm25("leav") == pytest.approx(math.log(1 + (4 - 2 + 0.5) / (2 + 0.5)))


def test_bm25_matches_hand_calculation(idx):
    # Single field, unit weight: reduce to textbook BM25 on the content field only.
    weights = {"title": 0, "tags": 0, "summary": 0, "content": 1, "author": 0}
    scores, _ = bm25_scores(idx, {"receipt": 1.0}, k1=1.2, b=0.75, field_weights=weights)
    d = idx.docs[4]
    tf, dl, avg = 1, d.lengths["content"], idx.avg_field_len["content"]
    idf = math.log(1 + (4 - 1 + 0.5) / (1 + 0.5))
    tf_n = tf / (1 - 0.75 + 0.75 * dl / avg)
    assert scores[4] == pytest.approx(idf * tf_n * 2.2 / (1.2 + tf_n))
    assert set(scores) == {4}


def test_bm25_ranks_more_specific_document_first(idx):
    scores, _ = bm25_scores(idx, {"annual": 1.0, "leav": 1.0})
    assert max(scores, key=scores.get) == 1
    assert scores[1] > scores[2] > 0


def test_tfidf_is_cosine_between_0_and_1(idx):
    scores, _ = tfidf_scores(idx, {"password": 1.0, "manag": 1.0})
    assert max(scores, key=scores.get) == 3
    assert all(0 < s <= 1 for s in scores.values())


def test_query_language(idx):
    pq = parse_query('"paid leave" -annual pass*', idx)
    assert [ [t.surface for t in ph] for ph in pq.phrases] == [["paid", "leave"]]
    assert pq.excluded == {"annual"}
    assert any(t.origin == "prefix" and t.surface == "password" for t in pq.terms)
    assert idx.phrase_match(2, pq.phrases[0])
    assert not idx.phrase_match(1, pq.phrases[0])


def test_metrics():
    rel = {1: 2, 2: 1}
    assert precision_at([1, 3, 2, 4, 5], rel, 5) == pytest.approx(0.4)
    assert reciprocal_rank([3, 1], rel) == 0.5
    assert average_precision([1, 3, 2], rel) == pytest.approx((1 / 1 + 2 / 3) / 2)
    assert ndcg_at([1, 2], rel, 10) == pytest.approx(1.0)
    assert ndcg_at([2, 1], rel, 10) < 1.0
