from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_diagnose_code_and_symptoms() -> None:
    payload = {
        "make": "Toyota",
        "model": "Corolla",
        "year": 2020,
        "mileage": 60000,
        "code": "P0171",
        "symptoms": "rough idle and poor fuel economy",
    }
    response = client.post("/diagnose", json=payload)
    assert response.status_code == 200

    body = response.json()
    expected_keys = {
        "diagnosis",
        "severity",
        "possible_causes",
        "repair_steps",
        "maintenance_recommendations",
        "confidence_score",
        "sources",
    }
    assert expected_keys.issubset(body.keys())
    assert isinstance(body["possible_causes"], list)
    assert isinstance(body["repair_steps"], list)
    assert isinstance(body["sources"], list)


def test_diagnose_maintenance_only() -> None:
    payload = {
        "make": "Toyota",
        "model": "Corolla",
        "mileage": 60000,
        "maintenance_query": "What service is due?",
    }
    response = client.post("/diagnose", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["maintenance_recommendations"], list)
    assert 0.0 <= float(body["confidence_score"]) <= 1.0
