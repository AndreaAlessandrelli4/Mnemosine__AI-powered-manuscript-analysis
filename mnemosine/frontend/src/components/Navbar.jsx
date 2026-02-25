import React from 'react'
import { NavLink } from 'react-router-dom'

const links = [
    { to: '/', label: 'Home' },
    { to: '/metadata', label: 'Metadata' },
]

export default function Navbar() {
    return (
        <nav className="navbar">
            <div className="navbar-logo">
                <img src="/mnemosine_logo.png" alt="Mnemosine" style={{ height: 32, marginRight: 8, verticalAlign: 'middle' }} />
                Mnemosine
            </div>
            <ul className="navbar-links">
                {links.map((link) => (
                    <li key={link.to}>
                        <NavLink
                            to={link.to}
                            className={({ isActive }) => isActive ? 'active' : ''}
                            end={link.to === '/'}
                        >
                            {link.label}
                        </NavLink>
                    </li>
                ))}
            </ul>
        </nav>
    )
}
