import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import HomePage from './pages/HomePage'
import MetadataPage from './pages/MetadataPage'

export default function App() {
    return (
        <>
            <Navbar />
            <main className="page-container">
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/metadata" element={<MetadataPage />} />
                </Routes>
            </main>
        </>
    )
}
