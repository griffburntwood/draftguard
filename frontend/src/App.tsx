import { useState } from 'react'
import ComparisonView from './ComparisonView'
import ProcessingForm from './ProcessingForm'
import { apiUrl, processText } from './api'
import type {
  ComparisonResult,
  ProcessingRequest,
  ProcessingResponse,
} from './api'
import './App.css'

type DisplayComparison = ComparisonResult & {
  is_demo?: boolean
  notice?: string
}

export default function App() {
  const [comparison, setComparison] = useState<DisplayComparison | null>(null)
  const [classification, setClassification] =
    useState<ProcessingResponse['classification'] | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function resetResults() {
    setComparison(null)
    setClassification(null)
    setError(null)
  }

  async function handleSubmit(request: ProcessingRequest) {
    setBusy(true)
    resetResults()
    try {
      const result = await processText(request)
      setClassification(result.classification)
      setComparison(result.comparison)
    } catch (error) {
      setError(
        error instanceof Error ? error.message : 'Processing failed. Please retry.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function loadDemo() {
    setBusy(true)
    resetResults()
    try {
      const response = await fetch(apiUrl('/demo/comparison'))
      if (!response.ok) {
        throw new Error(`Demo unavailable (HTTP ${response.status}).`)
      }
      const data: DisplayComparison = await response.json()
      setComparison(data)
    } catch (error) {
      setError(
        error instanceof Error ? error.message : 'Unable to load the demo.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="page">
      <p className="eyebrow">DraftGuard</p>
      <h1>Shipping document review</h1>

      <ProcessingForm busy={busy} onSubmit={handleSubmit} />

      <p>
        <button type="button" disabled={busy} onClick={loadDemo}>
          Load synthetic demo
        </button>
      </p>

      {busy && <p role="status">Processing request…</p>}
      {error && (
        <p role="alert">
          {error} Your inputs are preserved; submit again to retry.
        </p>
      )}

      {classification && (
        <section aria-labelledby="classification-heading">
          <h2 id="classification-heading">Last submitted email</h2>
          <p><strong>{classification.category}</strong></p>
          <p>{classification.explanation}</p>
          {!comparison && (
            <p>This email was not routed for document comparison.</p>
          )}
        </section>
      )}

      {comparison && (
        <ComparisonView
          key={comparison.comparison_id}
          comparison={comparison}
        />
      )}
    </main>
  )
}
