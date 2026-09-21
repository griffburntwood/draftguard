const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL?.trim() || '/api'
).replace(/\/+$/, '')

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`
}

export type EmailRecord = {
  email_id: string
  from: string
  subject: string
  body: string
  attachments: string[]
}

export type TextDocumentInput = {
  document_id: string
  attachment_path: string
  text: string
}

export type ProcessingRequest = {
  email: EmailRecord
  si?: TextDocumentInput | null
  bl?: TextDocumentInput | null
}

export type SourceEvidence = {
  document_id: string
  location: string
  text: string | null
}

export type ExtractedField = {
  raw_value: string | null
  normalized_value: string | number | null
  state: 'extracted' | 'missing' | 'unreadable' | 'ambiguous'
  evidence: SourceEvidence[]
}

export type ComparisonResult = {
  comparison_id: string
  email_id: string
  si_document_id: string | null
  bl_document_id: string | null
  status: 'OK' | 'MISMATCH' | 'NEEDS_REVIEW'
  field_results: {
    field: string
    si: ExtractedField
    bl: ExtractedField
    outcome: 'MATCH' | 'MISMATCH' | 'UNKNOWN'
    explanation: string
  }[]
  defect_fields: string[]
  review_reasons: string[]
}

export type ProcessingResponse = {
  document_hashes?: Record<string, string>
  review_audit?: AuditEntry[]
  submission_entry?: SubmissionEntry
  classification: {
    email: EmailRecord
    category:
      | 'BL_COMPARISON'
      | 'SI_REQUEST'
      | 'INVOICE_QUERY'
      | 'GENERAL'
      | 'SPAM'
    explanation: string
  }
  comparison: ComparisonResult | null
}

export async function processText(
  request: ProcessingRequest,
): Promise<ProcessingResponse> {
  const response = await fetch(apiUrl('/process/text'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    if (response.status === 422) {
      throw new Error(
        'The request was rejected. Check the email and selected document details.',
      )
    }
    throw new Error(`Processing failed (HTTP ${response.status}). Please retry.`)
  }

  return response.json()
}

export type SubmissionEntry = {
  category: string
  status: 'OK' | 'MISMATCH' | 'NEEDS_REVIEW'
  review_reason: string | null
  has_defect: boolean
  defect_fields: string[]
}
export type AuditEntry = {
  side: 'si' | 'bl'
  field: string
  previous_value: string | number | null
  value: string | number
  reviewer: string
  reason: string
  timestamp: string
  original_comparison_id: string
}
export type InboxResponse = {
  submission: Record<string, SubmissionEntry>
  results: ProcessingResponse[]
  summary: { emails: number; categories: Record<string, number>; comparison_statuses: Record<string, number>; note: string }
}

async function post<T>(path: string, body: BodyInit, json = false): Promise<T> {
  const response = await fetch(apiUrl(path), {
    method: 'POST', body,
    headers: json ? { 'Content-Type': 'application/json' } : undefined,
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(typeof payload.detail === 'string' ? payload.detail : `Request failed (${response.status}). Check your inputs and retry.`)
  }
  return response.json()
}

export function processFiles(email: EmailRecord, si: File | null, bl: File | null) {
  const form = new FormData()
  form.append('email', JSON.stringify(email))
  if (si) form.append('si_file', si)
  if (bl) form.append('bl_file', bl)
  return post<ProcessingResponse>('/process/files', form)
}

export function processInbox(bundle: File) {
  const form = new FormData()
  form.append('bundle', bundle)
  return post<InboxResponse>('/process/inbox', form)
}

export function correctField(original: ProcessingResponse, reviewer: string, reason: string, side: string, field: string, value: string | number) {
  return post<ProcessingResponse>('/process/review', JSON.stringify({
    original, reviewer, reason, corrections: [{ side, field, value }],
  }), true)
}
