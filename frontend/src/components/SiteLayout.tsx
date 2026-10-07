import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth.tsx'
import { MatchProvider } from '../matches.tsx'
import ChatPanel from './ChatPanel.tsx'

export default function SiteLayout() {
  const { shopper, logout } = useAuth()
  const links = shopper
    ? [
        { to: '/', label: 'Home', end: true },
        { to: '/products', label: 'Products', end: false },
        { to: '/about', label: 'About us', end: false },
      ]
    : [
        { to: '/', label: 'Home', end: true },
        { to: '/products', label: 'Products', end: false },
        { to: '/about', label: 'About us', end: false },
        { to: '/login', label: 'Log in', end: false },
        { to: '/create-account', label: 'Create account', end: false },
      ]

  return (
    <MatchProvider>
    <div className="site">
      <p className="announcement">Yale hoodies, crewnecks, and college shirts</p>
      <header className="header">
        <NavLink to="/" className="wordmark" end>
          <span className="wordmark-shop">Campus Customs</span>
          <span className="wordmark-place">57 Broadway, New Haven</span>
        </NavLink>
        <nav className="nav" aria-label="Main">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              {link.label}
            </NavLink>
          ))}
          {shopper && (
            <>
              <span className="nav-user">Hi, {shopper.first_name}</span>
              <button type="button" className="nav-link nav-button" onClick={() => void logout()}>
                Log out
              </button>
            </>
          )}
        </nav>
      </header>
      <main className="main">
        <Outlet />
      </main>
      <ChatPanel />
      <footer className="footer">
        <p>Campus Customs · 57 Broadway, New Haven, CT 06511</p>
        <p className="footer-note">
          A class shop for this assignment. Not the official Yale Bulldog Blue store, and not a partnership with them.
        </p>
      </footer>
    </div>
    </MatchProvider>
  )
}
