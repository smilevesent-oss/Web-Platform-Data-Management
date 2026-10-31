export default function Notice({ kind = 'error', children, onClose }) {
  if (!children) return null
  return (
    <div className={`notice notice-${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      <span>{children}</span>
      {onClose && <button className="link-btn" onClick={onClose} aria-label="Dismiss">Dismiss</button>}
    </div>
  )
}
