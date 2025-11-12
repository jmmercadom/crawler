import os
from typing import Generator
import tempfile
from datetime import datetime

import pytest

from adapters.storage_adapter import StorageAdapter
from domain.execution_models import ExecutionRecord, ExecutionStatus


@pytest.fixture
def temp_base_path() -> Generator[str, None, None]:
    """Create a temporary base directory for the adapter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_save_and_load_execution(temp_base_path: str) -> None:
    adapter = StorageAdapter(base_path=temp_base_path)

    # Create a simple ExecutionRecord
    record = ExecutionRecord(
        url="http://example.com",
        execution_id="exec-123",
        status=ExecutionStatus.COMPLETED,
        content_hash="abc123",
        timestamp=datetime(2025, 1, 1, 0, 0, 0),
    )

    # Save the record
    adapter.save_execution(record)

    # Load it back
    loaded = adapter.load_last_execution(record.url)
    assert loaded is not None
    # Compare dict representations for equality
    assert loaded.to_dict() == record.to_dict()


def test_save_content_returns_path_and_writes_file(temp_base_path: str) -> None:
    adapter = StorageAdapter(base_path=temp_base_path)

    execution_id = "exec-456"
    content = "<html><body>Hello</body></html>"

    raw_path = adapter.save_content(execution_id, content)

    # Path should be inside <base>/content/<execution_id>/raw.html
    expected_dir = os.path.join(adapter.content_path, execution_id)
    expected_path = os.path.join(expected_dir, "raw.html")
    assert raw_path == expected_path
    assert os.path.isfile(raw_path)

    # File content should match the provided string
    with open(raw_path, "r") as f:
        file_content = f.read()
    assert file_content == content


def test_save_content_with_normalized(temp_base_path: str) -> None:
    """Verify that both raw and normalized content are saved."""
    adapter = StorageAdapter(base_path=temp_base_path)

    execution_id = "exec-789"
    raw_content = "<html>raw</html>"
    normalized_content = "<html>normalized</html>"

    raw_path = adapter.save_content(execution_id, raw_content, normalized_content)

    # Raw path should point to raw.html
    expected_raw = os.path.join(adapter.content_path, execution_id, "raw.html")
    assert raw_path == expected_raw
    assert os.path.isfile(expected_raw)

    # Normalized file should exist and contain the normalized content
    normalized_path = os.path.join(
        adapter.content_path, execution_id, "normalized.html"
    )
    assert os.path.isfile(normalized_path)

    with open(normalized_path, "r") as f:
        assert f.read() == normalized_content
