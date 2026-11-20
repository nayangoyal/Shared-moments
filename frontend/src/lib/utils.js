export const words = (s) => s.trim().split(/\s+/).filter(Boolean).length
export const firstName = (p) => p.n.split(' ')[0]

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
