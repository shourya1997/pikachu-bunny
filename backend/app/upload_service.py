from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

import pdfplumber

from app.pocketbase_client import PocketBaseClient


class UploadService:
    def __init__(self):
        self.pb_client: PocketBaseClient | None = None

    async def __aenter__(self) -> UploadService:
        self.pb_client = PocketBaseClient()
        await self.pb_client.__aenter__()
        return self

    async def __aexit__(self, *args) -> None:
        if self.pb_client:
            await self.pb_client.__aexit__(*args)

    async def process_pdf(self, file_bytes: bytes, user_id: str, file_name: str) -> dict:
        audit_id = str(uuid.uuid4())

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            text = self._extract_text(tmp_path)

            assert self.pb_client
            audit = await self.pb_client.create(
                "audits",
                {
                    "audit_id": audit_id,
                    "file_name": file_name,
                    "status": "processing",
                    "extracted_text": text[:10000],
                    "user_id": user_id,
                },
                user_id,
            )
            return audit
        finally:
            os.unlink(tmp_path)

    def _extract_text(self, pdf_path: str) -> str:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        return text.strip()
