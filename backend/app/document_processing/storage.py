"""Local filesystem storage for tender documents."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.config import Settings

logger = logging.getLogger(__name__)


class TenderDocumentStorage:
    def __init__(self, settings: Settings) -> None:
        self.root = Path(settings.document_storage_path).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if self.root not in candidate.parents and candidate != self.root:
            raise ValueError("Invalid tender document storage path.")
        return candidate

    def document_dir(self, tender_id: str, document_id: str) -> str:
        return str(Path("tenders") / tender_id / "documents" / document_id)

    def store_file(self, tender_id: str, document_id: str, filename: str, content: bytes) -> str:
        relative_dir = self.document_dir(tender_id, document_id)
        target_dir = self._resolve(relative_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / filename
        target_file.write_bytes(content)
        storage_path = str(Path(relative_dir) / filename)
        logger.info("Stored tender document", extra={"tender_id": tender_id, "document_id": document_id})
        return storage_path

    def store_extracted_manifest(self, tender_id: str, document_id: str, pages: list[dict]) -> str:
        relative_dir = self.document_dir(tender_id, document_id)
        target_dir = self._resolve(relative_dir) / "extracted_text"
        target_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = target_dir / "pages.json"
        manifest_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(manifest_path.relative_to(self.root))

    def read_file(self, storage_path: str) -> bytes:
        return self._resolve(storage_path).read_bytes()

    def delete_partial(self, storage_path: str) -> None:
        path = self._resolve(storage_path)
        if path.exists():
            path.unlink()

    def cleanup_temp_dir(self, tender_id: str, document_id: str) -> None:
        temp_dir = self._resolve(self.document_dir(tender_id, document_id)) / "tmp"
        if temp_dir.exists():
            for child in temp_dir.iterdir():
                if child.is_file():
                    child.unlink()
