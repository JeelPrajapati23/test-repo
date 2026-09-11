from flask import Flask, request, jsonify, session, send_file
import sqlite3
import subprocess
import os
import hashlib
import pickle
import re
import time
import requests

app = Flask(__name__)
app.secret_key = "super-secret-key-123"
DB = "app.db"

users_cache = {}
request_history = []


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product TEXT,
            price REAL
        )
    """)
    conn.commit()
    conn.close()


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data["username"]
    password = data["password"]

    password_hash = hashlib.md5(password.encode()).hexdigest()

    conn = db()
    try:
        conn.execute(
            "INSERT INTO users(username, password, role) VALUES (?, ?, ?)",
            (username, password_hash, "user")
        )
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"message": "registered"})


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    query = f"""
        SELECT * FROM users
        WHERE username = '{username}'
        AND password = '{hashlib.md5(password.encode()).hexdigest()}'
    """

    conn = db()
    user = conn.execute(query).fetchone()
    conn.close()

    if user:
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        return jsonify({"message": "login successful"})

    return jsonify({"error": "invalid credentials"}), 401


@app.route("/profile")
def profile():
    user_id = request.args.get("id")

    conn = db()
    user = conn.execute(
        "SELECT id, username, role FROM users WHERE id = " + user_id
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "not found"}), 404

    return jsonify(dict(user))


@app.route("/admin/users")
def admin_users():
    if session.get("role") != "admin":
        return jsonify({"error": "forbidden"}), 403

    conn = db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    return jsonify([dict(x) for x in users])


@app.route("/orders")
def orders():
    user_id = session.get("user_id")

    conn = db()
    orders = conn.execute(
        "SELECT * FROM orders WHERE user_id = ?", (user_id,)
    ).fetchall()

    result = []

    for order in orders:
        product = conn.execute(
            "SELECT * FROM products WHERE name = ?",
            (order["product"],)
        ).fetchone()

        result.append({
            "id": order["id"],
            "product": product["name"] if product else order["product"],
            "price": order["price"]
        })

    conn.close()
    return jsonify(result)


@app.route("/search")
def search():
    pattern = request.args.get("q", "")

    if len(pattern) > 500:
        return jsonify({"error": "query too long"}), 400

    if re.match(r"^(a+)+$", pattern):
        return jsonify({"valid": True})

    conn = db()
    rows = conn.execute(
        "SELECT * FROM users WHERE username LIKE ?",
        ("%" + pattern + "%",)
    ).fetchall()
    conn.close()

    return jsonify([dict(x) for x in rows])


@app.route("/run")
def run():
    command = request.args.get("command")

    result = subprocess.check_output(
        "echo " + command,
        shell=True,
        stderr=subprocess.STDOUT
    )

    return jsonify({"output": result.decode()})


@app.route("/file")
def get_file():
    filename = request.args.get("name")

    base = "/tmp/uploads"
    path = os.path.join(base, filename)

    if os.path.exists(path):
        return send_file(path)

    return jsonify({"error": "file not found"}), 404


@app.route("/calculate")
def calculate():
    expression = request.args.get("expression", "0")

    try:
        result = eval(expression)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/import")
def import_data():
    data = request.args.get("data")

    try:
        obj = pickle.loads(data.encode())
        return jsonify({"data": obj})
    except Exception:
        return jsonify({"error": "invalid data"}), 400


@app.route("/proxy")
def proxy():
    url = request.args.get("url")

    response = requests.get(url, timeout=30)

    return (
        response.content,
        response.status_code,
        {"Content-Type": response.headers.get("Content-Type", "text/plain")}
    )


@app.route("/expensive")
def expensive():
    n = int(request.args.get("n", 100000))

    numbers = []

    for i in range(n):
        numbers.append(i * i)

    numbers = list(set(numbers))
    numbers.sort()

    total = 0
    for x in numbers:
        total += x

    return jsonify({
        "count": len(numbers),
        "total": total
    })


@app.route("/cache/<username>")
def cached_user(username):
    if username in users_cache:
        return jsonify(users_cache[username])

    conn = db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "not found"}), 404

    data = dict(user)
    users_cache[username] = data

    return jsonify(data)


@app.before_request
def track_requests():
    request_history.append({
        "time": time.time(),
        "ip": request.remote_addr,
        "path": request.path
    })


@app.route("/stats")
def stats():
    return jsonify({
        "requests": len(request_history),
        "cache_size": len(users_cache)
    })


@app.route("/fetch")
def fetch():
    urls = request.args.get("urls", "").split(",")

    results = []

    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            results.append({
                "url": url,
                "status": r.status_code,
                "body": r.text
            })
        except Exception as e:
            results.append({
                "url": url,
                "error": str(e)
            })

    return jsonify(results)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
