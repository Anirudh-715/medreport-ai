"""
Azure Document Intelligence Service Client with Automatic Fallback.

Provides document analysis capabilities using Azure's Document Intelligence
(formerly Form Recognizer) service. Extracts raw text, tables, and key-value
pairs from uploaded medical reports.

If Azure Document Intelligence is unavailable, or if the file exceeds
Azure Free Tier limits (4MB / page limit), it automatically falls back
to local high-speed PDF text extraction (pypdf).
"""

import io
import pypdf
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential

from app.config import Config


class DocumentIntelligenceService:
    """Service wrapper for Azure Document Intelligence with local fallback."""

    def __init__(self):
        """Initialize Document Intelligence client if configured."""
        endpoint = Config.AZURE_DOC_INTEL_ENDPOINT
        key = Config.AZURE_DOC_INTEL_KEY

        if endpoint and key and "your-resource-name" not in endpoint and "your-key" not in key:
            try:
                self.client = DocumentIntelligenceClient(
                    endpoint=endpoint,
                    credential=AzureKeyCredential(key),
                )
            except Exception as e:
                print(f"[DocIntel] Failed to init client: {e}")
                self.client = None
        else:
            self.client = None

    def extract_text(self, file_bytes: bytes) -> dict:
        """Extract text from document via Azure Document Intelligence or local fallback.

        Args:
            file_bytes: Binary content of uploaded document.

        Returns:
            dict with raw_text, tables, and key_value_pairs.
        """
        # Try Azure Document Intelligence first if file is <= 4MB
        if self.client is not None and len(file_bytes) <= 4 * 1024 * 1024:
            try:
                print("[DocIntel] Analyzing with Azure Document Intelligence...")
                req = AnalyzeDocumentRequest(bytes_source=file_bytes)
                poller = self.client.begin_analyze_document(
                    "prebuilt-layout",
                    body=req,
                )
                result = poller.result()

                raw_text = result.content if result.content else ""
                tables = self._extract_tables(result.tables)
                key_value_pairs = self._extract_key_value_pairs(result.key_value_pairs)

                if raw_text.strip():
                    print(f"[DocIntel] Azure extraction succeeded ({len(raw_text)} chars).")
                    return {
                        "raw_text": raw_text,
                        "tables": tables,
                        "key_value_pairs": key_value_pairs,
                    }
            except Exception as exc:
                print(f"[DocIntel] Azure Document Intelligence error: {exc}. Falling back to local extractor...")

        # Local Fallback using pypdf
        print("[DocIntel] Using local document parser...")
        local_text = self._extract_local_pdf(file_bytes)
        if local_text.strip():
            return {
                "raw_text": local_text,
                "tables": [],
                "key_value_pairs": [],
            }

        return {
            "error": "Could not extract text from document. Please ensure it is a readable PDF or clear image."
        }

    def _extract_local_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF bytes using pypdf."""
        try:
            stream = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(stream)
            extracted_pages = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(f"--- Page {i + 1} ---\n{page_text}")
            return "\n\n".join(extracted_pages)
        except Exception as e:
            print(f"[DocIntel] Local PDF extraction failed: {e}")
            return ""

    def _extract_tables(self, tables) -> list:
        """Parse table objects from Azure analysis result."""
        if not tables:
            return []

        extracted_tables = []
        for table in tables:
            col_count = table.column_count if table.column_count else 0
            row_count = table.row_count if table.row_count else 0
            if col_count == 0 or row_count == 0:
                continue

            grid = [["" for _ in range(col_count)] for _ in range(row_count)]
            for cell in table.cells:
                row_idx = cell.row_index
                col_idx = cell.column_index
                content = cell.content if cell.content else ""
                if row_idx < row_count and col_idx < col_count:
                    grid[row_idx][col_idx] = content

            headers = grid[0] if grid else []
            rows = grid[1:] if len(grid) > 1 else []
            extracted_tables.append({"headers": headers, "rows": rows})

        return extracted_tables

    def _extract_key_value_pairs(self, kv_pairs) -> list:
        """Parse key-value pair objects from Azure analysis result."""
        if not kv_pairs:
            return []

        extracted_pairs = []
        for pair in kv_pairs:
            key = pair.key.content if pair.key and pair.key.content else ""
            value = pair.value.content if pair.value and pair.value.content else ""
            if key or value:
                extracted_pairs.append({"key": key.strip(), "value": value.strip()})

        return extracted_pairs
