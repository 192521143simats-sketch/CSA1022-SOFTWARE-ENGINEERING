import pytest
import app as todo_app


@pytest.fixture(autouse=True)
def clean():
    todo_app.TODOS.clear()
    todo_app._next_id = 1


@pytest.fixture
def client():
    return todo_app.app.test_client()


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_home_page_loads(client):
    r = client.get("/")
    assert r.status_code == 200 and b"My To-Do List" in r.data


def test_add_task(client):
    client.post("/add", data={"title": "Buy milk"})
    assert client.get("/api/todos").get_json()[0]["title"] == "Buy milk"


def test_toggle_task(client):
    client.post("/add", data={"title": "Study Docker"})
    client.post("/toggle/1")
    assert client.get("/api/todos").get_json()[0]["done"] is True


def test_delete_task(client):
    client.post("/add", data={"title": "Temp"})
    client.post("/delete/1")
    assert client.get("/api/todos").get_json() == []


def test_api_requires_title(client):
    assert client.post("/api/todos", json={}).status_code == 400
