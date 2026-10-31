import { Link } from 'react-router-dom'
import { categoryColor, formatDate, Highlight, nf } from '../util'

export default function DocCard({ doc, query, onOpen }) {
  const color = categoryColor(doc.category?.slug)
  return (
    <article className="doc-card" style={{ '--tab': color }}>
      <div className="doc-card-tab">
        <span>{doc.doc_type}</span>
      </div>
      <div className="doc-card-body">
        <h3 className="doc-card-title">
          <Link to={`/documents/${doc.slug}`} onClick={onOpen}>
            <Highlight text={doc.title} query={query} />
          </Link>
        </h3>
        <p className="doc-card-summary"><Highlight text={doc.summary} query={query} /></p>
        <div className="doc-card-meta">
          {doc.category && (
            <Link to={`/?category=${doc.category.slug}`} className="cat-link" style={{ color }}>{doc.category.name}</Link>
          )}
          <span>{doc.author?.full_name || doc.author?.username || 'Unknown author'}</span>
          <time dateTime={doc.created_at}>{formatDate(doc.created_at)}</time>
          <span>{nf(doc.views_count)} views</span>
        </div>
        {doc.tags?.length > 0 && (
          <ul className="tag-list" aria-label="Tags">
            {doc.tags.map((t) => (
              <li key={t.id}><Link to={`/?tag=${t.slug}`} className="tag">{t.name}</Link></li>
            ))}
          </ul>
        )}
      </div>
    </article>
  )
}
