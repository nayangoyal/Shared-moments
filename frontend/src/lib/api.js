// Talks to the Shared Moments API (same site, under /api). Every call carries a Firebase ID token.
import { initializeApp } from 'firebase/app'
import { getAuth, onAuthStateChanged, signInAnonymously } from 'firebase/auth'
import { firebaseConfig } from './firebaseConfig'

const auth = getAuth(initializeApp(firebaseConfig))

// Resolves once there is a signed-in user (anonymous on first visit; the same user on reloads).
const ready = new Promise((resolve, reject) => {
  const stop = onAuthStateChanged(auth, (user) => {
    if (user) { stop(); resolve(user) }
  })
  signInAnonymously(auth).catch((e) => { stop(); reject(e) })
})

export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === 'string' ? detail : detail?.message || 'Something went wrong')
    this.status = status
    this.code = detail?.code
  }
}

async function call(method, path, body) {
  const user = await ready
  const token = await user.getIdToken()
  const res = await fetch('/api' + path, {
    method,
    headers: { Authorization: `Bearer ${token}`, ...(body ? { 'Content-Type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new ApiError(res.status, data.detail)
  return data
}

export const api = {
  session: () => call('POST', '/session'),
  state: (rev) => call('GET', '/state' + (rev != null ? `?rev=${rev}` : '')),
  saveAbout: (about) => call('PUT', '/me', about),
  deleteMe: () => call('DELETE', '/me'),
  createRequest: (kind, data) => call('POST', '/requests', { kind, data }),
  removeRequest: (id) => call('DELETE', `/requests/${id}`),
  dismiss: (matchId) => call('POST', `/matches/${matchId}/dismiss`),
  send: (matchId, text) => call('POST', `/matches/${matchId}/messages`, { text }),
  reset: (persona) => call('POST', '/demo/reset', { persona }),
}
