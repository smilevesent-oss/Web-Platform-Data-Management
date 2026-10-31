import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import Notice from '../../components/Notice'
import { nf, useTitle } from '../../util'

// Fill missing days so the chart has a continuous x axis.
function fillDays(rows, days, keys) {
  const map = Object.fromEntries(rows.map((r) => [r.date, r]))
  const out = []
  const today = new Date()
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today); d.setUTCDate(d.getUTCDate() - i)
    const iso = d.toISOString().slice(0, 10)
    out.push({ date: iso, ...Object.fromEntries(keys.map((k) => [k, map[iso]?.[k] || 0])) })
  }
  return out
}

function BarChart({ rows, series, label }) {
  const max = Math.max(1, ...rows.flatMap((r) => series.map((s) => r[s.key])))
  const w = 100 / rows.length
  return (
    <figure className="chart">
      <svg viewBox="0 0 100 40" preserveAspectRatio="none" role="img" aria-label={label}>
        {[0.25, 0.5, 0.75].map((g) => <line key={g} x1="0" x2="100" y1={40 - g * 38} y2={40 - g * 38} className="grid" />)}
        {rows.map((r, i) =>
          series.map((s, j) => {
            const h = (r[s.key] / max) * 38
            const bw = (w * 0.8) / series.length
            return (
              <rect key={`${r.date}-${s.key}`} x={i * w + w * 0.1 + j * bw} y={40 - h} width={Math.max(bw - 0.15, 0.2)} height={h}
                className={`bar bar-${j}`}><title>{`${r.date}: ${r[s.key]} ${s.name}`}</title></rect>
            )
          })
        )}
      </svg>
      <figcaption>
        <span className="muted small">{rows[0]?.date}</span>
        <span className="legend">{series.map((s, j) => <span key={s.key}><i className={`swatch bar-${j}`} />{s.name}</span>)}</span>
        <span className="muted small">{rows[rows.length - 1]?.date}</span>
      </figcaption>
      <p className="muted small">Peak: {nf(max)} per day</p>
    </figure>
  )
}

export default function Analytics() {
  useTitle('Analytics')
  const [days, setDays] = useState(30)
  const [a, setA] = useState(null)
  const [err, setErr] = useState(null)
  useEffect(() => { setA(null); api('/analytics/summary', { params: { days } }).then(setA).catch((e) => setErr(e.message)) }, [days])

  const t = a?.totals
  const maxCat = a ? Math.max(1, ...a.by_category.map((c) => c.views)) : 1

  return (
    <div className="analytics">
      <div className="page-head">
        <h1>Analytics</h1>
        <div className="segmented" role="group" aria-label="Period">
          {[7, 30, 90].map((d) => <button key={d} className={days === d ? 'on' : ''} aria-pressed={days === d} onClick={() => setDays(d)}>Last {d} days</button>)}
        </div>
      </div>
      <Notice>{err}</Notice>
      {!a ? <p className="muted">Loading…</p> : (
        <>
          <dl className="kpis">
            <div><dt>Document views</dt><dd>{nf(t.views_in_period)}</dd></div>
            <div><dt>Searches</dt><dd>{nf(t.searches_in_period)}</dd></div>
            <div><dt>Search click-through</dt><dd>{t.search_ctr != null ? `${Math.round(t.search_ctr * 100)}%` : '—'}</dd></div>
            <div><dt>Average clicked position</dt><dd>{t.avg_click_rank ?? '—'}</dd></div>
            <div><dt>Published documents</dt><dd>{nf(t.published)} <small className="muted">of {nf(t.documents)}</small></dd></div>
            <div><dt>Comments · likes</dt><dd>{nf(t.comments)} · {nf(t.likes)}</dd></div>
          </dl>

          <div className="grid-2">
            <section className="panel">
              <h2>Views per day</h2>
              <BarChart rows={fillDays(a.views_by_day, days, ['views'])} series={[{ key: 'views', name: 'views' }]} label="Document views per day" />
            </section>
            <section className="panel">
              <h2>Searches and clicks per day</h2>
              <BarChart rows={fillDays(a.searches_by_day, days, ['searches', 'clicks'])}
                series={[{ key: 'searches', name: 'searches' }, { key: 'clicks', name: 'clicks' }]} label="Searches and result clicks per day" />
            </section>
          </div>

          <div className="grid-2">
            <section className="panel">
              <h2>Top queries</h2>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Query</th><th className="num">Searches</th><th className="num">Clicks</th><th className="num">CTR</th><th className="num">Avg results</th></tr></thead>
                  <tbody>
                    {a.top_queries.map((q) => (
                      <tr key={q.query}>
                        <td><Link to={`/?q=${encodeURIComponent(q.query)}`}>{q.query}</Link></td>
                        <td className="num">{q.searches}</td><td className="num">{q.clicks}</td>
                        <td className="num">{q.ctr != null ? `${Math.round(q.ctr * 100)}%` : '—'}</td>
                        <td className="num">{q.avg_results ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
            <section className="panel">
              <h2>Searches with no results</h2>
              <p className="muted small">Content gaps: people looked for these and found nothing.</p>
              {a.zero_result_queries.length === 0 ? <p className="muted">None in this period.</p> : (
                <ul className="plain-list">{a.zero_result_queries.map((z) => <li key={z.query}><span>{z.query}</span><span className="muted">{z.count}×</span></li>)}</ul>
              )}
            </section>
          </div>

          <div className="grid-2">
            <section className="panel">
              <h2>Most viewed documents</h2>
              <ol className="plain-list">
                {a.top_documents.map((d) => <li key={d.id}><Link to={`/documents/${d.slug}`}>{d.title}</Link><span className="muted">{nf(d.views)}</span></li>)}
              </ol>
            </section>
            <section className="panel">
              <h2>Views by collection</h2>
              <ul className="hbars">
                {a.by_category.map((c) => (
                  <li key={c.category}>
                    <span className="hbar-label">{c.category} <span className="muted">({c.documents})</span></span>
                    <span className="hbar"><span style={{ width: `${(c.views / maxCat) * 100}%` }} /></span>
                    <span className="num">{nf(c.views)}</span>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </>
      )}
    </div>
  )
}
