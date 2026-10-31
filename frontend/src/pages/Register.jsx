import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import Notice from '../components/Notice'
import { useSite } from '../components/Layout'
import { useTitle } from '../util'

export default function Register() {
  useTitle('Create account')
  const site = useSite()
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', email: '', full_name: '', password: '', confirm: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm) { setError('The two passwords do not match.'); return }
    setBusy(true); setError(null)
    try {
      await register({ username: form.username.trim(), email: form.email.trim(), full_name: form.full_name.trim(), password: form.password })
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (site.registration_open === false) {
    return <div className="empty"><h2>Registration is closed</h2><p>Ask an administrator to create an account for you.</p></div>
  }

  return (
    <div className="auth-page single">
      <form className="panel auth-form" onSubmit={submit}>
        <h1>Create an account</h1>
        <Notice>{error}</Notice>
        <div className="field">
          <label htmlFor="r-name">Full name</label>
          <input id="r-name" autoComplete="name" value={form.full_name} onChange={set('full_name')} maxLength={120} />
        </div>
        <div className="field">
          <label htmlFor="r-user">Username</label>
          <input id="r-user" autoComplete="username" required pattern="[A-Za-z0-9_.]{3,50}" value={form.username}
            onChange={set('username')} aria-describedby="r-user-hint" />
          <small id="r-user-hint" className="muted">3–50 letters, numbers, dots or underscores. Colleagues tag you with @username.</small>
        </div>
        <div className="field">
          <label htmlFor="r-email">Work e-mail</label>
          <input id="r-email" type="email" autoComplete="email" required value={form.email} onChange={set('email')} />
        </div>
        <div className="field">
          <label htmlFor="r-pass">Password</label>
          <input id="r-pass" type="password" autoComplete="new-password" required minLength={8} value={form.password} onChange={set('password')} />
          <small className="muted">At least 8 characters.</small>
        </div>
        <div className="field">
          <label htmlFor="r-confirm">Repeat password</label>
          <input id="r-confirm" type="password" autoComplete="new-password" required minLength={8} value={form.confirm} onChange={set('confirm')} />
        </div>
        <button className="btn btn-ink btn-block" disabled={busy}>{busy ? 'Creating account…' : 'Create account'}</button>
        <p className="muted">Already registered? <Link to="/login">Sign in</Link></p>
      </form>
    </div>
  )
}
