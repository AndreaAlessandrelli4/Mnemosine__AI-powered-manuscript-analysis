import React from 'react'

export default function PlaceholderPage({ title, description }) {
    return (
        <div className="placeholder-page fade-in">
            <div className="card" style={{ maxWidth: 560, margin: '0 auto', padding: '64px 40px' }}>
                <h2>{title}</h2>
                <p style={{ marginTop: 12 }}>{description}</p>
                <p className="text-small" style={{ marginTop: 24 }}>
                    This module is under development. Check back soon.
                </p>
            </div>
        </div>
    )
}
