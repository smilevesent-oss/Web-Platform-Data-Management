import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="empty">
      <h2>Page not found</h2>
      <p>The address may be mistyped, or the page has moved.</p>
      <Link to="/" className="btn btn-ink">Browse documents</Link>
    </div>
  )
}
