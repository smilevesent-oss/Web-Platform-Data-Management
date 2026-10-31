import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../auth'
import Notice from '../../components/Notice'
import { useTitle } from '../../util'

const EMPTY = {
  title: '', summary: '', content: '', doc_type: 'Policy', department: '', category_id: '',
  tags: '', status: 'draft', cover_image_url: '', cover_image_alt: '',
}
const TYPES = ['Policy', 'Procedure', 'SOP', 'Standard', 'Guide', 'Checklist', 'Runbook', 'Playbook', 'Report',
  'Research Report', 'Research Note', 'Analysis', 'Survey Report', 'Postmortem', 'Decision Record', 'Template', 'Requirements', 'Plan']

export default function DocumentEditor() {
  const { id } = useParams()
  const isNew = !id
  useTitle(isNew ? 'New document' : 'Edit document')
  const { can } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [original, setOriginal] = useState(null)
  const [categories, setCategories] = useState([])
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api('/admin/categories').catch(() => api('/categories')).then(setCategories).catch(() => {})
    if (!isNew) {
      api(`/admin/documents/${id}`).then((d) => {
        setOriginal(d)
        setForm({
          title: d.title, summary: d.summary, content: d.content, doc_type: d.doc_type, department: d.department,
          category_id: d.category?.id ?? '', tags: d.tags.map((t) => t.name).join(', '), status: d.status,
          cover_image_url: d.cover_image_url || '', cover_image_alt: d.cover_image_alt || '',
        })
      }).catch((e) => setError(e.message))
    }
  }, [id, isNew])

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  const canPublish = can('documents.publish')

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null); setSaved(null)
    const body = {
      ...form,
      category_id: form.category_id === '' ? null : Number(form.category_id),
      tags: form.tags.split(',').map((t) => t.trim()).filter(Boolean),
      cover_image_url: form.cover_image_url.trim() || null,
      cover_image_alt: form.cover_image_alt.trim() || null,
    }
    if (!canPublish) delete body.status
    try {
      const d = isNew
        ? await api('/admin/documents', { method: 'POST', body })
        : await api(`/admin/documents/${id}`, { method: 'PUT', body })
      if (isNew) navigate(`/admin/documents/${d.id}`, { replace: true })
      setOriginal(d)
      setSaved(isNew ? 'Document created.' : 'Changes saved.')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const words = form.content.trim() ? form.content.trim().split(/\s+/).length : 0

  return (
    <form onSubmit={submit} className="editor">
      <div className="page-head">
        <h1>{isNew ? 'New document' : 'Edit document'}</h1>
        <div className="row">
          {original?.status === 'published' && <Link className="btn btn-ghost" to={`/documents/${original.slug}`}>View live</Link>}
          <Link className="btn btn-ghost" to="/admin/documents">Back to list</Link>
        </div>
      </div>
      <Notice kind="success" onClose={() => setSaved(null)}>{saved}</Notice>
      <Notice onClose={() => setError(null)}>{error}</Notice>

      <div className="editor-grid">
        <div className="stack">
          <div className="field">
            <label htmlFor="e-title">Title</label>
            <input id="e-title" required minLength={3} maxLength={300} value={form.title} onChange={set('title')} />
          </div>
          <div className="field">
            <label htmlFor="e-summary">Summary</label>
            <textarea id="e-summary" rows={3} maxLength={2000} value={form.summary} onChange={set('summary')}
              aria-describedby="e-summary-hint" />
            <small id="e-summary-hint" className="muted">Shown in listings. Leave empty to use the first lines of the content.</small>
          </div>
          <div className="field">
            <label htmlFor="e-content">Content</label>
            <textarea id="e-content" className="content-input" rows={20} required minLength={10} value={form.content}
              onChange={set('content')} aria-describedby="e-content-hint" />
            <small id="e-content-hint" className="muted">Plain text. Separate paragraphs with a blank line. {words} words.</small>
          </div>
        </div>

        <aside className="stack panel">
          <div className="field">
            <label htmlFor="e-status">Status</label>
            <select id="e-status" value={form.status} onChange={set('status')} disabled={!canPublish}>
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>
            {!canPublish && <small className="muted">Your role can save drafts only.</small>}
          </div>
          <div className="field">
            <label htmlFor="e-cat">Collection</label>
            <select id="e-cat" value={form.category_id} onChange={set('category_id')}>
              <option value="">No collection</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="e-type">Document type</label>
            <input id="e-type" list="doc-types" value={form.doc_type} onChange={set('doc_type')} maxLength={50} />
            <datalist id="doc-types">{TYPES.map((t) => <option key={t} value={t} />)}</datalist>
          </div>
          <div className="field">
            <label htmlFor="e-dept">Owning department</label>
            <input id="e-dept" value={form.department} onChange={set('department')} maxLength={100} />
          </div>
          <div className="field">
            <label htmlFor="e-tags">Tags</label>
            <input id="e-tags" value={form.tags} onChange={set('tags')} placeholder="Security, Compliance" />
            <small className="muted">Separate with commas. New tags are created automatically.</small>
          </div>
          <div className="field">
            <label htmlFor="e-img">Cover image URL</label>
            <input id="e-img" type="url" value={form.cover_image_url} onChange={set('cover_image_url')} placeholder="https://…" />
          </div>
          <div className="field">
            <label htmlFor="e-alt">Image alt text</label>
            <input id="e-alt" value={form.cover_image_alt} onChange={set('cover_image_alt')} maxLength={300} />
          </div>
          {form.cover_image_url && <img className="editor-preview" src={form.cover_image_url} alt={form.cover_image_alt || ''} />}
          <button className="btn btn-ink btn-block" disabled={busy}>{busy ? 'Saving…' : isNew ? 'Create document' : 'Save changes'}</button>
        </aside>
      </div>
    </form>
  )
}
