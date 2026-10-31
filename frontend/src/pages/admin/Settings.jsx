import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import Notice from '../../components/Notice'
import { formatDate, useTitle } from '../../util'

const LABELS = {
  site_name: 'Site name',
  site_tagline: 'Tagline',
  registration_open: 'Allow self-registration',
  comments_enabled: 'Allow comments',
  comments_require_approval: 'Hold new comments for approval',
  default_page_size: 'Documents per page',
}

function SettingRow({ s, onSaved, onErr }) {
  const [value, setValue] = useState(s.value)
  const save = async (v = value) => {
    try { onSaved(await api(`/admin/settings/${s.key}`, { method: 'PUT', body: { value: v } })) } catch (e) { onErr(e.message) }
  }
  const id = `set-${s.key}`
  if (typeof s.value === 'boolean') {
    return (
      <li className="setting">
        <label className="check" htmlFor={id}>
          <input id={id} type="checkbox" checked={value} onChange={(e) => { setValue(e.target.checked); save(e.target.checked) }} />
          <span><strong>{LABELS[s.key] || s.key}</strong><span className="muted small">{s.description}</span></span>
        </label>
      </li>
    )
  }
  const numeric = typeof s.value === 'number'
  return (
    <li className="setting">
      <form onSubmit={(e) => { e.preventDefault(); save() }}>
        <label htmlFor={id}><strong>{LABELS[s.key] || s.key}</strong><span className="muted small">{s.description}</span></label>
        <div className="row">
          <input id={id} type={numeric ? 'number' : 'text'} min={numeric ? 1 : undefined} max={numeric ? 100 : undefined}
            value={value} required onChange={(e) => setValue(numeric ? Number(e.target.value) : e.target.value)} />
          <button className="btn btn-ink" disabled={value === s.value}>Save</button>
        </div>
      </form>
      <span className="muted small">Last changed {formatDate(s.updated_at, true)}</span>
    </li>
  )
}

export default function Settings() {
  useTitle('Global settings')
  const [items, setItems] = useState(null)
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  useEffect(() => { api('/admin/settings').then(setItems).catch((e) => setErr(e.message)) }, [])

  return (
    <div>
      <h1>Global settings</h1>
      <Notice kind="success" onClose={() => setMsg(null)}>{msg}</Notice>
      <Notice onClose={() => setErr(null)}>{err}</Notice>
      {!items ? <p className="muted">Loading…</p> : (
        <ul className="settings-list panel">
          {items.map((s) => (
            <SettingRow key={s.key} s={s} onErr={(m) => { setMsg(null); setErr(m) }}
              onSaved={(u) => { setErr(null); setMsg(`${LABELS[u.key] || u.key} saved.`); setItems((xs) => xs.map((x) => (x.key === u.key ? u : x))) }} />
          ))}
        </ul>
      )}
    </div>
  )
}
