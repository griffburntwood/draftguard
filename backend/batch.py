"""Offline participant inbox runner. Never reads ground truth or runs bundle code."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from .classification import classify_email
from .documents import MAX_FILE_BYTES, document_kind, parse_document, read_document
from .models import EmailCategory, EmailRecord
from .processing import process_selected


class ParticipantInbox:
    def __init__(self, source):
        self.path = Path(source)
        self.archive = ZipFile(self.path) if self.path.is_file() else None

    def close(self):
        if self.archive:
            self.archive.close()

    def read(self, name):
        normalized = name.replace('\\', '/')
        parts = PurePosixPath(normalized)
        if parts.is_absolute() or '..' in parts.parts or (parts.parts and ':' in parts.parts[0]):
            raise ValueError('Unsafe participant path')
        if self.archive:
            if self.archive.getinfo(normalized).file_size > MAX_FILE_BYTES:
                raise ValueError('Participant file exceeds size limit')
            return self.archive.read(normalized)
        file = (self.path / normalized).resolve()
        if not file.is_relative_to(self.path.resolve()):
            raise ValueError('Participant file escapes dataset directory')
        with file.open('rb') as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise ValueError('Participant file exceeds size limit')
        return data

    def emails(self):
        names = self.archive.namelist() if self.archive else [str(p.relative_to(self.path)).replace('\\', '/') for p in (self.path / 'inbox').glob('email_*.json')]
        names = sorted(n for n in names if n.startswith('inbox/email_') and n.endswith('.json'))
        if not names:
            raise ValueError('No inbox/email_*.json files found; select the participant bundle root')
        emails = [EmailRecord.model_validate(json.loads(self.read(n))) for n in names]
        if len({e.email_id for e in emails}) != len(emails):
            raise ValueError('Duplicate email IDs in inbox')
        return emails


def run_inbox(source):
    inbox = ParticipantInbox(source)
    entries, details = {}, []
    try:
        for email in inbox.emails():
            classified = classify_email(email)
            selected = {'SI': [], 'BL': []}
            selection_reasons = []
            if classified.category == EmailCategory.BL_COMPARISON:
                for name in email.attachments:
                    try:
                        data = inbox.read(name)
                    except (OSError, KeyError, ValueError):
                        selection_reasons.append(f'Attachment is missing or unavailable: {name}')
                        continue
                    stem = PurePosixPath(name).stem.upper()
                    # Explicit participant filename roles select candidates, not correctness.
                    role = 'SI' if stem.endswith('_SI') else 'BL' if stem.endswith('_BL') else None
                    if role is None:
                        try:
                            text, _ = read_document(data, name)
                            kind = document_kind(text)
                            role = kind if kind in selected else None
                        except Exception:
                            pass
                    if role is None:
                        selection_reasons.append(f'Could not identify SI/BL role: {name}')
                        continue
                    selected[role].append(parse_document(data, name, f'{role.lower()}_{sha256(data).hexdigest()}', role))
            docs = [selected[role][0] if len(selected[role]) == 1 else None for role in ['SI', 'BL']]
            response = process_selected(classified, *docs)
            if response['comparison']:
                for role in selected:
                    if len(selected[role]) > 1:
                        selection_reasons.append(f'Multiple {role} candidates; a human must select the authoritative document.')
                response['comparison']['review_reasons'].extend(selection_reasons)
                if selection_reasons:
                    from .comparison_models import ComparisonResult
                    from .submission import build_submission_entry
                    response['comparison']['status'] = 'NEEDS_REVIEW'
                    response['comparison']['review_codes'].append('missing_attachment')
                    response['submission_entry'] = build_submission_entry(classified, ComparisonResult.model_validate(response['comparison']))
            entries[email.email_id] = response['submission_entry']
            details.append(response)
        summary = {
            'emails': len(entries),
            'categories': dict(Counter(e['category'] for e in entries.values())),
            'comparison_statuses': dict(Counter(e['status'] for e in entries.values() if e['category'] == 'BL_COMPARISON')),
            'review_reasons': dict(Counter(e['review_reason'] for e in entries.values() if e['review_reason'])),
            'note': 'Coverage and predictions only. No answer key was accessed; this is not an accuracy score.',
        }
        return entries, details, summary
    finally:
        inbox.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', help='Participant ZIP or folder containing inbox/ and attachments/')
    parser.add_argument('--output', default='data/results/submission.json')
    args = parser.parse_args()
    entries, details, summary = run_inbox(args.source)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(entries, indent=2), encoding='utf-8')
    output.with_name('processing_details.json').write_text(json.dumps(details, indent=2), encoding='utf-8')
    output.with_name('coverage_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    print(f'Saved {output}')


if __name__ == '__main__':
    main()
