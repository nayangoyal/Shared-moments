import { SOLS } from '../data/data'
import { go } from '../hooks/useHashRoute'
import { useStore } from '../store/StoreContext'

const STEPS = [
  ['Reconnect', <>the site opens straight into a form. You describe the friend you lost. That becomes your private request.</>],
  ['Reunited', <>your requests (waiting for a match), then <i>"This might be your moment"</i> when someone matches, then the friends you're chatting with.</>],
  ['Meet New', <>describe the moment you want. That becomes a request too.</>],
  ['New Friends', <>the same layout as Reunited, for new people.</>],
]

export default function JudgesSection() {
  const { becomeNew, becomeOld } = useStore()
  return (
    <section className="judges">
      <div className="inner">
        <div className="notes" aria-label="Notes for the judges">
          <p className="muted label">FOR THE JUDGES</p>
          <h2>You describe. We match. Nobody browses people.</h2>
          <div className="box">
            {STEPS.map(([t, d], i) => (
              <div className="r" key={t}><b>{i + 1}</b><span><b style={{ color: 'inherit' }}>{t}</b>: {d}</span></div>
            ))}
          </div>
          <p className="muted label">TRY IT AS</p>
          <div className="seg">
            <button className="btn small" type="button" onClick={() => { becomeNew(); go('reconnect') }}>A new user (empty)</button>
            <button className="btn small" type="button" onClick={() => { becomeOld(); go('reunited') }}>A returning user</button>
          </div>
          <p className="muted" style={{ margin: 0, fontSize: 15 }}>
            As <b>a new user</b>: on Reconnect, tap <b>Fill an example</b> and send it. You'll be asked about you once: tap <b>Fill an example</b> there too
            (you're Rahul, "Golu"). Gemini checks that you and Aarav describe each other, and a match appears in a few seconds. Try the name <b>Riya</b> to see a request that waits.
          </p>
        </div>
        <div className="notes">
          <p className="muted label">IF YOUR FRIEND ISN'T ON THE SITE</p>
          <div className="sols">
            {SOLS.map((s) => (
              <div className="sol" key={s.t}>
                <b>{s.t}</b>
                <p>{s.d}</p>
                <span className={'tag' + (s.live ? ' live' : '')}>{s.live ? 'Working in this demo' : 'Next to build'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
