import uuid
from datetime import date

from app.modules.purchasing.source_engine import (
    InfoRecordInput,
    QuotaInput,
    SourceListInput,
    determine_sources,
)

TODAY = date(2026, 6, 1)


def _sid() -> uuid.UUID:
    return uuid.uuid4()


def test_no_rules_yields_no_candidates():
    result = determine_sources([], [], [], set(), TODAY)
    assert result == []


def test_fixed_source_wins_outright_over_cheaper_info_record():
    fixed_supplier = _sid()
    cheaper_supplier = _sid()
    result = determine_sources(
        source_list=[SourceListInput(fixed_supplier, is_fixed=True, is_blocked=False, valid_from=None, valid_to=None)],
        quotas=[],
        info_records=[
            InfoRecordInput(cheaper_supplier, price=1.0, valid_from=None, valid_to=None),
            InfoRecordInput(fixed_supplier, price=100.0, valid_from=None, valid_to=None),
        ],
        blocked_supplier_ids=set(),
        as_of=TODAY,
    )
    assert len(result) == 1
    assert result[0].supplier_id == fixed_supplier
    assert "Fixed" in result[0].reason


def test_blocked_supplier_is_never_a_candidate_even_if_fixed():
    blocked_supplier = _sid()
    result = determine_sources(
        source_list=[SourceListInput(blocked_supplier, is_fixed=True, is_blocked=False, valid_from=None, valid_to=None)],
        quotas=[],
        info_records=[],
        blocked_supplier_ids={blocked_supplier},
        as_of=TODAY,
    )
    assert result == []


def test_source_list_block_excludes_supplier_from_quota_ranking():
    blocked_via_source_list = _sid()
    eligible = _sid()
    result = determine_sources(
        source_list=[
            SourceListInput(blocked_via_source_list, is_fixed=False, is_blocked=True, valid_from=None, valid_to=None)
        ],
        quotas=[
            QuotaInput(blocked_via_source_list, quota_percentage=90, valid_from=None, valid_to=None),
            QuotaInput(eligible, quota_percentage=10, valid_from=None, valid_to=None),
        ],
        info_records=[],
        blocked_supplier_ids=set(),
        as_of=TODAY,
    )
    assert len(result) == 1
    assert result[0].supplier_id == eligible


def test_quota_ranks_descending_by_percentage():
    high = _sid()
    low = _sid()
    result = determine_sources(
        source_list=[],
        quotas=[
            QuotaInput(low, quota_percentage=30, valid_from=None, valid_to=None),
            QuotaInput(high, quota_percentage=70, valid_from=None, valid_to=None),
        ],
        info_records=[],
        blocked_supplier_ids=set(),
        as_of=TODAY,
    )
    assert [c.supplier_id for c in result] == [high, low]
    assert result[0].rank == 1
    assert result[1].rank == 2


def test_info_records_rank_ascending_by_price_when_no_quota_or_fixed_source():
    cheap = _sid()
    expensive = _sid()
    result = determine_sources(
        source_list=[],
        quotas=[],
        info_records=[
            InfoRecordInput(expensive, price=50.0, valid_from=None, valid_to=None),
            InfoRecordInput(cheap, price=10.0, valid_from=None, valid_to=None),
        ],
        blocked_supplier_ids=set(),
        as_of=TODAY,
    )
    assert [c.supplier_id for c in result] == [cheap, expensive]
    assert result[0].price == 10.0


def test_expired_info_record_is_excluded():
    expired_supplier = _sid()
    result = determine_sources(
        source_list=[],
        quotas=[],
        info_records=[
            InfoRecordInput(expired_supplier, price=10.0, valid_from=date(2020, 1, 1), valid_to=date(2021, 1, 1))
        ],
        blocked_supplier_ids=set(),
        as_of=TODAY,
    )
    assert result == []


def test_quota_takes_precedence_over_info_record_even_when_info_record_is_cheaper():
    quota_supplier = _sid()
    info_record_supplier = _sid()
    result = determine_sources(
        source_list=[],
        quotas=[QuotaInput(quota_supplier, quota_percentage=100, valid_from=None, valid_to=None)],
        info_records=[InfoRecordInput(info_record_supplier, price=1.0, valid_from=None, valid_to=None)],
        blocked_supplier_ids=set(),
        as_of=TODAY,
    )
    assert len(result) == 1
    assert result[0].supplier_id == quota_supplier
