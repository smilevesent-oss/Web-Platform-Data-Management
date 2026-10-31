import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, getSessionId, logClick } from '../api/client'
import DocCard from '../components/DocCard'
import Notice from '../components/Notice'
import Pagination from '../components/Pagination'
import { useSite } from '../components/Layout'
import { categoryColor, formatDate, nf, useTitle } from '../util'

const FILTER_KEYS = ['q', 'category', 'tag', 'doc_type', 'date_from', 'date_to', 'sort']

export default function Home() {
  const site = useSite()
  const [params, setParams] = useSearchParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [categories, setCategories] = useState([])
  const [tags, setTags] = useState([])
  const [docTypes, setDocTypes] = useState([])
  const [popular, setPopular] = useState([])
  const [showFilters, setShowFilters] = useState(false)

  const q = params.get('q') || ''
  const page = Number(params.get('page') || 1)
  const filters = Object.fromEntries(FILTER_KEYS.map((k) => [k, params.get(k) || '']))
  const filtering = FILTER_KEYS.some((k) => k !== 'sort' && filters[k])
  useTitle(q ? `Search: ${q}` : null)

  useEffect(() => {
    api('/categories').then(setCategories).catch(() => {})
    api('/tags', { params: { limit: 24 } }).then(setTags).catch(() => {})
    api('/documents/doc-types').then(setDocTypes).catch(() => {})
    api('/documents/popular', { params: { limit: 5 } }).then(setPopular).catch(() => {})
  }, [])

  const key = params.toString()
  useEffect(() => {
    let alive = true
    setError(null)
    api('/documents', {
      params: { ...filters, sort: filters.sort || 'latest', page, session_id: q ? getSessionId() : undefined },
    })
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(e.message))
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  const update = (patch) => {
    const next = new URLSearchParams(params)
    Object.entries(patch).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)))
    if (!('page' in patch)) next.delete('page')
    setParams(next)
  }
  const clearAll = () => setParams(new URLSearchParams())

  const activeCategory = categories.find((c) => c.slug === filters.category)
  const activeTag = tags.find((t) => t.slug === filters.tag)

  return (
    <div className="home">
      {!filtering && page === 1 && (
        <section className="intro">
          <h1>{site.site_tagline || 'Policies, research and know-how in one place'}</h1>
          <p className="muted">
            {data ? `${nf(data.total)} published documents across ${categories.length} collections.` : ' '}
          </p>
          <ul className="shelf" aria-label="Collections">
            {categories.map((c) => (
              <li key={c.id}>
                <Link to={`/?category=${c.slug}`} style={{ '--tab': categoryColor(c.slug) }}>
                  <span className="shelf-name">{c.name}</span>
                  <span className="shelf-count">{c.document_count}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="browse">
        <aside className={`filters ${showFilters ? 'open' : ''}`} aria-label="Filters">
          <div className="filters-head">
            <h2>Refine</h2>
            {filtering && <button className="link-btn" onClick={clearAll}>Clear all</button>}
          </div>

          <div className="field">
            <label htmlFor="f-category">Collection</label>
            <select id="f-category" value={filters.category} onChange={(e) => update({ category: e.target.value })}>
              <option value="">All collections</option>
              {categories.map((c) => <option key={c.id} value={c.slug}>{c.name} ({c.document_count})</option>)}
            </select>
          </div>

          <div className="field">
            <label htmlFor="f-type">Document type</label>
            <select id="f-type" value={filters.doc_type} onChange={(e) => update({ doc_type: e.target.value })}>
              <option value="">Any type</option>
              {docTypes.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>

          <fieldset className="field date-range">
            <legend>Date added</legend>
            <label htmlFor="f-from" className="sr-only">From</label>
            <input id="f-from" type="date" value={filters.date_from} max={filters.date_to || undefined}
              onChange={(e) => update({ date_from: e.target.value })} />
            <span className="muted">to</span>
            <label htmlFor="f-to" className="sr-only">To</label>
            <input id="f-to" type="date" value={filters.date_to} min={filters.date_from || undefined}
              onChange={(e) => update({ date_to: e.target.value })} />
          </fieldset>

          <div className="field">
            <span className="field-label">Popular tags</span>
            <div className="tag-cloud">
              {tags.map((t) => (
                <button key={t.id} className={`tag ${filters.tag === t.slug ? 'tag-on' : ''}`}
                  aria-pressed={filters.tag === t.slug}
                  onClick={() => update({ tag: filters.tag === t.slug ? '' : t.slug })}>
                  {t.name}
                </button>
              ))}
            </div>
          </div>

          {popular.length > 0 && (
            <div className="field popular">
              <span className="field-label">Most read</span>
              <ol>
                {popular.map((d) => (
                  <li key={d.id}><Link to={`/documents/${d.slug}`}>{d.title}</Link>
                    <span className="muted"> {nf(d.views_count)} views</span></li>
                ))}
              </ol>
            </div>
          )}
        </aside>

        <section className="results" aria-live="polite">
          <div className="results-head">
            <div>
              <h2>
                {q ? <>Results for “{q}”</> : activeCategory ? activeCategory.name : activeTag ? `Tagged “${activeTag.name}”` : 'Latest documents'}
              </h2>
              {data && (
                <p className="muted">
                  {nf(data.total)} {data.total === 1 ? 'document' : 'documents'}
                  {filters.date_from && ` from ${formatDate(filters.date_from)}`}
                  {filters.date_to && ` until ${formatDate(filters.date_to)}`}
                </p>
              )}
            </div>
            <div className="results-tools">
              <button className="btn btn-ghost filters-toggle" aria-expanded={showFilters}
                onClick={() => setShowFilters((s) => !s)}>Filters</button>
              <label htmlFor="sort" className="sr-only">Sort by</label>
              <select id="sort" value={filters.sort || 'latest'} onChange={(e) => update({ sort: e.target.value })}>
                <option value="latest">Newest first</option>
                <option value="oldest">Oldest first</option>
                <option value="views">Most viewed</option>
                <option value="title">Title A–Z</option>
              </select>
            </div>
          </div>

          <Notice>{error}</Notice>
          {!data && !error && <p className="muted">Loading documents…</p>}
          {data && data.items.length === 0 && (
            <div className="empty">
              <h3>No documents match {q ? `“${q}”` : 'these filters'}</h3>
              <p>Try fewer or different words, check the spelling, or remove a filter.</p>
              {filtering && <button className="btn btn-ink" onClick={clearAll}>Show all documents</button>}
            </div>
          )}
          <div className="doc-list">
            {data?.items.map((d, i) => (
              <DocCard key={d.id} doc={d} query={q}
                onOpen={q ? () => logClick(q, d.id, (data.page - 1) * data.page_size + i + 1) : undefined} />
            ))}
          </div>
          {data && <Pagination page={data.page} pages={data.pages}
            onChange={(p) => { update({ page: String(p) }); window.scrollTo({ top: 0 }) }} />}
        </section>
      </div>
    </div>
  )
}
