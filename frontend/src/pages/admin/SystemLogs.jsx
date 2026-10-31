import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import Notice from '../../components/Notice'
import Pagination from '../../components/Pagination'
import { formatDate, nf, useDebounced, useTitle } from '../../util'

export default function SystemLogs() {
  useTitle('System log')
  const [action, setAction] = useState('')
  const da = useDebounced(action)
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  useEffect(() => { api('/admin/system-logs', { params: { action: da, page } }).then(setData).catch((e) => setErr(e.message)) }, [da, page])

  return (
    <div>
      <h1>System log</h1>
      <p className="muted">Sign-ins, failed sign-ins and every administrative change, newest first.</p>
      <Notice>{err}</Notice>
      <div className="toolbar">
        <label htmlFor="sl-action" className="sr-only">Filter by action</label>
        <input id="sl-action" type="search" list="actions" placeholder="Filter by action, e.g. document. or auth.login_failed"
          value={action} onChange={(e) => { setAction(e.target.value); setPage(1) }} />
        <datalist id="actions">
          {['auth.login', 'auth.login_failed', 'user.', 'role.', 'document.', 'comment.', 'report.', 'seo.', 'setting.'].map((a) => <option key={a} value={a} />)}
        </datalist>
        {data && <span className="muted">{nf(data.total)} entries</span>}
      </div>
      {!data ? <p className="muted">Loading…</p> : (
        <div className="table-wrap">
          <table className="compact">
            <thead><tr><th>Time</th><th>Who</th><th>Action</th><th>Target</th><th>Details</th><th>IP</th></tr></thead>
            <tbody>
              {data.items.map((l) => (
                <tr key={l.id}>
                  <td>{formatDate(l.created_at, true)}</td>
                  <td>{l.user ? `@${l.user.username}` : <span className="muted">anonymous</span>}</td>
                  <td><code>{l.action}</code></td>
                  <td>{l.entity_type ? `${l.entity_type} ${l.entity_id ?? ''}` : ''}</td>
                  <td className="small details">{l.detail ? JSON.stringify(l.detail) : ''}</td>
                  <td className="muted small">{l.ip_address}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && <Pagination page={data.page} pages={data.pages} onChange={setPage} />}
    </div>
  )
}
