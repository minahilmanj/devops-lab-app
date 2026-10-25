import os, time
from flask import Flask, request, render_template_string
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
            conn.commit()
            cur.close(); conn.close()
            return
        except Exception as e:
            print("Waiting for DB...", e)
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
  <ul id="notes">
    {% for n in notes %}<li>{{ n }}</li>{% endfor %}
  </ul>
</body></html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_conn()
    cur = conn.cursor()
    if request.method == "POST" and request.form.get("note"):
        cur.execute("INSERT INTO notes (text) VALUES (%s)", (request.form["note"],))
        conn.commit()
    cur.execute("SELECT text FROM notes ORDER BY id DESC")
    notes = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return render_template_string(PAGE, notes=notes, host=os.environ.get("INSTANCE_NAME", "unknown"))

@app.route("/health")
def health():
    return "OK", 200

init_db()
