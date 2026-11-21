from flask import Flask, jsonify, request

app = Flask(__name__)

STUDENTS = {1: {"id": 1, "name": "Arun", "dept": "CSE"},
            2: {"id": 2, "name": "Priya", "dept": "IT"}}


@app.route("/")
def home():
    return jsonify(message="Student API running on Kubernetes", version="1.0")


@app.route("/health")
def health():
    return jsonify(status="healthy")


@app.route("/api/students", methods=["GET"])
def list_students():
    return jsonify(list(STUDENTS.values()))


@app.route("/api/students/<int:sid>", methods=["GET"])
def get_student(sid):
    s = STUDENTS.get(sid)
    return (jsonify(s), 200) if s else (jsonify(error="student not found"), 404)


@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify(error="name is required"), 400
    sid = max(STUDENTS) + 1
    STUDENTS[sid] = {"id": sid, "name": data["name"], "dept": data.get("dept", "CSE")}
    return jsonify(STUDENTS[sid]), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
