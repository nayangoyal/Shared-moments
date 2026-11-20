import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { EMPTY_FORM, EMPTY_MEET } from '../data/data'
import { api } from '../lib/api'

const POLL_MS = 4000

const Ctx = createContext(null)

// New "This might be your moment" matches and new replies, comparing two server states
function changes(prev, next) {
  const out = { moments: {}, replies: [] }
  if (!prev) return out
  for (const kind of ['re', 'nw']) {
    const had = new Set(prev[kind].moments.map((m) => m.id))
    const fresh = next[kind].moments.filter((m) => !had.has(m.id))
    if (fresh.length) out.moments[kind] = fresh.length
    for (const c of next[kind].chats) {
      const theirs = (msgs) => (msgs || []).filter((m) => !m.me).length
      if (theirs(next.msgs[c.id]) > theirs(prev.msgs[c.id])) out.replies.push(c.pid)
    }
  }
  return out
}

export function StoreProvider({ children }) {
  // Server state: { rev, me, re: {reqs, moments, chats}, nw: {...}, msgs, people }
  const [st, setSt] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const stRef = useRef(null)

  // Toast
  const [toastText, setToastText] = useState(null)
  const toastTimer = useRef()
  const toast = useCallback((t) => {
    setToastText(t)
    clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToastText(null), 2600)
  }, [])

  // Overlay: { type: 'moment', kind, count } or null
  const [overlay, setOverlay] = useState(null)
  const closeOverlay = useCallback(() => setOverlay(null), [])

  // Screen state kept across tab switches (not saved)
  const [form, setForm] = useState(EMPTY_FORM)
  const [meet, setMeet] = useState(EMPTY_MEET)
  const [open, setOpenState] = useState({ re: null, nw: null })
  const setOpen = useCallback((kind, v) => setOpenState((o) => ({ ...o, [kind]: v })), [])
  // "About me" is asked once, the first time someone sends a request: { kind, data } waiting to be sent
  const [aboutGate, setAboutGate] = useState(null)
  const [busy, setBusy] = useState(false)

  const person = useCallback((pid) => stRef.current?.people[pid] || { n: 'Someone', a: '', place: '', c: '#8a8f96' }, [])

  const apply = useCallback((next, { notify = true } = {}) => {
    if (!next || next.unchanged) return
    const diff = changes(stRef.current, next)
    stRef.current = next
    setSt(next)
    if (!notify) return
    const kinds = Object.keys(diff.moments)
    if (kinds.length) setOverlay({ type: 'moment', kind: kinds[0], count: diff.moments[kinds[0]] })
    if (diff.replies.length) {
      const p = next.people[diff.replies[0]]
      toast(`${(p?.n || 'They').split(' ')[0]} replied`)
    }
  }, [toast])

  const refresh = useCallback(async () => {
    try {
      apply(await api.state(stRef.current?.rev))
    } catch { /* offline for a moment: try again on the next poll */ }
  }, [apply])

  // First load: sign in (anonymously) and fetch this user's state
  const load = useCallback(async () => {
    setLoadError(null)
    try {
      apply(await api.session(), { notify: false })
    } catch (e) {
      setLoadError(e.message || 'Could not connect')
    }
  }, [apply])
  useEffect(() => { load() }, [load])

  // Poll while the page is visible
  useEffect(() => {
    if (!st) return undefined
    const tick = () => { if (document.visibilityState === 'visible') refresh() }
    const id = setInterval(tick, POLL_MS)
    document.addEventListener('visibilitychange', tick)
    return () => { clearInterval(id); document.removeEventListener('visibilitychange', tick) }
  }, [st != null, refresh]) // eslint-disable-line react-hooks/exhaustive-deps

  const run = useCallback(async (fn, okMsg) => {
    try {
      await fn()
      if (okMsg) toast(okMsg)
      await refresh()
      return true
    } catch (e) {
      toast(e.message)
      return false
    }
  }, [refresh, toast])

  // ---- actions ----
  /** Save a private request. Returns 'ok', 'about' (About me needed first) or 'error'. */
  const submitRequest = useCallback(async (kind, data) => {
    setBusy(true)
    try {
      await api.createRequest(kind, data)
      await refresh()
      return 'ok'
    } catch (e) {
      if (e.code === 'about_required') { setAboutGate({ kind, data }); return 'about' }
      toast(e.message)
      return 'error'
    } finally {
      setBusy(false)
    }
  }, [refresh, toast])

  /** Save About me, then send the request that was waiting for it (if any). */
  const saveAbout = useCallback(async (about) => {
    setBusy(true)
    try {
      apply(await api.saveAbout(about), { notify: false })
      const pending = aboutGate
      setAboutGate(null)
      if (pending) {
        await api.createRequest(pending.kind, pending.data)
        await refresh()
      }
      return pending
    } catch (e) {
      toast(e.message)
      return false
    } finally {
      setBusy(false)
    }
  }, [aboutGate, apply, refresh, toast])

  const dismissMoment = useCallback((kind, matchId) => run(() => api.dismiss(matchId), "Okay, we'll keep looking"), [run])
  const removeRequest = useCallback((kind, id) => run(() => api.removeRequest(id), 'Request removed'), [run])

  const sendMessage = useCallback(async (kind, matchId, pid, text) => {
    // show it straight away; the server confirms on the next refresh
    const cur = stRef.current
    const box = cur[kind]
    const isMoment = box.moments.some((m) => m.id === matchId)
    const optimistic = {
      ...cur,
      msgs: { ...cur.msgs, [matchId]: [...(cur.msgs[matchId] || []), { me: true, t: text }] },
      [kind]: isMoment
        ? { ...box, moments: box.moments.filter((m) => m.id !== matchId), chats: [{ id: matchId, pid }, ...box.chats] }
        : box,
    }
    stRef.current = optimistic
    setSt(optimistic)
    return run(() => api.send(matchId, text))
  }, [run])

  const reset = useCallback(async (persona) => {
    setOpenState({ re: null, nw: null })
    setAboutGate(null)
    stRef.current = null
    setSt(null) // show the loading screen, never the previous user's data, while the server resets
    try {
      apply(await api.reset(persona), { notify: false })
      toast(persona === 'new' ? "Now you're a brand-new user" : "Now you're a returning user")
    } catch (e) {
      toast(e.message)
      await load()
    }
  }, [apply, load, toast])
  const becomeNew = useCallback(() => reset('new'), [reset])
  const becomeOld = useCallback(() => reset('returning'), [reset])

  const value = useMemo(() => ({
    st, loadError, load, busy, toast, toastText, overlay, closeOverlay, person,
    form, setForm, meet, setMeet, open, setOpen, aboutGate, setAboutGate,
    submitRequest, saveAbout, dismissMoment, removeRequest, sendMessage, becomeNew, becomeOld,
  }), [st, loadError, load, busy, toast, toastText, overlay, closeOverlay, person, form, meet, open, setOpen,
    aboutGate, submitRequest, saveAbout, dismissMoment, removeRequest, sendMessage, becomeNew, becomeOld])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export const useStore = () => useContext(Ctx)
