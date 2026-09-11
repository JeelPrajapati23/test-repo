import pytest
import json
from app import app, init_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr("app.DB", str(db_file))

    init_db()

    with app.test_client() as client:
        yield client


def test_register(client):
    response = client.post(
        "/register",
        json={
            "username": "alice",
            "password": "password123"
        }
    )

    assert response.status_code == 200


def test_login(client):
    client.post(
        "/register",
        json={
            "username": "alice",
            "password": "password123"
        }
    )

    response = client.post(
        "/login",
        data={
            "username": "alice",
            "password": "password123"
        }
    )

    assert response.status_code == 200


def test_invalid_login(client):
    client.post(
        "/register",
        json={
            "username": "alice",
            "password": "password123"
        }
    )

    response = client.post(
        "/login",
        data={
            "username": "alice",
            "password": "wrong-password"
        }
    )

    assert response.status_code == 401


def test_profile(client):
    client.post(
        "/register",
        json={
            "username": "alice",
            "password": "password123"
        }
    )

    response = client.get("/profile?id=1")

    assert response.status_code == 200
    assert response.json["username"] == "alice"


def test_admin_requires_authentication(client):
    response = client.get("/admin/users")

    assert response.status_code == 403


def test_search(client):
    client.post(
        "/register",
        json={
            "username": "alice",
            "password": "password123"
        }
    )

    response = client.get("/search?q=ali")

    assert response.status_code == 200
    assert len(response.json) == 1


def test_calculate(client):
    response = client.get("/calculate?expression=10*5")

    assert response.status_code == 200
    assert response.json["result"] == 50


def test_run_command(client):
    response = client.get("/run?command=hello")

    assert response.status_code == 200
    assert "hello" in response.json["output"]


def test_missing_file(client):
    response = client.get("/file?name=missing.txt")

    assert response.status_code == 404


def test_expensive_operation(client):
    response = client.get("/expensive?n=1000")

    assert response.status_code == 200
    assert response.json["count"] == 1000


def test_user_cache(client):
    client.post(
        "/register",
        json={
            "username": "bob",
            "password": "password123"
        }
    )

    response = client.get("/cache/bob")

    assert response.status_code == 200
    assert response.json["username"] == "bob"


def test_stats(client):
    client.get("/stats")

    response = client.get("/stats")

    assert response.status_code == 200
    assert response.json["requests"] >= 2


def test_proxy_invalid_url(client):
    response = client.get(
        "/proxy?url=http://127.0.0.1:9999"
    )

    assert response.status_code >= 400


def test_fetch_empty_urls(client):
    response = client.get("/fetch?urls=")

    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_long_search_query(client):
    query = "a" * 501

    response = client.get("/search?q=" + query)

    assert response.status_code == 400


def test_duplicate_registration(client):
    data = {
        "username": "alice",
        "password": "password123"
    }

    client.post("/register", json=data)
    response = client.post("/register", json=data)

    assert response.status_code == 500
