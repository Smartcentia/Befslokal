"""Storage service for file management using Local Filesystem (Fly.io Volumes)."""
import os
from pathlib import Path
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)

class StorageService:
    def __init__(self):
        # Fly.io Volume usually mounted at /data or /app/data
        # We'll use /app/data/files as default
        self.local_base_path = Path("/app/data/files")
        self.local_base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized Local Storage at {self.local_base_path}")

    def list_blobs(self, prefix: str = None):
        """List files in the local storage."""
        try:
            p = self.local_base_path / (prefix or "")
            if not p.exists(): return []
            return [str(f.relative_to(self.local_base_path)) for f in p.glob("**/*") if f.is_file()]
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []

    def generate_upload_sas(self, blob_name: str, duration_minutes: int = 15) -> str:
        """
        Not supported for local storage. 
        Returns a direct API endpoint if we implemented a proxy, 
        but for now we'll indicate it's not available.
        """
        # Alternatively, return a direct path to the API endpoint that serves the file
        # e.g., /api/v1/files/download/{blob_name}
        # But legacy expectation was a SAS URL.
        logger.warning("generate_upload_sas calls are not supported on local storage.")
        return ""

    def get_file(self, path: str) -> bytes:
        """Read file from local storage."""
        clean_path = path.lstrip("/")
        
        # LEGACY FIX: Strip /app/data/files prefix if present
        legacy_prefix = "app/data/files/"
        if clean_path.startswith(legacy_prefix):
            clean_path = clean_path[len(legacy_prefix):]
        
        full_path = self.local_base_path / clean_path
        
        if not full_path.exists():
            # Try checking relative to root if absolute path was stored
            if Path(path).exists():
                 return Path(path).read_bytes()
                 
            logger.error(f"File not found locally: {full_path}")
            raise FileNotFoundError(f"File not found: {clean_path}")
            
        return full_path.read_bytes()

    def save_file(self, path: str, content: bytes) -> str:
        """Save file to local storage. Returns the stored relative path."""
        clean_path = path.lstrip("/")
        full_path = self.local_base_path / clean_path
        
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(content)
            logger.info(f"Saved file: {clean_path}")
            return clean_path
        except Exception as e:
            logger.error(f"Failed to save file {clean_path}: {e}")
            raise

def get_storage():
    return StorageService()
