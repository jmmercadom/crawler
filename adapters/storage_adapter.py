import os
import json
import hashlib
from typing import Optional
from domain.execution_models import ExecutionRecord


class StorageAdapter:
    """Adapter for storing execution records and content."""

    def __init__(self, base_path: str = "executions"):
        self.base_path = base_path
        self.metadata_path = os.path.join(base_path, "metadata")
        self.content_path = os.path.join(base_path, "content")
        os.makedirs(self.metadata_path, exist_ok=True)
        os.makedirs(self.content_path, exist_ok=True)

    def _get_url_hash(self, url: str) -> str:
        """Generate MD5 hash of normalized URL."""
        return hashlib.md5(url.encode()).hexdigest()

    def _get_metadata_file(self, url: str) -> str:
        """Get path to metadata file for URL."""
        url_hash = self._get_url_hash(url)
        # Create directory structure: ab/cd/ef...
        dir_path = os.path.join(self.metadata_path, url_hash[:2], url_hash[2:4])
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, "executions.jsonl")

    def load_last_execution(self, url: str) -> Optional[ExecutionRecord]:
        """Load the most recent execution record for a URL."""
        file_path = self._get_metadata_file(url)

        if not os.path.exists(file_path):
            return None

        with open(file_path, "r") as f:
            # Read last line in JSONL file
            last_line = None
            for line in f:
                last_line = line.strip()
            if last_line:
                data = json.loads(last_line)
                return ExecutionRecord.from_dict(data)
        return None

    def save_execution(self, execution: ExecutionRecord) -> None:
        """Save execution record to JSONL file."""
        file_path = self._get_metadata_file(execution.url)

        with open(file_path, "a") as f:
            f.write(json.dumps(execution.to_dict()) + "\n")

    def save_content(
        self, execution_id: str, content: str, normalized_content: str | None = None
    ) -> str:
        """Save raw (and optionally normalized) content to files and return raw file path."""
        content_dir = os.path.join(self.content_path, execution_id)
        os.makedirs(content_dir, exist_ok=True)

        raw_path = os.path.join(content_dir, "raw.html")
        with open(raw_path, "w") as f:
            f.write(content)

        if normalized_content is not None:
            normalized_path = os.path.join(content_dir, "normalized.html")
            with open(normalized_path, "w") as f:
                f.write(normalized_content)

        return raw_path
