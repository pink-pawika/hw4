import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'

export type Shopper = {
  id: number
  first_name: string
  last_name: string
  name: string
  email: string
}

export class ApiError extends Error {
  errors: Record<string, string>

  constructor(message: string, errors: Record<string, string> = {}) {
    super(message)
    this.errors = errors
  }
}

type AccountInput = {
  first_name: string
  last_name: string
  email: string
  password: string
}

type AuthValue = {
  shopper: Shopper | null
  ready: boolean
  createAccount: (input: AccountInput) => Promise<void>
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthValue | null>(null)

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  })
  const data = (await response.json().catch(() => ({}))) as {
    detail?: string
    errors?: Record<string, string>
  }
  if (!response.ok) {
    const message = typeof data.detail === 'string' ? data.detail : 'Check the form.'
    throw new ApiError(message, data.errors ?? {})
  }
  return data as T
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [shopper, setShopper] = useState<Shopper | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let active = true
    fetch('/api/me', { credentials: 'include' })
      .then(async (response) => {
        if (!response.ok) return null
        return (await response.json()) as Shopper
      })
      .then((user) => {
        if (active) setShopper(user)
      })
      .finally(() => {
        if (active) setReady(true)
      })
    return () => {
      active = false
    }
  }, [])

  async function createAccount(input: AccountInput) {
    await postJson('/api/accounts', input)
  }

  async function login(email: string, password: string) {
    const user = await postJson<Shopper>('/api/login', { email, password })
    setShopper(user)
  }

  async function logout() {
    await postJson('/api/logout', {})
    setShopper(null)
  }

  return (
    <AuthContext.Provider value={{ shopper, ready, createAccount, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext)
  if (!value) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return value
}
