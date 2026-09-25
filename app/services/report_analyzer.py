"""
Report Analyzer — Orchestrator Service.

Coordinates the full medical report analysis pipeline:

1. **Upload** the original file to Azure Blob Storage (optional).
2. **Extract** text, tables, and key-value pairs via Azure Document
   Intelligence.
3. **Summarize** the extracted text using Azure OpenAI.

Each step degrades gracefully when its backing Azure service is not
configured, allowing the application to run in partial-functionality
mode during development or when only a subset of services is available.
"""

from app.services.blob_storage import BlobStorageService
from app.services.document_intelligence import DocumentIntelligenceService
from app.services.openai_summarizer import OpenAISummarizerService


class ReportAnalyzerService:
    """High-level orchestrator for medical report analysis.

    Instantiates and coordinates the three underlying Azure service
    wrappers, combining their outputs into a single result dictionary
    that the API layer can return directly.
    """

    def __init__(self):
        """Initialize the underlying service clients."""
        self.blob_service = BlobStorageService()
        self.doc_intel_service = DocumentIntelligenceService()
        self.openai_service = OpenAISummarizerService()

    def analyze(self, file_bytes: bytes, filename: str) -> dict:
        """Run the full analysis pipeline on a medical document.

        Args:
            file_bytes: The binary content of the uploaded medical report.
            filename: The original filename of the uploaded file.

        Returns:
            A dict combining all pipeline outputs::

                {
                    "blob_url": str,
                    "extracted_text": str,
                    "tables": list,
                    "key_value_pairs": list,
                    "summary": str,
                    "key_findings": [str, ...],
                    "abnormal_values": [dict, ...],
                    "recommendations": [str, ...],
                    "severity": str,
                    "errors": [str, ...]  # non-fatal warnings
                }
        """
        errors: list[str] = []

        # ---- Step 1: Upload to Blob Storage (optional) ----
        print("[ReportAnalyzer] Step 1/3 — Uploading file to Blob Storage…")
        blob_url = self._upload_to_blob(file_bytes, filename, errors)

        # ---- Step 2: Extract text via Document Intelligence ----
        print("[ReportAnalyzer] Step 2/3 — Extracting text with Document Intelligence…")
        extraction = self._extract_text(file_bytes, errors)

        # ---- Step 3: Summarize via Azure OpenAI ----
        print("[ReportAnalyzer] Step 3/3 — Summarizing with Azure OpenAI…")
        summary_result = self._summarize(extraction["raw_text"], errors)

        # ---- Combine results ----
        result = {
            "blob_url": blob_url,
            "extracted_text": extraction["raw_text"],
            "tables": extraction["tables"],
            "key_value_pairs": extraction["key_value_pairs"],
            "summary": summary_result.get("summary", ""),
            "key_findings": summary_result.get("key_findings", []),
            "abnormal_values": summary_result.get("abnormal_values", []),
            "recommendations": summary_result.get("recommendations", []),
            "severity": summary_result.get("severity", "Normal"),
            "errors": errors,
        }

        print("[ReportAnalyzer] Analysis complete.")
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _upload_to_blob(
        self, file_bytes: bytes, filename: str, errors: list
    ) -> str:
        """Attempt to upload the file to Blob Storage.

        Returns:
            The blob URL on success, or an empty string on failure.
        """
        try:
            blob_url = self.blob_service.upload_file(file_bytes, filename)
            if blob_url:
                print(f"[ReportAnalyzer] File uploaded: {blob_url}")
            else:
                errors.append(
                    "Blob Storage is not configured — file was not persisted."
                )
            return blob_url
        except Exception as exc:
            msg = f"Blob Storage upload failed: {str(exc)}"
            print(f"[ReportAnalyzer] {msg}")
            errors.append(msg)
            return ""

    def _extract_text(self, file_bytes: bytes, errors: list) -> dict:
        """Attempt to extract text using Document Intelligence.

        Falls back to a placeholder message when the service is not
        configured or fails.

        Returns:
            A dict with ``raw_text``, ``tables``, and ``key_value_pairs``.
        """
        fallback = {
            "raw_text": (
                "Document text extraction is unavailable. "
                "Please configure Azure Document Intelligence "
                "(AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and "
                "AZURE_DOCUMENT_INTELLIGENCE_KEY) to enable "
                "automatic text extraction from uploaded reports."
            ),
            "tables": [],
            "key_value_pairs": [],
        }

        try:
            result = self.doc_intel_service.extract_text(file_bytes)

            if "error" in result:
                err_detail = result['error']
                msg = f"Document Intelligence: {err_detail}"
                print(f"[ReportAnalyzer] {msg}")
                errors.append(msg)
                return {
                    "raw_text": f"Document Text Extraction Error: {err_detail}",
                    "tables": [],
                    "key_value_pairs": [],
                }

            print(
                f"[ReportAnalyzer] Extracted {len(result.get('raw_text', ''))} "
                f"chars, {len(result.get('tables', []))} table(s), "
                f"{len(result.get('key_value_pairs', []))} KV pair(s)."
            )
            return result

        except Exception as exc:
            msg = f"Document Intelligence extraction failed: {str(exc)}"
            print(f"[ReportAnalyzer] {msg}")
            errors.append(msg)
            return fallback

    def _summarize(self, extracted_text: str, errors: list) -> dict:
        """Attempt to summarize the extracted text using Azure OpenAI.

        Falls back to a basic placeholder summary when the service is
        not configured or fails.

        Returns:
            A dict with ``summary``, ``key_findings``, ``abnormal_values``,
            ``recommendations``, and ``severity``.
        """
        fallback = {
            "summary": (
                "Automated summarization is unavailable. "
                "Please configure Azure OpenAI (AZURE_OPENAI_ENDPOINT "
                "and AZURE_OPENAI_KEY) to enable AI-powered report analysis."
            ),
            "key_findings": [],
            "abnormal_values": [],
            "recommendations": [
                "Configure Azure OpenAI to unlock automated medical report analysis."
            ],
            "severity": "Normal",
        }

        try:
            result = self.openai_service.summarize_report(extracted_text)

            if "error" in result:
                err_detail = result['error']
                msg = f"OpenAI Summarizer: {err_detail}"
                print(f"[ReportAnalyzer] {msg}")
                errors.append(msg)
                return {
                    "summary": f"AI Summarization Error: {err_detail}",
                    "key_findings": [],
                    "abnormal_values": [],
                    "recommendations": [
                        "Please check your API key and credentials in the .env file."
                    ],
                    "severity": "Normal",
                }

            print("[ReportAnalyzer] Summarization succeeded.")
            return result

        except Exception as exc:
            msg = f"OpenAI summarization failed: {str(exc)}"
            print(f"[ReportAnalyzer] {msg}")
            errors.append(msg)
            return fallback
