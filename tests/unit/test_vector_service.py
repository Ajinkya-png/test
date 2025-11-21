import pytest
from app.services.vector_service import VectorService

@pytest.mark.skipif(True, reason="Requires OpenAI + Qdrant keys")
def test_upsert_and_search():
    """Integration-style test for semantic vector search (manual run)."""
    vs = VectorService()

    items = [{
        "id": "m1",
        "name": "Spicy Paneer",
        "description": "Hot and spicy paneer dish",
        "price": 200
    }]

    # Test upsert
    res = vs.upsert_menu_items(items)
    assert res["success"]

    # Test semantic search
    hits = vs.semantic_search("something spicy and hot")
    assert isinstance(hits, list)
