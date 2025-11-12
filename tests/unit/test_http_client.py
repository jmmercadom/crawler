import pytest
from typing import Dict, Any, Optional
from types import TracebackType
from unittest.mock import MagicMock, patch
from adapters.http_client import HTTPClientAdapter
from requests.exceptions import RequestException


class DummySpan:
    """Simple mock for an OpenTelemetry span."""

    def __init__(self) -> None:
        self.attributes: Dict[str, Any] = {}

    def __enter__(self) -> "DummySpan":
        return self

    def __exit__(
        self,
        exc_type: Optional[BaseException],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        pass

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def set_attributes(self, attrs: Dict[str, Any]) -> None:
        self.attributes.update(attrs)


class DummyTracer:
    """Tracer mock that returns a DummySpan."""

    def __init__(self) -> None:
        self.last_span: Optional[DummySpan] = None

    def start_as_current_span(self, name: str) -> DummySpan:
        span = DummySpan()
        self.last_span = span
        return span


@pytest.fixture
def dummy_tracer() -> DummyTracer:
    """Provides a DummyTracer instance for tests."""
    return DummyTracer()


def test_head_success(dummy_tracer: DummyTracer) -> None:
    # Mock response for a successful HEAD request
    mock_response = MagicMock()
    mock_response.headers = {"ETag": "test-etag", "Content-Type": "text/html"}
    mock_response.status_code = 200

    mock_session = MagicMock()
    mock_session.head.return_value = mock_response

    with patch("adapters.http_client.get_tracer", return_value=dummy_tracer):
        client = HTTPClientAdapter(session=mock_session, base_wait_time=0)
        etag, headers = client.head("http://example.com")

    assert etag == "test-etag"
    assert headers["Content-Type"] == "text/html"
    # Verify that the span recorded the URL and status code
    span = dummy_tracer.last_span
    assert span is not None
    assert span.attributes["url"] == "http://example.com"
    assert span.attributes["status_code"] == 200


def test_head_retry_on_exception(dummy_tracer: DummyTracer) -> None:
    # First call raises an exception, second call succeeds
    mock_response = MagicMock()
    mock_response.headers = {"ETag": "retry-etag"}
    mock_response.status_code = 200

    mock_session = MagicMock()
    mock_session.head.side_effect = [RequestException("temp error"), mock_response]

    with patch("adapters.http_client.get_tracer", return_value=dummy_tracer):
        client = HTTPClientAdapter(
            max_retries=1, session=mock_session, base_wait_time=0
        )
        etag, _ = client.head("http://example.com")

    assert etag == "retry-etag"
    # Ensure the span recorded the final successful request
    span = dummy_tracer.last_span
    assert span is not None
    assert span.attributes["url"] == "http://example.com"
    assert span.attributes["status_code"] == 200


def test_get_success(dummy_tracer: DummyTracer) -> None:
    # Mock response for a successful GET request
    mock_response = MagicMock()
    mock_response.headers = {"ETag": "get-etag"}
    mock_response.text = "response body"
    mock_response.status_code = 200

    mock_session = MagicMock()
    mock_session.get.return_value = mock_response

    with patch("adapters.http_client.get_tracer", return_value=dummy_tracer):
        client = HTTPClientAdapter(session=mock_session, base_wait_time=0)
        etag, content, status = client.get("http://example.com")

    assert etag == "get-etag"
    assert content == "response body"
    assert status == 200
    span = dummy_tracer.last_span
    assert span is not None
    assert span.attributes is not None
    assert span.attributes["url"] == "http://example.com"
    assert span.attributes["status_code"] == 200
    assert span.attributes["content_length"] == len("response body")
    assert span.attributes["execution_status"] == "completed"


def test_get_retry_and_failure(dummy_tracer: DummyTracer) -> None:
    # All attempts raise an exception, should propagate after retries
    mock_session = MagicMock()
    mock_session.get.side_effect = RequestException("persistent error")

    with patch("adapters.http_client.get_tracer", return_value=dummy_tracer):
        client = HTTPClientAdapter(
            max_retries=2, session=mock_session, base_wait_time=0
        )
        with pytest.raises(RequestException):
            client.get("http://example.com")

    # Span should have recorded the error and execution status FAILED
    span = dummy_tracer.last_span
    assert span is not None
    assert span.attributes is not None
    assert span.attributes["url"] == "http://example.com"
    assert span.attributes["error"] == "persistent error"
    assert span.attributes["execution_status"] == "failed"


def test_head_failure_raises(dummy_tracer: DummyTracer) -> None:
    """Ensure that a RequestException is re‑raised after max retries are exhausted
    and that the span records the error."""
    mock_session = MagicMock()
    mock_session.head.side_effect = RequestException("fatal error")

    with patch("adapters.http_client.get_tracer", return_value=dummy_tracer):
        client = HTTPClientAdapter(
            session=mock_session, max_retries=0, base_wait_time=0
        )
        with pytest.raises(RequestException):
            client.head("http://example.com")

    span = dummy_tracer.last_span
    assert span is not None
    assert span.attributes["url"] == "http://example.com"
    assert span.attributes["error"] == "fatal error"


def test_head_fallback_return(dummy_tracer: DummyTracer) -> None:
    """When ``max_retries`` is set to ``-1`` the retry loop is skipped,
    causing the method to fall back to the ``(None, {})`` return."""
    mock_session = MagicMock()
    # No need to configure ``head`` because it will never be called.

    with patch("adapters.http_client.get_tracer", return_value=dummy_tracer):
        client = HTTPClientAdapter(
            session=mock_session, max_retries=-1, base_wait_time=0
        )
        result = client.head("http://example.com")

    assert result == (None, {})
    span = dummy_tracer.last_span
    assert span is not None
    # No status_code should be recorded in this path
    assert "status_code" not in span.attributes


def test_get_fallback_return(dummy_tracer: DummyTracer) -> None:
    """When ``max_retries`` is set to ``-1`` the retry loop is skipped,
    causing the method to fall back to the ``(None, "", 0)`` return."""
    mock_session = MagicMock()
    # No need to configure ``get`` because it will never be called.

    with patch("adapters.http_client.get_tracer", return_value=dummy_tracer):
        client = HTTPClientAdapter(
            session=mock_session, max_retries=-1, base_wait_time=0
        )
        result = client.get("http://example.com")

    assert result == (None, "", 0)
    span = dummy_tracer.last_span
    assert span is not None
    # No status_code should be recorded in this path
    assert "status_code" not in span.attributes
