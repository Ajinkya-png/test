"""
VectorService using Qdrant and OpenAI embeddings.
- upsert_menu_items: upserts menu item documents with embeddings
- semantic_search: search by text query (OpenAI embedding -> Qdrant search)
"""

import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
import os
import time
import backoff
import openai
from ..core.config import settings

logger = logging.getLogger(__name__)

openai.api_key = settings.OPENAI_API_KEY

class VectorService:
    def __init__(self):
        # Qdrant connection (supports URL + API key)
        self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        self.collection = "menu_items"

    def ensure_collection(self, dim=1536):
        try:
            if not self.client.get_collection(self.collection):
                self.client.recreate_collection(self.collection, vectors_config=qdrant_models.VectorParams(size=dim, distance=qdrant_models.Distance.COSINE))
        except Exception:
            # If not found, create it
            self.client.recreate_collection(self.collection, vectors_config=qdrant_models.VectorParams(size=dim, distance=qdrant_models.Distance.COSINE))

    def _get_embedding(self, text: str) -> List[float]:
        # Using OpenAI embeddings (text-embedding-3-small or text-embedding-3-large)
        resp = openai.Embedding.create(model="text-embedding-3-small", input=text)
        return resp["data"][0]["embedding"]

    def upsert_menu_items(self, items: List[Dict[str, Any]]):
        """
        items: list of dicts containing 'id', 'name', 'description', 'price', 'restaurant_id'
        """
        self.ensure_collection()
        points = []
        for item in items:
            text = f"{item.get('name')} - {item.get('description', '')}"
            emb = self._get_embedding(text)
            point = qdrant_models.PointStruct(id=str(item["id"]), vector=emb, payload=item)
            points.append(point)
        # batch upsert
        self.client.upsert(collection_name=self.collection, points=points)
        return {"success": True, "upserted": len(points)}

    def semantic_search(self, query: str, top_k: int = 5):
        emb = self._get_embedding(query)
        hits = self.client.search(collection_name=self.collection, query_vector=emb, limit=top_k)
        results = []
        for hit in hits:
            results.append({"id": hit.id, "score": hit.score, "payload": hit.payload})
        return results
