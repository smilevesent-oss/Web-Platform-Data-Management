import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import Notice from '../../components/Notice'
import Pagination from '../../components/Pagination'
import { formatDate, nf, useDebounced, useTitle } from '../../util'

export default function SearchLogs() {
  useTitle('Search & click log')
  const [q, setQ] = useState('')
  const dq = useDebounced(q)
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    api('/analytics/search-logs', { params: { q: dq, event_type: type, page, page_size: 50 } }).then(setData).catch((e) => setErr(e.message))
  }, [dq, type, page])

  const download = async () => {
    try {
      const res = await api('/analytics/search-logs.csv', { raw: true })
      if (!res.ok) throw new Error(`Export failed (${res.status})`)
      const url = URL.createObjectURL(await res.blob())
      const a = document.createElement('a'); a.href = url; a.download = 'search_logs.csv'; a.click()
      URL.revokeObjectURL(url)
    } catch (e) { setErr(e.message) }
  }

  return (
    <div>
      <div className="page-head">
        <h1>Search & click log</h1>
        <button className="btn btn-ghost" onClick={download}>Download CSV</button>
      </div>
      <p className="muted">Every executed search and every click on a result. This is the training and evaluation data for ranked search in Phase 2.</p>
      <Notice onClose={() => setErr(null)}>{err}</Notice>
      <div className="toolbar">
        <label htmlFor="sl-q" className="sr-only">Filter by query</label>
        <input id="sl-q" type="search" placeholder="Filter by query" value={q} onChange={(e) => { setQ(e.target.value); setPage(1) }} />
        <div className="segmented" role="group" aria-label="Event type">
          {[['', 'All events'], ['search', 'Searches'], ['click', 'Clicks']].map(([v, l]) => (
            <button key={v} className={type === v ? 'on' : ''} aria-pressed={type === v} onClick={() => { setType(v); setPage(1) }}>{l}</button>
          ))}
        </div>
        {data && <span className="muted">{nf(data.total)} events</span>}
      </div>
      {!data ? <p className="muted">Loading…</p> : (
        <div className="table-wrap">
          <table className="compact">
            <thead><tr><th>Time</th><th>Event</th><th>Query</th><th className="num">Results</th><th>Clicked document</th><th className="num">Position</th><th>User</th><th>Session</th></tr></thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.id}>
                  <td>{formatDate(r.timestamp, true)}</td>
                  <td><span className={`status status-${r.event_type}`}>{r.event_type}</span></td>
                  <td>{r.query_string}</td>
                  <td className="num">{r.results_count ?? ''}</td>
                  <td>{r.clicked_doc_id ? <Link to={`/documents/${r.clicked_doc_id}`}>#{r.clicked_doc_id}</Link> : ''}</td>
                  <td className="num">{r.rank_position ?? ''}</td>
                  <td>{r.user_id ?? <span className="muted">guest</span>}</td>
                  <td className="muted small">{r.session_id?.slice(0, 8)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && <Pagination page={data.page} pages={data.pages} onChange={setPage} />}
    </div>
  )
}
