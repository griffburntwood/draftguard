import { useEffect, useState } from 'react'
import './App.css'

type Value = string | number | null

type Evidence = {
  document_id: string
  location: string
  text: string | null
}

type ExtractedField = {
  raw_value: string | null
  normalized_value: Value
  state: 'extracted' | 'missing' | 'unreadable' | 'ambiguous'
  evidence: Evidence[]
}

type FieldResult = {
  field: string
  si: ExtractedField
  bl: ExtractedField
  outcome: 'MATCH' | 'MISMATCH' | 'UNKNOWN'
  explanation: string
}

type Comparison = {
  is_demo: boolean
  notice: string
  comparison_id: string
  email_id: string
  si_document_id: string | null
  bl_document_id: string | null
  status: 'OK' | 'MISMATCH' | 'NEEDS_REVIEW'
  field_results: FieldResult[]
  defect_fields: string[]
  review_reasons: string[]
}

const fieldLabels: Record<string, string> = {
  shipper: 'Shipper',
  consignee: 'Consignee',
  notify_party: 'Notify party',
  port_of_loading: 'Port of loading',
  port_of_discharge: 'Port of discharge',
  container_count: 'Container count',
  gross_weight_kg: 'Gross weight (kg)',
}

function formatValue(value: Value) {
  return value === null ? 'Not available' : String(value)
}

function App() {
  const [comparison, setComparison] = useState<Comparison | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedFields, setExpandedFields] = useState<Set<string>>(new Set())
  const [requestNumber, setRequestNumber] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    async function loadComparison() {
      setLoading(true)
      setError(null)

      try {
        const response = await fetch('/api/demo/comparison', {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`The server returned ${response.status}.`)
        }

        const data: Comparison = await response.json()
        setComparison(data)
      } catch (caughtError) {
        if (caughtError instanceof DOMException && caughtError.name === 'AbortError') {
          return
        }

        setComparison(null)
        setError(
          caughtError instanceof Error
            ? caughtError.message
            : 'Unable to load the comparison.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadComparison()

    return () => controller.abort()
  }, [requestNumber])

  function toggleEvidence(field: string) {
    setExpandedFields((current) => {
      const next = new Set(current)
      if (next.has(field)) {
        next.delete(field)
      } else {
        next.add(field)
      }
      return next
    })
  }

  if (loading) {
    return (
      <main className="page">
        <p className="eyebrow">DraftGuard</p>
        <h1>Loading comparison…</h1>
        <p>Please wait while the local demo response is loaded.</p>
      </main>
    )
  }

  if (error) {
    return (
      <main className="page">
        <p className="eyebrow">DraftGuard</p>
        <h1>Comparison unavailable</h1>
        <p>{error}</p>
        <button type="button" onClick={() => setRequestNumber((value) => value + 1)}>
          Retry
        </button>
      </main>
    )
  }

  if (!comparison) {
    return null
  }

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">DraftGuard</p>
          <h1>Shipping instruction comparison</h1>
          <p>Compare the source Shipping Instructions (SI) with the draft Bill of Lading (BL).</p>
        </div>
        <span className={`status status-${comparison.status.toLowerCase()}`}>
          {comparison.status.replace('_', ' ')}
        </span>
      </header>

      {comparison.is_demo && (
        <aside className="demo-notice" aria-label="Synthetic demo notice">
          <strong>Synthetic demo</strong>
          <span>{comparison.notice}</span>
        </aside>
      )}

      <section className="comparison-meta" aria-label="Comparison details">
        <span>SI: {comparison.si_document_id ?? 'Not available'}</span>
        <span>BL: {comparison.bl_document_id ?? 'Not available'}</span>
      </section>

      <section className="comparison-table" aria-label="Field comparison">
        <div className="table-heading">
          <span>Field</span>
          <span>Shipping instructions</span>
          <span>Draft bill of lading</span>
          <span>Result</span>
        </div>

        {comparison.field_results.map((result) => {
          const expanded = expandedFields.has(result.field)
          const mismatch = result.outcome === 'MISMATCH'

          return (
            <article
              className={`field-row ${mismatch ? 'field-row-mismatch' : ''}`}
              key={result.field}
            >
              <div className="field-name">
                <strong>{fieldLabels[result.field] ?? result.field}</strong>
                <button
                  type="button"
                  className="evidence-toggle"
                  aria-expanded={expanded}
                  onClick={() => toggleEvidence(result.field)}
                >
                  {expanded ? 'Hide evidence' : 'Show evidence'}
                </button>
              </div>
              <div>{formatValue(result.si.normalized_value)}</div>
              <div>{formatValue(result.bl.normalized_value)}</div>
              <div>
                <span className={`outcome outcome-${result.outcome.toLowerCase()}`}>
                  {result.outcome}
                </span>
                <p className="explanation">{result.explanation}</p>
              </div>

              {expanded && (
                <div className="evidence-panel">
                  <EvidenceList title="SI source evidence" evidence={result.si.evidence} />
                  <EvidenceList title="BL source evidence" evidence={result.bl.evidence} />
                </div>
              )}
            </article>
          )
        })}
      </section>
    </main>
  )
}

function EvidenceList({ title, evidence }: { title: string; evidence: Evidence[] }) {
  return (
    <section className="evidence-list">
      <h2>{title}</h2>
      {evidence.length === 0 ? (
        <p>No source evidence is available.</p>
      ) : (
        <ul>
          {evidence.map((item, index) => (
            <li key={`${item.document_id}-${item.location}-${index}`}>
              <strong>{item.document_id}</strong>
              <span>{item.location}</span>
              {item.text && <q>{item.text}</q>}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default App