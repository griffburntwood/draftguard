import { useState } from 'react'

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
  is_demo?: boolean
  notice?: string
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

export default function ComparisonView({ comparison }: { comparison: Comparison }) {
  const [expandedFields, setExpandedFields] = useState<Set<string>>(new Set())

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

  return (
    <section className="comparison-result">
      <header className="page-header">
        <div>
          <p className="eyebrow">DraftGuard</p>
          <h2>Document comparison result</h2>
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

      {comparison.review_reasons.length > 0 && (
        <section className="review-notice" aria-labelledby="review-heading">
          <h2 id="review-heading">Review required</h2>
          <ul>
            {comparison.review_reasons.map((reason, index) => (
              <li key={`${index}-${reason}`}>{reason}</li>
            ))}
          </ul>
        </section>
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
              <div className="document-value">
                <span className="document-label">Shipping instructions (SI)</span>
                <span>{formatValue(result.si.normalized_value)}</span>
              </div>
              <div className="document-value">
                <span className="document-label">Draft bill of lading (BL)</span>
                <span>{formatValue(result.bl.normalized_value)}</span>
              </div>
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
    </section>
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

