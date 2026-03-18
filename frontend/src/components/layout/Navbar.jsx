import { BriefcaseBusiness, Database, Gauge, Moon, Sun } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useTheme } from '../../context/ThemeContext'

const navLinks = [
  { to: '/', label: 'Dashboard', icon: Gauge },
  { to: '/candidates', label: 'Candidates', icon: Database },
]

function Navbar() {
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-icon">
          <BriefcaseBusiness size={18} />
        </div>
        <div>
          <p className="brand-title">JobMatch AI</p>
          <p className="brand-subtitle">Resume Screening Agent</p>
        </div>
      </div>

      <div className="topbar-right">
        <nav className="topbar-nav" aria-label="Main navigation">
          {navLinks.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `nav-link${isActive ? ' nav-link-active' : ''}`
              }
            >
              <Icon size={16} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <button type="button" className="theme-toggle" onClick={toggleTheme}>
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
        </button>
      </div>
    </header>
  )
}

export default Navbar
