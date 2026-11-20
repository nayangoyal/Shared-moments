import { useRef } from 'react'
import { ACTS, EMPTY_MEET, EXAMPLE_MEET, MIN_WORDS, WHEN } from '../data/data'
import { go } from '../hooks/useHashRoute'
import { words } from '../lib/utils'
import { useStore } from '../store/StoreContext'
import { Chips, Intro, Meter, TopBar } from '../components/ui'

// Meet New: describe the moment you want. Submitting saves a private request; matches show up in New Friends.
export default function MeetScreen() {
  const { meet, setMeet, submitRequest, setOpen, toast, busy } = useStore()
  const moreRef = useRef(null)
  const set = (patch) => setMeet((m) => ({ ...m, ...patch }))

  const n = words(meet.text)
  const level = n < MIN_WORDS ? 'low' : n < 40 ? 'mid' : 'high'
  const text = n < MIN_WORDS ? `${n} words · write at least ${MIN_WORDS} to continue`
    : n < 40 ? `${n} words · good, a little more helps your chances` : `${n} words · great detail, strong chance of a match`

  const togglePick = (a) => set({ picked: meet.picked.includes(a) ? meet.picked.filter((x) => x !== a) : [...meet.picked, a] })

  const find = async () => {
    if (!meet.picked.length) { toast("Pick at least one thing you'd like to do"); return }
    if (n < MIN_WORDS) { moreRef.current?.focus(); toast(`Please describe it in more detail (at least ${MIN_WORDS} words)`); return }
    const result = await submitRequest('nw', { acts: meet.picked.join(', '), when: meet.when, where: meet.area, desc: meet.text.trim() })
    if (result !== 'ok') return
    setMeet((m) => ({ ...EMPTY_MEET, area: m.area }))
    setOpen('nw', null)
    go('newfriends')
    toast("Request saved. We're looking for your people.")
  }

  return (
    <>
      <TopBar title="Meet New" />
      <div className="screen">
        <Intro title="What moment are you looking for?">
          Describe it, and we'll match you with people who want the same. Only you can see this.
        </Intro>
        <div className="mainbox formgrid">
          <div className="field span">
            <span className="lab">What would you like to do?</span>
            <Chips options={ACTS} selected={(a) => meet.picked.includes(a)} onToggle={togglePick} />
          </div>
          <div className="field span">
            <span className="lab">When?</span>
            <Chips options={WHEN} selected={(w) => w === meet.when} onToggle={(w) => set({ when: w })} />
          </div>
          <div className="field span">
            <label htmlFor="area">Where?</label>
            <input className="input" id="area" value={meet.area} onChange={(e) => set({ area: e.target.value })} />
          </div>
          <div className="field span">
            <label htmlFor="more">Describe the moment you want, in detail <span className="hint">(required)</span></label>
            <div className="tip"><b>The more detail you write, the better your chances of a match.</b> Say what you'd like to do, when, what kind of person, and why it matters to you.</div>
            <textarea ref={moreRef} className="input" id="more" value={meet.text} onChange={(e) => set({ text: e.target.value })}
              placeholder="e.g. I've just moved to Bandra and walk at Carter Road most evenings around 7. I'd love a calm walking buddy, any age, who enjoys a cutting chai after." />
            <Meter pct={Math.min(100, Math.round((n / 40) * 100))} level={level} text={text} />
          </div>
          <div className="sticky-go span">
            <button className="btn main full" type="button" onClick={find} disabled={busy}>{busy ? 'Saving…' : 'Find my people'}</button>
            <button className="link center" type="button"
              onClick={() => set({ picked: [...new Set([...meet.picked, ...EXAMPLE_MEET.acts])], when: EXAMPLE_MEET.when, text: EXAMPLE_MEET.text })}>
              Fill an example
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
