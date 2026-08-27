"""Storage service abstractions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StoredFile:
    storage_path: str
    stored_filename: str


class StorageService(ABC):
    @abstractmethod
    def store(self, company_id: str, stored_filename: str, content: bytes) -> StoredFile:
        raise NotImplementedError

    @abstractmethod
    def retrieve(self, storage_path: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def delete(self, storage_path: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, storage_path: str) -> bool:
        raise NotImplementedError
