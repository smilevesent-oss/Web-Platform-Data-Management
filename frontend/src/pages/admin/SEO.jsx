import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import Notice from '../../components/Notice'
import Pagination from '../../components/Pagination'
import { nf, useDebounced, useTitle } from '../../util'

function SeoRow({ item, onSaved, onErr }) {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    seo_title: item.seo_title || '', seo_description: item.seo_description || '',
    seo_keywords: item.seo_keywords || '', cover_image_alt: item.cover_image_alt || '',
  })
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  const save = async (e) => {
    e.preventDefault()
    try { onSaved(await api(`/seo/documents/${item.id}`, { method: 'PUT', body: form })); setOpen(false) } catch (err) { onErr(err.message) }
  }
  const fid = (k) => `seo-${item.id}-${k}`
  return (
    <li className="panel seo-item">
      <div className="seo-head">
        <div>
          <strong>{item.title}</strong> <span className={`status status-${item.status}`}>{item.status}</span>
          {item.issues.length ? (
            <ul className="issue-list">{item.issues.map((i) => <li key={i}>{i}</li>)}</ul>
          ) : <p className="ok small">No SEO issues</p>}
        </div>
        <button className="btn btn-ghost" aria-expanded={open} onClick={() => setOpen((o) => !o)}>{open ? 'Close' : 'Edit metadata'}</button>
      </div>
      {open && (
        <form onSubmit={save} className="seo-form">
          <div className="field">
            <label htmlFor={fid('t')}>SEO title <span className="muted">({form.seo_title.length}/60)</span></label>
            <input id={fid('t')} maxLength={300} value={form.seo_title} onChange={set('seo_title')} />
          </div>
          <div className="field">
            <label htmlFor={fid('d')}>Meta description <span className="muted">({form.seo_description.length}, aim for 50–160)</span></label>
            <textarea id={fid('d')} rows={2} maxLength={500} value={form.seo_description} onChange={set('seo_description')} />
          </div>
          <div className="field">
            <label htmlFor={fid('k')}>Keywords</label>
            <input id={fid('k')} maxLength={500} value={form.seo_keywords} onChange={set('seo_keywords')} placeholder="comma, separated, keywords" />
          </div>
          <div className="field">
            <label htmlFor={fid('a')}>Image alt text</label>
            <input id={fid('a')} maxLength={300} value={form.cover_image_alt} onChange={set('cover_image_alt')}
              disabled={!item.cover_image_url} placeholder={item.cover_image_url ? 'Describe the image' : 'This document has no image'} />
          </div>
          <div className="serp-preview" aria-label="Search result preview">
            <span className="serp-title">{form.seo_title || item.title}</span>
            <span className="serp-url">/documents/{item.slug}</span>
            <span className="serp-desc">{form.seo_description || 'No description: search engines will pick text from the page.'}</span>
          </div>
          <button className="btn btn-ink">Save metadata</button>
        </form>
      )}
    </li>
  )
}

export default function SEO() {
  useTitle('SEO metadata')
  const [q, setQ] = useState('')
  const dq = useDebounced(q)
  const [onlyIssues, setOnlyIssues] = useState(true)
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)

  const load = () => api('/seo/documents', { params: { q: dq, only_issues: onlyIssues, page, page_size: 15 } }).then(setData).catch((e) => setErr(e.message))
  useEffect(() => { load() }, [dq, onlyIssues, page]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <h1>SEO metadata</h1>
      <Notice kind="success" onClose={() => setMsg(null)}>{msg}</Notice>
      <Notice onClose={() => setErr(null)}>{err}</Notice>
      <div className="toolbar">
        <label htmlFor="seo-q" className="sr-only">Search by title</label>
        <input id="seo-q" type="search" placeholder="Search by title" value={q} onChange={(e) => { setQ(e.target.value); setPage(1) }} />
        <label className="check"><input type="checkbox" checked={onlyIssues} onChange={(e) => { setOnlyIssues(e.target.checked); setPage(1) }} /> Only documents with issues</label>
        {data && <span className="muted">{nf(data.total)} documents</span>}
      </div>
      {!data ? <p className="muted">Loading…</p> : data.items.length === 0 ? (
        <div className="empty"><h3>All metadata is complete</h3><p>No documents need SEO attention.</p></div>
      ) : (
        <ul className="seo-list">
          {data.items.map((i) => (
            <SeoRow key={i.id} item={i} onErr={setErr}
              onSaved={(u) => { setMsg(`Metadata saved for “${u.title}”.`); setData((d) => ({ ...d, items: d.items.map((x) => (x.id === u.id ? u : x)) })) }} />
          ))}
        </ul>
      )}
      {data && <Pagination page={data.page} pages={data.pages} onChange={setPage} />}
    </div>
  )
}
