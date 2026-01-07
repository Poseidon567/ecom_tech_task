from fastapi.testclient import TestClient
from my_app.main_api import app 
import pytest

@pytest.fixture(scope = "session")
def client():
    return TestClient(app)
