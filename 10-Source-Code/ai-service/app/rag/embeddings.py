import hashlib
from abc import ABC, abstractmethod

from app.core.config import settings


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class LocalHashEmbedding(EmbeddingProvider):
    """Deterministic, dependency-free fallback so the service runs offline (dev/CI) without
    an embedding API key. NOT semantically meaningful — swap in a real provider for production
    RAG quality. Same interface as a real provider, so the swap is a config change only."""

    def __init__(self, dimensions: int):
        self.dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Repeat the digest bytes to fill the target dimensionality, normalize to [-1, 1].
        values = [digest[i % len(digest)] for i in range(self.dimensions)]
        return [(v / 127.5) - 1.0 for v in values]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


def get_embedding_provider() -> EmbeddingProvider:
    # A real deployment would wire a provider such as Voyage AI here (Anthropic's recommended
    # embeddings partner) behind this same EmbeddingProvider interface, gated on an API key
    # being configured. Left as LocalHashEmbedding until that key is provisioned.
    return LocalHashEmbedding(dimensions=settings.embedding_dimensions)
