import { useEffect, useRef, useState } from 'react'
import { LABELS } from '../data/data'
import { firstName, reqTitle } from '../lib/utils'
import { useStore } from '../store/StoreContext'
import { HeartIcon, PairIcon } from '../components/Icons'
import { Avatar, EmptyState, Intro, Tick, TopBar } from '../components/ui'

// Reunited (kind 're') and New Friends (kind 'nw') share this layout:
// possible matches → chats → your requests. Tapping a chat or request opens it.
export default function FoundTab({ kind }) {
  const { open } = useStore()
  const o = open[kind]
  if (o?.type === 'chat') return <ChatView kind={kind} matchId={o.id} />
  if (o?.type === 'req') return <RequestView kind={kind} id={o.id} />
  return <Overview kind={kind} />
}

const title = (kind) => (kind === 're' ? 'Reunited' : 'New Friends')
const WHY = { name: 'name', nickname: 'nickname', phone: 'old phone number', school: 'school', year: 'year', area: 'area', memory: 'shared memory' }
const whyText = (why) => why.map((w) => WHY[w] || w).join(', ').toLowerCase()

function Overview({ kind }) {
  const { st, setOpen, dismissMoment, person } = useStore()
  const box = st[kind]
  const isRe = kind === 're'
  const meetBtn = <a className="btn main" href="#meet">Meet new people</a>
  const nothing = !box.reqs.length && !box.chats.length && !box.moments.length
  const onlyRequests = !nothing && !box.chats.length && !box.moments.length

  return (
    <>
      <TopBar title={title(kind)} />
      <div className="screen">
        <Intro title={isRe ? 'Friends you found again' : 'Your new friends'} />

        {box.moments.length > 0 && (
          <div className="section">
            <h3>This might be your moment · {box.moments.length}</h3>
            <div className="grid">
              {box.moments.map((m) => {
                const p = person(m.pid)
                const r = box.reqs.find((x) => x.id === m.req)
                return (
                  <div className="fcard" key={m.id}>
                    <div className="ph" style={{ '--c': p.c }}>{p.n[0]}</div>
                    <div className="b">
                      <b>{p.n}{p.a ? `, ${p.a}` : ''}<Tick /></b>
                      <p>{p.place}</p>
                      {m.why.length > 0 && <span className="pill ok" style={{ alignSelf: 'flex-start' }}>Matches your {whyText(m.why)}</span>}
                      {r && <p className="one" style={{ fontSize: 13 }}>For: {reqTitle(kind, r.data)}</p>}
                      <button className="btn small main" type="button" onClick={() => setOpen(kind, { type: 'chat', id: m.id })}>Say hi</button>
                      <button className="link center" type="button" onClick={() => dismissMoment(kind, m.id)}>Not them</button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {box.chats.length > 0 && (
          <div className="section">
            <h3>{isRe ? 'Reunited' : 'New friends'} · {box.chats.length}</h3>
            <div className="mainbox listbox">
              <div className="list">
                {box.chats.map((c) => {
                  const p = person(c.pid)
                  const ch = st.msgs[c.id] || []
                  const last = ch[ch.length - 1]
                  return (
                    <button key={c.id} className="row click" type="button" onClick={() => setOpen(kind, { type: 'chat', id: c.id })}>
                      <Avatar color={p.c}>{p.n[0]}</Avatar>
                      <span className="txt">
                        <span className="name">{p.n}<Tick /></span>
                        <span className="sub one">{last ? (last.me ? 'You: ' : '') + last.t : ''}</span>
                      </span>
                      <span className="chev" aria-hidden="true">›</span>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        )}

        {onlyRequests && (
          <div className="nudge">
            <b className="h2">No match yet</b>
            <p className="muted" style={{ margin: 0 }}>
              {isRe
                ? "Your friend may not be on Shared Moments yet. Your request stays active, and when they join and describe you, we'll match you."
                : "We're still looking. New people join every day."} Meanwhile, meet new people nearby.
            </p>
            {meetBtn}
          </div>
        )}

        {box.reqs.length > 0 && (
          <div className="section">
            <h3>Your requests · {box.reqs.length}</h3>
            <div className="mainbox listbox">
              <div className="list">
                {box.reqs.map((r) => {
                  const n = box.moments.filter((m) => m.req === r.id).length
                  return (
                    <button key={r.id} className="row click" type="button" onClick={() => setOpen(kind, { type: 'req', id: r.id })}>
                      <span className="txt">
                        <span className="name" style={{ fontSize: 17 }}>{reqTitle(kind, r.data)}</span>
                        <span className={'pill ' + (n ? 'ok' : 'wait')}>{n ? `${n} possible ${n === 1 ? 'match' : 'matches'}` : 'Waiting for a match'}</span>
                      </span>
                      <span className="chev" aria-hidden="true">›</span>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        )}

        {nothing && (isRe ? (
          <EmptyState icon={<PairIcon />} title="No one reunited yet" text="Describe a friend you lost touch with, and we'll look out for them.">
            <a className="btn main" href="#reconnect">Find a lost friend</a>
            <a className="btn" href="#meet">Meet new people</a>
          </EmptyState>
        ) : (
          <EmptyState icon={<HeartIcon />} title="No new friends yet" text="Describe the moment you want, and we'll find people who want it too.">
            {meetBtn}
          </EmptyState>
        ))}
      </div>
    </>
  )
}

function RequestView({ kind, id }) {
  const { st, setOpen, removeRequest } = useStore()
  const box = st[kind]
  const r = box.reqs.find((x) => x.id === id)
  const back = () => setOpen(kind, null)
  useEffect(() => { if (!r) back() })
  if (!r) return null

  const n = box.moments.filter((m) => m.req === id).length
  const rows = Object.entries(r.data).filter(([k, v]) => v && String(v).trim() && LABELS[k])
  return (
    <>
      <TopBar title={title(kind)} onBack={back} />
      <div className="screen">
        <div className="intro">
          <h2>Your request</h2>
          <p><span className={'pill ' + (n ? 'ok' : 'wait')}>{n ? `${n} possible ${n === 1 ? 'match' : 'matches'}` : 'Waiting for a match'}</span></p>
        </div>
        <div className="mainbox stack">
          <dl className="facts">
            {rows.map(([k, v]) => <div key={k} className="fact"><dt>{LABELS[k]}</dt><dd>{v}</dd></div>)}
          </dl>
          <p className="muted" style={{ margin: 0 }}>
            Only you can see this. {kind === 're'
              ? "If your friend isn't on Shared Moments yet, this stays active and matches when they join."
              : "We'll keep matching it with new people who join."}
          </p>
        </div>
        <button className="link" type="button" onClick={async () => { if (await removeRequest(kind, id)) back() }}>Remove this request</button>
      </div>
    </>
  )
}

function ChatView({ kind, matchId }) {
  const { st, setOpen, sendMessage, person } = useStore()
  const [draft, setDraft] = useState('')
  const chatRef = useRef(null)
  const inputRef = useRef(null)
  const box = st[kind]
  const m = box.moments.find((x) => x.id === matchId)
  const c = box.chats.find((x) => x.id === matchId)
  const pid = m?.pid || c?.pid
  const ch = st.msgs[matchId] || []
  const back = () => setOpen(kind, null)

  // Keep the newest message in view
  useEffect(() => {
    const el = chatRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [ch.length])
  useEffect(() => { if (!pid) back() })
  if (!pid) return null

  const p = person(pid)
  const isMoment = Boolean(m)
  const send = (e) => {
    e.preventDefault()
    const v = draft.trim()
    if (!v) return
    sendMessage(kind, matchId, pid, v)
    setDraft('')
    inputRef.current?.focus()
  }

  return (
    <>
      <TopBar title={title(kind)} onBack={back} />
      <div className="screen">
        <div className="chathead">
          <Avatar color={p.c}>{p.n[0]}</Avatar>
          <div style={{ minWidth: 0 }}>
            <b style={{ fontSize: 20 }}>{p.n}<Tick /></b>
            <span className="muted" style={{ display: 'block', fontSize: 15 }}>{p.place}{m?.why?.length ? ' · matches your ' + whyText(m.why) : ''}</span>
          </div>
        </div>
        {isMoment && <div className="tip"><b>This might be your moment.</b> Say hi. They can't see your request, only your message.</div>}
        <div className="mainbox chat" ref={chatRef} aria-live="polite">
          {ch.length
            ? ch.map((x, i) => <div key={i} className={'bubble ' + (x.me ? 'me' : 'them')}>{x.t}</div>)
            : <p className="muted" style={{ margin: 'auto' }}>No messages yet.</p>}
        </div>
        <form className="composer" onSubmit={send}>
          <label htmlFor="chatIn" className="sr-only">Message</label>
          <input ref={inputRef} className="input" id="chatIn" autoComplete="off" maxLength={1000} value={draft} onChange={(e) => setDraft(e.target.value)}
            placeholder={isMoment ? `Say hi to ${firstName(p)}…` : 'Write a message…'} />
          <button className="btn main" type="submit">Send</button>
        </form>
      </div>
    </>
  )
}
