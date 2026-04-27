import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import get_db, Base
import models 

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db



@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_headers(client):

    email = "testuser@example.com"
    password = "password123"
    
    reg_res = client.post("/users/create_user/", json={"email": email, "password": password})
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"

    
    response = client.post("/token", data={"username": email, "password": password})
    assert response.status_code == 200, f"Login failed: {response.text}"

    
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}