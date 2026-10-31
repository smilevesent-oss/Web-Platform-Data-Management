import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import Notice from '../../components/Notice'
import Pagination from '../../components/Pagination'
import { nf, timeAgo, useTitle } from '../../util'

const TABS = [['pending', 'Awaiting approval'], ['reported', 'Reported'], ['spam', 'Spam'], ['hidden', 'Hidden'], ['visible', 'Visible'], ['', 'All']]

export default function Moderation() {
  useTitle('Comments')
  const [params, setParams] = useSearchParams()
  const status = params.get('status') ?? 'pending'
  const page = Number(params.get('page') || 1)
  const [data, setData] = useState(null)
  const [stats, setStats] = useState(null)
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)

  const load = () => {
    api('/moderation/comments', { params: { status, page } }).then(setData).catch((e) => setErr(e.message))
    api('/moderation/stats').then(setStats).catch(() => {})
  }
  useEffect(() => { load() }, [status, page]) // eslint-disable-line react-hooks/exhaustive-deps

  const setStatusTab = (s) => setParams({ status: s })
  const act = async (c, s) => {
    try { await api(`/moderation/comments/${c.id}`, { method: 'PATCH', body: { status: s } }); setMsg(`Comment by @${c.user.username} marked ${s}.`); load() }
    catch (e) { setErr(e.message) }
  }
  const remove = async (c) => {
    if (!window.confirm('Delete this comment and its replies permanently?')) return
    try { await api(`/moderation/comments/${c.id}`, { method: 'DELETE' }); setMsg('Comment deleted.'); load() } catch (e) { setErr(e.message) }
  }
  const count = (s) => (stats ? (s === 'reported' ? stats.open_reports : stats.comments[s]) : null)

  return (
    <div>
      <h1>Comments</h1>
      <Notice kind="success" onClose={() => setMsg(null)}>{msg}</Notice>
      <Notice onClose={() => setErr(null)}>{err}</Notice>
      <div className="segmented" role="group" aria-label="Filter comments">
        {TABS.map(([v, l]) => (
          <button key={v} className={status === v ? 'on' : ''} aria-pressed={status === v} onClick={() => setStatusTab(v)}>
            {l}{count(v) != null && v !== 'reported' ? ` (${nf(count(v))})` : ''}
          </button>
        ))}
      </div>

      {!data ? <p className="muted">Loading…</p> : data.items.length === 0 ? (
        <div className="empty"><h3>Nothing here</h3><p>No comments with this status.</p></div>
      ) : (
        <ul className="mod-list">
          {data.items.map((c) => (
            <li key={c.id} className="panel">
              <div className="mod-head">
                <strong>{c.user.full_name}</strong> <span className="muted">@{c.user.username}</span>
                <span className="muted">{timeAgo(c.created_at)} on</span>
                <Link to={`/documents/${c.document_id}#comment-${c.id}`}>{c.document_title}</Link>
                <span className={`status status-${c.status}`}>{c.status}</span>
                {c.report_count > 0 && <span className="badge badge-warn">{c.report_count} open report{c.report_count > 1 ? 's' : ''}</span>}
              </div>
              <p className="mod-body">{c.body}</p>
              <div className="row">
                {c.status !== 'visible' && <button className="btn btn-ink" onClick={() => act(c, 'visible')}>Approve</button>}
                {c.status !== 'hidden' && <button className="btn btn-ghost" onClick={() => act(c, 'hidden')}>Hide</button>}
                {c.status !== 'spam' && <button className="btn btn-ghost" onClick={() => act(c, 'spam')}>Mark as spam</button>}
                <button className="btn btn-ghost danger" onClick={() => remove(c)}>Delete</button>
              </div>
            </li>
          ))}
        </ul>
      )}
      {data && <Pagination page={data.page} pages={data.pages} onChange={(p) => setParams({ status, page: String(p) })} />}
    </div>
  )
}
