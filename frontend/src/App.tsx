import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import './App.css'

const API_BASE = '/api'

type DatasetMeta = {
  id: string
  name: string
  description: string
  table_name: string
  row_count: number
  columns: string[]
  example_queries?: string[]
  learning_goals?: string[]
}

type ErrorExplanation = {
  meaning?: string[]
  reason?: string[]
  fix?: string[]
}

function App() {
  const [datasets, setDatasets] = useState<DatasetMeta[]>([])
  const [selectedDataset, setSelectedDataset] = useState<DatasetMeta | null>(null)
  const [tableData, setTableData] = useState<Record<string, unknown>[]>([])
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<Record<string, unknown>[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ErrorExplanation | null>(null)
  const [explainSteps, setExplainSteps] = useState<string[]>([])
  const [loadingDatasets, setLoadingDatasets] = useState(true)

  const tableName = selectedDataset?.table_name ?? ''

  const fetchDatasets = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/datasets`)
      if (!res.ok) throw new Error('Failed to load datasets')
      const data = await res.json()
      setDatasets(data.datasets ?? [])
      if (data.datasets?.length && !selectedDataset) {
        setSelectedDataset(data.datasets[0])
      }
    } catch {
      setDatasets([])
    } finally {
      setLoadingDatasets(false)
    }
  }, [])

  useEffect(() => {
    fetchDatasets()
  }, [fetchDatasets])

  const fetchTableData = useCallback(async (name: string) => {
    if (!name) return
    try {
      const res = await fetch(`${API_BASE}/dataset/${encodeURIComponent(name)}/data`)
      if (!res.ok) throw new Error('Failed to load data')
      const data = await res.json()
      setTableData(data.rows ?? [])
      setResult(null)
      setError(null)
    } catch {
      setTableData([])
    }
  }, [])

  useEffect(() => {
    if (tableName) fetchTableData(tableName)
  }, [tableName, fetchTableData])

  const runQuery = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setExplainSteps([])
    try {
      const res = await fetch(`${API_BASE}/run-query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim() }),
      })
      const data = await res.json()
      if (data.error && data.error_explanation) {
        setError(data.error_explanation as ErrorExplanation)
        setResult(null)
      } else {
        setResult(data.rows ?? [])
        setError(null)
        const explainRes = await fetch(`${API_BASE}/explain-query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query.trim() }),
        })
        const explainData = await explainRes.json()
        setExplainSteps(Array.isArray(explainData.steps) ? explainData.steps : [])
      }
    } catch {
      setError({
        meaning: ['The request failed.'],
        reason: ['The server might be offline or the request was invalid.'],
        fix: ['Make sure the backend is running and try again.'],
      })
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const exportCSV = async () => {
    if (!query.trim()) return
    try {
      const res = await fetch(`${API_BASE}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim(), format: 'csv' }),
      })
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'seeql-export.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // ignore
    }
  }

  const exportJSON = async () => {
    if (!query.trim()) return
    try {
      const res = await fetch(`${API_BASE}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim(), format: 'json' }),
      })
      const data = await res.json()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'seeql-export.json'
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // ignore
    }
  }

  const exploreRows = tableData
  const exploreColumns = exploreRows.length > 0
    ? Object.keys(exploreRows[0])
    : (selectedDataset?.columns ?? [])
  const resultColumns = result && result.length > 0
    ? Object.keys(result[0])
    : (selectedDataset?.columns ?? [])

  return (
    <div className="app">
      <header className="header">
        <h1>SeeQL</h1>
        <p>See how SQL changes your data — a visual playground for beginners.</p>
      </header>

      <section className="section">
        <span className="section-label">Choose Dataset</span>
        <div className="dataset-grid">
          {loadingDatasets ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Loading datasets…</p>
          ) : (
            datasets.map((d) => (
              <button
                key={d.id}
                type="button"
                className={`dataset-btn ${selectedDataset?.id === d.id ? 'active' : ''}`}
                onClick={() => setSelectedDataset(d)}
              >
                {d.name}
              </button>
            ))
          )}
        </div>
        <div className="upload-area">
          <span className="upload-label">Optional — use your own data</span>
          <label className="upload-btn">
            <input
              type="file"
              accept=".csv"
              className="upload-input"
              onChange={async (e) => {
                const file = e.target.files?.[0]
                if (!file) return
                try {
                  const form = new FormData()
                  form.append('file', file)
                  const res = await fetch(`${API_BASE}/upload-dataset`, {
                    method: 'POST',
                    body: form,
                  })
                  if (!res.ok) throw new Error('Upload failed')
                  const data = await res.json()
                  const meta: DatasetMeta = {
                    id: data.dataset_id ?? data.table_name,
                    name: data.name ?? file.name.replace('.csv', ''),
                    description: 'Your uploaded dataset.',
                    table_name: data.table_name,
                    row_count: data.row_count ?? 0,
                    columns: data.columns ?? [],
                  }
                  setDatasets((prev) => [...prev, meta])
                  setSelectedDataset(meta)
                } catch {
                  // could add toast
                }
                e.target.value = ''
              }}
            />
            Upload CSV
          </label>
        </div>
      </section>

      {selectedDataset && (
        <>
          <section className="section">
            <span className="section-label">Explore Data</span>
            <p className="table-meta">
              {selectedDataset.description}
              <span> · {exploreRows.length} row{exploreRows.length !== 1 ? 's' : ''}</span>
            </p>
            <div className="table-wrap card">
              <AnimatePresence mode="wait">
                {exploreRows.length === 0 ? (
                  <motion.p
                    key="empty"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    style={{ padding: 24, color: 'var(--text-muted)' }}
                  >
                    No data to show. Run a query or select another dataset.
                  </motion.p>
                ) : (
                  <motion.table
                    key="table"
                    className="data-table"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <thead>
                      <tr>
                        {exploreColumns.map((col) => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {exploreRows.map((row, i) => (
                        <motion.tr
                          key={i}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: Math.min(i * 0.02, 0.3), duration: 0.2 }}
                        >
                          {exploreColumns.map((col) => (
                            <td key={col} className={row[col] == null ? 'cell-null' : ''}>
                              {row[col] == null ? '—' : String(row[col])}
                            </td>
                          ))}
                        </motion.tr>
                      ))}
                    </tbody>
                  </motion.table>
                )}
              </AnimatePresence>
            </div>
          </section>

          <section className="section">
            <span className="section-label">Write SQL</span>
            <div className="editor-wrap card">
              <textarea
                className="editor-textarea"
                placeholder={`e.g. SELECT * FROM ${tableName} LIMIT 10`}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                spellCheck={false}
              />
              <div className="editor-actions">
                <button
                  type="button"
                  className="run-btn"
                  onClick={runQuery}
                  disabled={loading || !query.trim()}
                >
                  {loading ? 'Running…' : 'Run Query'}
                </button>
              </div>
            </div>
          </section>

          <AnimatePresence>
            {result !== null && (
              <motion.section
                className="section"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
              >
                <span className="section-label">See the Result</span>
                <span className="result-badge">Query result</span>
                <p className="table-meta">{result.length} row{result.length !== 1 ? 's' : ''}</p>
                <div className="table-wrap card">
                  {result.length === 0 ? (
                    <p style={{ padding: 24, color: 'var(--text-muted)' }}>No rows returned.</p>
                  ) : (
                    <table className="data-table">
                      <thead>
                        <tr>
                          {resultColumns.map((col) => (
                            <th key={col}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {result.map((row, i) => (
                          <motion.tr
                            key={i}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: Math.min(i * 0.02, 0.3) }}
                          >
                            {resultColumns.map((col) => (
                              <td key={col} className={row[col] == null ? 'cell-null' : ''}>
                                {row[col] == null ? '—' : String(row[col])}
                              </td>
                            ))}
                          </motion.tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
                <div className="export-btns" style={{ marginTop: 12 }}>
                  <button type="button" onClick={exportCSV}>Export CSV</button>
                  <button type="button" onClick={exportJSON}>Export JSON</button>
                </div>
              </motion.section>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {error && (
              <motion.section
                className="section"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <span className="section-label">What went wrong</span>
                <div className="error-card">
                  <h4>Friendly explanation</h4>
                  {error.meaning?.length ? (
                    <>
                      <p><strong>Meaning:</strong></p>
                      <ul>{error.meaning.map((m, i) => <li key={i}>{m}</li>)}</ul>
                    </>
                  ) : null}
                  {error.reason?.length ? (
                    <>
                      <p><strong>Why:</strong></p>
                      <ul>{error.reason.map((r, i) => <li key={i}>{r}</li>)}</ul>
                    </>
                  ) : null}
                  {error.fix?.length ? (
                    <>
                      <p><strong>How to fix:</strong></p>
                      <ul>{error.fix.map((f, i) => <li key={i}>{f}</li>)}</ul>
                    </>
                  ) : null}
                </div>
              </motion.section>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {explainSteps.length > 0 && !error && (
              <motion.section
                className="section"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <span className="section-label">Understand What Happened</span>
                <ul className="understand-list">
                  {explainSteps.map((step, i) => (
                    <motion.li
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      {step}
                    </motion.li>
                  ))}
                </ul>
              </motion.section>
            )}
          </AnimatePresence>

          {selectedDataset && (selectedDataset.example_queries?.length ?? 0) > 0 && (
            <section className="section">
              <span className="section-label">Learning tips</span>
              <div className="learning-tip">
                <strong>Try these:</strong> {selectedDataset.learning_goals?.join(' · ') ?? 'Filter, sort, and explore.'}
                <details className="example-queries">
                  <summary>Example queries</summary>
                  {selectedDataset.example_queries?.map((q, i) => (
                    <pre key={i}><code>{q}</code></pre>
                  ))}
                </details>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}

export default App
