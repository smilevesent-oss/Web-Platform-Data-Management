export default function Pagination({ page, pages, onChange }) {
  if (!pages || pages <= 1) return null
  const nums = []
  const lo = Math.max(1, page - 2)
  const hi = Math.min(pages, page + 2)
  if (lo > 1) nums.push(1)
  if (lo > 2) nums.push('…l')
  for (let i = lo; i <= hi; i++) nums.push(i)
  if (hi < pages - 1) nums.push('…r')
  if (hi < pages) nums.push(pages)
  return (
    <nav className="pagination" aria-label="Pagination">
      <button className="btn btn-ghost" disabled={page <= 1} onClick={() => onChange(page - 1)}>Previous</button>
      {nums.map((n) =>
        typeof n === 'number' ? (
          <button key={n} className={`page-num ${n === page ? 'current' : ''}`} aria-current={n === page ? 'page' : undefined}
            onClick={() => onChange(n)}>{n}</button>
        ) : <span key={n} className="muted">…</span>
      )}
      <button className="btn btn-ghost" disabled={page >= pages} onClick={() => onChange(page + 1)}>Next</button>
    </nav>
  )
}
