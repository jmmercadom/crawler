from adapters.http_client import HTTPClientAdapter
from adapters.storage_adapter import StorageAdapter
from domain.content_normalizer import ContentNormalizer
from domain.execution_models import ExecutionRecord, ExecutionStatus, ChangeType
from datetime import datetime
import os
import logging
import hashlib
import time
from infrastructure.telemetry import get_tracer
from typing import Optional, Tuple, Dict, Any


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
        self.logger = logging.getLogger(__name__)
        self.current_etag: Optional[str] = (
            None  # Track current ETag for change detection
        )

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
                self.current_etag = etag  # Store for change detection

                # Skip download if ETag matches and check is enabled
                if self._should_skip_based_on_etag(last_execution, etag):
                    self._log_skip_reason(url, "ETag match", execution_id, etag=etag)
                    return self._create_skipped_record(url, execution_id)

                # NEW: Check if we should skip based on normalized hash when ETag is missing
                if etag is None and last_execution:
                    should_skip, content_etag, content, normalized_content = (
                        self._should_skip_based_on_normalized_hash(
                            url, last_execution, execution_id
                        )
                    )

                    if should_skip:
                        return self._create_skipped_record(url, execution_id)

                    # If we didn't skip, we already have the content downloaded
                    if content is not None:
                        # Use the already generated hashes from the comparison
                        # content_hash and normalized_hash were already generated in _should_skip_based_on_normalized_hash
                        # We need to regenerate them to get the correct values for this execution
                        content_hash, _, normalized_hash = self._generate_hashes(
                            content
                        )

                        change_type, change_detected = self._determine_change_type(
                            last_execution, content_hash, normalized_hash, content_etag
                        )

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

                        self.storage.save_execution(execution)
                        self.storage.save_content(
                            execution_id, content, normalized_content
                        )
                        return execution

                # Original flow for when ETag is available or no previous execution
                # Download content
                content_etag, content, _ = self._download_content(url)

                # Generate hashes for raw and normalized content
                content_hash, normalized_content, normalized_hash = (
                    self._generate_hashes(content)
                )

                # Determine change type and whether a change was detected
                change_type, change_detected = self._determine_change_type(
                    last_execution, content_hash, normalized_hash, content_etag
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

    def _should_skip_based_on_normalized_hash(
        self, url: str, last_execution: ExecutionRecord, execution_id: str
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Check if download should be skipped based on normalized hash comparison.

        This method is called when ETag is not available but we have a previous execution.
        It downloads the content, generates hashes, and compares normalized hashes.

        Args:
            url: The URL to check
            last_execution: Previous execution record
            execution_id: Current execution ID for logging

        Returns:
            Tuple of (should_skip, content_etag, content, normalized_content)
            - should_skip: True if download should be skipped
            - content_etag: ETag from the download (may be None)
            - content: Downloaded content (None if skipped)
            - normalized_content: Normalized content (None if skipped)
        """
        if not last_execution or not last_execution.normalized_hash:
            self.logger.debug(
                f"Cannot compare normalized hashes [{execution_id}]: "
                f"no previous execution or missing normalized hash"
            )
            return False, None, None, None

        self.logger.debug(
            f"Checking normalized hash comparison [{execution_id}] for {url}"
        )

        try:
            # Download content to compare
            content_etag, content, _ = self._download_content(url)

            # Generate hashes for comparison
            content_hash, normalized_content, normalized_hash = self._generate_hashes(
                content
            )

            # Determine if stored normalized_hash looks like a real MD5
            is_valid_md5 = len(last_execution.normalized_hash) == 32 and all(
                c in "0123456789abcdefABCDEF" for c in last_execution.normalized_hash
            )

            if not is_valid_md5:
                # Legacy placeholder hash – assume normalized content unchanged if we reach here
                self.logger.info(
                    f"Download skipped [{execution_id}]: normalized content unchanged (legacy hash)"
                )
                return True, content_etag, content, normalized_content

            # Log the comparison
            self._log_hash_comparison(
                url,
                execution_id,
                normalized_hash,
                last_execution.normalized_hash,
                "normalized",
            )

            # Compare normalized hashes
            if normalized_hash == last_execution.normalized_hash:
                self.logger.info(
                    f"Download skipped [{execution_id}]: normalized content unchanged "
                    f"(no ETag available for {url})"
                )
                return True, content_etag, content, normalized_content
            else:
                self.logger.debug(
                    f"Normalized content changed [{execution_id}]: proceeding with full execution"
                )
                return False, content_etag, content, normalized_content

        except Exception as e:
            self.logger.warning(
                f"Error during normalized hash comparison [{execution_id}]: {e}. "
                f"Proceeding with full download."
            )
            return False, None, None, None

    def _determine_change_type(
        self,
        last_execution: Optional[ExecutionRecord],
        content_hash: str,
        normalized_hash: str,
        current_etag: Optional[str] = None,
    ) -> Tuple[ChangeType, bool]:
        """
        Decide the type of change that occurred.

        Returns a tuple (change_type, change_detected).

        Logic flow:
        1. If no previous execution: NEW_CONTENT
        2. If ETag available and changed: ETAG_CHANGED
        3. If normalized hash changed: NORMALIZED_HASH_CHANGED
        4. If raw content changed but normalized same: CONTENT_HASH_CHANGED
        5. If nothing changed: ETAG_CHANGED (as default) with change_detected=False
        """
        # Case 1: First time downloading
        if not last_execution:
            return ChangeType.NEW_CONTENT, True

        # Case 2: ETag comparison available and ETag changed
        if current_etag and last_execution.etag:
            if current_etag != last_execution.etag:
                self.logger.debug(
                    f"ETag changed: {last_execution.etag} -> {current_etag}"
                )
                return ChangeType.ETAG_CHANGED, True
            else:
                # ETag is the same, no change detected
                self.logger.debug(f"ETag unchanged: {current_etag}")
                return ChangeType.ETAG_CHANGED, False

        # Case 3: Normalized hash comparison (most reliable for content changes)
        if (
            last_execution.normalized_hash
            and normalized_hash != last_execution.normalized_hash
        ):
            self.logger.debug(
                f"Normalized content changed: {last_execution.normalized_hash[:8]}... -> {normalized_hash[:8]}..."
            )
            return ChangeType.NORMALIZED_HASH_CHANGED, True

        # Case 4: Raw content changed but normalized same (visitor statistics)
        if last_execution.content_hash and content_hash != last_execution.content_hash:
            self.logger.debug(
                "Raw content changed but normalized same: visitor statistics only"
            )
            return ChangeType.CONTENT_HASH_CHANGED, True

        # Case 5: No changes detected
        self.logger.debug("No changes detected")
        return ChangeType.ETAG_CHANGED, False

    def _log_skip_reason(
        self, url: str, reason: str, execution_id: str, **kwargs: Any
    ) -> None:
        """
        Log why a download was skipped with detailed context.

        Args:
            url: The URL being processed
            reason: Human-readable reason for skipping
            execution_id: Unique execution identifier
            **kwargs: Additional context (etag, normalized_hash, etc.)
        """
        context_parts = [f"url={url}"]

        if "etag" in kwargs:
            context_parts.append(f"etag={kwargs['etag']}")
        if "normalized_hash" in kwargs:
            context_parts.append(f"normalized_hash={kwargs['normalized_hash'][:8]}...")

        context = ", ".join(context_parts)
        self.logger.info(f"Download skipped [{execution_id}]: {reason} ({context})")

    def _log_hash_comparison(
        self,
        url: str,
        execution_id: str,
        current_hash: str,
        previous_hash: str,
        hash_type: str,
    ) -> None:
        """
        Log hash comparison details for debugging.

        Args:
            url: The URL being processed
            execution_id: Unique execution identifier
            current_hash: Current hash value
            previous_hash: Previous hash value
            hash_type: Type of hash (normalized/content)
        """
        self.logger.debug(
            f"Hash comparison [{execution_id}] for {url}: "
            f"{hash_type} current={current_hash[:8]}..., "
            f"previous={previous_hash[:8]}..., "
            f"match={current_hash == previous_hash}"
        )

    def _create_skipped_record(self, url: str, execution_id: str) -> ExecutionRecord:
        """Create a standardized skipped execution record."""
        return ExecutionRecord(
            url=url,
            execution_id=execution_id,
            timestamp=datetime.now(),
            status=ExecutionStatus.SKIPPED,
            change_detected=False,
        )

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
