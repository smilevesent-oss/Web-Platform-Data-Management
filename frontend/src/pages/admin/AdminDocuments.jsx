import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../auth'
import Notice from '../../components/Notice'
import Pagination from '../../components/Pagination'
import { formatDate, nf, useDebounced, useTitle } from '../../util'

export default function AdminDocuments() {
  useTitle('Documents')
  const { can } = useAuth()
  const [params, setParams] = useSearchParams()
  const [q, setQ] = useState(params.get('q') || '')
  const dq = useDebounced(q)
  const status = params.get('status') || ''
  const page = Number(params.get('page') || 1)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [msg, setMsg] = useState(null)

  const load = () =>
    api('/admin/documents', { params: { q: dq, status, page, page_size: 20 } }).then(setData).catch((e) => setError(e.message))
  useEffect(() => { load() }, [dq, status, page]) // eslint-disable-line react-hooks/exhaustive-deps

  const setParam = (k, v) => { const n = new URLSearchParams(params); v ? n.set(k, v) : n.delete(k); if (k !== 'page') n.delete('page'); setParams(n) }

  const changeStatus = async (d, s) => {
    try {
      await api(`/admin/documents/${d.id}/status`, { method: 'PATCH', body: { status: s } })
      setMsg(`“${d.title}” is now ${s}.`); load()
    } catch (e) { setError(e.message) }
  }
  const remove = async (d) => {
    if (!window.confirm(`Delete “${d.title}” permanently? Comments, likes and ratings are deleted too.`)) return
    try { await api(`/admin/documents/${d.id}`, { method: 'DELETE' }); setMsg(`Deleted “${d.title}”.`); load() } catch (e) { setError(e.message) }
  }

  return (
    <div>
      <div className="page-head">
        <h1>Documents</h1>
        {can('documents.create') && <Link to="new" className="btn btn-ink">New document</Link>}
      </div>
      <Notice kind="success" onClose={() => setMsg(null)}>{msg}</Notice>
      <Notice onClose={() => setError(null)}>{error}</Notice>
      <div className="toolbar">
        <label htmlFor="ad-q" className="sr-only">Search titles and content</label>
        <input id="ad-q" type="search" placeholder="Search titles and content" value={q}
          onChange={(e) => { setQ(e.target.value); setParam('page', '') }} />
        <div className="segmented" role="group" aria-label="Status">
          {[['', 'All'], ['published', 'Published'], ['draft', 'Drafts'], ['archived', 'Archived']].map(([v, l]) => (
            <button key={v} aria-pressed={status === v} className={status === v ? 'on' : ''} onClick={() => setParam('status', v)}>{l}</button>
          ))}
        </div>
      </div>

      {!data ? <p className="muted">Loading…</p> : data.items.length === 0 ? <p className="empty">No documents found.</p> : (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Title</th><th>Status</th><th>Collection</th><th>Author</th><th>Updated</th><th className="num">Views</th><th><span className="sr-only">Actions</span></th></tr></thead>
            <tbody>
              {data.items.map((d) => (
                <tr key={d.id}>
                  <td>
                    {can('documents.update') ? <Link to={String(d.id)}>{d.title}</Link> : d.title}
                    <div className="muted small">{d.doc_type}</div>
                  </td>
                  <td><span className={`status status-${d.status}`}>{d.status}</span></td>
                  <td>{d.category?.name || '—'}</td>
                  <td>{d.author?.full_name || '—'}</td>
                  <td>{formatDate(d.updated_at)}</td>
                  <td className="num">{nf(d.views_count)}</td>
                  <td className="actions">
                    <Link to={`/documents/${d.slug}`} className="link-btn">View</Link>
                    {can('documents.publish') && (d.status === 'published'
                      ? <button className="link-btn" onClick={() => changeStatus(d, 'draft')}>Unpublish</button>
                      : <button className="link-btn" onClick={() => changeStatus(d, 'published')}>Publish</button>)}
                    {can('documents.publish') && d.status !== 'archived' &&
                      <button className="link-btn" onClick={() => changeStatus(d, 'archived')}>Archive</button>}
                    {can('documents.delete') && <button className="link-btn danger" onClick={() => remove(d)}>Delete</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && <p className="muted small">{nf(data.total)} documents</p>}
      {data && <Pagination page={data.page} pages={data.pages} onChange={(p) => setParam('page', String(p))} />}
    </div>
  )
}
