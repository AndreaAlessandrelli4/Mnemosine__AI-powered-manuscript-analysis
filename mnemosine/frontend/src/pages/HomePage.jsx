import React from 'react'
import { useNavigate } from 'react-router-dom'

export default function HomePage() {
    const navigate = useNavigate()

    return (
        <div className="fade-in">
            {/* Hero Section */}
            <section className="hero">
                <img
                    src="/mnemosine_logo.png"
                    alt="Mnemosine Logo"
                    style={{ width: 100, height: 100, marginBottom: 16, borderRadius: 16 }}
                />
                <h1>Mnemosine</h1>
                <p>
                    AI-powered manuscript analysis for the Ministry of Culture.
                    Extract metadata, transcribe pages, and aggregate results with
                    state-of-the-art Vision-Language models.
                </p>
                <div className="hero-actions">
                    <button className="btn btn-primary" onClick={() => navigate('/metadata')}>
                        Start Analysis
                    </button>
                    <button className="btn btn-secondary" onClick={() => window.open('https://github.com', '_blank')}>
                        Documentation
                    </button>
                </div>
            </section>

            {/* Features */}
            <div className="features-grid">
                <div className="card feature-card">
                    <div className="icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                            <polyline points="14 2 14 8 20 8" />
                            <line x1="16" y1="13" x2="8" y2="13" />
                            <line x1="16" y1="17" x2="8" y2="17" />
                        </svg>
                    </div>
                    <h3>Metadata Extraction</h3>
                    <p>Extract structured metadata per page — notation, decorations, conservation state, language, and more.</p>
                </div>

                <div className="card feature-card">
                    <div className="icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                            <line x1="8" y1="7" x2="16" y2="7" />
                            <line x1="8" y1="11" x2="14" y2="11" />
                        </svg>
                    </div>
                    <h3>Transcription</h3>
                    <p>Faithful OCR transcription preserving original spelling, abbreviations, and layout structure.</p>
                </div>

                <div className="card feature-card">
                    <div className="icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="3" y="3" width="18" height="18" rx="2" />
                            <path d="M3 9h18" />
                            <path d="M9 21V9" />
                        </svg>
                    </div>
                    <h3>Work Aggregation</h3>
                    <p>Intelligent aggregation of per-page metadata into a unified work-level description following deterministic rules.</p>
                </div>

                <div className="card feature-card">
                    <div className="icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M12 20h9" />
                            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
                        </svg>
                    </div>
                    <h3>Human Review</h3>
                    <p>Edit, correct, and refine AI-generated metadata and transcriptions. Save changes and regenerate aggregates.</p>
                </div>
            </div>

            {/* Team Section */}
            <section className="team-section">
                <div className="team-header">
                    <img
                        src="/italian_job_logo.png"
                        alt="The Italian Job"
                        className="team-logo"
                    />
                    <div>
                        <h2>The Italian Job</h2>
                        <p className="text-muted">Il team dietro Mnemosine</p>
                    </div>
                </div>

                <div className="team-grid">
                    <div className="card team-card">
                        <div className="team-avatar">PM</div>
                        <h3>Pasquale Maritato</h3>
                        <span className="team-role">Data Scientist</span>
                    </div>

                    <div className="card team-card">
                        <div className="team-avatar">AA</div>
                        <h3>Andrea Alessandrelli</h3>
                        <span className="team-role">AI Researcher</span>
                    </div>

                    <div className="card team-card">
                        <div className="team-avatar">FT</div>
                        <h3>Fabrizio Tomasso</h3>
                        <span className="team-role">Python Developer</span>
                    </div>
                </div>
            </section>
        </div>
    )
}
