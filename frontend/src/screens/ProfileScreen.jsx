import { useEffect, useState } from 'react'
import { EXAMPLE_ABOUT } from '../data/data'
import { useStore } from '../store/StoreContext'
import AboutFields, { EMPTY_ABOUT } from '../components/AboutFields'
import { Avatar, Intro, Tick, TopBar } from '../components/ui'

// Your profile: what others see, how old friends would remember you (used for matching), your data.
export default function ProfileScreen() {
  const { st, saveAbout, deleteMyData, toast, busy } = useStore()
  const saved = { ...EMPTY_ABOUT, ...(st.me.about || {}) }
  const [a, setA] = useState(saved)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const changed = JSON.stringify(a) !== JSON.stringify(saved)

  // when the saved profile changes (e.g. after "A new user"), show it
  useEffect(() => { setA({ ...EMPTY_ABOUT, ...(st.me.about || {}) }) }, [JSON.stringify(st.me.about)]) // eslint-disable-line react-hooks/exhaustive-deps

  const save = async () => {
    if (!a.name.trim()) { toast('Please add your name'); return }
    if ((await saveAbout(a)) !== false) {
      toast(st.re.reqs.length || st.nw.reqs.length ? "Saved. We're re-checking your requests." : 'Saved')
    }
  }

  const remove = async () => {
    if (!confirmDelete) { setConfirmDelete(true); return }
    setConfirmDelete(false)
    await deleteMyData()
  }

  const card = a.name.trim() ? { n: a.name.trim(), a: a.age, place: a.place, c: st.me.card?.c || '#c2552d' } : null
  const count = (kind) => st[kind].reqs.length
  const matches = st.re.moments.length + st.nw.moments.length
  const chats = st.re.chats.length + st.nw.chats.length

  return (
    <>
      <TopBar title="Profile" />
      <div className="screen">
        <Intro title="Your profile">
          How old friends would remember you. It's how someone looking for you finds you, so keep it accurate.
        </Intro>

        {st.me.isDemo && (
          <div className="nudge">
            <b className="h2">You're using the demo identity</b>
            <p className="muted" style={{ margin: 0 }}>
              Right now you're <b style={{ color: 'var(--ink)' }}>Rahul Sharma, "Golu"</b> from the example. Demo identities only match the
              demo people (like Aarav). To find a real friend, replace these details with your own and save.
            </p>
          </div>
        )}

        <div className="section">
          <h3>What others see</h3>
          <div className="mainbox listbox">
            <div className="row">
              {card ? (
                <>
                  <Avatar color={card.c}>{card.n[0].toUpperCase()}</Avatar>
                  <span className="txt">
                    <span className="name">{card.n}{card.a ? `, ${card.a}` : ''}<Tick /></span>
                    <span className="sub">{card.place || 'Area not added'}</span>
                  </span>
                </>
              ) : <span className="muted">Add your name to see your card.</span>}
            </div>
          </div>
          <p className="muted small-note">Only people you match with see this. Everything else stays private and is used only for matching.</p>
        </div>

        <div className="mainbox formgrid">
          <AboutFields value={a} onChange={setA} />
          <div className="sticky-go span">
            <button className="btn main full" type="button" onClick={save} disabled={busy || !changed}>
              {busy ? 'Saving…' : changed ? 'Save changes' : 'Saved'}
            </button>
            {!st.me.hasAbout && <button className="link center" type="button" onClick={() => setA({ ...EXAMPLE_ABOUT })}>Fill an example</button>}
          </div>
        </div>

        <div className="section">
          <h3>Your activity</h3>
          <div className="stats">
            <a className="stat" href="#reunited"><b>{count('re')}</b><span>Friends you're looking for</span></a>
            <a className="stat" href="#newfriends"><b>{count('nw')}</b><span>Meet New requests</span></a>
            <a className="stat" href="#reunited"><b>{matches}</b><span>Possible matches</span></a>
            <a className="stat" href="#reunited"><b>{chats}</b><span>Chats</span></a>
          </div>
        </div>

        <div className="section">
          <h3>Your data</h3>
          <div className="mainbox stack">
            <p className="muted" style={{ margin: 0 }}>
              Delete your profile, all your requests, matches and chats. This can't be undone. We never sell or share your data.
            </p>
            <button className={'btn ' + (confirmDelete ? 'danger' : '')} type="button" onClick={remove} disabled={busy}
              onBlur={() => setConfirmDelete(false)}>
              {confirmDelete ? 'Tap again to delete everything' : 'Delete all my data'}
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
