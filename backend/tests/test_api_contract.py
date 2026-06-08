from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_response_shape():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["message"] == "success"
    assert body["requestId"].startswith("req-")
    assert body["data"]["status"] == "ok"


def test_protected_endpoint_requires_token_before_database_access():
    response = client.get("/api/v1/customers")
    assert response.status_code == 401
    body = response.json()
    assert body["code"] == 40101
    assert body["data"] is None


def test_validation_error_uses_common_response_shape():
    response = client.post("/api/v1/auth/login", json={})
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == 40001
    assert isinstance(body["data"], list)


def test_room_static_routes_are_declared_before_dynamic_room_id_route():
    paths = [route.path for route in app.routes if hasattr(route, "path")]
    assert paths.index("/api/v1/rooms/available") < paths.index("/api/v1/rooms/{roomId}")
    assert paths.index("/api/v1/rooms/status-overview") < paths.index(
        "/api/v1/rooms/{roomId}"
    )
