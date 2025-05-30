# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from core.settings import Settings

class TestSettings(Settings):
    REDIS_URL: str = "redis://localhost:6379/15"
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
