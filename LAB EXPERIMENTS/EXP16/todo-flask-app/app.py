from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)
TODOS = []          # [{"id": 1, "title": "...", "done": False}]
_next_id = 1

PAGE = """
<!doctype html><html><head><meta charset="utf-8"><title>To-Do List</title>
<style>
 body{font-family:Segoe UI,Arial,sans-serif;background:#f1f5f9;margin:0}
 .box{max-width:620px;margin:50px auto;background:#fff;border-radius:16px;padding:28px 32px;box-shadow:0 10px 30px #0001}
 h1{margin:0 0 4px;color:#1e293b} p.sub{margin:0 0 20px;color:#64748b}
 form.add{display:flex;gap:10px;margin-bottom:18px}
 input[type=text]{flex:1;padding:12px 14px;border:1px solid #cbd5e1;border-radius:10px;font-size:16px}
 button{padding:10px 16px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-size:15px;cursor:pointer}
 li{display:flex;align-items:center;gap:10px;padding:12px 4px;border-bottom:1px solid #e2e8f0;list-style:none}
 ul{padding:0;margin:0} .done span{text-decoration:line-through;color:#94a3b8}
 li span{flex:1;font-size:17px} .x{background:#ef4444} .ok{background:#16a34a}
 .count{margin-top:14px;color:#64748b;font-size:14px}
</style></head><body><div class="box">
<h1>My To-Do List</h1><p class="sub">Flask app running inside a Docker container</p>
<form class="add" method="post" action="{{ url_for('add') }}">
  <input type="text" name="title" placeholder="What needs to be done?" required><button>Add</button></form>
<ul>
{% for t in todos %}
 <li class="{{ 'done' if t.done else '' }}"><span>{{ t.title }}</span>
  <form method="post" action="{{ url_for('toggle', todo_id=t.id) }}"><button class="ok">{{ 'Undo' if t.done else 'Done' }}</button></form>
  <form method="post" action="{{ url_for('delete', todo_id=t.id) }}"><button class="x">Delete</button></form></li>
{% else %}<li><span>No tasks yet - add one above.</span></li>{% endfor %}
</ul>
<div class="count">{{ todos|selectattr('done')|list|length }} of {{ todos|length }} tasks completed</div>
</div></body></html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE, todos=TODOS)


@app.route("/add", methods=["POST"])
def add():
    global _next_id
    title = request.form.get("title", "").strip()
    if title:
        TODOS.append({"id": _next_id, "title": title, "done": False})
        _next_id += 1
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>", methods=["POST"])
def toggle(todo_id):
    for t in TODOS:
        if t["id"] == todo_id:
            t["done"] = not t["done"]
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    TODOS[:] = [t for t in TODOS if t["id"] != todo_id]
    return redirect(url_for("index"))


@app.route("/api/todos", methods=["GET"])
def api_list():
    return jsonify(TODOS)


@app.route("/api/todos", methods=["POST"])
def api_add():
    global _next_id
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    todo = {"id": _next_id, "title": title, "done": False}
    _next_id += 1
    TODOS.append(todo)
    return jsonify(todo), 201


@app.route("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
