import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../auth'
import Notice from '../../components/Notice'
import { formatDate, timeAgo, useTitle } from '../../util'

function ReportQueue({ onMsg, onErr }) {
  const [status, setStatus] = useState('open')
  const [items, setItems] = useState(null)
  const [notes, setNotes] = useState({})
  const load = () => api('/moderation/reports', { params: { status } }).then(setItems).catch((e) => onErr(e.message))
  useEffect(() => { load() }, [status]) // eslint-disable-line react-hooks/exhaustive-deps

  const handle = async (r, s, hide) => {
    try {
      await api(`/moderation/reports/${r.id}`, { method: 'PATCH', body: { status: s, note: notes[r.id] || '', hide_target: hide } })
      onMsg(`Report ${s}${hide ? ` and ${r.target_type === 'comment' ? 'comment hidden' : 'document unpublished'}` : ''}.`)
      load()
    } catch (e) { onErr(e.message) }
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Reports</h2>
        <div className="segmented" role="group" aria-label="Report status">
          {['open', 'resolved', 'dismissed', 'all'].map((s) => (
            <button key={s} className={status === s ? 'on' : ''} aria-pressed={status === s} onClick={() => setStatus(s)}>{s[0].toUpperCase() + s.slice(1)}</button>
          ))}
        </div>
      </div>
      {!items ? <p className="muted">Loading…</p> : items.length === 0 ? <p className="muted">No {status !== 'all' ? status : ''} reports.</p> : (
        <ul className="mod-list">
          {items.map((r) => (
            <li key={r.id} className="report">
              <div className="mod-head">
                <span className="badge">{r.target_type}</span>
                {r.target_link ? <Link to={r.target_link}>{r.target_preview}</Link> : <span>{r.target_preview}</span>}
              </div>
              <p><strong>Reason:</strong> {r.reason}</p>
              <p className="muted small">Reported by @{r.reporter?.username || 'deleted user'} {timeAgo(r.created_at)}</p>
              {r.status === 'open' ? (
                <>
                  <label htmlFor={`note-${r.id}`} className="sr-only">Resolution note</label>
                  <input id={`note-${r.id}`} placeholder="Note for the record (optional)" value={notes[r.id] || ''}
                    onChange={(e) => setNotes({ ...notes, [r.id]: e.target.value })} />
                  <div className="row">
                    <button className="btn btn-ink" onClick={() => handle(r, 'resolved', true)}>
                      {r.target_type === 'comment' ? 'Hide comment and resolve' : 'Unpublish and resolve'}
                    </button>
                    <button className="btn btn-ghost" onClick={() => handle(r, 'resolved', false)}>Resolve without action</button>
                    <button className="btn btn-ghost" onClick={() => handle(r, 'dismissed', false)}>Dismiss</button>
                  </div>
                </>
              ) : (
                <p className="small"><span className={`status status-${r.status}`}>{r.status}</span> by @{r.handled_by?.username} on {formatDate(r.handled_at)}
                  {r.resolution_note && <> — {r.resolution_note}</>}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function SpamFilter({ onMsg, onErr }) {
  const [items, setItems] = useState([])
  const [kw, setKw] = useState('')
  const load = () => api('/moderation/spam-keywords').then(setItems).catch((e) => onErr(e.message))
  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps
  const add = async (e) => {
    e.preventDefault()
    try { await api('/moderation/spam-keywords', { method: 'POST', body: { keyword: kw } }); setKw(''); onMsg('Keyword added to the spam filter.'); load() }
    catch (err) { onErr(err.message) }
  }
  const remove = async (k) => {
    try { await api(`/moderation/spam-keywords/${k.id}`, { method: 'DELETE' }); onMsg('Keyword removed.'); load() } catch (err) { onErr(err.message) }
  }
  return (
    <section className="panel">
      <h2>Spam filter</h2>
      <p className="muted small">New comments containing any of these phrases are held as spam instead of being published.</p>
      <form className="inline-form" onSubmit={add}>
        <div className="field grow"><label htmlFor="kw">Blocked phrase</label>
          <input id="kw" required minLength={2} maxLength={100} value={kw} onChange={(e) => setKw(e.target.value)} /></div>
        <button className="btn btn-ink">Add phrase</button>
      </form>
      <ul className="tag-admin">
        {items.map((k) => (
          <li key={k.id}><span>{k.keyword}</span><button className="link-btn danger" onClick={() => remove(k)}>Remove</button></li>
        ))}
      </ul>
    </section>
  )
}

export default function Reports() {
  useTitle('Reports & spam')
  const { can } = useAuth()
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  const onMsg = (m) => { setErr(null); setMsg(m) }
  const onErr = (m) => { setMsg(null); setErr(m) }
  return (
    <div className="stack">
      <h1>Reports & spam</h1>
      <Notice kind="success" onClose={() => setMsg(null)}>{msg}</Notice>
      <Notice onClose={() => setErr(null)}>{err}</Notice>
      {can('reports.manage') && <ReportQueue onMsg={onMsg} onErr={onErr} />}
      {can('spam.manage') && <SpamFilter onMsg={onMsg} onErr={onErr} />}
    </div>
  )
}
