import pytest
from app import app


@pytest.fixture
def client():
    with app.test_client() as c:
        yield c


def test_register(client):
    r = client.post("/register", json={
        "username": "alice",
        "password": "1234"
    })
    assert r.status_code == 200


def test_login(client):
    client.post("/register", json={
        "username": "bob",
        "password": "pass"
    })

    r = client.post("/login", data={
        "username": "bob",
        "password": "pass"
    })
    assert r.json["login"] is True


def test_calc(client):
    r = client.get("/calc?exp=2*5")
    assert r.json["result"] == 10


def test_users(client):
    r = client.get("/users")
    assert r.status_code == 200
