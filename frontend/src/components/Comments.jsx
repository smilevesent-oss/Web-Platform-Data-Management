import { Fragment, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth'
import { useSite } from './Layout'
import Avatar from './Avatar'
import Notice from './Notice'
import { timeAgo } from '../util'

// Render @username as a highlighted mention.
function CommentBody({ text }) {
  return text.split(/(@[A-Za-z0-9_.]{3,50})/g).map((part, i) =>
    i % 2 === 1 ? <span key={i} className="mention">{part}</span> : <Fragment key={i}>{part}</Fragment>
  )
}

function CommentForm({ docId, parentId, initial = '', onDone, onCancel, submitLabel = 'Post comment', commentId }) {
  const [body, setBody] = useState(initial)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const ref = useRef(null)

  const mentionQuery = () => {
    const el = ref.current
    if (!el) return null
    const before = body.slice(0, el.selectionStart)
    const m = before.match(/@([A-Za-z0-9_.]{1,50})$/)
    return m ? m[1] : null
  }

  useEffect(() => {
    const q = mentionQuery()
    if (!q) { setSuggestions([]); return }
    const t = setTimeout(() => api('/users/search', { params: { q } }).then(setSuggestions).catch(() => {}), 200)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [body])

  const pick = (username) => {
    const el = ref.current
    const pos = el.selectionStart
    const before = body.slice(0, pos).replace(/@([A-Za-z0-9_.]{1,50})$/, `@${username} `)
    setBody(before + body.slice(pos))
    setSuggestions([])
    requestAnimationFrame(() => { el.focus(); el.setSelectionRange(before.length, before.length) })
  }

  const submit = async (e) => {
    e.preventDefault()
    if (!body.trim()) return
    setBusy(true); setError(null)
    try {
      const res = commentId
        ? await api(`/comments/${commentId}`, { method: 'PUT', body: { body } })
        : await api(`/documents/${docId}/comments`, { method: 'POST', body: { body, parent_id: parentId || null } })
      setBody('')
      onDone(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const id = `c-${commentId || parentId || 'new'}`
  return (
    <form className="comment-form" onSubmit={submit}>
      <label htmlFor={id} className="sr-only">{submitLabel}</label>
      <div className="mention-wrap">
        <textarea id={id} ref={ref} rows={3} value={body} maxLength={5000}
          placeholder="Share a question or correction. Type @ to tag a colleague."
          onChange={(e) => setBody(e.target.value)} />
        {suggestions.length > 0 && (
          <ul className="mention-menu" role="listbox" aria-label="Tag a colleague">
            {suggestions.map((u) => (
              <li key={u.id}>
                <button type="button" onClick={() => pick(u.username)}>
                  <strong>@{u.username}</strong> <span className="muted">{u.full_name}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <Notice>{error}</Notice>
      <div className="row">
        <button className="btn btn-ink" disabled={busy || !body.trim()}>{busy ? 'Posting…' : submitLabel}</button>
        {onCancel && <button type="button" className="btn btn-ghost" onClick={onCancel}>Cancel</button>}
      </div>
    </form>
  )
}

export default function Comments({ docId }) {
  const { user } = useAuth()
  const site = useSite()
  const [items, setItems] = useState([])
  const [replyTo, setReplyTo] = useState(null)
  const [editing, setEditing] = useState(null)
  const [notice, setNotice] = useState(null)

  const load = () => api(`/documents/${docId}/comments`).then(setItems).catch(() => {})
  useEffect(() => { load() }, [docId]) // eslint-disable-line react-hooks/exhaustive-deps

  const afterPost = (c) => {
    if (c.status === 'pending') setNotice('Your comment was received and will appear after a moderator approves it.')
    else if (c.status === 'spam') setNotice('Your comment was held by the spam filter for review by a moderator.')
    else setNotice(null)
    setReplyTo(null); setEditing(null)
    load()
  }
  const remove = async (c) => {
    if (!window.confirm('Delete this comment? This cannot be undone.')) return
    try { await api(`/comments/${c.id}`, { method: 'DELETE' }); load() } catch (e) { setNotice(e.message) }
  }
  const report = async (c) => {
    const reason = window.prompt('Why are you reporting this comment?')
    if (!reason || reason.trim().length < 3) return
    try {
      const r = await api('/reports', { method: 'POST', body: { target_type: 'comment', target_id: c.id, reason } })
      setNotice(r.message)
    } catch (e) { setNotice(e.message) }
  }

  const roots = items.filter((c) => !c.parent_id || !items.some((p) => p.id === c.parent_id))
  const childrenOf = (id) => items.filter((c) => c.parent_id === id)

  const renderComment = (c, depth = 0) => (
    <li key={c.id} id={`comment-${c.id}`} className={`comment ${c.status !== 'visible' ? 'comment-pending' : ''}`}>
      <Avatar name={c.user.full_name || c.user.username} url={c.user.avatar_url} size={34} />
      <div className="comment-main">
        <div className="comment-head">
          <strong>{c.user.full_name || c.user.username}</strong>
          <span className="muted">@{c.user.username}</span>
          <time className="muted" dateTime={c.created_at}>{timeAgo(c.created_at)}</time>
          {c.status === 'pending' && <span className="badge">Awaiting approval</span>}
        </div>
        {editing === c.id ? (
          <CommentForm commentId={c.id} initial={c.body} submitLabel="Save changes"
            onDone={afterPost} onCancel={() => setEditing(null)} />
        ) : (
          <p className="comment-body"><CommentBody text={c.body} /></p>
        )}
        {user && editing !== c.id && (
          <div className="comment-actions">
            {depth === 0 && <button className="link-btn" onClick={() => setReplyTo(replyTo === c.id ? null : c.id)}>Reply</button>}
            {user.id === c.user.id && <button className="link-btn" onClick={() => setEditing(c.id)}>Edit</button>}
            {(user.id === c.user.id || user.permissions.includes('comments.moderate')) &&
              <button className="link-btn" onClick={() => remove(c)}>Delete</button>}
            {user.id !== c.user.id && <button className="link-btn" onClick={() => report(c)}>Report</button>}
          </div>
        )}
        {replyTo === c.id && (
          <CommentForm docId={docId} parentId={c.id} submitLabel="Post reply" onDone={afterPost} onCancel={() => setReplyTo(null)} />
        )}
        {childrenOf(c.id).length > 0 && <ul className="comment-children">{childrenOf(c.id).map((r) => renderComment(r, depth + 1))}</ul>}
      </div>
    </li>
  )

  return (
    <section className="comments" aria-labelledby="comments-h">
      <h2 id="comments-h">Discussion <span className="muted">({items.filter((c) => c.status === 'visible').length})</span></h2>
      <Notice kind="info" onClose={() => setNotice(null)}>{notice}</Notice>
      {site.comments_enabled === false ? (
        <p className="muted">Comments are turned off.</p>
      ) : user ? (
        <CommentForm docId={docId} onDone={afterPost} />
      ) : (
        <p className="muted"><Link to="/login">Sign in</Link> to join the discussion.</p>
      )}
      {items.length === 0 ? <p className="muted">No comments yet. Questions and corrections help keep this document accurate.</p> : (
        <ul className="comment-list">{roots.map((c) => renderComment(c))}</ul>
      )}
    </section>
  )
}
