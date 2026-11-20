import { useState } from 'react'
import { EMPTY_FORM, EMPTY_MEET, EXAMPLE_ABOUT } from '../data/data'
import { go } from '../hooks/useHashRoute'
import { useStore } from '../store/StoreContext'
import AboutFields, { EMPTY_ABOUT } from '../components/AboutFields'
import { Intro, TopBar } from '../components/ui'

// Asked once, before the first request: how old friends would remember YOU.
// Matching is two-way, so a lost friend can only find you if they describe you too.
export default function AboutScreen() {
  const { st, aboutGate, setAboutGate, saveAbout, setForm, setMeet, setOpen, toast, busy } = useStore()
  const [a, setA] = useState({ ...EMPTY_ABOUT, ...(st?.me?.about || {}) })
  const kind = aboutGate?.kind

  const save = async () => {
    if (!a.name.trim()) { toast('Please add your name'); return }
    const pending = await saveAbout(a)
    if (pending === false) return
    if (pending?.kind === 're') { setForm(EMPTY_FORM); setOpen('re', null); go('reunited'); toast("Request saved. We'll look out for them.") }
    else if (pending?.kind === 'nw') { setMeet((m) => ({ ...EMPTY_MEET, area: m.area })); setOpen('nw', null); go('newfriends'); toast("Request saved. We're looking for your people.") }
    else toast('Saved')
  }

  return (
    <>
      <TopBar title="About you" onBack={() => setAboutGate(null)} />
      <div className="screen">
        <Intro title="First, a little about you">
          {kind === 'nw'
            ? 'People you match with will see your name, age and area. Nothing else.'
            : 'Matching works both ways: your friend finds you when they describe you too. So tell us how old friends would remember you.'}
        </Intro>
        <div className="mainbox formgrid">
          <div className="tip span"><b>Only your name, age and area are ever shown,</b> and only to people you match with. The rest is used for matching and stays private. You can change it later in Profile.</div>
          <AboutFields value={a} onChange={setA} />
          <div className="sticky-go span">
            <button className="btn main full" type="button" onClick={save} disabled={busy}>
              {busy ? 'Saving…' : aboutGate ? (kind === 'nw' ? 'Save and find my people' : 'Save and start looking') : 'Save'}
            </button>
            <button className="link center" type="button" onClick={() => setA({ ...EXAMPLE_ABOUT })}>Fill an example</button>
          </div>
        </div>
      </div>
    </>
  )
}
