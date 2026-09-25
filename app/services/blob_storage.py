"""
Azure Blob Storage Service.

Provides file upload and download capabilities using Azure Blob Storage.
Uploaded files receive a UUID-prefixed blob name to guarantee uniqueness.
The service gracefully degrades when credentials are not configured,
returning empty strings and empty bytes instead of raising exceptions.
"""

import uuid

from azure.storage.blob import BlobServiceClient

from app.config import Config


class BlobStorageService:
    """Service wrapper for Azure Blob Storage.

    Handles uploading medical report files to a configured container
    and downloading them by blob name. Automatically creates the
    target container if it does not already exist.

    Attributes:
        client: An authenticated BlobServiceClient instance, or None
                if the connection string is not configured.
        container_name: The name of the blob container to use.
    """

    def __init__(self):
        """Initialize the Blob Storage client.

        Reads the connection string and container name from application
        configuration. If the connection string is missing, the client
        is set to None and all operations become safe no-ops.
        """
        connection_string = Config.AZURE_STORAGE_CONN_STR
        self.container_name = Config.AZURE_STORAGE_CONTAINER or "medical-reports"

        if connection_string:
            try:
                self.client = BlobServiceClient.from_connection_string(connection_string)
                self._ensure_container_exists()
            except Exception as exc:
                print(f"[BlobStorage] Failed to initialize client: {exc}")
                self.client = None
        else:
            self.client = None

    def _ensure_container_exists(self):
        """Create the blob container if it does not already exist.

        Silently ignores ``ResourceExistsError`` so the service is
        idempotent across restarts.
        """
        try:
            container_client = self.client.get_container_client(self.container_name)
            if not container_client.exists():
                self.client.create_container(self.container_name)
                print(f"[BlobStorage] Created container '{self.container_name}'.")
        except Exception as exc:
            print(f"[BlobStorage] Could not verify/create container: {exc}")

    def upload_file(self, file_bytes: bytes, filename: str) -> str:
        """Upload a file to Azure Blob Storage.

        The blob name is constructed by prepending a UUID to the
        original filename, ensuring uniqueness even when the same file
        is uploaded multiple times.

        Args:
            file_bytes: The binary content of the file to upload.
            filename: The original filename (used as a suffix in the
                      blob name).

        Returns:
            The full URL of the uploaded blob on success, or an empty
            string if blob storage is not configured or the upload fails.
        """
        if self.client is None:
            print("[BlobStorage] Client not configured — skipping upload.")
            return ""

        try:
            unique_prefix = str(uuid.uuid4())
            blob_name = f"{unique_prefix}/{filename}"

            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=blob_name,
            )
            blob_client.upload_blob(file_bytes, overwrite=True)

            print(f"[BlobStorage] Uploaded blob: {blob_name}")
            return blob_client.url

        except Exception as exc:
            print(f"[BlobStorage] Upload failed: {exc}")
            return ""

    def download_file(self, blob_name: str) -> bytes:
        """Download a file from Azure Blob Storage.

        Args:
            blob_name: The name (path) of the blob to download.

        Returns:
            The binary content of the blob on success, or empty bytes
            if blob storage is not configured or the download fails.
        """
        if self.client is None:
            print("[BlobStorage] Client not configured — skipping download.")
            return b""

        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=blob_name,
            )
            stream = blob_client.download_blob()
            data = stream.readall()

            print(f"[BlobStorage] Downloaded blob: {blob_name} ({len(data)} bytes)")
            return data

        except Exception as exc:
            print(f"[BlobStorage] Download failed: {exc}")
            return b""
