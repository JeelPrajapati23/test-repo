import os
import tempfile

import pytest

from taskapi import create_app

HEADERS = {"X-Api-Key": "dev-local-only-key"}


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    app = create_app(db_path=path)
    app.testing = True
    with app.test_client() as client:
        yield client
    try:
        os.remove(path)
    except PermissionError:
        pass


def test_create_and_get_task(client):
    resp = client.post(
        "/tasks", json={"title": "Write tests", "tag": "work"}, headers=HEADERS
    )
    assert resp.status_code == 201
    task_id = resp.get_json()["id"]

    resp = client.get(f"/tasks/{task_id}", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "Write tests"


def test_create_requires_title(client):
    resp = client.post("/tasks", json={}, headers=HEADERS)
    assert resp.status_code == 400


def test_list_pagination(client):
    for i in range(5):
        client.post("/tasks", json={"title": f"task {i}"}, headers=HEADERS)

    resp = client.get("/tasks?page=1&page_size=2", headers=HEADERS)
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2


def test_requires_api_key(client):
    resp = client.get("/tasks")
    assert resp.status_code == 401


def test_delete_task(client):
    resp = client.post("/tasks", json={"title": "temp"}, headers=HEADERS)
    task_id = resp.get_json()["id"]

    resp = client.delete(f"/tasks/{task_id}", headers=HEADERS)
    assert resp.status_code == 204

    resp = client.get(f"/tasks/{task_id}", headers=HEADERS)
    assert resp.status_code == 404
