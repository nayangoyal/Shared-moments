// Small shared building blocks
import { BackIcon } from './Icons'

export const Tick = ({ big }) => (
  <span className="tick" style={big ? { width: 22, height: 22, fontSize: 13 } : undefined} aria-label="Verified">✓</span>
)

export const Avatar = ({ color, children }) => <span className="av" style={{ '--c': color }}>{children}</span>

export function TopBar({ title, onBack }) {
  return (
    <div className="head">
      {onBack && <button className="back" type="button" onClick={onBack}><BackIcon /> Back</button>}
      <span className="eyebrow">{title}</span>
    </div>
  )
}

export const Intro = ({ title, children }) => (
  <div className="intro">
    <h2>{title}</h2>
    {children && <p className="muted">{children}</p>}
  </div>
)

// Single- or multi-select chip row. selected(value) -> bool
export const Chips = ({ options, selected, onToggle }) => (
  <div className="chips">
    {options.map((o) => (
      <button key={o} type="button" className="chip" aria-pressed={selected(o)} onClick={() => onToggle(o)}>{o}</button>
    ))}
  </div>
)

// Progress meter under a textarea. level: 'low' | 'mid' | 'high'
export const Meter = ({ pct, level, text }) => (
  <>
    <div className="meter" aria-hidden="true"><span className={level} style={{ width: pct + '%' }} /></div>
    <span className="hint" aria-live="polite">{text}</span>
  </>
)

export const EmptyState = ({ icon, title, text, children }) => (
  <div className="empty">
    <div className="circle">{icon}</div>
    <b className="h2">{title}</b>
    <p className="muted" style={{ margin: 0 }}>{text}</p>
    {children}
  </div>
)
