/**
 * API client for Mnemosine backend.
 * All calls go through the Vite proxy (/api → localhost:8000).
 */

const BASE = 'http://localhost:8000';

async function request(path, options = {}) {
    const url = `${BASE}${path}`;
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || JSON.stringify(err));
    }
    return res.json();
}

export const api = {
    // Health
    health: () => request('/health'),

    // Models
    getCatalog: () => request('/models/catalog'),

    // Analyze
    analyze: (body) =>
        request('/analyze', { method: 'POST', body: JSON.stringify(body) }),

    getJobStatus: (jobId) => request(`/jobs/${jobId}/status`),
    getJobResults: (jobId) => request(`/jobs/${jobId}/results`),

    // Manuscripts
    browse: (path) =>
        request(`/manuscripts/browse${path ? `?path=${encodeURIComponent(path)}` : ''}`),

    getPages: (msPath) =>
        request(`/pages?manuscript_path=${encodeURIComponent(msPath)}`),

    // Page data
    getPageMetadata: (msPath, filename) =>
        request(
            `/pages/${encodeURIComponent(filename)}/metadata?manuscript_path=${encodeURIComponent(msPath)}`
        ),

    updatePageMetadata: (msPath, filename, content) =>
        request(
            `/pages/${encodeURIComponent(filename)}/metadata?manuscript_path=${encodeURIComponent(msPath)}`,
            { method: 'PUT', body: JSON.stringify({ content }) }
        ),

    getPageTranscription: (msPath, filename) =>
        request(
            `/pages/${encodeURIComponent(filename)}/transcription?manuscript_path=${encodeURIComponent(msPath)}`
        ),

    updatePageTranscription: (msPath, filename, content) =>
        request(
            `/pages/${encodeURIComponent(filename)}/transcription?manuscript_path=${encodeURIComponent(msPath)}`,
            { method: 'PUT', body: JSON.stringify({ content }) }
        ),

    // Work metadata
    getWorkMetadata: (msPath) =>
        request(`/work/metadata?manuscript_path=${encodeURIComponent(msPath)}`),

    updateWorkMetadata: (msPath, content) =>
        request(
            `/work/metadata?manuscript_path=${encodeURIComponent(msPath)}`,
            { method: 'PUT', body: JSON.stringify({ content }) }
        ),

    regenerateWorkMetadata: (msPath, provider = 'openai', device = 'auto', textModel = '') =>
        request(
            `/work/metadata/regenerate?manuscript_path=${encodeURIComponent(msPath)}&provider=${provider}&device=${device}&text_model=${textModel}`,
            { method: 'POST' }
        ),

    // Image URL (not through fetch — direct URL for <img>)
    getPageImageUrl: (msPath, filename) =>
        `${BASE}/pages/${encodeURIComponent(filename)}/image?manuscript_path=${encodeURIComponent(msPath)}`,
};
