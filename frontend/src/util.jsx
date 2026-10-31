import { Fragment, useEffect, useState } from 'react'

export function formatDate(iso, withTime = false) {
  if (!iso) return '—'
  const d = new Date(iso)
  const opts = { year: 'numeric', month: 'short', day: 'numeric' }
  if (withTime) Object.assign(opts, { hour: '2-digit', minute: '2-digit' })
  return d.toLocaleString('en-GB', opts)
}

export function timeAgo(iso) {
  const s = Math.round((Date.now() - new Date(iso).getTime()) / 1000)
  if (s < 60) return 'just now'
  const m = Math.round(s / 60); if (m < 60) return `${m} min ago`
  const h = Math.round(m / 60); if (h < 24) return `${h} h ago`
  const d = Math.round(h / 24); if (d < 30) return `${d} days ago`
  return formatDate(iso)
}

export const nf = (n) => (n ?? 0).toLocaleString('en-US')

// Category colour drives the "file tab" on each document.
const CATEGORY_COLORS = {
  'human-resources': '#B5654A',
  'information-security': '#2F5D8A',
  'engineering-architecture': '#5A4E9C',
  'operations-sops': '#8A6D1F',
  'finance-procurement': '#2F6F5E',
  'legal-compliance': '#7A3B5E',
  'research-market-insights': '#1F7287',
  'product-customer-experience': '#9C4A2F',
}
export function categoryColor(slug) {
  if (!slug) return '#5B6577'
  if (CATEGORY_COLORS[slug]) return CATEGORY_COLORS[slug]
  let h = 0
  for (const c of slug) h = (h * 31 + c.charCodeAt(0)) % 360
  return `hsl(${h} 38% 38%)`
}

function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') }

// Wrap the search terms in <mark>; returns React nodes (no innerHTML).
export function Highlight({ text, query }) {
  const terms = (query || '').split(/\s+/).filter((t) => t.length > 1)
  if (!terms.length || !text) return text || null
  const re = new RegExp(`(${terms.map(escapeRe).join('|')})`, 'gi')
  return text.split(re).map((part, i) =>
    i % 2 === 1 ? <mark key={i}>{part}</mark> : <Fragment key={i}>{part}</Fragment>
  )
}

// Body excerpt around the first matching term, for search results.
export function snippetFor(content, query, len = 220) {
  const terms = (query || '').toLowerCase().split(/\s+/).filter(Boolean)
  const lower = content.toLowerCase()
  let idx = -1
  for (const t of terms) { idx = lower.indexOf(t); if (idx >= 0) break }
  if (idx < 0) return null
  const start = Math.max(0, idx - 70)
  let s = content.slice(start, start + len).replace(/\s+/g, ' ')
  return (start > 0 ? '…' : '') + s + (start + len < content.length ? '…' : '')
}

export function useDebounced(value, ms = 300) {
  const [v, setV] = useState(value)
  useEffect(() => { const t = setTimeout(() => setV(value), ms); return () => clearTimeout(t) }, [value, ms])
  return v
}

export function useTitle(title) {
  useEffect(() => { document.title = title ? `${title} · Document Repository` : 'Document Repository' }, [title])
}

export function initials(name) {
  return (name || '?').split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join('')
}
