import { useEffect } from 'react'
import { go } from '../hooks/useHashRoute'
import { useStore } from '../store/StoreContext'
import { SparkIcon } from './Icons'

// "This might be your moment": shown when a saved request finds a match
export default function Overlays() {
  const { overlay: o, closeOverlay, setOpen } = useStore()

  useEffect(() => {
    if (!o) return
    const onKey = (e) => e.key === 'Escape' && closeOverlay()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [o, closeOverlay])

  if (!o || o.type !== 'moment') return null
  const n = o.count
  const see = () => {
    closeOverlay()
    setOpen(o.kind, null)
    go(o.kind === 're' ? 'reunited' : 'newfriends')
  }

  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="momentTitle" onClick={(e) => e.target === e.currentTarget && closeOverlay()}>
      <div className="match">
        <div className="empty" style={{ padding: 0 }}><div className="circle"><SparkIcon /></div></div>
        <b id="momentTitle" style={{ fontSize: 26 }}>This might be your moment</b>
        <p className="muted" style={{ margin: 0 }}>
          {n === 1 ? 'Someone' : `${n} people`} on Shared Moments {n === 1 ? 'matches' : 'match'} your request.
        </p>
        <button className="btn main full" type="button" onClick={see} autoFocus>See who</button>
        <button className="btn full" type="button" onClick={closeOverlay}>Later</button>
      </div>
    </div>
  )
}
