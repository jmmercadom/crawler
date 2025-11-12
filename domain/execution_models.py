from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any


class ExecutionStatus(Enum):
    """Status of URL execution."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class ChangeType(Enum):
    """Type of content change detected."""

    ETAG_CHANGED = "etag_changed"
    CONTENT_HASH_CHANGED = "content_hash_changed"
    NORMALIZED_HASH_CHANGED = "normalized_hash_changed"
    NEW_CONTENT = "new_content"


class ExecutionRecord:
    """Domain model representing a URL execution record."""

    def __init__(
        self,
        url: str,
        execution_id: str,
        timestamp: datetime,
        status: ExecutionStatus,
        content_hash: Optional[str] = None,
        normalized_hash: Optional[str] = None,
        etag: Optional[str] = None,
        content_size: int = 0,
        download_duration_ms: Optional[int] = None,
        change_detected: bool = False,
        change_type: Optional[ChangeType] = None,
        error_message: Optional[str] = None,
    ):
        self.url = url
        self.execution_id = execution_id
        self.timestamp = timestamp
        self.status = status
        self.content_hash = content_hash
        self.normalized_hash = normalized_hash
        self.etag = etag
        self.content_size = content_size
        self.download_duration_ms = download_duration_ms
        self.change_detected = change_detected
        self.change_type = change_type
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "content_hash": self.content_hash,
            "normalized_hash": self.normalized_hash,
            "etag": self.etag,
            "content_size": self.content_size,
            "download_duration_ms": self.download_duration_ms,
            "change_detected": self.change_detected,
            "change_type": self.change_type.value if self.change_type else None,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionRecord":
        """Create from dictionary."""
        return cls(
            url=data["url"],
            execution_id=data["execution_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=ExecutionStatus(data["status"]),
            content_hash=data.get("content_hash"),
            normalized_hash=data.get("normalized_hash"),
            etag=data.get("etag"),
            content_size=data.get("content_size", 0),
            download_duration_ms=data.get("download_duration_ms"),
            change_detected=data.get("change_detected", False),
            change_type=ChangeType(data["change_type"])
            if data.get("change_type")
            else None,
            error_message=data.get("error_message"),
        )
