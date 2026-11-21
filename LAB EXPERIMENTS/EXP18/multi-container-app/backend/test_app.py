import app as m

def test_health_memory_mode():
    assert m.app.test_client().get("/api/health").get_json()["status"] == "ok"

def test_add_and_list_note():
    c = m.app.test_client()
    assert c.post("/api/notes", json={"text": "hello k8s"}).status_code == 201
    assert "hello k8s" in c.get("/api/notes").get_json()

def test_empty_note_rejected():
    assert m.app.test_client().post("/api/notes", json={"text": " "}).status_code == 400
