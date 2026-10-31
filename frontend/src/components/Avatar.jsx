import { initials } from '../util'

export default function Avatar({ name, url, size = 32 }) {
  const style = { width: size, height: size, fontSize: Math.round(size * 0.4) }
  if (url) return <img className="avatar" src={url} alt="" style={style} />
  return <span className="avatar" style={style} aria-hidden="true">{initials(name)}</span>
}
