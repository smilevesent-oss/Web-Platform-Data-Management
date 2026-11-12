"""Phase 2 search engine: tokenisation, positional inverted index, TF-IDF and BM25F ranking.

Everything here is implemented from scratch (no Elasticsearch, no PostgreSQL
full-text search) so each step of the pipeline can be inspected and explained:

    tokenizer.py   normalise -> tokenise -> stop words -> Porter stemming
    stemmer.py     Porter (1980) suffix-stripping stemmer
    index.py       positional multi-field inverted index + collection statistics
    query.py       query language: words, "phrases", -exclusions, prefix*
    ranking.py     TF-IDF cosine and BM25F scoring
    engine.py      index lifecycle, search, snippets, did-you-mean
    evaluation.py  P@k, recall, MAP, MRR, nDCG against judged queries (qrels.json)
"""
from .engine import ALGORITHMS, Params, SearchEngine, engine  # noqa: F401
