import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { useAuth } from '../../auth'
import Notice from '../../components/Notice'
import { useTitle } from '../../util'

const LOCKED = { super_admin: ['users.manage', 'roles.manage'] }

export default function Roles() {
  useTitle('Roles & permissions')
  const { refresh } = useAuth()
  const [roles, setRoles] = useState([])
  const [perms, setPerms] = useState([])
  const [draft, setDraft] = useState({})
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)

  const load = () => api('/admin/roles').then((rs) => {
    setRoles(rs)
    setDraft(Object.fromEntries(rs.map((r) => [r.id, new Set(r.permissions.map((p) => p.code))])))
  }).catch((e) => setErr(e.message))
  useEffect(() => { load(); api('/admin/permissions').then(setPerms).catch((e) => setErr(e.message)) }, [])

  const toggle = (roleId, code) => setDraft((d) => {
    const s = new Set(d[roleId]); s.has(code) ? s.delete(code) : s.add(code); return { ...d, [roleId]: s }
  })
  const dirty = (r) => {
    const a = draft[r.id]; const b = new Set(r.permissions.map((p) => p.code))
    return a && (a.size !== b.size || [...a].some((c) => !b.has(c)))
  }
  const save = async (r) => {
    try {
      await api(`/admin/roles/${r.id}/permissions`, { method: 'PUT', body: { permission_codes: [...draft[r.id]] } })
      setErr(null); setMsg(`Permissions saved for ${r.display_name}. Users with this role get the change immediately.`)
      load(); refresh()
    } catch (e) { setMsg(null); setErr(e.message) }
  }

  return (
    <div>
      <h1>Roles & permissions</h1>
      <p className="muted">Tick what each role may do. Changes apply to every user with that role as soon as you save.</p>
      <Notice kind="success" onClose={() => setMsg(null)}>{msg}</Notice>
      <Notice onClose={() => setErr(null)}>{err}</Notice>
      <div className="table-wrap">
        <table className="perm-matrix">
          <thead>
            <tr>
              <th>Permission</th>
              {roles.map((r) => <th key={r.id} className="center">{r.display_name}<div className="muted small">{r.user_count} users</div></th>)}
            </tr>
          </thead>
          <tbody>
            {perms.map((p) => (
              <tr key={p.code}>
                <td><code>{p.code}</code><div className="muted small">{p.description}</div></td>
                {roles.map((r) => {
                  const locked = LOCKED[r.name]?.includes(p.code)
                  return (
                    <td key={r.id} className="center">
                      <input type="checkbox" aria-label={`${r.display_name}: ${p.code}`} disabled={locked}
                        checked={draft[r.id]?.has(p.code) || false} onChange={() => toggle(r.id, p.code)} />
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td className="muted small">Locked boxes keep at least one role able to manage users.</td>
              {roles.map((r) => (
                <td key={r.id} className="center">
                  <button className="btn btn-ink" disabled={!dirty(r)} onClick={() => save(r)}>Save</button>
                </td>
              ))}
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}
