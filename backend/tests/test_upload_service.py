import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import os

from app.upload_service import UploadService


@pytest.mark.asyncio
async def test_upload_service_process_pdf():
    pdf_bytes = b"%PDF-1.4\n%fake pdf content"

    with patch("app.upload_service.PocketBaseClient") as mock_pb_class:
        mock_pb = AsyncMock()
        mock_pb_class.return_value = mock_pb

        mock_pb.create.return_value = {"id": "audit-123", "audit_id": "audit-123"}

        with patch("app.upload_service.pdfplumber") as mock_pdfplumber:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Basic: 50000\nPF: 5000\n"
            mock_pdf.pages = [mock_page]
            mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

            service = UploadService()
            async with service:
                result = await service.process_pdf(pdf_bytes, "user-1", "test.pdf")

        assert result["audit_id"] == "audit-123"
        assert result["id"] == "audit-123"


@pytest.mark.asyncio
async def test_upload_service_pdf_extraction():
    with patch("app.upload_service.pdfplumber") as mock_pdfplumber:
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample salary slip text"
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        service = UploadService()
        text = service._extract_text("/fake/path.pdf")

    assert "Sample salary slip text" in text


@pytest.mark.asyncio
async def test_upload_service_cleans_temp_file():
    pdf_bytes = b"%PDF-1.4"
    temp_files = []

    def track_temp_file(suffix=""):
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            temp_files.append(tmp.name)
            return tmp

    with patch("app.upload_service.tempfile.NamedTemporaryFile", side_effect=track_temp_file):
        with patch("app.upload_service.PocketBaseClient"):
            with patch("app.upload_service.pdfplumber"):
                service = UploadService()
                try:
                    async with service:
                        await service.process_pdf(pdf_bytes, "user-1", "test.pdf")
                except Exception:
                    pass

    for tmp_file in temp_files:
        assert not os.path.exists(tmp_file), f"Temp file {tmp_file} was not cleaned up"
