import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import Notice from '../components/Notice'
import { useTitle } from '../util'

const DEMO = [
  ['superadmin', 'Super Admin'],
  ['content.manager', 'Content Manager'],
  ['moderator', 'Moderator'],
  ['seo.analyst', 'Data & SEO Specialist'],
  ['sarah.lee', 'Member'],
]

export default function Login() {
  useTitle('Sign in')
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try {
      const u = await login(username.trim(), password)
      navigate(u.permissions.length ? '/admin' : '/')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="panel auth-form" onSubmit={submit}>
        <h1>Sign in</h1>
        <Notice>{error}</Notice>
        <div className="field">
          <label htmlFor="username">Username or e-mail</label>
          <input id="username" autoComplete="username" required value={username} onChange={(e) => setUsername(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" autoComplete="current-password" required value={password}
            onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button className="btn btn-ink btn-block" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
        <p className="muted">New here? <Link to="/register">Create an account</Link></p>
      </form>
      <aside className="panel demo-accounts">
        <h2>Demo accounts</h2>
        <p className="muted small">Every demo account uses the password <code>Password123!</code></p>
        <ul>
          {DEMO.map(([u, role]) => (
            <li key={u}>
              <button type="button" className="link-btn" onClick={() => { setUsername(u); setPassword('Password123!') }}>
                {u}
              </button>
              <span className="muted">{role}</span>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  )
}
