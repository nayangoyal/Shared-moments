import { OLD, PEOPLE } from '../data/data'

export const words = (s) => s.trim().split(/\s+/).filter(Boolean).length
export const firstName = (p) => p.n.split(' ')[0]

const WEIGHTS = { name: 3, nickname: 3, school: 2, year: 1, area: 2 }

// Reconnect request → up to 2 old friends on the site. Returns [{ pid, why }]
export function matchOld(d) {
  const L = (s) => (s || '').trim().toLowerCase()
  return OLD.map((p) => {
    const why = []
    if (L(d.name) && L(d.name).split(/\s+/).some((w) => w.length > 1 && p.n.toLowerCase().includes(w))) why.push('name')
    if (L(d.nick) && p.nick && p.nick.toLowerCase() === L(d.nick)) why.push('nickname')
    if (L(d.school) && p.school.toLowerCase().includes(L(d.school))) why.push('school')
    if ((d.year || '').trim() && p.year === d.year.trim()) why.push('year')
    if (L(d.area) && L(d.area).split(/[ ,]+/).some((w) => w.length > 2 && p.area.toLowerCase().includes(w))) why.push('area')
    const score = why.reduce((s, w) => s + (WEIGHTS[w] || 0), 0)
    return { pid: p.id, why, score }
  })
    .filter((x) => x.score >= 4)
    .sort((a, b) => b.score - a.score)
    .slice(0, 2)
    .map(({ pid, why }) => ({ pid, why }))
}

// Meet New request → up to 3 people who share an activity
export function matchNew(d) {
  const want = d.acts.split(', ')
  return PEOPLE.map((p) => ({ pid: p.id, why: p.acts.filter((a) => want.includes(a)) }))
    .filter((x) => x.why.length)
    .sort((a, b) => b.why.length - a.why.length)
    .slice(0, 3)
}

// One-line title for a saved request
export function reqTitle(kind, d) {
  if (kind === 'nw') return 'Looking for: ' + d.acts.toLowerCase()
  const who = [d.name, d.nick && `"${d.nick}"`].filter(Boolean).join(' ') || 'A friend'
  const from = [d.school, d.year].filter(Boolean).join(', ') || d.area || d.how || ''
  return who + (from ? ' · ' + from : '')
}

// How complete the Reconnect form is: 0-10 points
export function reconnectScore(rf) {
  const fields = Object.entries(rf).filter(([k, v]) => k !== 'memory' && v.trim()).length
  return fields + Math.min(3, Math.floor(words(rf.memory) / 10))
}
