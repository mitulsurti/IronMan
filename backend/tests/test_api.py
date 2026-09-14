from fastapi.testclient import TestClient

from ironman.api.main import app


client = TestClient(app)


def test_current_user_is_human_single_user_boundary() -> None:
    response = client.get("/api/v1/me")
    assert response.status_code == 200
    assert response.json() == {"actor_id": "owner", "actor_type": "human"}
