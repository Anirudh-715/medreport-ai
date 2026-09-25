"""
Configuration module — loads Azure credentials from environment variables.
"""

import os


class Config:
    """Application configuration loaded from environment variables."""

    # --- Azure Document Intelligence ---
    AZURE_DOC_INTEL_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "")
    AZURE_DOC_INTEL_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")

    # --- Azure OpenAI (if available) ---
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

    # --- Standard OpenAI ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # --- Free Alternative AI Providers ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    # --- Azure Blob Storage ---
    AZURE_STORAGE_CONN_STR = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "medical-reports")

    @classmethod
    def validate(cls) -> dict[str, bool]:
        """Check which Azure services are configured.

        Returns a dict mapping service name → True if credentials are present.
        """
        return {
            "document_intelligence": bool(cls.AZURE_DOC_INTEL_ENDPOINT and cls.AZURE_DOC_INTEL_KEY),
            "openai": bool(
                (cls.AZURE_OPENAI_ENDPOINT and cls.AZURE_OPENAI_KEY) or cls.OPENAI_API_KEY
            ),
            "blob_storage": bool(cls.AZURE_STORAGE_CONN_STR),
        }

    @classmethod
    def get_missing_services(cls) -> list[str]:
        """Return names of services that are NOT configured."""
        status = cls.validate()
        return [name for name, configured in status.items() if not configured]
