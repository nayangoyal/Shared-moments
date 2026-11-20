import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { EMPTY_FORM, EMPTY_MEET, REPLY, byId, seedNew, seedOld } from '../data/data'
import { firstName, matchNew, matchOld } from '../lib/utils'

const KEY = 'sharedmoments-v6'
const MATCH_DELAY_MS = 3000
const REPLY_DELAY_MS = 2500

function load() {
  try {
    const s = JSON.parse(localStorage.getItem(KEY))
    if (s && s.re && s.nw && s.msgs) return s
  } catch { /* storage blocked or bad JSON: start fresh */ }
  return seedOld()
}

const Ctx = createContext(null)

export function StoreProvider({ children }) {
  // Saved in this browser: requests, possible matches, chats and messages
  const [st, setSt] = useState(load)
  const stRef = useRef(st)
  stRef.current = st
  useEffect(() => {
    try { localStorage.setItem(KEY, JSON.stringify(st)) } catch { /* ignore */ }
  }, [st])

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
  const [form, setForm] = useState(EMPTY_FORM) // Reconnect form
  const [meet, setMeet] = useState(EMPTY_MEET) // Meet New form
  // What's open inside Reunited / New Friends: null | { type: 'chat' | 'req', id }
  const [open, setOpenState] = useState({ re: null, nw: null })
  const setOpen = useCallback((kind, v) => setOpenState((o) => ({ ...o, [kind]: v })), [])

  const updateBox = useCallback((kind, fn) => setSt((s) => ({ ...s, [kind]: fn(s[kind]) })), [])

  // Save a private request. Matching runs "in the background" (3 s in the demo).
  const submitRequest = useCallback((kind, data) => {
    const id = (kind === 're' ? 'r' : 'n') + Date.now()
    updateBox(kind, (b) => ({ ...b, reqs: [{ id, data }, ...b.reqs] }))
    const matches = kind === 're' ? matchOld(data) : matchNew(data)
    if (!matches.length) return
    setTimeout(() => {
      const box = stRef.current[kind]
      if (!box.reqs.some((r) => r.id === id)) return // removed meanwhile
      const fresh = matches.filter((m) => !box.moments.some((x) => x.pid === m.pid) && !box.chats.includes(m.pid))
      if (!fresh.length) return
      updateBox(kind, (b) => ({ ...b, moments: [...fresh.map((m) => ({ ...m, req: id })), ...b.moments] }))
      setOverlay({ type: 'moment', kind, count: fresh.length })
    }, MATCH_DELAY_MS)
  }, [updateBox])

  const dismissMoment = useCallback((kind, pid) => {
    updateBox(kind, (b) => ({ ...b, moments: b.moments.filter((m) => m.pid !== pid) }))
    toast("Okay, we'll keep looking")
  }, [updateBox, toast])

  const removeRequest = useCallback((kind, id) => {
    updateBox(kind, (b) => ({ ...b, reqs: b.reqs.filter((r) => r.id !== id), moments: b.moments.filter((m) => m.req !== id) }))
    toast('Request removed')
  }, [updateBox, toast])

  // Send a chat message. The first message to a possible match turns it into a chat.
  const sendMessage = useCallback((kind, pid, text) => {
    const isMoment = !stRef.current[kind].chats.includes(pid)
    setSt((s) => ({
      ...s,
      msgs: { ...s.msgs, [pid]: [...(s.msgs[pid] || []), { me: true, t: text }] },
      [kind]: isMoment
        ? { ...s[kind], moments: s[kind].moments.filter((m) => m.pid !== pid), chats: [pid, ...s[kind].chats.filter((c) => c !== pid)] }
        : s[kind],
    }))
    if (!isMoment) return
    setTimeout(() => {
      setSt((s) => ({ ...s, msgs: { ...s.msgs, [pid]: [...(s.msgs[pid] || []), { me: false, t: REPLY[pid] || 'Hi! Nice to hear from you.' }] } }))
      toast(firstName(byId(pid)) + ' replied')
    }, REPLY_DELAY_MS)
  }, [toast])

  const becomeNew = useCallback(() => {
    setOpenState({ re: null, nw: null })
    setSt(seedNew())
    toast("Now you're a brand-new user")
  }, [toast])

  const becomeOld = useCallback(() => {
    setOpenState({ re: null, nw: null })
    setSt(seedOld())
    toast("Now you're a returning user")
  }, [toast])

  const value = useMemo(() => ({
    st, toast, toastText, overlay, closeOverlay,
    form, setForm, meet, setMeet, open, setOpen,
    submitRequest, dismissMoment, removeRequest, sendMessage, becomeNew, becomeOld,
  }), [st, toast, toastText, overlay, closeOverlay, form, meet, open, setOpen, submitRequest, dismissMoment, removeRequest, sendMessage, becomeNew, becomeOld])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export const useStore = () => useContext(Ctx)
