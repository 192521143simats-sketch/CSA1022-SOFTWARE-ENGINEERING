import app as m


def c():
    return m.app.test_client()


def test_home():
    assert c().get("/").get_json()["version"] == "1.0"


def test_health():
    assert c().get("/health").get_json()["status"] == "healthy"


def test_list_students():
    assert len(c().get("/api/students").get_json()) >= 2


def test_get_missing_student():
    assert c().get("/api/students/999").status_code == 404


def test_add_student():
    r = c().post("/api/students", json={"name": "Meena", "dept": "ECE"})
    assert r.status_code == 201 and r.get_json()["name"] == "Meena"


def test_add_requires_name():
    assert c().post("/api/students", json={}).status_code == 400
