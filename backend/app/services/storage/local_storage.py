"""Local filesystem storage implementation."""

import logging
from pathlib import Path

from app.config import Settings
from app.services.storage.base import StorageService, StoredFile

logger = logging.getLogger(__name__)


class LocalStorageService(StorageService):
    def __init__(self, settings: Settings):
        self.root = Path(settings.upload_storage_path).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, storage_path: str) -> Path:
        candidate = (self.root / storage_path).resolve()
        if self.root not in candidate.parents and candidate != self.root:
            raise ValueError("Invalid storage path.")
        return candidate

    def store(self, company_id: str, stored_filename: str, content: bytes) -> StoredFile:
        relative_dir = Path("companies") / company_id
        target_dir = self._resolve_path(str(relative_dir))
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / stored_filename
        target_file.write_bytes(content)
        storage_path = str(relative_dir / stored_filename)
        logger.info("Stored company document", extra={"company_id": company_id, "storage_path": storage_path})
        return StoredFile(storage_path=storage_path, stored_filename=stored_filename)

    def retrieve(self, storage_path: str) -> bytes:
        return self._resolve_path(storage_path).read_bytes()

    def delete(self, storage_path: str) -> None:
        path = self._resolve_path(storage_path)
        if path.exists():
            path.unlink()

    def exists(self, storage_path: str) -> bool:
        return self._resolve_path(storage_path).exists()
