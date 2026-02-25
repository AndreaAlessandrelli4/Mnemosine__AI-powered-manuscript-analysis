import React, { useState, useEffect } from 'react';

// Helper to format keys (e.g. "NOTAZIONE_MUSICALE" -> "Notazione musicale")
const formatLabel = (key) => {
    const spaced = key.replace(/_/g, ' ');
    return spaced.charAt(0).toUpperCase() + spaced.slice(1).toLowerCase();
};

export default function MetadataStructuredEditor({ value, onChange, disabled }) {
    const [rawMode, setRawMode] = useState(false);
    const [parsedData, setParsedData] = useState(null);
    const [parseError, setParseError] = useState(false);

    useEffect(() => {
        try {
            if (!value) {
                setParsedData(null);
                setParseError(false);
                return;
            }
            const parsed = JSON.parse(value);
            // Ensure it's an object
            if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
                setParsedData(parsed);
                setParseError(false);
            } else {
                setParseError(true);
            }
        } catch (e) {
            setParseError(true);
        }
    }, [value]);

    const handleFieldChange = (path, newValue) => {
        if (!parsedData) return;

        // Deep clone the object to update it safely
        const newData = JSON.parse(JSON.stringify(parsedData));

        // Traverse the path and update the value
        let current = newData;
        for (let i = 0; i < path.length - 1; i++) {
            current = current[path[i]];
        }
        current[path[path.length - 1]] = newValue;

        // Propagate the change as a stringified JSON
        onChange(JSON.stringify(newData, null, 2));
    };

    if (rawMode || parseError || !parsedData) {
        return (
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 400 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, alignItems: 'center' }}>
                    <span style={{ fontSize: 13, color: 'var(--mn-muted)' }}>
                        {parseError ? "⚠ Invalid JSON detected. Falling back to Raw Editor." : "Raw JSON Editor"}
                    </span>
                    {!parseError && parsedData && (
                        <button className="btn btn-ghost btn-sm" onClick={() => setRawMode(false)}>
                            ↹ Switch to Structured View
                        </button>
                    )}
                </div>
                <textarea
                    className="editor-area"
                    value={value || ''}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                    placeholder="No metadata available. Run analysis first."
                    style={{ flex: 1 }}
                />
            </div>
        );
    }

    // Render recursively
    const renderFields = (obj, path = []) => {
        return Object.entries(obj).map(([key, val]) => {
            const currentPath = [...path, key];

            if (typeof val === 'object' && val !== null && !Array.isArray(val)) {
                // Nested object logic
                return (
                    <div key={key} style={{ marginBottom: 16, gridColumn: '1 / -1' }}>
                        <h4 style={{ fontSize: 14, marginBottom: 8, color: 'var(--mn-text)' }}>
                            {formatLabel(key)}
                        </h4>
                        <div style={{
                            padding: '12px',
                            borderLeft: '2px solid var(--mn-border)',
                            backgroundColor: 'rgba(0,0,0,0.01)',
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                            gap: '12px 16px'
                        }}>
                            {renderFields(val, currentPath)}
                        </div>
                    </div>
                );
            } else {
                // Primitive field
                const isString = typeof val === 'string';
                const isLongText = isString && (val.length > 50 || key.toLowerCase().includes('descrizione') || key.toLowerCase().includes('testo'));

                return (
                    <div key={key} className="form-group" style={{ marginBottom: 8, gridColumn: isLongText ? '1 / -1' : 'auto' }}>
                        <label style={{ display: 'block', fontSize: 13, marginBottom: 4, color: 'var(--mn-muted)', fontWeight: 600 }}>
                            {formatLabel(key)}
                        </label>
                        {isLongText ? (
                            <textarea
                                className="form-control"
                                value={val || ''}
                                onChange={(e) => handleFieldChange(currentPath, e.target.value)}
                                disabled={disabled}
                                style={{ minHeight: 80, resize: 'vertical' }}
                            />
                        ) : (
                            <input
                                type="text"
                                className="form-control"
                                value={val === null ? '' : val}
                                onChange={(e) => handleFieldChange(currentPath, e.target.value)}
                                disabled={disabled}
                            />
                        )}
                    </div>
                );
            }
        });
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
                <button className="btn btn-ghost btn-sm" onClick={() => setRawMode(true)}>
                    § Switch to Raw JSON
                </button>
            </div>

            <div style={{ overflowY: 'auto', paddingRight: 4 }}>
                {Object.entries(parsedData).map(([sectionKey, sectionObj]) => (
                    <div key={sectionKey} className="card" style={{ marginBottom: 16, padding: 16 }}>
                        <h3 style={{ marginBottom: 16, borderBottom: '1px solid var(--mn-border)', paddingBottom: 8, color: 'var(--mn-primary)' }}>
                            {formatLabel(sectionKey)}
                        </h3>
                        {typeof sectionObj === 'object' && sectionObj !== null && !Array.isArray(sectionObj) ? (
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px 16px' }}>
                                {renderFields(sectionObj, [sectionKey])}
                            </div>
                        ) : (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr' }}>
                                {renderFields({ [sectionKey]: sectionObj })}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
