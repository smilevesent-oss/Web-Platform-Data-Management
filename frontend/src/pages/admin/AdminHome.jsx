import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../auth'
import { nf, useTitle } from '../../util'
import { visibleSections } from './AdminLayout'

export default function AdminHome() {
  useTitle('Workspace')
  const { can, user } = useAuth()
  const [counts, setCounts] = useState({})

  useEffect(() => {
    const jobs = []
    if (can('documents.read_all')) {
      jobs.push(api('/admin/documents', { params: { status: 'draft', page_size: 1 } }).then((d) => ({ drafts: d.total })))
    }
    if (can('comments.moderate')) jobs.push(api('/moderation/stats').then((s) => ({ pending: s.comments.pending, spam: s.comments.spam, reports: s.open_reports })))
    if (can('seo.manage')) jobs.push(api('/seo/documents', { params: { only_issues: true, page_size: 1 } }).then((d) => ({ seo: d.total })))
    if (can('analytics.view')) jobs.push(api('/analytics/summary', { params: { days: 7 } }).then((a) => ({ searches: a.totals.searches_in_period, views: a.totals.views_in_period })))
    if (can('users.manage')) jobs.push(api('/admin/users', { params: { page_size: 1 } }).then((d) => ({ users: d.total })))
    Promise.allSettled(jobs).then((rs) => setCounts(Object.assign({}, ...rs.filter((r) => r.status === 'fulfilled').map((r) => r.value))))
  }, [can])

  const facts = [
    counts.drafts !== undefined && { n: counts.drafts, label: 'drafts waiting to be published', to: 'documents?status=draft' },
    counts.pending !== undefined && { n: counts.pending, label: 'comments awaiting approval', to: 'comments?status=pending' },
    counts.reports !== undefined && { n: counts.reports, label: 'open reports', to: 'reports' },
    counts.seo !== undefined && { n: counts.seo, label: 'documents with SEO issues', to: 'seo' },
    counts.searches !== undefined && { n: counts.searches, label: 'searches in the last 7 days', to: 'analytics' },
    counts.views !== undefined && { n: counts.views, label: 'document views in the last 7 days', to: 'analytics' },
    counts.users !== undefined && { n: counts.users, label: 'user accounts', to: 'users' },
  ].filter(Boolean)

  return (
    <div>
      <h1>Welcome, {user.full_name || user.username}</h1>
      <p className="muted">Your role: <strong>{user.role.display_name}</strong>. These are the areas you can work on.</p>

      {facts.length > 0 && (
        <ul className="todo-list">
          {facts.map((f) => (
            <li key={f.label}><Link to={f.to}><strong>{nf(f.n)}</strong> {f.label}</Link></li>
          ))}
        </ul>
      )}

      {visibleSections(can).map((s) => (
        <section key={s.group} className="admin-section">
          <h2>{s.group} <span className="muted small">({s.role})</span></h2>
          <div className="admin-tiles">
            {s.items.map((i) => (
              <Link key={i.to} to={i.to} className="admin-tile">
                <strong>{i.label}</strong>
                <span className="muted">{i.desc}</span>
              </Link>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
