# backend/tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

from backend.app import create_app
from core.settings import Settings

# Load environment variables from .env file
load_dotenv()

class TestSettings(Settings):
    # Use Upstash Redis URL from environment or fallback to a mock/test URL
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/15")
    SAXO_APP_KEY: str = "test_key"
    SAXO_SECRET: str = "test_secret"
    SAXO_REDIRECT_URI: str = "http://localhost/callback"
    # any other overrides...

@pytest.fixture(scope="session")
def app():
    app = create_app()
    # override real settings with test settings
    app.dependency_overrides[Settings] = lambda: TestSettings()
    return app

@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)
