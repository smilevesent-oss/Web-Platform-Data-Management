import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import Notice from '../../components/Notice'
import { formatDate, nf, useTitle } from '../../util'

const TABS = [
  { key: 'overview', label: 'Index & ranking' },
  { key: 'explain', label: 'Explain a query' },
  { key: 'inspect', label: 'Inspect terms' },
  { key: 'evaluate', label: 'Evaluation' },
]
const METRICS = [
  ['p@5', 'P@5', 'Share of the top 5 results that are relevant'],
  ['r@10', 'R@10', 'Share of all relevant documents found in the top 10'],
  ['map', 'MAP', 'Mean average precision'],
  ['mrr', 'MRR', '1 / rank of the first relevant result'],
  ['ndcg@10', 'nDCG@10', 'Graded relevance, discounted by rank, vs. the ideal ordering'],
]
const SYSTEM_LABEL = { like: 'Exact words (LIKE)', tfidf: 'TF-IDF', bm25: 'BM25' }
const fmt = (v, d = 3) => (v == null ? '—' : Number(v).toFixed(d))

export default function SearchEngine() {
  useTitle('Search engine')
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') || 'overview'
  const [err, setErr] = useState(null)
  return (
    <div className="search-engine">
      <div className="page-head">
        <h1>Search engine</h1>
        <div className="segmented" role="tablist" aria-label="Sections">
          {TABS.map((t) => (
            <button key={t.key} role="tab" aria-selected={tab === t.key} className={tab === t.key ? 'on' : ''}
              onClick={() => { setErr(null); setParams({ tab: t.key }) }}>{t.label}</button>
          ))}
        </div>
      </div>
      <Notice onClose={() => setErr(null)}>{err}</Notice>
      {tab === 'overview' && <Overview onErr={setErr} />}
      {tab === 'explain' && <Explain onErr={setErr} initial={params.get('q') || ''} />}
      {tab === 'inspect' && <Inspect onErr={setErr} />}
      {tab === 'evaluate' && <Evaluate onErr={setErr} />}
    </div>
  )
}

// ------------------------------------------------------------- overview ---

function Overview({ onErr }) {
  const [s, setS] = useState(null)
  const [cfg, setCfg] = useState(null)
  const [msg, setMsg] = useState(null)
  const [busy, setBusy] = useState(false)
  const load = () => api('/admin/search/stats').then((d) => { setS(d); setCfg(d.config) }).catch((e) => onErr(e.message))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load() }, [])

  const save = async (e) => {
    e.preventDefault()
    try {
      const c = await api('/admin/search/config', { method: 'PUT', body: { algorithm: cfg.algorithm, k1: Number(cfg.k1), b: Number(cfg.b) } })
      setCfg(c); setS((x) => ({ ...x, config: c })); setMsg('Ranking settings saved. New searches use them immediately.')
    } catch (e2) { onErr(e2.message) }
  }
  const rebuild = async () => {
    setBusy(true)
    try { await api('/admin/search/rebuild', { method: 'POST' }); await load(); setMsg('Index rebuilt from the published documents.') } catch (e) { onErr(e.message) }
    setBusy(false)
  }

  if (!s) return <p className="muted">Loading…</p>
  const dirty = cfg && (cfg.algorithm !== s.config.algorithm || Number(cfg.k1) !== s.config.k1 || Number(cfg.b) !== s.config.b)
  return (
    <>
      <Notice kind="success" onClose={() => setMsg(null)}>{msg}</Notice>
      <dl className="kpis">
        <div><dt>Indexed documents</dt><dd>{nf(s.documents)}</dd></div>
        <div><dt>Vocabulary (stems)</dt><dd>{nf(s.vocabulary)}</dd></div>
        <div><dt>Postings</dt><dd>{nf(s.postings)}</dd></div>
        <div><dt>Indexed tokens</dt><dd>{nf(s.tokens)}</dd></div>
        <div><dt>Last build</dt><dd>{fmt(s.build_ms, 1)} <small className="muted">ms</small></dd></div>
        <div><dt>Builds since start</dt><dd>{nf(s.rebuilds)}</dd></div>
      </dl>

      <div className="grid-2">
        <section className="panel">
          <h2>Ranking settings</h2>
          <form onSubmit={save} className="stack">
            <fieldset className="field">
              <legend>Default algorithm for site search</legend>
              <div className="segmented" role="radiogroup">
                {['bm25', 'tfidf', 'like'].map((a) => (
                  <button type="button" key={a} role="radio" aria-checked={cfg.algorithm === a}
                    className={cfg.algorithm === a ? 'on' : ''} onClick={() => setCfg({ ...cfg, algorithm: a })}>{SYSTEM_LABEL[a]}</button>
                ))}
              </div>
            </fieldset>
            <div className="field">
              <label htmlFor="k1">BM25 k1 <span className="muted small">— term-frequency saturation ({cfg.k1})</span></label>
              <input id="k1" type="range" min="0" max="3" step="0.1" value={cfg.k1} onChange={(e) => setCfg({ ...cfg, k1: e.target.value })} />
            </div>
            <div className="field">
              <label htmlFor="b">BM25 b <span className="muted small">— length normalisation ({cfg.b})</span></label>
              <input id="b" type="range" min="0" max="1" step="0.05" value={cfg.b} onChange={(e) => setCfg({ ...cfg, b: e.target.value })} />
            </div>
            <div className="row">
              <button className="btn btn-ink" disabled={!dirty}>Save settings</button>
              <button type="button" className="btn btn-ghost" disabled={busy} onClick={rebuild}>{busy ? 'Rebuilding…' : 'Rebuild index'}</button>
            </div>
            <p className="muted small">
              The index rebuilds itself automatically whenever a published document changes; the button forces a rebuild.
              Last built {s.built_at ? formatDate(new Date(s.built_at * 1000).toISOString(), true) : '—'}.
            </p>
          </form>
        </section>

        <section className="panel">
          <h2>Field weights</h2>
          <p className="muted small">A match in the title counts more than one in the body. Average field length is used for BM25 length normalisation.</p>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Field</th><th className="num">Weight</th><th className="num">Avg. length (tokens)</th></tr></thead>
              <tbody>
                {Object.entries(s.config.field_weights).map(([f, w]) => (
                  <tr key={f}><td>{f}</td><td className="num">{w}</td><td className="num">{s.avg_field_length[f]}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <section className="panel">
        <h2>Most common terms</h2>
        <p className="muted small">High document frequency means low IDF: these words say little about which document is relevant.</p>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Stem</th><th>Words</th><th className="num">Documents (df)</th><th className="num">BM25 IDF</th></tr></thead>
            <tbody>
              {s.top_terms.map((t) => (
                <tr key={t.term}><td><code>{t.term}</code></td><td className="muted">{t.words.join(', ')}</td>
                  <td className="num">{t.df}</td><td className="num">{fmt(t.idf)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

// -------------------------------------------------------------- explain ---

function Explain({ onErr, initial }) {
  const [q, setQ] = useState(initial || 'annual leave carry over')
  const [algo, setAlgo] = useState('bm25')
  const [res, setRes] = useState(null)
  const run = async (e, a = algo) => {
    e?.preventDefault()
    if (!q.trim()) return
    try { setRes(await api('/admin/search/explain', { params: { q, algo: a } })) } catch (e2) { onErr(e2.message) }
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { run() }, [])
  const terms = res?.term_stats || []
  const max = res?.results[0]?.score || 1

  return (
    <>
      <form className="toolbar" onSubmit={run}>
        <label htmlFor="ex-q" className="sr-only">Query</label>
        <input id="ex-q" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder='e.g. "data protection" -impact' />
        <div className="segmented" role="group" aria-label="Algorithm">
          {['bm25', 'tfidf'].map((a) => (
            <button type="button" key={a} className={algo === a ? 'on' : ''} aria-pressed={algo === a}
              onClick={() => { setAlgo(a); run(null, a) }}>{SYSTEM_LABEL[a]}</button>
          ))}
        </div>
        <button className="btn btn-ink">Explain</button>
      </form>
      {res && (
        <>
          <section className="panel">
            <h2>How the query was understood</h2>
            <div className="chips">
              {res.parsed.terms.map((t, i) => (
                <span key={i} className="chip" title={`origin: ${t.origin}, weight ${t.weight}`}>
                  {t.word} → <code>{t.term}</code>{t.origin !== 'word' && <small className="muted"> {t.origin}</small>}
                </span>
              ))}
              {res.parsed.phrases.map((p) => <span key={p} className="chip chip-phrase">phrase: “{p}”</span>)}
              {res.parsed.excluded.map((x) => <span key={x} className="chip chip-out">excluded: {x}</span>)}
            </div>
            {res.parsed.unknown.length > 0 && <p className="muted small">Not in the index: {res.parsed.unknown.join(', ')}</p>}
            {res.suggestion && <p className="small">Did you mean <strong>{res.suggestion}</strong>?</p>}
            <p className="muted small">{nf(res.total)} matching documents · {res.took_ms} ms</p>
          </section>
          <section className="panel">
            <h2>Score breakdown (top {res.results.length})</h2>
            <p className="muted small">
              {res.algorithm === 'bm25'
                ? 'BM25F: each cell is idf(t) · tf~(k1+1) / (k1 + tf~), where tf~ sums field-weighted, length-normalised term counts.'
                : 'TF-IDF: each cell is the term’s share of the cosine similarity between query and document vectors.'}
            </p>
            <div className="table-wrap">
              <table className="explain-table">
                <thead>
                  <tr><th className="num">#</th><th>Document</th>
                    {terms.map((t) => <th key={t.term} className="num" title={`df ${t.df}, idf ${t.idf}`}><code>{t.term}</code><br /><small className="muted">idf {fmt(t.idf, 2)}</small></th>)}
                    <th className="num">Score</th></tr>
                </thead>
                <tbody>
                  {res.results.map((r) => (
                    <tr key={r.doc_id}>
                      <td className="num">{r.rank}</td>
                      <td><Link to={`/documents/${r.doc_id}`}>{r.title}</Link>
                        <span className="score-bar"><span style={{ width: `${(r.score / max) * 100}%` }} /></span></td>
                      {terms.map((t) => <td key={t.term} className={`num ${r.contributions[t.term] ? '' : 'muted'}`}>{r.contributions[t.term] ? fmt(r.contributions[t.term]) : '·'}</td>)}
                      <td className="num"><strong>{fmt(r.score)}</strong></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </>
  )
}

// -------------------------------------------------------------- inspect ---

function Inspect({ onErr }) {
  const [text, setText] = useState("The employee's remote-work policies were updated.")
  const [tokens, setTokens] = useState(null)
  const [word, setWord] = useState('policies')
  const [term, setTerm] = useState(null)
  const analyze = (e) => { e?.preventDefault(); api('/admin/search/analyze', { params: { text } }).then((d) => setTokens(d.tokens)).catch((x) => onErr(x.message)) }
  const lookup = (e) => { e?.preventDefault(); api('/admin/search/term', { params: { word } }).then(setTerm).catch((x) => onErr(x.message)) }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { analyze(); lookup() }, [])

  return (
    <div className="grid-2">
      <section className="panel">
        <h2>Analyser</h2>
        <p className="muted small">Normalise (lower-case, strip accents) → split into words → drop stop words → Porter stemming.</p>
        <form onSubmit={analyze} className="stack">
          <label htmlFor="an-text" className="sr-only">Text</label>
          <textarea id="an-text" rows={3} value={text} onChange={(e) => setText(e.target.value)} />
          <div><button className="btn btn-ink">Analyse</button></div>
        </form>
        {tokens && (
          <div className="table-wrap">
            <table>
              <thead><tr><th className="num">Pos</th><th>Original</th><th>Normalised</th><th>Index term</th></tr></thead>
              <tbody>
                {tokens.map((t, i) => (
                  <tr key={i} className={t.removed ? 'muted' : ''}>
                    <td className="num">{t.position}</td><td>{t.original}</td><td>{t.normalised}</td>
                    <td>{t.term ? <code>{t.term}</code> : <small>{t.removed}</small>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel">
        <h2>Postings list</h2>
        <p className="muted small">Which documents contain a term, in which fields, and at which word positions.</p>
        <form onSubmit={lookup} className="row">
          <label htmlFor="term-word" className="sr-only">Word</label>
          <input id="term-word" value={word} onChange={(e) => setWord(e.target.value)} />
          <button className="btn btn-ink">Look up</button>
        </form>
        {term && (term.term ? (
          <>
            <p className="small">
              <code>{term.term}</code> · df {term.df} · BM25 idf {fmt(term.idf_bm25)} · TF-IDF idf {fmt(term.idf_tfidf)}
              {term.words.length > 0 && <span className="muted"> · forms: {term.words.join(', ')}</span>}
            </p>
            {term.postings.length === 0 ? <p className="muted">Not in any published document.</p> : (
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Document</th><th className="num">tf</th><th>Positions by field</th></tr></thead>
                  <tbody>
                    {term.postings.map((p) => (
                      <tr key={p.doc_id}>
                        <td><Link to={`/documents/${p.doc_id}`}>{p.title}</Link></td>
                        <td className="num">{p.tf}</td>
                        <td className="small">{Object.entries(p.fields).map(([f, pos]) => <div key={f}><strong>{f}</strong> {pos.join(', ')}</div>)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        ) : <p className="muted">{term.note}</p>)}
      </section>
    </div>
  )
}

// ------------------------------------------------------------- evaluate ---

function Evaluate({ onErr }) {
  const [res, setRes] = useState(null)
  const [grid, setGrid] = useState(null)
  const [busy, setBusy] = useState(false)
  useEffect(() => { api('/admin/search/evaluate').then(setRes).catch((e) => onErr(e.message)) }, [onErr])
  const tune = async () => {
    setBusy(true)
    try { setGrid((await api('/admin/search/evaluate/tune')).grid) } catch (e) { onErr(e.message) }
    setBusy(false)
  }
  if (!res) return <p className="muted">Running evaluation…</p>
  const systems = Object.keys(res.summary)
  const best = Object.fromEntries(METRICS.map(([k]) => [k, Math.max(...systems.map((s) => res.summary[s][k]))]))

  return (
    <>
      <section className="panel">
        <h2>Ranking quality on {res.queries} judged queries</h2>
        <p className="muted small">
          Relevance judgements live in <code>backend/app/search/qrels.json</code> (2 = the answer, 1 = useful).
          Run the same comparison from the command line with <code>python -m app.search.evaluate</code>.
        </p>
        <div className="table-wrap">
          <table>
            <thead><tr><th>System</th>{METRICS.map(([k, l, h]) => <th key={k} className="num" title={h}>{l}</th>)}<th className="num">Queries with 0 results</th></tr></thead>
            <tbody>
              {systems.map((s) => (
                <tr key={s}>
                  <td>{SYSTEM_LABEL[s] || s}</td>
                  {METRICS.map(([k]) => <td key={k} className="num">{res.summary[s][k] === best[k] ? <strong>{fmt(res.summary[s][k])}</strong> : fmt(res.summary[s][k])}</td>)}
                  <td className="num">{res.summary[s].zero_result_queries}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {res.missing_titles.length > 0 && <Notice kind="warn">Titles in qrels.json not found: {res.missing_titles.join('; ')}</Notice>}
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>BM25 parameter search</h2>
          <button className="btn btn-ghost" disabled={busy} onClick={tune}>{busy ? 'Running…' : 'Try k1 × b grid'}</button>
        </div>
        {!grid ? <p className="muted small">Scores 20 combinations of k1 and b on the judged queries.</p> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th className="num">k1</th><th className="num">b</th>{METRICS.map(([k, l]) => <th key={k} className="num">{l}</th>)}</tr></thead>
              <tbody>
                {grid.slice(0, 10).map((g) => (
                  <tr key={`${g.k1}-${g.b}`}><td className="num">{g.k1}</td><td className="num">{g.b}</td>
                    {METRICS.map(([k]) => <td key={k} className="num">{fmt(g[k])}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel">
        <h2>Per query (nDCG@10 · rank of first relevant result)</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Query</th>{systems.map((s) => <th key={s} className="num">{SYSTEM_LABEL[s] || s}</th>)}</tr></thead>
            <tbody>
              {res.per_query.map((r) => (
                <tr key={r.query}>
                  <td><Link to={`?tab=explain&q=${encodeURIComponent(r.query)}`}>{r.query}</Link></td>
                  {systems.map((s) => {
                    const m = r.systems[s]
                    return <td key={s} className={`num ${m['ndcg@10'] === 0 ? 'danger' : ''}`}>
                      {fmt(m['ndcg@10'], 2)} <small className="muted">· {m.first_relevant_rank ?? '—'}</small></td>
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}
