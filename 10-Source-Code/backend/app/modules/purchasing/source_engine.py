"""Pure deterministic source-determination engine (SAP MM FR-009 / ADR-0005, simplified —
one org scope, no plant/organization shadowing since AIMS has a single purchasing scope per
org). Kept dependency-free (no DB, no ORM) so it can be unit tested directly — see
tests/test_source_determination.py.

Precedence, most to least authoritative:
  1. A blocked source (Supplier.is_blocked, or a SourceListEntry.is_blocked for this material)
     is never a candidate, regardless of any other rule.
  2. A fixed source-list entry wins outright — it is the only candidate returned.
  3. Otherwise, a quota arrangement ranks eligible suppliers by descending quota percentage.
  4. Otherwise, a purchasing info record ranks eligible suppliers by ascending price
     (cheapest first) — SAP's price/condition-scale mechanism, simplified to one price per
     supplier/material pair with no quantity-break scales (see purchasing/models.py).
  5. No rule produces a candidate -> the caller sees an empty list ("no source found").

Every candidate carries a `reason` string so the result is explainable, per FR-009's
"receives only eligible candidates with exact explanations" acceptance rule.
"""

import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SourceListInput:
    supplier_id: uuid.UUID
    is_fixed: bool
    is_blocked: bool
    valid_from: date | None
    valid_to: date | None


@dataclass(frozen=True)
class QuotaInput:
    supplier_id: uuid.UUID
    quota_percentage: float
    valid_from: date | None
    valid_to: date | None


@dataclass(frozen=True)
class InfoRecordInput:
    supplier_id: uuid.UUID
    price: float
    valid_from: date | None
    valid_to: date | None


@dataclass(frozen=True)
class SourceCandidate:
    supplier_id: uuid.UUID
    rank: int
    reason: str
    price: float | None


def _is_effective(valid_from: date | None, valid_to: date | None, as_of: date) -> bool:
    if valid_from and as_of < valid_from:
        return False
    if valid_to and as_of > valid_to:
        return False
    return True


def determine_sources(
    source_list: list[SourceListInput],
    quotas: list[QuotaInput],
    info_records: list[InfoRecordInput],
    blocked_supplier_ids: set[uuid.UUID],
    as_of: date,
) -> list[SourceCandidate]:
    effective_source_list = [
        e for e in source_list if _is_effective(e.valid_from, e.valid_to, as_of)
    ]

    explicitly_blocked = blocked_supplier_ids | {
        e.supplier_id for e in effective_source_list if e.is_blocked
    }

    fixed = [
        e for e in effective_source_list if e.is_fixed and e.supplier_id not in explicitly_blocked
    ]
    if fixed:
        chosen = fixed[0]
        return [
            SourceCandidate(
                supplier_id=chosen.supplier_id, rank=1, reason="Fixed source list entry", price=None
            )
        ]

    effective_quotas = [
        q
        for q in quotas
        if _is_effective(q.valid_from, q.valid_to, as_of) and q.supplier_id not in explicitly_blocked
    ]
    if effective_quotas:
        ranked = sorted(effective_quotas, key=lambda q: q.quota_percentage, reverse=True)
        return [
            SourceCandidate(
                supplier_id=q.supplier_id,
                rank=i + 1,
                reason=f"Quota arrangement: {q.quota_percentage:g}%",
                price=None,
            )
            for i, q in enumerate(ranked)
        ]

    effective_info_records = [
        r
        for r in info_records
        if _is_effective(r.valid_from, r.valid_to, as_of) and r.supplier_id not in explicitly_blocked
    ]
    if effective_info_records:
        ranked = sorted(effective_info_records, key=lambda r: r.price)
        return [
            SourceCandidate(
                supplier_id=r.supplier_id,
                rank=i + 1,
                reason=f"Purchasing info record price: {r.price:g}",
                price=r.price,
            )
            for i, r in enumerate(ranked)
        ]

    return []
