import { createContext, useContext, useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth'
import Avatar from './Avatar'

const SiteContext = createContext({})
export const useSite = () => useContext(SiteContext)

function HeaderSearch() {
  const [params] = useSearchParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [q, setQ] = useState(params.get('q') || '')
  useEffect(() => { if (location.pathname === '/') setQ(params.get('q') || '') }, [params, location.pathname])

  const submit = (e) => {
    e.preventDefault()
    const next = new URLSearchParams(location.pathname === '/' ? params : undefined)
    if (q.trim()) next.set('q', q.trim()); else next.delete('q')
    next.delete('page')
    navigate(`/?${next.toString()}`)
  }
  return (
    <form className="header-search" role="search" onSubmit={submit}>
      <label htmlFor="global-search" className="sr-only">Search documents</label>
      <input
        id="global-search"
        type="search"
        placeholder="Search policies, procedures, research…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <button type="submit" className="btn btn-ink">Search</button>
    </form>
  )
}

export default function Layout() {
  const { user, logout, isStaff } = useAuth()
  const [site, setSite] = useState({})
  const [menuOpen, setMenuOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => { api('/site').then(setSite).catch(() => {}) }, [])
  useEffect(() => { setMenuOpen(false) }, [location.pathname])

  return (
    <SiteContext.Provider value={site}>
      <a href="#main" className="skip-link">Skip to content</a>
      <header className="site-header">
        <div className="wrap header-row">
          <Link to="/" className="brand" aria-label="Home">
            <span className="brand-mark" aria-hidden="true" />
            <span className="brand-text">{site.site_name || 'Document Repository'}</span>
          </Link>
          <HeaderSearch />
          <button className="menu-toggle" aria-expanded={menuOpen} onClick={() => setMenuOpen((o) => !o)}>
            Menu
          </button>
          <nav className={`main-nav ${menuOpen ? 'open' : ''}`} aria-label="Main">
            <NavLink to="/" end>Browse</NavLink>
            {isStaff && <NavLink to="/admin">Workspace</NavLink>}
            {user ? (
              <>
                <NavLink to="/profile" className="nav-user">
                  <Avatar name={user.full_name || user.username} url={user.avatar_url} size={28} />
                  <span>{user.full_name || user.username}</span>
                </NavLink>
                <button className="link-btn" onClick={() => { logout(); navigate('/') }}>Sign out</button>
              </>
            ) : (
              <>
                <NavLink to="/login">Sign in</NavLink>
                {site.registration_open !== false && <NavLink to="/register" className="btn btn-ghost">Create account</NavLink>}
              </>
            )}
          </nav>
        </div>
      </header>
      <main id="main" className="wrap main">
        <Outlet />
      </main>
      <footer className="site-footer">
        <div className="wrap">
          <span>{site.site_name || 'Document Repository'}</span>
          <span className="muted">{site.site_tagline}</span>
        </div>
      </footer>
    </SiteContext.Provider>
  )
}
