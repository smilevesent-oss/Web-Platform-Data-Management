import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth'
import Avatar from '../components/Avatar'
import Notice from '../components/Notice'
import { formatDate, timeAgo, useTitle } from '../util'

export default function Profile() {
  useTitle('Your profile')
  const { user, setUser } = useAuth()
  const [form, setForm] = useState({
    full_name: user.full_name, email: user.email, department: user.department, bio: user.bio, avatar_url: user.avatar_url || '',
  })
  const [pw, setPw] = useState({ current_password: '', new_password: '' })
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  const [pwMsg, setPwMsg] = useState(null)
  const [pwErr, setPwErr] = useState(null)
  const [mentions, setMentions] = useState([])

  useEffect(() => { api('/me/mentions').then(setMentions).catch(() => {}) }, [])
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const save = async (e) => {
    e.preventDefault(); setMsg(null); setErr(null)
    try {
      setUser(await api('/auth/me', { method: 'PUT', body: { ...form, avatar_url: form.avatar_url || null } }))
      setMsg('Profile saved.')
    } catch (ex) { setErr(ex.message) }
  }
  const changePw = async (e) => {
    e.preventDefault(); setPwMsg(null); setPwErr(null)
    try {
      await api('/auth/change-password', { method: 'POST', body: pw })
      setPw({ current_password: '', new_password: '' }); setPwMsg('Password changed.')
    } catch (ex) { setPwErr(ex.message) }
  }
  const markRead = async () => {
    await api('/me/mentions/read', { method: 'POST' })
    setMentions((m) => m.map((x) => ({ ...x, is_read: true })))
  }
  const unread = mentions.filter((m) => !m.is_read).length

  return (
    <div className="profile">
      <header className="profile-head">
        <Avatar name={user.full_name || user.username} url={user.avatar_url} size={64} />
        <div>
          <h1>{user.full_name || user.username}</h1>
          <p className="muted">@{user.username} · {user.role.display_name} · member since {formatDate(user.created_at)}</p>
        </div>
      </header>

      <div className="profile-grid">
        <form className="panel" onSubmit={save}>
          <h2>Profile details</h2>
          <Notice kind="success">{msg}</Notice><Notice>{err}</Notice>
          <div className="field"><label htmlFor="p-name">Full name</label><input id="p-name" value={form.full_name} onChange={set('full_name')} maxLength={120} /></div>
          <div className="field"><label htmlFor="p-email">E-mail</label><input id="p-email" type="email" required value={form.email} onChange={set('email')} /></div>
          <div className="field"><label htmlFor="p-dept">Department</label><input id="p-dept" value={form.department} onChange={set('department')} maxLength={100} /></div>
          <div className="field"><label htmlFor="p-avatar">Avatar image URL</label><input id="p-avatar" type="url" value={form.avatar_url} onChange={set('avatar_url')} placeholder="https://…" /></div>
          <div className="field"><label htmlFor="p-bio">About you</label><textarea id="p-bio" rows={4} value={form.bio} onChange={set('bio')} maxLength={2000} /></div>
          <button className="btn btn-ink">Save profile</button>
        </form>

        <div className="stack">
          <form className="panel" onSubmit={changePw}>
            <h2>Change password</h2>
            <Notice kind="success">{pwMsg}</Notice><Notice>{pwErr}</Notice>
            <div className="field"><label htmlFor="pw-cur">Current password</label>
              <input id="pw-cur" type="password" autoComplete="current-password" required value={pw.current_password}
                onChange={(e) => setPw({ ...pw, current_password: e.target.value })} /></div>
            <div className="field"><label htmlFor="pw-new">New password</label>
              <input id="pw-new" type="password" autoComplete="new-password" required minLength={8} value={pw.new_password}
                onChange={(e) => setPw({ ...pw, new_password: e.target.value })} /></div>
            <button className="btn btn-ink">Change password</button>
          </form>

          <section className="panel">
            <div className="panel-head">
              <h2>Mentions {unread > 0 && <span className="badge">{unread} new</span>}</h2>
              {unread > 0 && <button className="link-btn" onClick={markRead}>Mark all as read</button>}
            </div>
            {mentions.length === 0 ? <p className="muted">When a colleague tags you with @{user.username}, it shows up here.</p> : (
              <ul className="mention-feed">
                {mentions.map((m) => (
                  <li key={m.comment_id} className={m.is_read ? '' : 'unread'}>
                    <p><strong>{m.by.full_name || m.by.username}</strong> mentioned you on{' '}
                      <Link to={`/documents/${m.document_slug}#comment-${m.comment_id}`}>{m.document_title}</Link></p>
                    <p className="muted small">“{m.body}” · {timeAgo(m.created_at)}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}
