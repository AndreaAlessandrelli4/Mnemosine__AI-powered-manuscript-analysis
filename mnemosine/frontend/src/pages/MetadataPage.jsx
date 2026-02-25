import React, { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '../api'
import MetadataStructuredEditor from '../components/MetadataStructuredEditor'

export default function MetadataPage() {
    // ── State ────────────────────────────────────────────
    const [catalog, setCatalog] = useState(null)
    const [manuscripts, setManuscripts] = useState([])
    const [msPath, setMsPath] = useState('')
    const [customPath, setCustomPath] = useState('')
    const [pages, setPages] = useState([])
    const [selectedPage, setSelectedPage] = useState(null)

    // Config
    const [device, setDevice] = useState('auto')
    const [provider, setProvider] = useState('hf')
    const [mode, setMode] = useState('both')
    const [granularity, setGranularity] = useState('both')
    const [vlMetaModel, setVlMetaModel] = useState('')
    const [vlTrascModel, setVlTrascModel] = useState('')
    const [textModel, setTextModel] = useState('')

    // Job
    const [jobId, setJobId] = useState(null)
    const [jobStatus, setJobStatus] = useState(null)
    const [isRunning, setIsRunning] = useState(false)
    const pollRef = useRef(null)

    // Editor
    const [activeTab, setActiveTab] = useState('metadata')
    const [metadataContent, setMetadataContent] = useState('')
    const [transcriptionContent, setTranscriptionContent] = useState('')
    const [workMetadata, setWorkMetadata] = useState(null)
    const [isStale, setIsStale] = useState(false)
    const [saveMsg, setSaveMsg] = useState('')
    const [error, setError] = useState('')

    // ── Load catalog on mount ────────────────────────────
    useEffect(() => {
        api.getCatalog()
            .then(setCatalog)
            .catch((e) => setError(`Failed to load model catalog: ${e.message}`))
    }, [])

    // ── Set defaults when catalog loads ──────────────────
    useEffect(() => {
        if (catalog) {
            const isGpu = catalog.gpu_available
            setVlMetaModel(isGpu ? 'Qwen/Qwen3-VL-8B-Instruct' : 'Qwen/Qwen3-VL-2B-Instruct')
            setVlTrascModel(isGpu ? 'Qwen/Qwen3-VL-8B-Instruct' : 'Qwen/Qwen3-VL-2B-Instruct')
            setTextModel(isGpu ? 'Qwen/Qwen2.5-7B-Instruct' : 'Qwen/Qwen2.5-3B-Instruct')
        }
    }, [catalog])

    // ── Resolved device ──────────────────────────────────
    const resolvedDevice = device === 'auto' ? (catalog?.detected_device || 'cpu') : device
    const gpuAvailable = catalog?.gpu_available || false

    const isModelDisabled = (model) => {
        if (provider === 'openai') return false
        if (resolvedDevice === 'cpu' && model.requires_gpu) return true
        return false
    }

    // ── Browse manuscripts ───────────────────────────────
    const browseMss = useCallback(async (path) => {
        try {
            const data = await api.browse(path || undefined)
            setManuscripts(data.manuscripts || [])
        } catch (e) {
            setManuscripts([])
        }
    }, [])

    useEffect(() => { browseMss() }, [browseMss])

    // ── Load pages when manuscript selected ──────────────
    useEffect(() => {
        if (!msPath) {
            setPages([])
            return
        }
        api.getPages(msPath)
            .then((p) => { setPages(p); setSelectedPage(null) })
            .catch(() => setPages([]))
    }, [msPath])

    // ── Load page content ────────────────────────────────
    useEffect(() => {
        if (!selectedPage || !msPath) return
        setMetadataContent('')
        setTranscriptionContent('')

        if (selectedPage.has_metadata) {
            api.getPageMetadata(msPath, selectedPage.filename)
                .then((d) => setMetadataContent(d.content))
                .catch(() => { })
        }
        if (selectedPage.has_transcription) {
            api.getPageTranscription(msPath, selectedPage.filename)
                .then((d) => setTranscriptionContent(d.content))
                .catch(() => { })
        }
    }, [selectedPage, msPath])

    // ── Load work metadata ───────────────────────────────
    const loadWorkMeta = useCallback(() => {
        if (!msPath) return
        api.getWorkMetadata(msPath)
            .then((d) => { setWorkMetadata(d.content); setIsStale(d.is_stale) })
            .catch(() => { setWorkMetadata(null) })
    }, [msPath])

    useEffect(() => { loadWorkMeta() }, [loadWorkMeta])

    // ── Start analysis ──────────────────────────────────
    const startAnalysis = async () => {
        setError('')
        setSaveMsg('')
        try {
            const body = {
                manuscript_path: msPath || customPath,
                mode,
                granularity,
                device,
                provider,
                models: {
                    vl_metadata: vlMetaModel,
                    vl_transcription: vlTrascModel,
                    text_aggregator: textModel,
                },
            }
            const res = await api.analyze(body)
            setJobId(res.job_id)
            setIsRunning(true)
            startPolling(res.job_id)
        } catch (e) {
            setError(e.message)
        }
    }

    const startPolling = (id) => {
        if (pollRef.current) clearInterval(pollRef.current)
        pollRef.current = setInterval(async () => {
            try {
                const s = await api.getJobStatus(id)
                setJobStatus(s)
                if (s.status === 'completed' || s.status === 'failed') {
                    clearInterval(pollRef.current)
                    pollRef.current = null
                    setIsRunning(false)
                    // Reload pages and work meta
                    if (msPath) {
                        api.getPages(msPath).then(setPages).catch(() => { })
                        loadWorkMeta()
                    }
                }
            } catch {
                clearInterval(pollRef.current)
                pollRef.current = null
                setIsRunning(false)
            }
        }, 2000)
    }

    useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

    // ── Save handlers ────────────────────────────────────
    const saveMetadata = async () => {
        try {
            await api.updatePageMetadata(msPath, selectedPage.filename, metadataContent)
            setSaveMsg('Metadata saved ✓')
            setIsStale(true)
            setTimeout(() => setSaveMsg(''), 3000)
        } catch (e) {
            setError(`Save failed: ${e.message}`)
        }
    }

    const saveTranscription = async () => {
        try {
            await api.updatePageTranscription(msPath, selectedPage.filename, transcriptionContent)
            setSaveMsg('Transcription saved ✓')
            setTimeout(() => setSaveMsg(''), 3000)
        } catch (e) {
            setError(`Save failed: ${e.message}`)
        }
    }

    const saveWorkMetadata = async () => {
        try {
            await api.updateWorkMetadata(msPath, workMetadata)
            setSaveMsg('Work metadata saved ✓')
            setIsStale(false)
            setTimeout(() => setSaveMsg(''), 3000)
        } catch (e) {
            setError(`Save failed: ${e.message}`)
        }
    }

    const regenerateWork = async () => {
        try {
            setSaveMsg('Regenerating...')
            await api.regenerateWorkMetadata(msPath, provider, device, textModel)
            loadWorkMeta()
            setSaveMsg('Work metadata regenerated ✓')
            setTimeout(() => setSaveMsg(''), 3000)
        } catch (e) {
            setError(`Regeneration failed: ${e.message}`)
        }
    }

    // ── Render helpers ───────────────────────────────────
    const vlModels = catalog?.models?.filter((m) => m.type === 'vl') || []
    const textModels = catalog?.models?.filter((m) => m.type === 'text') || []

    return (
        <div className="fade-in">
            {/* Provider badge */}
            {provider === 'openai' && (
                <div className="alert alert-warning">
                    <strong>OpenAI (demo)</strong> — May incur costs. Configure OPENAI_API_KEY in .env.
                </div>
            )}

            {error && (
                <div className="alert alert-error">
                    {error}
                    <button className="btn btn-ghost btn-sm" onClick={() => setError('')} style={{ marginLeft: 'auto' }}>✕</button>
                </div>
            )}

            {saveMsg && <div className="alert alert-success">{saveMsg}</div>}

            <div className="metadata-layout">
                {/* ── Sidebar ──────────────────────────────── */}
                <aside className="sidebar">
                    {/* Directory Selection */}
                    <div className="card" style={{ marginBottom: 16 }}>
                        <div className="card-header">
                            <h3>Manuscript</h3>
                            <p className="text-small">Select or type a manuscript directory</p>
                        </div>

                        <div className="form-group">
                            <label>Browse</label>
                            <select
                                className="form-control"
                                value={msPath}
                                onChange={(e) => { setMsPath(e.target.value); setCustomPath('') }}
                            >
                                <option value="">— Select —</option>
                                {manuscripts.map((m) => (
                                    <option key={m.path} value={m.path}>
                                        {m.name} {m.has_output ? '✓' : ''}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Or enter path</label>
                            <input
                                className="form-control"
                                placeholder="/path/to/manuscript"
                                value={customPath}
                                onChange={(e) => { setCustomPath(e.target.value); setMsPath('') }}
                            />
                        </div>
                    </div>

                    {/* Config */}
                    <div className="card" style={{ marginBottom: 16 }}>
                        <div className="card-header">
                            <h3>Configuration</h3>
                        </div>

                        <div className="form-group">
                            <label>Provider</label>
                            <select className="form-control" value={provider} onChange={(e) => setProvider(e.target.value)}>
                                <option value="openai">OpenAI (API)</option>
                                <option value="hf">HuggingFace (local)</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Device</label>
                            <select className="form-control" value={device} onChange={(e) => setDevice(e.target.value)}>
                                <option value="auto">Auto ({catalog?.detected_device || '...'})</option>
                                <option value="cpu">CPU</option>
                                <option value="cuda">CUDA</option>
                                <option value="mps">MPS (Apple Silicon)</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Mode</label>
                            <select className="form-control" value={mode} onChange={(e) => setMode(e.target.value)}>
                                <option value="both">Both (Metadata + Transcription)</option>
                                <option value="metadata">Metadata only</option>
                                <option value="transcription">Transcription only</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Granularity</label>
                            <select className="form-control" value={granularity} onChange={(e) => setGranularity(e.target.value)}>
                                <option value="both">Both (Page + Work)</option>
                                <option value="page">Page only</option>
                                <option value="work">Work only</option>
                            </select>
                        </div>
                    </div>

                    {/* Model Selection (only relevant for HF, shown for reference) */}
                    {provider === 'hf' && (
                        <div className="card" style={{ marginBottom: 16 }}>
                            <div className="card-header">
                                <h3>Models</h3>
                                {!gpuAvailable && <span className="badge badge-warning" style={{ marginLeft: 8 }}>CPU only</span>}
                            </div>

                            <div className="form-group">
                                <label>VL — Metadata</label>
                                <select className="form-control" value={vlMetaModel} onChange={(e) => setVlMetaModel(e.target.value)}>
                                    {vlModels.map((m) => (
                                        <option key={m.id} value={m.id} disabled={isModelDisabled(m)}>
                                            {m.label}{isModelDisabled(m) ? ' (GPU only)' : ''}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-group">
                                <label>VL — Transcription</label>
                                <select className="form-control" value={vlTrascModel} onChange={(e) => setVlTrascModel(e.target.value)}>
                                    {vlModels.map((m) => (
                                        <option key={m.id} value={m.id} disabled={isModelDisabled(m)}>
                                            {m.label}{isModelDisabled(m) ? ' (GPU only)' : ''}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="form-group">
                                <label>Text — Aggregator</label>
                                <select className="form-control" value={textModel} onChange={(e) => setTextModel(e.target.value)}>
                                    {textModels.map((m) => (
                                        <option key={m.id} value={m.id} disabled={isModelDisabled(m)}>
                                            {m.label}{isModelDisabled(m) ? ' (GPU only)' : ''}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    )}

                    {/* Launch */}
                    <button
                        className="btn btn-primary"
                        style={{ width: '100%' }}
                        onClick={startAnalysis}
                        disabled={isRunning || (!msPath && !customPath)}
                    >
                        {isRunning ? 'Running...' : 'Start Analysis'}
                    </button>
                </aside>

                {/* ── Main Panel ──────────────────────────── */}
                <div>
                    {/* Progress */}
                    {jobStatus && (
                        <div className="card" style={{ marginBottom: 16 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                                <span className="text-small">Job: {jobStatus.job_id}</span>
                                <span className={`badge badge-${jobStatus.status === 'completed' ? 'success' : jobStatus.status === 'failed' ? 'error' : 'primary'}`}>
                                    {jobStatus.status}
                                </span>
                            </div>
                            <div className="progress-bar">
                                <div className="progress-bar-fill" style={{ width: `${jobStatus.progress || 0}%` }} />
                            </div>
                            <p className="text-small" style={{ marginTop: 8 }}>
                                {jobStatus.current_step}
                                {jobStatus.progress > 0 && ` — ${Math.round(jobStatus.progress)}%`}
                            </p>
                            {jobStatus.errors?.length > 0 && (
                                <div className="alert alert-error" style={{ marginTop: 8 }}>
                                    {jobStatus.errors.map((e, i) => <div key={i}>{e}</div>)}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Page list and editor */}
                    {pages.length > 0 && (
                        <div className="card">
                            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <h3>Pages ({pages.length})</h3>
                            </div>

                            {/* Tabs */}
                            <div className="tabs">
                                <button
                                    className={`tab ${activeTab === 'metadata' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('metadata')}
                                >
                                    Metadata
                                </button>
                                <button
                                    className={`tab ${activeTab === 'transcription' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('transcription')}
                                >
                                    Transcription
                                </button>
                                <button
                                    className={`tab ${activeTab === 'work' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('work')}
                                >
                                    Work Metadata
                                    {isStale && <span className="badge badge-warning" style={{ marginLeft: 6 }}>stale</span>}
                                </button>
                            </div>

                            {activeTab !== 'work' ? (
                                <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 16 }}>
                                    {/* Page list */}
                                    <ul className="page-list">
                                        {pages.map((p) => (
                                            <li
                                                key={p.filename}
                                                className={selectedPage?.filename === p.filename ? 'active' : ''}
                                                onClick={() => setSelectedPage(p)}
                                            >
                                                <span
                                                    className={`status-dot ${activeTab === 'metadata'
                                                        ? p.has_metadata ? 'done' : 'pending'
                                                        : p.has_transcription ? 'done' : 'pending'
                                                        }`}
                                                />
                                                <span style={{ fontSize: 13 }}>{p.page_number.toString().padStart(3, '0')}</span>
                                                <span className="text-small" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                    {p.filename}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>

                                    {/* Editor */}
                                    <div>
                                        {selectedPage ? (
                                            <>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                                    <span style={{ fontWeight: 600 }}>{selectedPage.filename}</span>
                                                    <button
                                                        className="btn btn-primary btn-sm"
                                                        onClick={activeTab === 'metadata' ? saveMetadata : saveTranscription}
                                                    >
                                                        Save
                                                    </button>
                                                </div>

                                                {/* Image preview */}
                                                {msPath && (
                                                    <div style={{ marginBottom: 12, textAlign: 'center' }}>
                                                        <img
                                                            src={api.getPageImageUrl(msPath, selectedPage.filename)}
                                                            alt={selectedPage.filename}
                                                            style={{
                                                                maxWidth: '100%',
                                                                maxHeight: 200,
                                                                borderRadius: 8,
                                                                border: '1px solid var(--mn-border)',
                                                            }}
                                                            onError={(e) => { e.target.style.display = 'none' }}
                                                        />
                                                    </div>
                                                )}

                                                {activeTab === 'metadata' ? (
                                                    <div style={{ height: 'calc(100vh - 350px)' }}>
                                                        <MetadataStructuredEditor
                                                            value={metadataContent}
                                                            onChange={setMetadataContent}
                                                        />
                                                    </div>
                                                ) : (
                                                    <textarea
                                                        className="editor-area"
                                                        value={transcriptionContent}
                                                        onChange={(e) => setTranscriptionContent(e.target.value)}
                                                        placeholder="No transcription available. Run analysis first."
                                                    />
                                                )}
                                            </>
                                        ) : (
                                            <div style={{ textAlign: 'center', padding: 40, color: 'var(--mn-muted)' }}>
                                                Select a page from the list
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                /* Work Metadata Tab */
                                <div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                                        <h3 style={{ fontSize: 16 }}>Aggregated Work Metadata</h3>
                                        <div style={{ display: 'flex', gap: 8 }}>
                                            {workMetadata && (
                                                <button className="btn btn-primary btn-sm" onClick={saveWorkMetadata}>
                                                    Save
                                                </button>
                                            )}
                                            {isStale && (
                                                <button className="btn btn-warning btn-sm" onClick={regenerateWork}>
                                                    Regenerate
                                                </button>
                                            )}
                                        </div>
                                    </div>

                                    {workMetadata ? (
                                        <div style={{ height: 'calc(100vh - 250px)' }}>
                                            <MetadataStructuredEditor
                                                value={workMetadata}
                                                onChange={setWorkMetadata}
                                            />
                                        </div>
                                    ) : (
                                        <div style={{ textAlign: 'center', padding: 40, color: 'var(--mn-muted)' }}>
                                            No work metadata available. Run analysis with granularity "work" or "both".
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Empty state */}
                    {!pages.length && !jobStatus && (
                        <div className="card" style={{ textAlign: 'center', padding: 60 }}>
                            <h3 style={{ color: 'var(--mn-muted)', marginBottom: 8 }}>No manuscript selected</h3>
                            <p className="text-small">Select a manuscript directory from the sidebar, then start the analysis.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
