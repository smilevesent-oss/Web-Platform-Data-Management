import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../auth'

export const ADMIN_SECTIONS = [
  {
    group: 'Content', role: 'Content Manager', items: [
      { to: 'documents', label: 'Documents', perm: 'documents.read_all', desc: 'Create, edit, publish and unpublish documents.' },
      { to: 'taxonomy', label: 'Categories & tags', perm: 'taxonomy.manage', desc: 'Organise collections and tags.' },
    ],
  },
  {
    group: 'Moderation', role: 'Moderator', items: [
      { to: 'comments', label: 'Comments', perm: 'comments.moderate', desc: 'Approve, hide or remove comments.' },
      { to: 'reports', label: 'Reports & spam', perm: ['reports.manage', 'spam.manage'], desc: 'Resolve flags and maintain the spam filter.' },
    ],
  },
  {
    group: 'SEO & data', role: 'Data & SEO Specialist', items: [
      { to: 'seo', label: 'SEO metadata', perm: 'seo.manage', desc: 'Titles, descriptions, keywords and alt text.' },
      { to: 'analytics', label: 'Analytics', perm: 'analytics.view', desc: 'Views, searches and click-through.' },
      { to: 'search-logs', label: 'Search & click log', perm: 'analytics.view', desc: 'Raw query and click events for Phase 2.' },
    ],
  },
  {
    group: 'Administration', role: 'Super Admin', items: [
      { to: 'users', label: 'Users', perm: 'users.manage', desc: 'Accounts, roles and access.' },
      { to: 'roles', label: 'Roles & permissions', perm: 'roles.manage', desc: 'What each role is allowed to do.' },
      { to: 'settings', label: 'Global settings', perm: 'settings.manage', desc: 'Site name, registration, comments.' },
      { to: 'system-logs', label: 'System log', perm: 'logs.view', desc: 'Audit trail of administrative actions.' },
    ],
  },
]

export function visibleSections(can) {
  return ADMIN_SECTIONS.map((s) => ({
    ...s, items: s.items.filter((i) => can(...(Array.isArray(i.perm) ? i.perm : [i.perm]))),
  })).filter((s) => s.items.length)
}

export default function AdminLayout() {
  const { can, user } = useAuth()
  const sections = visibleSections(can)
  return (
    <div className="admin">
      <aside className="admin-nav" aria-label="Workspace">
        <NavLink to="/admin" end className="admin-home-link">Workspace</NavLink>
        <p className="muted small">Signed in as {user.role.display_name}</p>
        {sections.map((s) => (
          <div key={s.group} className="admin-nav-group">
            <h2>{s.group}</h2>
            {s.items.map((i) => <NavLink key={i.to} to={i.to}>{i.label}</NavLink>)}
          </div>
        ))}
        {sections.length === 0 && <p className="muted small">Your role has no workspace permissions.</p>}
      </aside>
      <div className="admin-main">
        <Outlet />
      </div>
    </div>
  )
}
