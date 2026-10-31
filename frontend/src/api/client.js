// Thin fetch wrapper around the FastAPI backend.
const BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')
const TOKEN_KEY = 'docrepo.token'

export function getToken() {
  try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
}
export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch { /* storage unavailable */ }
}

export class ApiError extends Error {
  constructor(status, message, details) {
    super(message)
    this.status = status
    this.details = details
  }
}

function formatDetail(detail) {
  if (!detail) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = Array.isArray(d.loc) ? d.loc.filter((x) => x !== 'body' && x !== 'query').join('.') : ''
        return field ? `${field}: ${d.msg}` : d.msg
      })
      .join('; ')
  }
  return JSON.stringify(detail)
}

export async function api(path, { method = 'GET', body, params, raw = false } = {}) {
  let url = `${BASE}${path}`
  if (params) {
    const qs = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') qs.append(k, v)
    })
    const s = qs.toString()
    if (s) url += `?${s}`
  }
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let res
  try {
    res = await fetch(url, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Check that the API is running.')
  }
  if (raw) return res
  const text = await res.text()
  const data = text ? (() => { try { return JSON.parse(text) } catch { return text } })() : null
  if (!res.ok) {
    const msg = formatDetail(data && data.detail) || `Request failed (${res.status})`
    throw new ApiError(res.status, msg, data)
  }
  return data
}

// One id per browser tab session; groups searches and clicks for Phase 2.
export function getSessionId() {
  try {
    let id = sessionStorage.getItem('docrepo.session')
    if (!id) {
      id = (crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2)).replace(/-/g, '').slice(0, 32)
      sessionStorage.setItem('docrepo.session', id)
    }
    return id
  } catch {
    return null
  }
}

export function logClick(query, docId, rank) {
  // Fire-and-forget; navigation must not wait for logging.
  api('/logs/click', {
    method: 'POST',
    body: { query_string: query, clicked_doc_id: docId, rank_position: rank, session_id: getSessionId() },
  }).catch(() => {})
}
