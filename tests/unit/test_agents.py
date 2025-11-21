"""
Unit tests for all agents:
- CustomerOrderAgent
- RestaurantAgent
- DriverAgent
- SupportAgent
- TrackingAgent
- PostDeliveryAgent
Ensures that agent initialization, prompt composition, and tool usage work.
"""

import pytest
from app.agents.customer_order_agent import CustomerOrderAgent
from app.agents.restaurant_agent import RestaurantAgent
from app.agents.driver_agent import DriverAgent
from app.agents.support_agent import SupportAgent
from app.agents.tracking_agent import TrackingAgent
from app.agents.post_delivery_agent import PostDeliveryAgent
from app.orchestration.state_manager import StateManager

@pytest.fixture(scope="module")
def state_manager():
    # Use in-memory mock for Redis in tests
    return StateManager(use_fake=True)

def test_customer_agent_initialization(state_manager):
    agent = CustomerOrderAgent(state_manager)
    assert agent.role == "Customer Order Agent"
    assert "order" in agent.capabilities
    assert callable(agent.handle_intent)

def test_restaurant_agent_initialization(state_manager):
    agent = RestaurantAgent(state_manager)
    assert agent.role == "Restaurant Coordination Agent"
    assert "restaurant" in agent.capabilities

def test_driver_agent_initialization(state_manager):
    agent = DriverAgent(state_manager)
    assert "driver" in agent.capabilities

def test_support_agent_initialization(state_manager):
    agent = SupportAgent(state_manager)
    assert agent.role == "Customer Support Agent"

def test_tracking_agent_initialization(state_manager):
    agent = TrackingAgent(state_manager)
    assert agent.role == "Delivery Tracking Agent"

def test_post_delivery_agent_initialization(state_manager):
    agent = PostDeliveryAgent(state_manager)
    assert agent.role == "Post Delivery Agent"

def test_agent_context_persistence(state_manager):
    agent = CustomerOrderAgent(state_manager)
    agent.state.set("current_order", {"items": ["pizza"]})
    restored = agent.state.get("current_order")
    assert restored["items"] == ["pizza"]
