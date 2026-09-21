import { useState } from 'react'
import type { FormEvent } from 'react'
import type { ProcessingRequest } from './api'

type Props = {
  busy: boolean
  onSubmit: (request: ProcessingRequest) => Promise<void>
}

export default function ProcessingForm({ busy, onSubmit }: Props) {
  const [sender, setSender] = useState('')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [siText, setSiText] = useState('')
  const [blText, setBlText] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return

    const id = crypto.randomUUID()
    const si = siText.trim()
      ? {
          document_id: `${id}_si`,
          attachment_path: 'si.txt',
          text: siText,
        }
      : null
    const bl = blText.trim()
      ? {
          document_id: `${id}_bl`,
          attachment_path: 'bl.txt',
          text: blText,
        }
      : null

    await onSubmit({
      email: {
        email_id: id,
        from: sender,
        subject,
        body,
        attachments: [
          ...(si ? [si.attachment_path] : []),
          ...(bl ? [bl.attachment_path] : []),
        ],
      },
      si,
      bl,
    })
  }

  return (
    <section className="processing-input" aria-labelledby="processing-heading">
      <h2 id="processing-heading">Process email and document text</h2>
      <p>
        Paste the email and select the document roles by placing each text
        in its labelled box. Leave unavailable documents blank.
      </p>

      <form onSubmit={handleSubmit}>
        <fieldset disabled={busy}>
          <legend>Email details</legend>

          <label htmlFor="email-sender">Sender email</label>
          <input
            id="email-sender"
            type="email"
            required
            value={sender}
            onChange={(event) => setSender(event.target.value)}
          />

          <label htmlFor="email-subject">Subject</label>
          <input
            id="email-subject"
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
          />

          <label htmlFor="email-body">Email body</label>
          <textarea
            id="email-body"
            required
            rows={4}
            value={body}
            onChange={(event) => setBody(event.target.value)}
          />

          <label htmlFor="si-text">Shipping instructions (SI) text</label>
          <textarea
            id="si-text"
            rows={8}
            value={siText}
            onChange={(event) => setSiText(event.target.value)}
          />

          <label htmlFor="bl-text">Draft bill of lading (BL) text</label>
          <textarea
            id="bl-text"
            rows={8}
            value={blText}
            onChange={(event) => setBlText(event.target.value)}
          />

          <button type="submit">
            {busy ? 'Processing…' : 'Process email'}
          </button>
        </fieldset>
      </form>
    </section>
  )
}
