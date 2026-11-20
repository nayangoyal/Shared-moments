import { useEffect } from 'react'
import Header from './components/Header'
import JudgesSection from './components/JudgesSection'
import Overlays from './components/Overlays'
import SidePanel from './components/SidePanel'
import Toast from './components/Toast'
import { useHashRoute } from './hooks/useHashRoute'
import { useStore } from './store/StoreContext'
import AboutScreen from './screens/AboutScreen'
import FoundTab from './screens/FoundTab'
import MeetScreen from './screens/MeetScreen'
import ProfileScreen from './screens/ProfileScreen'
import ReconnectScreen from './screens/ReconnectScreen'

const SCREENS = {
  reconnect: () => <ReconnectScreen />,
  reunited: () => <FoundTab kind="re" />,
  meet: () => <MeetScreen />,
  newfriends: () => <FoundTab kind="nw" />,
  profile: () => <ProfileScreen />,
}

function Loading() {
  const { loadError, load } = useStore()
  return (
    <div className="loading" role="status">
      {loadError ? (
        <>
          <b className="h2">We couldn't connect</b>
          <p className="muted" style={{ margin: 0 }}>{loadError}</p>
          <button className="btn main" type="button" onClick={load}>Try again</button>
        </>
      ) : (
        <>
          <span className="spinner" aria-hidden="true" />
          <p className="muted" style={{ margin: 0 }}>Opening Shared Moments…</p>
        </>
      )}
    </div>
  )
}

export default function App() {
  const route = useHashRoute()
  const { st, closeOverlay, open, aboutGate } = useStore()

  // Changing tab closes any open dialog and scrolls to the top
  useEffect(() => { closeOverlay(); window.scrollTo(0, 0) }, [route, closeOverlay])
  // Opening a chat, a request or About me also starts at the top
  useEffect(() => { window.scrollTo(0, 0) }, [open.re, open.nw, aboutGate])

  let screen
  if (!st) screen = <Loading />
  else if (aboutGate) screen = <AboutScreen />
  else screen = SCREENS[route]()

  return (
    <>
      <Header route={route} />
      <main className="inner wrap">
        <div style={{ minWidth: 0 }} aria-live="polite">{screen}</div>
        <SidePanel route={route} />
      </main>
      <JudgesSection />
      <Toast />
      <Overlays />
    </>
  )
}
