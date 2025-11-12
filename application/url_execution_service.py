from adapters.http_client import HTTPClientAdapter
from adapters.storage_adapter import StorageAdapter
from domain.content_normalizer import ContentNormalizer
from domain.execution_models import ExecutionRecord, ExecutionStatus, ChangeType
from datetime import datetime
import os
import hashlib
import time
from infrastructure.telemetry import get_tracer
from typing import Optional, Tuple, Dict


class URLExecutionService:
    """Service for executing URL downloads and detecting changes."""

    def __init__(
        self,
        http_client: HTTPClientAdapter,
        storage: StorageAdapter,
        normalizer: ContentNormalizer,
    ):
        self.http_client = http_client
        self.storage = storage
        self.normalizer = normalizer

    def execute_url(self, url: str) -> ExecutionRecord:
        """
        Execute a URL and detect changes using three-tier verification.

        Args:
            url: The URL to execute

        Returns:
            ExecutionRecord with execution results
        """
        start_time = time.time()
        execution_id = hashlib.md5(
            f"{url}-{datetime.now().isoformat()}".encode()
        ).hexdigest()

        with get_tracer().start_as_current_span("url_execution") as span:
            span.set_attribute("url", url)

            try:
                # Load previous execution record
                last_execution = self._load_last_execution(url)

                # Perform HEAD request to obtain ETag
                etag, _ = self._perform_head_request(url)

                # Skip download if ETag matches and check is enabled
                if self._should_skip_based_on_etag(last_execution, etag):
                    return ExecutionRecord(
                        url=url,
                        execution_id=execution_id,
                        timestamp=datetime.now(),
                        status=ExecutionStatus.SKIPPED,
                        change_detected=False,
                    )

                # Download content
                content_etag, content, _ = self._download_content(url)

                # Generate hashes for raw and normalized content
                content_hash, normalized_content, normalized_hash = (
                    self._generate_hashes(content)
                )

                # Determine change type and whether a change was detected
                change_type, change_detected = self._determine_change_type(
                    last_execution, content_hash, normalized_hash
                )

                # Build execution record
                execution = self._create_execution_record(
                    url=url,
                    execution_id=execution_id,
                    content_hash=content_hash,
                    normalized_hash=normalized_hash,
                    etag=content_etag,
                    content_size=len(content),
                    download_duration_ms=int((time.time() - start_time) * 1000),
                    change_detected=change_detected,
                    change_type=change_type,
                )

                # Persist execution and both raw/normalized content
                self.storage.save_execution(execution)
                self.storage.save_content(execution_id, content, normalized_content)

                return execution

            except Exception as e:
                span.set_attribute("error", str(e))
                return ExecutionRecord(
                    url=url,
                    execution_id=execution_id,
                    timestamp=datetime.now(),
                    status=ExecutionStatus.FAILED,
                    error_message=str(e),
                )

    # -------------------------------------------------------------------------
    # Private helper methods – each encapsulates a distinct step of execute_url
    # -------------------------------------------------------------------------

    def _load_last_execution(self, url: str) -> Optional[ExecutionRecord]:
        """Retrieve the most recent execution record for the given URL."""
        return self.storage.load_last_execution(url)

    def _perform_head_request(self, url: str) -> Tuple[Optional[str], Dict[str, str]]:
        """Perform a HEAD request and return the ETag (may be None) and response headers."""
        return self.http_client.head(url)

    def _should_skip_based_on_etag(
        self, last_execution: Optional[ExecutionRecord], etag: Optional[str]
    ) -> bool:
        """
        Determine whether the execution can be skipped based on ETag comparison.

        Returns True if:
          * ETag checking is enabled via ENABLE_ETAG_CHECK env var, and
          * a previous execution exists with a matching ETag.
        """
        if os.getenv("ENABLE_ETAG_CHECK", "true").lower() != "true":
            return False
        return bool(last_execution and etag is not None and last_execution.etag == etag)

    def _download_content(self, url: str) -> Tuple[Optional[str], str, int]:
        """Download the content of the URL, returning ETag (may be None), body, and status code."""
        return self.http_client.get(url)

    def _generate_hashes(self, content: str) -> Tuple[str, str, str]:
        """
        Compute hashes for raw and normalized content.

        Returns a tuple:
            (content_hash, normalized_content, normalized_hash)
        """
        content_hash = hashlib.md5(content.encode()).hexdigest()
        normalized_content = self.normalizer.normalize(content)
        normalized_hash = hashlib.md5(normalized_content.encode()).hexdigest()
        return content_hash, normalized_content, normalized_hash

    def _determine_change_type(
        self,
        last_execution: Optional[ExecutionRecord],
        content_hash: str,
        normalized_hash: str,
    ) -> Tuple[ChangeType, bool]:
        """
        Decide the type of change that occurred.

        Returns a tuple (change_type, change_detected).
        """
        if last_execution:
            if content_hash != last_execution.content_hash:
                return ChangeType.CONTENT_HASH_CHANGED, True
            if normalized_hash != last_execution.normalized_hash:
                return ChangeType.NORMALIZED_HASH_CHANGED, True
            return ChangeType.ETAG_CHANGED, True
        return ChangeType.NEW_CONTENT, True

    def _create_execution_record(
        self,
        url: str,
        execution_id: str,
        content_hash: str,
        normalized_hash: str,
        etag: Optional[str],
        content_size: int,
        download_duration_ms: int,
        change_detected: bool,
        change_type: ChangeType,
    ) -> ExecutionRecord:
        """Construct an ExecutionRecord for a successful execution."""
        return ExecutionRecord(
            url=url,
            execution_id=execution_id,
            timestamp=datetime.now(),
            status=ExecutionStatus.COMPLETED,
            content_hash=content_hash,
            normalized_hash=normalized_hash,
            etag=etag,
            content_size=content_size,
            download_duration_ms=download_duration_ms,
            change_detected=change_detected,
            change_type=change_type,
        )
