import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError, useAuth } from '../auth.tsx'

const empty = { first_name: '', last_name: '', email: '', password: '' }

export default function CreateAccountPage() {
  const { createAccount } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(empty)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)

  function setField(field: keyof typeof empty, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setErrors({})
    try {
      await createAccount(form)
      navigate('/login', { state: { created: true } })
    } catch (error) {
      if (error instanceof ApiError) {
        setErrors(error.errors)
      } else {
        setErrors({ form: "Couldn't save the account." })
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <article className="prose narrow">
      <p className="eyebrow">Create account</p>
      <h1>Make an account.</h1>
      <p>First name, last name, email, and a password. All four are required.</p>
      <form className="form" onSubmit={onSubmit} noValidate>
        <label>
          First name
          <input
            type="text"
            name="firstName"
            autoComplete="given-name"
            value={form.first_name}
            onChange={(event) => setField('first_name', event.target.value)}
          />
          {errors.first_name && <span className="field-error">{errors.first_name}</span>}
        </label>
        <label>
          Last name
          <input
            type="text"
            name="lastName"
            autoComplete="family-name"
            value={form.last_name}
            onChange={(event) => setField('last_name', event.target.value)}
          />
          {errors.last_name && <span className="field-error">{errors.last_name}</span>}
        </label>
        <label>
          Email
          <input
            type="email"
            name="email"
            autoComplete="email"
            value={form.email}
            onChange={(event) => setField('email', event.target.value)}
          />
          {errors.email && <span className="field-error">{errors.email}</span>}
        </label>
        <label>
          Password
          <input
            type="password"
            name="password"
            autoComplete="new-password"
            value={form.password}
            onChange={(event) => setField('password', event.target.value)}
          />
          {errors.password && <span className="field-error">{errors.password}</span>}
        </label>
        {errors.form && <p className="field-error">{errors.form}</p>}
        <button className="button" type="submit" disabled={busy}>
          {busy ? 'Saving…' : 'Create account'}
        </button>
      </form>
      <p className="form-switch">
        Already have one? <Link to="/login">Log in</Link>
      </p>
    </article>
  )
}
