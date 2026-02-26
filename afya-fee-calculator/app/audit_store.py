"""In-memory audit log with query support for fee calculations."""

from datetime import datetime
from typing import Optional

from app.models import AuditEntry, FeeCalculationResponse


class AuditStore:
    """Thread-safe in-memory audit store for fee calculation results."""

    def __init__(self) -> None:
        self._entries: dict[str, AuditEntry] = {}

    def log(self, result: FeeCalculationResponse) -> None:
        """Log a fee calculation result."""
        entry = AuditEntry(
            transaction_id=result.transaction_id,
            timestamp=result.timestamp,
            country_code=result.input.country_code,
            payment_method=result.input.payment_method,
            amount=result.input.amount,
            currency=result.input.currency,
            result=result,
        )
        self._entries[result.transaction_id] = entry

    def get_by_id(self, transaction_id: str) -> Optional[AuditEntry]:
        """Get a specific audit entry by transaction ID."""
        return self._entries.get(transaction_id)

    def query(
        self,
        country_code: Optional[str] = None,
        payment_method: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[int, list[AuditEntry]]:
        """
        Query audit entries with optional filters.

        Returns (total_matching, page_of_entries).
        """
        results = list(self._entries.values())

        if country_code:
            results = [e for e in results if e.country_code == country_code.upper()]

        if payment_method:
            results = [e for e in results if e.payment_method == payment_method.lower()]

        if start_date:
            results = [e for e in results if e.timestamp >= start_date]

        if end_date:
            results = [e for e in results if e.timestamp <= end_date]

        # Sort by timestamp descending (most recent first)
        results.sort(key=lambda e: e.timestamp, reverse=True)

        total = len(results)
        page = results[offset : offset + limit]

        return total, page

    def clear(self) -> None:
        """Clear all audit entries (useful for testing)."""
        self._entries.clear()

    @property
    def count(self) -> int:
        """Number of entries in the store."""
        return len(self._entries)
