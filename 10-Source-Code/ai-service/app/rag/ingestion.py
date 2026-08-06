"""Batch ingestion job: summarizes source-of-truth rows into short text chunks and embeds
them into document_embedding. Run on a schedule (e.g. every 15 min) or triggered after
significant writes. Entry point: `python -m app.rag.ingestion`.
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.read_models import Asset, CorrosionRecord, Equipment, Finding, RiskAssessment
from app.rag.embeddings import get_embedding_provider
from app.rag.vector_store import upsert_embedding

logger = logging.getLogger(__name__)


async def _ingest_assets(db: AsyncSession, embeddings) -> int:
    rows = (await db.execute(select(Asset))).scalars().all()
    for asset in rows:
        content = f"Asset {asset.tag_number}: {asset.name}. Status: {asset.status}."
        embedding = await embeddings.embed(content)
        await upsert_embedding(
            db, org_id=asset.org_id, entity_type="Asset", entity_id=asset.id, content=content, embedding=embedding
        )
    return len(rows)


async def _ingest_risk_assessments(db: AsyncSession, embeddings) -> int:
    stmt = select(RiskAssessment, Asset).join(Asset, Asset.id == RiskAssessment.asset_id)
    rows = (await db.execute(stmt)).all()
    for risk, asset in rows:
        content = (
            f"Risk assessment for asset {asset.tag_number} on {risk.assessment_date}: "
            f"risk_rank={risk.risk_rank}, risk_score={risk.risk_score}, pof_score={risk.pof_score}, "
            f"next_inspection_date={risk.next_inspection_date}."
        )
        embedding = await embeddings.embed(content)
        await upsert_embedding(
            db, org_id=asset.org_id, entity_type="RiskAssessment", entity_id=risk.id,
            content=content, embedding=embedding,
        )
    return len(rows)


async def _ingest_findings(db: AsyncSession, embeddings) -> int:
    stmt = select(Finding, Equipment, Asset).join(Equipment, Equipment.id == Finding.equipment_id).join(
        Asset, Asset.id == Equipment.asset_id
    )
    rows = (await db.execute(stmt)).all()
    for finding, equipment, asset in rows:
        content = (
            f"Finding on {equipment.tag_number} (asset {asset.tag_number}): "
            f"{finding.finding_type}, severity={finding.severity}, status={finding.status}. "
            f"{finding.description}"
        )
        embedding = await embeddings.embed(content)
        await upsert_embedding(
            db, org_id=asset.org_id, entity_type="Finding", entity_id=finding.id,
            content=content, embedding=embedding,
        )
    return len(rows)


async def _ingest_corrosion_records(db: AsyncSession, embeddings) -> int:
    stmt = select(CorrosionRecord, Equipment, Asset).join(
        Equipment, Equipment.id == CorrosionRecord.equipment_id
    ).join(Asset, Asset.id == Equipment.asset_id)
    rows = (await db.execute(stmt)).all()
    for record, equipment, asset in rows:
        content = (
            f"Corrosion record for {equipment.tag_number} (asset {asset.tag_number}) on {record.assessment_date}: "
            f"governing_rate={record.governing_rate_mm_yr} mm/yr, "
            f"remaining_life={record.remaining_life_years} years, "
            f"next_inspection_date={record.next_inspection_date}."
        )
        embedding = await embeddings.embed(content)
        await upsert_embedding(
            db, org_id=asset.org_id, entity_type="CorrosionRecord", entity_id=record.id,
            content=content, embedding=embedding,
        )
    return len(rows)


async def run_ingestion() -> dict[str, int]:
    embeddings = get_embedding_provider()
    async with AsyncSessionLocal() as db:
        counts = {
            "assets": await _ingest_assets(db, embeddings),
            "risk_assessments": await _ingest_risk_assessments(db, embeddings),
            "findings": await _ingest_findings(db, embeddings),
            "corrosion_records": await _ingest_corrosion_records(db, embeddings),
        }
        await db.commit()
    logger.info("Ingestion complete: %s", counts)
    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_ingestion())
