import requests
import time
from typing import Optional, Tuple, Dict, Any
from requests.exceptions import RequestException, Timeout, ConnectionError
from domain.execution_models import ExecutionStatus
from infrastructure.telemetry import get_tracer
from requests import Session


class HTTPClientAdapter:
    """Adapter for making HTTP requests with telemetry and error handling."""

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        base_wait_time: int = 2,
        user_agent: str = "GacetaCrawler/1.0",
        verify_ssl: bool = True,
        session: Optional[Session] = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_wait_time = base_wait_time
        self.user_agent = user_agent
        self.verify_ssl = verify_ssl
        self.session = session if session is not None else requests.Session()
        self.headers = {"User-Agent": user_agent}

    def head(self, url: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Perform HTTP HEAD request and return ETag and headers.

        Returns:
            Tuple of (etag, headers_dict)
        """
        with get_tracer().start_as_current_span("http.head") as span:
            span.set_attribute("url", url)

            for attempt in range(self.max_retries + 1):
                try:
                    response = self.session.head(
                        url,
                        timeout=self.timeout,
                        headers=self.headers,
                        verify=self.verify_ssl,
                    )
                    etag = response.headers.get("ETag")
                    span.set_attribute("status_code", response.status_code)
                    return (etag, dict(response.headers))
                except (RequestException, ConnectionError, Timeout) as e:
                    if attempt < self.max_retries:
                        wait_time = (
                            0
                            if self.base_wait_time == 0
                            else self.base_wait_time**attempt
                        )
                        time.sleep(wait_time)
                        continue
                    span.set_attribute("error", str(e))
                    raise
        return (None, {})  # Fallback for type checking

    def get(self, url: str) -> Tuple[Optional[str], str, int]:
        """
        Perform HTTP GET request and return content.

        Returns:
            Tuple of (etag, content, status_code)
        """
        with get_tracer().start_as_current_span("http.get") as span:
            span.set_attribute("url", url)

            for attempt in range(self.max_retries + 1):
                try:
                    response = self.session.get(
                        url,
                        timeout=self.timeout,
                        headers=self.headers,
                        verify=self.verify_ssl,
                    )
                    etag = response.headers.get("ETag")
                    content = response.text
                    status_code = response.status_code

                    span.set_attributes(
                        {
                            "status_code": status_code,
                            "content_length": len(content),
                            "execution_status": ExecutionStatus.COMPLETED.value,
                        }
                    )
                    return (etag, content, status_code)
                except (RequestException, ConnectionError, Timeout) as e:
                    if attempt < self.max_retries:
                        wait_time = (
                            0
                            if self.base_wait_time == 0
                            else self.base_wait_time**attempt
                        )
                        time.sleep(wait_time)
                        continue
                    span.set_attributes(
                        {
                            "error": str(e),
                            "execution_status": ExecutionStatus.FAILED.value,
                        }
                    )
                    raise
        # Unreachable in normal flow; added for type checking
        return (None, "", 0)
