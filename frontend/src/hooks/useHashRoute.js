import { useEffect, useState } from 'react'

export const ROUTES = ['reconnect', 'reunited', 'meet', 'newfriends', 'profile']

const read = () => {
  const r = window.location.hash.slice(1)
  return ROUTES.includes(r) ? r : 'reconnect'
}

// Tiny hash router: #reconnect, #reunited, #meet, #newfriends
export function useHashRoute() {
  const [route, setRoute] = useState(read)
  useEffect(() => {
    const on = () => setRoute(read())
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return route
}

export const go = (route) => {
  window.location.hash = '#' + route
}
