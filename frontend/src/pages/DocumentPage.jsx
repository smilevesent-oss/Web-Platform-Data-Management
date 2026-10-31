import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth'
import Comments from '../components/Comments'
import Notice from '../components/Notice'
import { categoryColor, formatDate, nf } from '../util'

function setMeta(name, content) {
  let el = document.querySelector(`meta[name="${name}"]`)
  if (!el) { el = document.createElement('meta'); el.setAttribute('name', name); document.head.appendChild(el) }
  el.setAttribute('content', content || '')
}

function Stars({ value, onRate, disabled }) {
  const [hover, setHover] = useState(0)
  return (
    <div className="stars" role="radiogroup" aria-label="Your rating" onMouseLeave={() => setHover(0)}>
      {[1, 2, 3, 4, 5].map((n) => (
        <button key={n} type="button" role="radio" aria-checked={value === n} aria-label={`${n} star${n > 1 ? 's' : ''}`}
          disabled={disabled} className={(hover || value || 0) >= n ? 'on' : ''}
          onMouseEnter={() => setHover(n)} onClick={() => onRate(n)}>★</button>
      ))}
    </div>
  )
}

export default function DocumentPage() {
  const { ref } = useParams()
  const { user } = useAuth()
  const [doc, setDoc] = useState(null)
  const [error, setError] = useState(null)
  const [related, setRelated] = useState([])
  const [msg, setMsg] = useState(null)
  const [reporting, setReporting] = useState(false)
  const [reason, setReason] = useState('')
  const fetched = useRef(null)

  useEffect(() => {
    // Guard so React StrictMode's double effect does not count two views.
    if (fetched.current === ref) return
    fetched.current = ref
    setDoc(null); setError(null)
    api(`/documents/${encodeURIComponent(ref)}`)
      .then((d) => {
        setDoc(d)
        api(`/documents/${d.id}/related`).then(setRelated).catch(() => {})
      })
      .catch((e) => setError(e.status === 404 ? 'This document does not exist or is not published.' : e.message))
  }, [ref])

  useEffect(() => {
    if (!doc) return
    document.title = doc.seo_title || doc.title
    setMeta('description', doc.seo_description || doc.summary)
    setMeta('keywords', doc.seo_keywords || doc.tags.map((t) => t.name).join(', '))
    return () => { document.title = 'Document Repository' }
  }, [doc])

  if (error) return <div className="empty"><h2>Document not found</h2><p>{error}</p><Link to="/" className="btn btn-ink">Back to all documents</Link></div>
  if (!doc) return <p className="muted pad">Loading document…</p>

  const color = categoryColor(doc.category?.slug)
  const applyEngagement = (e) => setDoc((d) => ({ ...d, ...e }))
  const like = () => api(`/documents/${doc.id}/like`, { method: 'POST' }).then(applyEngagement).catch((e) => setMsg(e.message))
  const rate = (score) => api(`/documents/${doc.id}/rating`, { method: 'PUT', body: { score } }).then(applyEngagement).catch((e) => setMsg(e.message))
  const report = (e) => {
    e.preventDefault()
    api('/reports', { method: 'POST', body: { target_type: 'document', target_id: doc.id, reason } })
      .then((r) => { setMsg(r.message); setReporting(false); setReason('') })
      .catch((err) => setMsg(err.message))
  }

  return (
    <div className="doc-page" style={{ '--tab': color }}>
      <nav className="crumbs" aria-label="Breadcrumb">
        <Link to="/">All documents</Link>
        {doc.category && <> / <Link to={`/?category=${doc.category.slug}`}>{doc.category.name}</Link></>}
      </nav>

      {doc.status !== 'published' && (
        <Notice kind="warn">This document is {doc.status}. Only staff can see it.</Notice>
      )}

      <header className="doc-header">
        <span className="doc-type-tab">{doc.doc_type}</span>
        <h1>{doc.title}</h1>
        <p className="lede">{doc.summary}</p>
      </header>

      <div className="doc-layout">
        <article className="doc-body">
          {doc.cover_image_url && (
            <figure className="doc-figure">
              <img src={doc.cover_image_url} alt={doc.cover_image_alt || ''} loading="lazy"
                onError={(e) => { e.currentTarget.closest('figure').hidden = true }} />
              {doc.cover_image_alt && <figcaption>{doc.cover_image_alt}</figcaption>}
            </figure>
          )}
          {doc.content.split(/\n\s*\n/).map((p, i) => <p key={i}>{p.trim()}</p>)}
        </article>

        <aside className="doc-aside">
          <dl className="meta-list">
            <dt>Author</dt><dd>{doc.author?.full_name || doc.author?.username || '—'}</dd>
            <dt>Department</dt><dd>{doc.department || '—'}</dd>
            <dt>Published</dt><dd><time dateTime={doc.published_at || doc.created_at}>{formatDate(doc.published_at || doc.created_at)}</time></dd>
            <dt>Last updated</dt><dd><time dateTime={doc.updated_at}>{formatDate(doc.updated_at)}</time></dd>
            <dt>Views</dt><dd>{nf(doc.views_count)}</dd>
            <dt>Collection</dt>
            <dd>{doc.category ? <Link to={`/?category=${doc.category.slug}`}>{doc.category.name}</Link> : '—'}</dd>
          </dl>
          {doc.tags.length > 0 && (
            <ul className="tag-list" aria-label="Tags">
              {doc.tags.map((t) => <li key={t.id}><Link className="tag" to={`/?tag=${t.slug}`}>{t.name}</Link></li>)}
            </ul>
          )}

          <div className="engage">
            <button className={`btn ${doc.liked_by_me ? 'btn-ink' : 'btn-ghost'}`} onClick={like} disabled={!user}
              aria-pressed={doc.liked_by_me}>
              {doc.liked_by_me ? 'Liked' : 'Like'} · {nf(doc.likes_count)}
            </button>
            <div className="rating">
              <Stars value={doc.my_rating} onRate={rate} disabled={!user} />
              <span className="muted">
                {doc.rating_count ? `${doc.rating_avg.toFixed(1)} average from ${doc.rating_count}` : 'No ratings yet'}
              </span>
            </div>
            {!user && <p className="muted small"><Link to="/login">Sign in</Link> to like, rate and comment.</p>}
            {user && !reporting && <button className="link-btn small" onClick={() => setReporting(true)}>Report a problem with this document</button>}
            {reporting && (
              <form onSubmit={report} className="report-form">
                <label htmlFor="doc-report">What is wrong?</label>
                <textarea id="doc-report" rows={3} required minLength={3} value={reason} onChange={(e) => setReason(e.target.value)} />
                <div className="row">
                  <button className="btn btn-ink" type="submit">Send report</button>
                  <button className="btn btn-ghost" type="button" onClick={() => setReporting(false)}>Cancel</button>
                </div>
              </form>
            )}
            <Notice kind="info" onClose={() => setMsg(null)}>{msg}</Notice>
          </div>
        </aside>
      </div>

      {doc.status === 'published' && <Comments docId={doc.id} />}

      {related.length > 0 && (
        <section className="related">
          <h2>Related documents</h2>
          <ul>
            {related.map((r) => (
              <li key={r.id} style={{ '--tab': categoryColor(r.category?.slug) }}>
                <Link to={`/documents/${r.slug}`}>{r.title}</Link>
                <span className="muted small">{r.doc_type} · {formatDate(r.created_at)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
