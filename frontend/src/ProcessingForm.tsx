import { useState } from 'react'
import type { FormEvent } from 'react'
import type { EmailRecord, ProcessingRequest } from './api'

type Props = {
  busy: boolean
  onSubmit: (request: ProcessingRequest) => Promise<void>
  onFiles: (email: EmailRecord, si: File | null, bl: File | null) => Promise<void>
}
const EXAMPLE = `Shipper: Example Exporter
Consignee: Example Importer
Notify Party: Example Importer
Port of Loading: Singapore
Port of Discharge: Mersin
Container Count: 3
Gross Weight: 22,000 KG`

export default function ProcessingForm({ busy, onSubmit, onFiles }: Props) {
  const [sender, setSender] = useState('')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [siText, setSiText] = useState('')
  const [blText, setBlText] = useState('')
  const [mode, setMode] = useState('text')
  const [siFile, setSiFile] = useState<File | null>(null)
  const [blFile, setBlFile] = useState<File | null>(null)
  const [error, setError] = useState('')

  function fillExample() {
    setMode('text'); setSender('demo@example.com'); setSubject('Check draft BL')
    setBody('Please compare the BL against the SI.')
    setSiText(EXAMPLE); setBlText(EXAMPLE.replace('Count: 3', 'Count: 4'))
    setError('')
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    setError('')
    const id = crypto.randomUUID()
    const email = { email_id: id, from: sender, subject, body, attachments: [] as string[] }
    if (mode === 'files') {
      if ([siFile, blFile].some(file => file && file.size > 10 * 1024 * 1024)) {
        setError('Each file must be at most 10 MiB.'); return
      }
      email.attachments = [siFile, blFile].filter((file): file is File => !!file).map(file => file.name)
      await onFiles(email, siFile, blFile)
    } else {
      const si = siText.trim() ? { document_id: `${id}_si`, attachment_path: 'si.txt', text: siText } : null
      const bl = blText.trim() ? { document_id: `${id}_bl`, attachment_path: 'bl.txt', text: blText } : null
      email.attachments = [...(si ? ['si.txt'] : []), ...(bl ? ['bl.txt'] : [])]
      await onSubmit({ email, si, bl })
    }
  }

  return <section className="processing-input" aria-labelledby="processing-heading">
    <div className="section-heading"><div><p className="eyebrow">01 / Intake</p><h2 id="processing-heading">Check a shipment</h2></div>
      <button className="secondary" type="button" disabled={busy} onClick={fillExample}>Fill synthetic example</button></div>
    <p>Select the authoritative SI and draft BL. Missing documents are sent for review.</p>
    <form onSubmit={submit} aria-busy={busy}>
      <fieldset disabled={busy}>
        <legend>Email details</legend>
        <label htmlFor="sender">Sender email (required)</label><input id="sender" type="email" autoComplete="email" required value={sender} onChange={e => setSender(e.target.value)} />
        <label htmlFor="subject">Subject</label><input id="subject" value={subject} onChange={e => setSubject(e.target.value)} />
        <label htmlFor="body">Email body</label><textarea id="body" rows={3} value={body} onChange={e => setBody(e.target.value)} />
        <label htmlFor="input-mode">Document input</label><select id="input-mode" value={mode} onChange={e => { setMode(e.target.value); setSiFile(null); setBlFile(null) }}><option value="text">Paste text</option><option value="files">Upload files</option></select>
        {mode === 'text' ? <div className="document-inputs">
          <div><label htmlFor="si-text">Shipping instructions (SI)</label><textarea id="si-text" maxLength={1000000} rows={9} value={siText} onChange={e => setSiText(e.target.value)} /></div>
          <div><label htmlFor="bl-text">Draft bill of lading (BL)</label><textarea id="bl-text" maxLength={1000000} rows={9} value={blText} onChange={e => setBlText(e.target.value)} /></div>
        </div> : <>
          <p id="file-hint">TXT, PDF, DOCX, XLSX · 10 MiB per file. Scanned or unreadable documents require manual review.</p>
          <label htmlFor="si-file">Shipping instructions (SI) file</label><input id="si-file" type="file" accept=".txt,.pdf,.docx,.xlsx" aria-describedby="file-hint" onChange={e => setSiFile(e.target.files?.[0] ?? null)} />
          <label htmlFor="bl-file">Draft bill of lading (BL) file</label><input id="bl-file" type="file" accept=".txt,.pdf,.docx,.xlsx" aria-describedby="file-hint" onChange={e => setBlFile(e.target.files?.[0] ?? null)} />
        </>}
        {error && <p role="alert">{error}</p>}
        <button type="submit">{busy ? 'Processing…' : 'Process email'}</button>
      </fieldset>
    </form>
  </section>
}
