import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ApiError, useAuth } from '../auth.tsx'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const created = Boolean((location.state as { created?: boolean } | null)?.created)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't log in.")
    } finally {
      setBusy(false)
    }
  }

  return (
    <article className="prose narrow">
      <p className="eyebrow">Log in</p>
      <h1>Welcome back.</h1>
      <p>Use the email and password on the account.</p>
      {created && <p className="form-note">Account saved. Log in with that email and password.</p>}
      <form className="form" onSubmit={onSubmit}>
        <label>
          Email
          <input
            type="email"
            name="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            name="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        {error && <p className="field-error">{error}</p>}
        <button className="button" type="submit" disabled={busy}>
          {busy ? 'Checking…' : 'Log in'}
        </button>
      </form>
      <p className="form-switch">
        New here? <Link to="/create-account">Create account</Link>
      </p>
    </article>
  )
}
