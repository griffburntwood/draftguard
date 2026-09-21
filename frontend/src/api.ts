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
  const response = await fetch('/api/process/text', {
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
