"""Multipart upload endpoint; original filenames are never written to disk."""
import json
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from .classification import classify_email
from .documents import MAX_FILE_BYTES, SUPPORTED_TYPES, parse_document
from .models import EmailCategory, EmailRecord
from .processing import process_selected
from .processing_models import TextProcessingResponse
from hashlib import sha256
from pathlib import PurePosixPath

router = APIRouter()


@router.post('/process/files', response_model=TextProcessingResponse)
async def process_files(
    email: Annotated[str, Form(max_length=100_000)],
    si_file: Annotated[UploadFile | None, File()] = None,
    bl_file: Annotated[UploadFile | None, File()] = None,
):
    try:
        record = EmailRecord.model_validate(json.loads(email))
    except (ValueError, ValidationError):
        raise HTTPException(422, 'email must be a valid EmailRecord JSON string')
    classified = classify_email(record)
    documents = []
    try:
        if classified.category != EmailCategory.BL_COMPARISON:
            return process_selected(classified, None, None)
        for role, upload in [('SI', si_file), ('BL', bl_file)]:
            if upload is None:
                documents.append(None)
                continue
            filename = (upload.filename or '').replace('\\', '/')
            filename = PurePosixPath(filename).name
            if PurePosixPath(filename).suffix.lower() not in SUPPORTED_TYPES:
                raise HTTPException(415, 'Supported file types: TXT, PDF, DOCX, XLSX')
            data = await upload.read(MAX_FILE_BYTES + 1)
            if len(data) > MAX_FILE_BYTES:
                raise HTTPException(413, 'Each document must be at most 10 MiB')
            doc_id = f'{role.lower()}_{sha256(data).hexdigest()}'
            documents.append(await run_in_threadpool(parse_document, data, filename, doc_id, role))
        return process_selected(classified, *documents)
    finally:
        for upload in (si_file, bl_file):
            if upload:
                await upload.close()


@router.post('/process/inbox')
async def process_inbox(bundle: Annotated[UploadFile, File()]):
    from tempfile import TemporaryDirectory
    from pathlib import Path
    from .batch import run_inbox
    try:
        data = await bundle.read(30 * 1024 * 1024 + 1)
        if len(data) > 30 * 1024 * 1024:
            raise HTTPException(413, 'Inbox ZIP must be at most 30 MiB')
        from zipfile import ZipFile, BadZipFile
        from io import BytesIO
        try:
            with ZipFile(BytesIO(data)) as archive:
                info = archive.infolist()
                if len(info) > 3000 or sum(f.file_size for f in info) > 100 * 1024 * 1024:
                    raise HTTPException(413, 'Inbox ZIP exceeds expanded size or file-count limits')
                if sum(n.startswith('inbox/email_') and n.endswith('.json') for n in archive.namelist()) > 1000:
                    raise HTTPException(413, 'Inbox limit is 1000 emails')
            with TemporaryDirectory(prefix='draftguard-inbox-') as folder:
                path = Path(folder) / 'participant.zip'
                path.write_bytes(data)
                submission, results, summary = await run_in_threadpool(run_inbox, path)
            return {'submission': submission, 'results': results, 'summary': summary}
        except (BadZipFile, ValueError, KeyError, OSError):
            raise HTTPException(422, 'Use a participant ZIP containing inbox/email_*.json and attachments/.')
    finally:
        await bundle.close()
