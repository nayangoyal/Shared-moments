import { useEffect } from 'react'
import Header from './components/Header'
import JudgesSection from './components/JudgesSection'
import Overlays from './components/Overlays'
import SidePanel from './components/SidePanel'
import Toast from './components/Toast'
import { useHashRoute } from './hooks/useHashRoute'
import { useStore } from './store/StoreContext'
import FoundTab from './screens/FoundTab'
import MeetScreen from './screens/MeetScreen'
import ReconnectScreen from './screens/ReconnectScreen'

const SCREENS = {
  reconnect: () => <ReconnectScreen />,
  reunited: () => <FoundTab kind="re" />,
  meet: () => <MeetScreen />,
  newfriends: () => <FoundTab kind="nw" />,
}

export default function App() {
  const route = useHashRoute()
  const { closeOverlay, open } = useStore()

  // Changing tab closes any open dialog and scrolls to the top
  useEffect(() => { closeOverlay(); window.scrollTo(0, 0) }, [route, closeOverlay])
  // Opening a chat or request inside a tab also starts at the top
  useEffect(() => { window.scrollTo(0, 0) }, [open.re, open.nw])

  return (
    <>
      <Header route={route} />
      <main className="inner wrap">
        <div style={{ minWidth: 0 }} aria-live="polite">{SCREENS[route]()}</div>
        <SidePanel route={route} />
      </main>
      <JudgesSection />
      <Toast />
      <Overlays />
    </>
  )
}
