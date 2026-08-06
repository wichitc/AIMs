import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.read_models import Asset, RiskAssessment
from app.rag.embeddings import EmbeddingProvider
from app.rag.vector_store import DocumentEmbedding, similarity_search


@dataclass
class RetrievedContext:
    entity_type: str
    entity_id: uuid.UUID
    content: str


class Retriever:
    """Hybrid retrieval, always scoped to org_id from the caller's JWT (never client input) —
    see AI-Copilot-Design.md §3/§6."""

    def __init__(self, db: AsyncSession, embedding_provider: EmbeddingProvider):
        self.db = db
        self.embeddings = embedding_provider

    async def retrieve(self, question: str, org_id: uuid.UUID, top_k: int = 8) -> list[RetrievedContext]:
        vector_hits = await self._vector_search(question, org_id, top_k)
        structured_hits = await self._structured_fallback(question, org_id)

        seen: set[tuple[str, uuid.UUID]] = set()
        results: list[RetrievedContext] = []
        for hit in [*structured_hits, *vector_hits]:
            key = (hit.entity_type, hit.entity_id)
            if key in seen:
                continue
            seen.add(key)
            results.append(hit)
        return results[:top_k]

    async def _vector_search(self, question: str, org_id: uuid.UUID, top_k: int) -> list[RetrievedContext]:
        query_embedding = await self.embeddings.embed(question)
        hits: list[DocumentEmbedding] = await similarity_search(
            self.db, org_id=org_id, query_embedding=query_embedding, top_k=top_k
        )
        return [RetrievedContext(entity_type=h.entity_type, entity_id=h.entity_id, content=h.content) for h in hits]

    async def _structured_fallback(self, question: str, org_id: uuid.UUID) -> list[RetrievedContext]:
        """Common questions ("highest risk", "riskiest equipment") get precise structured
        answers rather than relying purely on semantic similarity."""
        lowered = question.lower()
        if "risk" not in lowered and "highest" not in lowered:
            return []

        stmt = (
            select(RiskAssessment, Asset)
            .join(Asset, Asset.id == RiskAssessment.asset_id)
            .where(Asset.org_id == org_id)
            .order_by(RiskAssessment.risk_score.desc())
            .limit(5)
        )
        rows = (await self.db.execute(stmt)).all()
        return [
            RetrievedContext(
                entity_type="RiskAssessment",
                entity_id=risk.id,
                content=(
                    f"Asset {asset.tag_number} ({asset.name}) has risk_rank={risk.risk_rank}, "
                    f"risk_score={risk.risk_score}, pof_score={risk.pof_score}, "
                    f"next_inspection_date={risk.next_inspection_date}."
                ),
            )
            for risk, asset in rows
        ]
