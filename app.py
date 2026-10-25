import os, time
from flask import Flask, request, render_template_string, redirect, jsonify
import psycopg2

app = Flask(__name__)

def get_conn():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        dbname=os.environ.get("DB_NAME", "appdb"),
        user=os.environ.get("DB_USER", "appuser"),
        password=os.environ.get("DB_PASSWORD", "apppass"),
    )

def init_db():
    for _ in range(30):
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, text TEXT NOT NULL)")
            cur.execute("ALTER TABLE notes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()")
            conn.commit()
            cur.close(); conn.close()
            return
        except Exception as e:
            print("Waiting for DB...", e, flush=True)
            time.sleep(2)

PAGE = """
<!doctype html>
<html><head><title>DevOps Notes</title></head>
<body style="font-family:sans-serif;max-width:600px;margin:40px auto">
  <h1 id="title">DevOps Notes App</h1>
  <p>Served by instance: <b id="host">{{ host }}</b></p>
  <form method="post">
    <input id="note" name="note" placeholder="Write a note" required>
    <button id="add" type="submit">Add</button>
  </form>
  <p>Total notes: <b id="count">{{ notes|length }}</b></p>
  <ul id="notes">
    {% for n in notes %}
    <li>
      {{ n.text }} <small style="color:gray">({{ n.time }})</small>
      <form method="post" action="/delete/{{ n.id }}" style="display:inline">
        <button class="delete" type="submit">Delete</button>
      </form>
    </li>
    {% endfor %}
  </ul>
</body></html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_conn()
    cur = conn.cursor()
    if request.method == "POST":
        text = request.form.get("note", "").strip()
        if text:
            cur.execute("INSERT INTO notes (text) VALUES (%s)", (text,))
            conn.commit()
        cur.close(); conn.close()
        return redirect("/")
    cur.execute("SELECT id, text, created_at FROM notes ORDER BY id DESC")
    notes = [{"id": r[0], "text": r[1], "time": r[2].strftime("%Y-%m-%d %H:%M") if r[2] else ""} for r in cur.fetchall()]
    cur.close(); conn.close()
    return render_template_string(PAGE, notes=notes, host=os.environ.get("INSTANCE_NAME", "unknown"))

@app.route("/delete/<int:note_id>", methods=["POST"])
def delete(note_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id = %s", (note_id,))
    conn.commit()
    cur.close(); conn.close()
    return redirect("/")

@app.route("/api/notes")
def api_notes():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, text, created_at FROM notes ORDER BY id DESC")
    data = [{"id": r[0], "text": r[1], "created_at": r[2].isoformat() if r[2] else None} for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(data)

@app.route("/health")
def health():
    return "OK", 200

init_db()
