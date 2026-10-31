import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import Notice from '../../components/Notice'
import { useTitle } from '../../util'

function CategoryPanel({ onMsg, onErr }) {
  const [items, setItems] = useState([])
  const [form, setForm] = useState({ name: '', description: '' })
  const [editing, setEditing] = useState(null)
  const load = () => api('/admin/categories').then(setItems).catch((e) => onErr(e.message))
  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const save = async (e) => {
    e.preventDefault()
    try {
      if (editing) await api(`/admin/categories/${editing}`, { method: 'PUT', body: form })
      else await api('/admin/categories', { method: 'POST', body: form })
      onMsg(editing ? 'Collection updated.' : 'Collection created.')
      setForm({ name: '', description: '' }); setEditing(null); load()
    } catch (err) { onErr(err.message) }
  }
  const remove = async (c) => {
    if (!window.confirm(`Delete “${c.name}”? Its ${c.document_count} documents will have no collection.`)) return
    try { await api(`/admin/categories/${c.id}`, { method: 'DELETE' }); onMsg('Collection deleted.'); load() } catch (err) { onErr(err.message) }
  }

  return (
    <section className="panel">
      <h2>Collections</h2>
      <form className="inline-form" onSubmit={save}>
        <div className="field"><label htmlFor="c-name">Name</label>
          <input id="c-name" required minLength={2} maxLength={100} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
        <div className="field grow"><label htmlFor="c-desc">Description</label>
          <input id="c-desc" maxLength={2000} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
        <button className="btn btn-ink">{editing ? 'Save collection' : 'Add collection'}</button>
        {editing && <button type="button" className="btn btn-ghost" onClick={() => { setEditing(null); setForm({ name: '', description: '' }) }}>Cancel</button>}
      </form>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Name</th><th>Description</th><th className="num">Documents</th><th><span className="sr-only">Actions</span></th></tr></thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id}>
                <td><Link to={`/?category=${c.slug}`}>{c.name}</Link></td>
                <td className="muted">{c.description}</td>
                <td className="num">{c.document_count}</td>
                <td className="actions">
                  <button className="link-btn" onClick={() => { setEditing(c.id); setForm({ name: c.name, description: c.description }) }}>Edit</button>
                  <button className="link-btn danger" onClick={() => remove(c)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function TagPanel({ onMsg, onErr }) {
  const [items, setItems] = useState([])
  const [name, setName] = useState('')
  const [filter, setFilter] = useState('')
  const load = () => api('/admin/tags').then(setItems).catch((e) => onErr(e.message))
  useEffect(() => { load() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const add = async (e) => {
    e.preventDefault()
    try { await api('/admin/tags', { method: 'POST', body: { name } }); setName(''); onMsg('Tag created.'); load() } catch (err) { onErr(err.message) }
  }
  const rename = async (t) => {
    const next = window.prompt('Rename tag', t.name)
    if (!next || next === t.name) return
    try { await api(`/admin/tags/${t.id}`, { method: 'PUT', body: { name: next } }); onMsg('Tag renamed.'); load() } catch (err) { onErr(err.message) }
  }
  const remove = async (t) => {
    if (!window.confirm(`Delete tag “${t.name}”? It is used by ${t.document_count} documents.`)) return
    try { await api(`/admin/tags/${t.id}`, { method: 'DELETE' }); onMsg('Tag deleted.'); load() } catch (err) { onErr(err.message) }
  }
  const shown = items.filter((t) => t.name.toLowerCase().includes(filter.toLowerCase()))

  return (
    <section className="panel">
      <h2>Tags <span className="muted small">({items.length})</span></h2>
      <form className="inline-form" onSubmit={add}>
        <div className="field"><label htmlFor="t-name">New tag</label>
          <input id="t-name" required minLength={2} maxLength={60} value={name} onChange={(e) => setName(e.target.value)} /></div>
        <button className="btn btn-ink">Add tag</button>
        <div className="field grow"><label htmlFor="t-filter">Find a tag</label>
          <input id="t-filter" type="search" value={filter} onChange={(e) => setFilter(e.target.value)} /></div>
      </form>
      <ul className="tag-admin">
        {shown.map((t) => (
          <li key={t.id}>
            <span>{t.name} <span className="muted">{t.document_count}</span></span>
            <button className="link-btn" onClick={() => rename(t)}>Rename</button>
            <button className="link-btn danger" onClick={() => remove(t)}>Delete</button>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function Taxonomy() {
  useTitle('Categories & tags')
  const [msg, setMsg] = useState(null)
  const [err, setErr] = useState(null)
  const onMsg = (m) => { setErr(null); setMsg(m) }
  const onErr = (m) => { setMsg(null); setErr(m) }
  return (
    <div className="stack">
      <h1>Categories & tags</h1>
      <Notice kind="success" onClose={() => setMsg(null)}>{msg}</Notice>
      <Notice onClose={() => setErr(null)}>{err}</Notice>
      <CategoryPanel onMsg={onMsg} onErr={onErr} />
      <TagPanel onMsg={onMsg} onErr={onErr} />
    </div>
  )
}
