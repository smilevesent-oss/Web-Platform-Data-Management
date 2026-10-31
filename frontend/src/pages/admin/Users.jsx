import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { useAuth } from '../../auth'
import Notice from '../../components/Notice'
import Pagination from '../../components/Pagination'
import { formatDate, nf, useDebounced, useTitle } from '../../util'

const BLANK = { username: '', email: '', full_name: '', department: '', password: '', role_id: '' }

export default function Users() {
  useTitle('Users')
  const { user: me } = useAuth()
  const [roles, setRoles] = useState([])
  const [q, setQ] = useState('')
  const dq = useDebounced(q)
  const [role, setRole] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState(BLANK)

  const load = () => api('/admin/users', { params: { q: dq, role, page } }).then(setData).catch((e) => setErr(e.message))
  useEffect(() => { api('/admin/roles').then(setRoles).catch(() => {}) }, [])
  useEffect(() => { load() }, [dq, role, page]) // eslint-disable-line react-hooks/exhaustive-deps

  const ok = (m) => { setErr(null); setMsg(m); load() }
  const fail = (e) => { setMsg(null); setErr(e.message) }

  const update = (u, body, label) => api(`/admin/users/${u.id}`, { method: 'PUT', body }).then(() => ok(label)).catch(fail)
  const resetPassword = (u) => {
    const pw = window.prompt(`New password for @${u.username} (at least 8 characters)`)
    if (pw) update(u, { password: pw }, `Password reset for @${u.username}.`)
  }
  const remove = (u) => {
    if (!window.confirm(`Delete @${u.username}? Their comments, likes and ratings are deleted too. Consider deactivating instead.`)) return
    api(`/admin/users/${u.id}`, { method: 'DELETE' }).then(() => ok(`Deleted @${u.username}.`)).catch(fail)
  }
  const create = (e) => {
    e.preventDefault()
    api('/admin/users', { method: 'POST', body: { ...form, role_id: Number(form.role_id) } })
      .then((u) => { setForm(BLANK); setCreating(false); ok(`Created @${u.username}.`) }).catch(fail)
  }
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <div>
      <div className="page-head">
        <h1>Users</h1>
        <button className="btn btn-ink" onClick={() => setCreating((c) => !c)} aria-expanded={creating}>{creating ? 'Close' : 'New user'}</button>
      </div>
      <Notice kind="success" onClose={() => setMsg(null)}>{msg}</Notice>
      <Notice onClose={() => setErr(null)}>{err}</Notice>

      {creating && (
        <form className="panel grid-form" onSubmit={create}>
          <div className="field"><label htmlFor="u-user">Username</label><input id="u-user" required pattern="[A-Za-z0-9_.]{3,50}" value={form.username} onChange={set('username')} /></div>
          <div className="field"><label htmlFor="u-email">E-mail</label><input id="u-email" type="email" required value={form.email} onChange={set('email')} /></div>
          <div className="field"><label htmlFor="u-name">Full name</label><input id="u-name" value={form.full_name} onChange={set('full_name')} /></div>
          <div className="field"><label htmlFor="u-dept">Department</label><input id="u-dept" value={form.department} onChange={set('department')} /></div>
          <div className="field"><label htmlFor="u-pass">Initial password</label><input id="u-pass" type="password" required minLength={8} value={form.password} onChange={set('password')} autoComplete="new-password" /></div>
          <div className="field"><label htmlFor="u-role">Role</label>
            <select id="u-role" required value={form.role_id} onChange={set('role_id')}>
              <option value="">Choose a role</option>
              {roles.map((r) => <option key={r.id} value={r.id}>{r.display_name}</option>)}
            </select></div>
          <button className="btn btn-ink">Create user</button>
        </form>
      )}

      <div className="toolbar">
        <label htmlFor="u-q" className="sr-only">Search users</label>
        <input id="u-q" type="search" placeholder="Search name, username or e-mail" value={q} onChange={(e) => { setQ(e.target.value); setPage(1) }} />
        <label htmlFor="u-rolef" className="sr-only">Filter by role</label>
        <select id="u-rolef" value={role} onChange={(e) => { setRole(e.target.value); setPage(1) }}>
          <option value="">All roles</option>
          {roles.map((r) => <option key={r.id} value={r.name}>{r.display_name} ({r.user_count})</option>)}
        </select>
        {data && <span className="muted">{nf(data.total)} users</span>}
      </div>

      {!data ? <p className="muted">Loading…</p> : (
        <div className="table-wrap">
          <table>
            <thead><tr><th>User</th><th>Role</th><th>Status</th><th>Last sign-in</th><th><span className="sr-only">Actions</span></th></tr></thead>
            <tbody>
              {data.items.map((u) => (
                <tr key={u.id} className={u.is_active ? '' : 'inactive'}>
                  <td><strong>{u.full_name || u.username}</strong><div className="muted small">@{u.username} · {u.email}{u.department && ` · ${u.department}`}</div></td>
                  <td>
                    <label htmlFor={`role-${u.id}`} className="sr-only">Role for {u.username}</label>
                    <select id={`role-${u.id}`} value={u.role.id} onChange={(e) => update(u, { role_id: Number(e.target.value) }, `Role updated for @${u.username}.`)}>
                      {roles.map((r) => <option key={r.id} value={r.id}>{r.display_name}</option>)}
                    </select>
                  </td>
                  <td><span className={`status ${u.is_active ? 'status-published' : 'status-archived'}`}>{u.is_active ? 'active' : 'deactivated'}</span></td>
                  <td>{u.last_login_at ? formatDate(u.last_login_at, true) : <span className="muted">never</span>}</td>
                  <td className="actions">
                    {u.id !== me.id && (u.is_active
                      ? <button className="link-btn" onClick={() => update(u, { is_active: false }, `Deactivated @${u.username}.`)}>Deactivate</button>
                      : <button className="link-btn" onClick={() => update(u, { is_active: true }, `Reactivated @${u.username}.`)}>Reactivate</button>)}
                    <button className="link-btn" onClick={() => resetPassword(u)}>Reset password</button>
                    {u.id !== me.id && <button className="link-btn danger" onClick={() => remove(u)}>Delete</button>}
                  </td>
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
