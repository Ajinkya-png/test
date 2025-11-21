"""
Global Pytest configuration for the Food Delivery Voice AI system.

This file:
- Initializes a test database and Redis mock.
- Creates a FastAPI TestClient fixture.
- Sets up environment variables for tests.
- Provides fixtures for fake data and mock state management.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.orchestration.state_manager import StateManager

# ---------------------------------------------------------------------
# ENVIRONMENT SETUP
# ---------------------------------------------------------------------

# Force test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "fakeredis://"

# ---------------------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------------------

# Use SQLite for fast tests (in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables before tests and drop after session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db_session():
    """Provide a transactional scope for tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override DB dependency in FastAPI
app.dependency_overrides[get_db] = override_get_db

# ---------------------------------------------------------------------
# REDIS STATE FIXTURE
# ---------------------------------------------------------------------

@pytest.fixture(scope="session")
def fake_state_manager():
    """Use an in-memory fake Redis for state management."""
    sm = StateManager(use_fake=True)
    return sm

# ---------------------------------------------------------------------
# FASTAPI CLIENT FIXTURE
# ---------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    """Return a test client for FastAPI app."""
    return TestClient(app)

# ---------------------------------------------------------------------
# DUMMY DATA FIXTURES
# ---------------------------------------------------------------------

@pytest.fixture
def sample_order():
    return {
        "customer_id": "cust_001",
        "items": [
            {"id": "itm_1", "name": "Paneer Tikka", "quantity": 2, "price": 180},
            {"id": "itm_2", "name": "Naan", "quantity": 3, "price": 40},
        ],
        "address": "KLE Technological University, Belgaum",
        "payment_method": "card",
    }

@pytest.fixture
def sample_customer():
    return {"name": "Ajinkya", "email": "aj@example.com", "phone_number": "9876543210"}
