import { useStore } from '../store/StoreContext'
import { HeartIcon, PairIcon, PeopleIcon, SearchIcon } from './Icons'

export default function Header({ route }) {
  const { st } = useStore()
  const tabs = [
    { id: 'reconnect', label: 'Reconnect', icon: <SearchIcon /> },
    // badge = possible matches you haven't answered yet
    { id: 'reunited', label: 'Reunited', icon: <PairIcon />, n: st?.re.moments.length || 0 },
    { id: 'meet', label: 'Meet New', icon: <PeopleIcon /> },
    { id: 'newfriends', label: 'New Friends', icon: <HeartIcon />, n: st?.nw.moments.length || 0 },
  ]
  const me = st?.me
  const initial = (me?.card?.n || '').trim()[0]?.toUpperCase()
  return (
    <header className="site-head">
      <div className="inner">
        <a className="brand" href="#reconnect"><i>S</i>Shared Moments</a>
        <nav className="site-nav" aria-label="Main">
          {tabs.map((t) => (
            <a key={t.id} href={'#' + t.id} aria-current={route === t.id ? 'page' : undefined}>
              <span className="ic">{t.icon}{t.n > 0 && <span className="n">{t.n}</span>}</span>
              {t.label}
            </a>
          ))}
        </nav>
        <a className="me-btn" href="#profile" aria-current={route === 'profile' ? 'page' : undefined}
          aria-label="Your profile" title="Your profile" style={{ '--c': me?.card?.c || 'var(--muted)' }}>
          {me?.hasAbout && initial ? initial : <PersonIcon />}
          {me?.isDemo && <span className="demo-dot" aria-hidden="true" />}
        </a>
      </div>
    </header>
  )
}

const PersonIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
    <circle cx="12" cy="8" r="4" /><path d="M4 21c.8-4 4-6 8-6s7.2 2 8 6" />
  </svg>
)
