import { useState } from 'react'
import type { FormEvent } from 'react'
import { correctField } from './api'
import type { ProcessingResponse } from './api'

type Props = { result: ProcessingResponse; busy: boolean; onCorrect: (work: () => Promise<ProcessingResponse>) => Promise<void> }
export default function ReviewPanel({ result, busy, onCorrect }: Props) {
  const [reviewer, setReviewer] = useState('')
  const [reason, setReason] = useState('')
  const [side, setSide] = useState('bl')
  const [field, setField] = useState('container_count')
  const [value, setValue] = useState('')
  const [error, setError] = useState('')
  async function submit(e: FormEvent) {
    e.preventDefault(); setError('')
    const numeric = field === 'container_count' || field === 'gross_weight_kg'
    const converted = numeric ? Number(value) : value.trim()
    if (!value.trim() || (numeric && (!Number.isFinite(converted) || Number(converted) < 0 || (field === 'container_count' && !Number.isInteger(converted))))) {
      setError('Enter a valid value; counts must be whole numbers and weights must be non-negative kilograms.'); return
    }
    await onCorrect(() => correctField(result, reviewer, reason, side, field, converted))
  }
  if (!result.comparison) return null
  return <details className="review-editor"><summary>Correct an extracted value and recheck</summary>
    <p>Use this only to correct extraction after reading the source. It does not edit or approve a shipping document. Original values and evidence are retained.</p>
    <form onSubmit={submit}><fieldset disabled={busy}>
      <legend>Human correction</legend>
      <label htmlFor="reviewer">Reviewer name (required)</label><input id="reviewer" autoComplete="name" required maxLength={120} value={reviewer} onChange={e => setReviewer(e.target.value)} />
      <label htmlFor="side">Document</label><select id="side" value={side} onChange={e => setSide(e.target.value)}><option value="si">SI</option><option value="bl">BL</option></select>
      <label htmlFor="field">Field</label><select id="field" value={field} onChange={e => setField(e.target.value)}>{result.comparison.field_results.map(f => <option key={f.field} value={f.field}>{f.field.replaceAll('_', ' ')}</option>)}</select>
      <label htmlFor="corrected-value">Correct value (weight in kg)</label><input id="corrected-value" required value={value} onChange={e => setValue(e.target.value)} />
      <label htmlFor="correction-reason">Reason (required)</label><textarea id="correction-reason" required maxLength={2000} value={reason} onChange={e => setReason(e.target.value)} />
      {error && <p role="alert">{error}</p>}
      <button type="submit">Save correction and recheck</button>
    </fieldset></form>
    {!!result.review_audit?.length && <ul>{result.review_audit.map((item, i) => <li key={i}>{item.reviewer}: {item.side.toUpperCase()} {item.field} → {String(item.value)}. {item.reason}</li>)}</ul>}
  </details>
}
