import os
from datetime import datetime
from typing import Any
from types import TracebackType

import pytest
from unittest.mock import MagicMock, patch

from application.url_execution_service import URLExecutionService
from domain.execution_models import ExecutionRecord, ExecutionStatus, ChangeType
from domain.content_normalizer import ContentNormalizer


class DummySpan:
    """Simple mock for an OpenTelemetry span."""

    def __init__(self) -> None:
        self.attributes: dict[str, Any] = {}

    def __enter__(self) -> "DummySpan":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def set_attributes(self, attrs: dict[str, Any]) -> None:
        self.attributes.update(attrs)


class DummyTracer:
    """Tracer mock that returns a DummySpan."""

    def __init__(self) -> None:
        self.last_span: DummySpan | None = None

    def start_as_current_span(self, name: str) -> DummySpan:
        span = DummySpan()
        self.last_span = span
        return span


@pytest.fixture
def dummy_tracer() -> DummyTracer:
    """Provides a DummyTracer instance for tests."""
    return DummyTracer()


@pytest.fixture
def mock_http_client() -> MagicMock:
    """HTTP client mock with configurable head/get responses."""
    client = MagicMock()
    client.head.return_value = ("etag-123", {"Content-Type": "text/html"})
    client.get.return_value = ("etag-123", "<html>content</html>", 200)
    return client


@pytest.fixture
def mock_storage() -> MagicMock:
    """Storage adapter mock."""
    storage = MagicMock()
    storage.load_last_execution.return_value = None
    storage.save_execution.return_value = None
    storage.save_content.return_value = "/tmp/dummy/raw.html"
    return storage


@pytest.fixture
def mock_normalizer() -> MagicMock:
    """Content normalizer mock."""
    normalizer = MagicMock(spec=ContentNormalizer)
    normalizer.normalize.return_value = "<html>normalized</html>"
    return normalizer


@pytest.mark.integration
def test_service_initialization(
    mock_http_client: MagicMock, mock_storage: MagicMock, mock_normalizer: MagicMock
) -> None:
    """Service should be instantiated with provided dependencies."""
    service = URLExecutionService(
        http_client=mock_http_client,
        storage=mock_storage,
        normalizer=mock_normalizer,
    )
    assert service.http_client is mock_http_client
    assert service.storage is mock_storage
    assert service.normalizer is mock_normalizer


@pytest.mark.integration
@patch("application.url_execution_service.get_tracer", return_value=DummyTracer())
def test_execute_url_new_content(
    dummy_tracer: DummyTracer,
    mock_http_client: MagicMock,
    mock_storage: MagicMock,
    mock_normalizer: MagicMock,
) -> None:
    """When no previous execution exists, a new record is created."""
    service = URLExecutionService(
        http_client=mock_http_client,
        storage=mock_storage,
        normalizer=mock_normalizer,
    )

    record = service.execute_url("https://example.com")

    assert record.status == ExecutionStatus.COMPLETED
    assert record.change_detected is True
    assert record.change_type == ChangeType.NEW_CONTENT
    assert record.content_hash is not None
    assert record.normalized_hash is not None

    mock_storage.save_execution.assert_called_once()
    mock_storage.save_content.assert_called_once()


@pytest.mark.integration
@patch("application.url_execution_service.get_tracer", return_value=DummyTracer())
def test_execute_url_skip_due_to_etag(
    dummy_tracer: DummyTracer,
    mock_http_client: MagicMock,
    mock_storage: MagicMock,
    mock_normalizer: MagicMock,
) -> None:
    """If the stored ETag matches the current one, execution is skipped."""
    previous = ExecutionRecord(
        url="https://example.com",
        execution_id="prev-id",
        timestamp=datetime(2025, 1, 1, 0, 0, 0),
        status=ExecutionStatus.COMPLETED,
        etag="etag-123",
        content_hash="hash1",
        normalized_hash="norm1",
    )
    mock_storage.load_last_execution.return_value = previous
    mock_http_client.head.return_value = ("etag-123", {})

    os.environ["ENABLE_ETAG_CHECK"] = "true"

    service = URLExecutionService(
        http_client=mock_http_client,
        storage=mock_storage,
        normalizer=mock_normalizer,
    )

    record = service.execute_url("https://example.com")

    assert record.status == ExecutionStatus.SKIPPED
    assert record.change_detected is False
    assert record.change_type is None

    mock_http_client.get.assert_not_called()
    mock_storage.save_execution.assert_not_called()
    mock_storage.save_content.assert_not_called()


@pytest.mark.integration
@patch("application.url_execution_service.get_tracer", return_value=DummyTracer())
def test_execute_url_error_handling(
    dummy_tracer: DummyTracer,
    mock_http_client: MagicMock,
    mock_storage: MagicMock,
    mock_normalizer: MagicMock,
) -> None:
    """When an exception occurs during download, a FAILED record is returned."""
    mock_http_client.get.side_effect = Exception("network failure")

    service = URLExecutionService(
        http_client=mock_http_client,
        storage=mock_storage,
        normalizer=mock_normalizer,
    )

    record = service.execute_url("https://example.com")

    assert record.status == ExecutionStatus.FAILED
    assert record.error_message is not None
    assert "network failure" in record.error_message

    mock_storage.save_execution.assert_not_called()
    mock_storage.save_content.assert_not_called()
