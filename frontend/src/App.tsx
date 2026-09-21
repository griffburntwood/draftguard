import { useState } from 'react'
import ComparisonView from './ComparisonView'
import ProcessingForm from './ProcessingForm'
import ReviewPanel from './ReviewPanel'
import { apiUrl, processText, processFiles, processInbox } from './api'
import type { ComparisonResult, ProcessingResponse, InboxResponse } from './api'
import './App.css'

type Snapshot = { result: ProcessingResponse; reviewed?: { name: string; at: string } }
type Demo = ComparisonResult & { is_demo: boolean; notice: string }
const STORAGE = 'draftguard-revisions-v1'
function fingerprint(result: ProcessingResponse) {
  return JSON.stringify({ hashes: result.document_hashes, fields: result.comparison?.field_results.map(f => [f.field, f.si.normalized_value, f.bl.normalized_value, f.si.state, f.bl.state]), codes: result.comparison?.review_reasons, audit: result.review_audit })
}
function restore(): Snapshot[] {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE) || '[]')
    return Array.isArray(saved) ? saved.filter(s => s?.result?.classification && s?.result?.comparison?.field_results).slice(-10) : []
  } catch { return [] }
}
function download(value: unknown, name: string) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }))
  const a = document.createElement('a'); a.href = url; a.download = name; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export default function App() {
  const [history, setHistory] = useState<Snapshot[]>(restore)
  const [result, setResult] = useState<ProcessingResponse | null>(() => restore().at(-1)?.result ?? null)
  const [demo, setDemo] = useState<Demo | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [storageNote, setStorageNote] = useState('')
  const [inbox, setInbox] = useState<InboxResponse | null>(null)
  const [filter, setFilter] = useState('ALL')
  const [bundle, setBundle] = useState<File | null>(null)
  const [reviewer, setReviewer] = useState('')
  const [formKey, setFormKey] = useState(0)
  const comparison = demo ?? result?.comparison
  const latest = history.at(-1)
  const previous = history.length > 1 ? history[history.length - 2] : undefined
  const isCurrent = !!result && result.comparison?.comparison_id === latest?.result.comparison?.comparison_id
  const changed = previous && latest && fingerprint(previous.result) !== fingerprint(latest.result)

  function save(next: Snapshot[]) {
    setHistory(next)
    try { localStorage.setItem(STORAGE, JSON.stringify(next)); setStorageNote('') }
    catch { setStorageNote('Browser storage is full. Download the review history before closing this page.') }
  }
  async function run(work: () => Promise<ProcessingResponse>) {
    if (busy) return
    setBusy(true); setError(null); setDemo(null); setResult(null)
    try {
      const response = await work()
      setResult(response)
      if (inbox && response.submission_entry && inbox.submission[response.classification.email.email_id]) {
        const id = response.classification.email.email_id
        setInbox({ ...inbox, submission: { ...inbox.submission, [id]: response.submission_entry }, results: inbox.results.map(r => r.classification.email.email_id === id ? response : r) })
      }
      if (response.comparison) {
        const same = history.at(-1) && fingerprint(history.at(-1)!.result) === fingerprint(response)
        save([...history.slice(same ? 0 : -9, same ? -1 : undefined), { result: response, reviewed: same ? history.at(-1)?.reviewed : undefined }])
      }
    } catch (e) { setError(e instanceof Error ? e.message : 'Processing failed. Please retry.') }
    finally { setBusy(false) }
  }
  async function loadDemo() {
    setBusy(true); setError(null); setResult(null); setDemo(null)
    try {
      const response = await fetch(apiUrl('/demo/comparison'))
      if (!response.ok) throw new Error(`Demo unavailable (${response.status}).`)
      setDemo(await response.json())
    } catch (e) { setError(e instanceof Error ? e.message : 'Demo failed.') }
    finally { setBusy(false) }
  }
  async function loadInbox() {
    if (!bundle) return
    if (bundle.size > 30 * 1024 * 1024) { setError('Participant ZIP must be at most 30 MiB.'); return }
    setBusy(true); setError(null); setDemo(null); setResult(null); setInbox(null)
    try { const loaded = await processInbox(bundle); setInbox(loaded) }
    catch (e) { setError(e instanceof Error ? e.message : 'Inbox processing failed.') }
    finally { setBusy(false) }
  }

  return <main className="page">
    <header className="workspace-header"><div><p className="eyebrow">DraftGuard / Document review workspace</p><h1>Check the draft.<br />Keep the evidence.</h1><p>Compare shipping instructions with the draft bill of lading, resolve uncertainty, and check what changed.</p></div><span className="workspace-badge">Human review stays in control</span></header>
    <ProcessingForm key={formKey} busy={busy} onSubmit={request => run(() => processText(request))} onFiles={(email, si, bl) => run(() => processFiles(email, si, bl))} />
    <div className="toolbar"><button className="secondary" disabled={busy} onClick={loadDemo}>Load synthetic demo</button><button className="secondary" disabled={busy} onClick={() => { save([]); setResult(null); setDemo(null); setInbox(null); setError(null); setFormKey(k => k + 1) }}>Start new shipment</button></div>
    <details className="inbox-import"><summary>Process an organizer inbox ZIP</summary><p>Select the participant bundle containing inbox/ and attachments/. Each email gets one submission entry. No answer key is used.</p><label htmlFor="bundle">Participant ZIP (up to 30 MiB)</label><input id="bundle" type="file" accept=".zip" disabled={busy} onChange={e => setBundle(e.target.files?.[0] ?? null)} /><button disabled={busy || !bundle} onClick={loadInbox}>Process inbox</button></details>
    {busy && <p role="status" className="processing-status">Processing… The hosted backend may take about a minute to wake. Your inputs are preserved.</p>}
    {error && <p role="alert">{error} Check your inputs or connection and retry.</p>}
    {storageNote && <p role="alert">{storageNote}</p>}
    <div className="toolbar">{inbox && <button onClick={() => download(inbox.submission, 'submission.json')}>Download inbox submission JSON ({Object.keys(inbox.submission).length} emails)</button>}{result?.submission_entry && <button className="secondary" onClick={() => download({ [result.classification.email.email_id]: result.submission_entry }, 'selected-result.json')}>Download selected result JSON</button>}</div>
    {inbox && <section className="inbox-results"><h2>Inbox action queue</h2><p>{inbox.summary.emails} emails processed. Counts are predictions, not an accuracy score.</p><label htmlFor="queue-filter">Show</label><select id="queue-filter" value={filter} onChange={e => setFilter(e.target.value)}><option value="ALL">All emails</option>{['NEEDS_REVIEW', 'MISMATCH', 'OK'].map(s => <option key={s}>{s}</option>)}</select><div className="queue-list">{inbox.results.filter(r => filter === 'ALL' || r.comparison?.status === filter).map(r => <button className="queue-item" disabled={busy} key={r.classification.email.email_id} onClick={() => { setResult(r); setDemo(null); save(r.comparison ? [{ result: r }] : []) }}><strong>{r.classification.email.email_id}</strong><span>{r.classification.email.subject}</span><span>{r.comparison?.status ?? r.classification.category}</span></button>)}</div></section>}
    {result && <section className="classification"><p className="eyebrow">02 / Routing</p><h2>{result.classification.category.replaceAll('_', ' ')}</h2><p>{result.classification.explanation}</p>{!result.comparison && <p>This email was not routed for document comparison.</p>}</section>}
    {comparison && <ComparisonView key={`comparison-${comparison.comparison_id}`} comparison={comparison} />}
    {result?.comparison && <ReviewPanel key={`review-${result.comparison.comparison_id}`} result={result} busy={busy} onCorrect={run} />}
    {history.length > 0 && <section className="revision-history"><div className="section-heading"><div><p className="eyebrow">03 / Revision check</p><h2>Current shipment history</h2></div><button className="secondary" onClick={() => download(history, 'draftguard-review-history.json')}>Download history</button></div><p>Saved only in this browser, up to 10 checks. Submit revised sources for the same shipment; use “Start new shipment” for unrelated documents. Reviewer names are self-reported.</p>
      {isCurrent && changed && <div className="review-notice"><strong>Sources or reviewed values changed. Review the new result.</strong><ul>{latest!.result.comparison!.field_results.map(f => {
        const before = previous!.result.comparison!.field_results.find(old => old.field === f.field)
        if (!before) return null
        const valuesChanged = JSON.stringify([before.si.normalized_value, before.bl.normalized_value, before.outcome]) !== JSON.stringify([f.si.normalized_value, f.bl.normalized_value, f.outcome])
        if (!valuesChanged) return null
        const label = before.outcome === 'MISMATCH' && f.outcome === 'MATCH' ? 'Fixed' : before.outcome !== 'MISMATCH' && f.outcome === 'MISMATCH' ? 'New mismatch' : 'Changed'
        return <li key={f.field}>{label}: {f.field.replaceAll('_', ' ')} ({before.outcome} → {f.outcome})</li>
      })}</ul>{latest!.result.comparison!.defect_fields.filter(f => previous!.result.comparison!.defect_fields.includes(f)).length > 0 && <p>Unresolved: {latest!.result.comparison!.defect_fields.filter(f => previous!.result.comparison!.defect_fields.includes(f)).join(', ')}</p>}</div>}
      <ol>{history.map((snapshot, index) => <li key={snapshot.result.comparison!.comparison_id}><button className="secondary" disabled={busy} onClick={() => { setResult(snapshot.result); setDemo(null) }}>Check {index + 1}: {snapshot.result.comparison!.status}</button><span>{snapshot.reviewed ? `Reviewed by ${snapshot.reviewed.name}${fingerprint(snapshot.result) !== fingerprint(latest!.result) ? ' — OUTDATED for current sources' : ''}` : 'Not yet reviewed'}</span></li>)}</ol>
      {isCurrent && <div className="review-ack"><label htmlFor="ack-name">Reviewer name</label><input id="ack-name" autoComplete="name" maxLength={120} value={reviewer} onChange={e => setReviewer(e.target.value)} /><button disabled={busy || !reviewer.trim() || result?.comparison?.status === 'NEEDS_REVIEW'} onClick={() => save(history.map((s, i) => i === history.length - 1 ? { ...s, reviewed: { name: reviewer.trim(), at: new Date().toISOString() } } : s))}>Record review of this version</button><p>A recorded review acknowledges these results; it does not approve or release a BL. Resolve uncertainty before recording review.</p></div>}
    </section>}
    <footer>DraftGuard · SI is the reference. Missing or unreadable information requires human review. Uploaded files are processed temporarily; the server does not keep a shared review history.</footer>
  </main>
}
