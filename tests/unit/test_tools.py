"""
Tests core business tools:
- customer_tools
- restaurant_tools
- driver_tools
- support_tools
"""

import pytest
from app.tools import customer_tools, restaurant_tools, driver_tools, support_tools

def test_add_to_order():
    order = {"items": []}
    result = customer_tools.add_to_order(order, "pizza", 1, {"size": "large"})
    assert len(result["items"]) == 1
    assert result["items"][0]["item"] == "pizza"

def test_calculate_total():
    order = {"items": [{"price": 200, "quantity": 2}, {"price": 100, "quantity": 1}]}
    total = customer_tools.calculate_total(order)
    assert total == 500

def test_restaurant_notify(monkeypatch):
    monkeypatch.setattr("requests.post", lambda *a, **k: type("R", (), {"ok": True})())
    res = restaurant_tools.notify_restaurant("rest_1", {"order_id": "123", "items": []})
    assert res["success"]

def test_driver_assign(monkeypatch):
    monkeypatch.setattr("requests.post", lambda *a, **k: type("R", (), {"ok": True})())
    res = driver_tools.assign_driver("driver_1", "order_123")
    assert res["success"]

def test_support_issue_creation():
    issue = support_tools.create_support_ticket("order_123", "Late delivery", "medium")
    assert issue["status"] == "open"
    assert "order_123" in issue["id"]
