from app import app


def test_home():
    assert app.test_client().get("/").get_json()["version"] == "1.0"


def test_health():
    assert app.test_client().get("/health").get_json() == {"status": "ok"}


def test_add():
    assert app.test_client().get("/add/2/3").get_json() == {"result": 5}
