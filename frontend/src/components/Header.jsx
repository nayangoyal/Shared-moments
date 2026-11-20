import { useStore } from '../store/StoreContext'
import { HeartIcon, PairIcon, PeopleIcon, SearchIcon } from './Icons'

export default function Header({ route }) {
  const { st } = useStore()
  const tabs = [
    { id: 'reconnect', label: 'Reconnect', icon: <SearchIcon /> },
    // badge = possible matches you haven't answered yet
    { id: 'reunited', label: 'Reunited', icon: <PairIcon />, n: st.re.moments.length },
    { id: 'meet', label: 'Meet New', icon: <PeopleIcon /> },
    { id: 'newfriends', label: 'New Friends', icon: <HeartIcon />, n: st.nw.moments.length },
  ]
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
      </div>
    </header>
  )
}
