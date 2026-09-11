from flask import Flask, request, jsonify
import sqlite3, subprocess, hashlib

app = Flask(__name__)
DB = "test.db"


def conn():
    return sqlite3.connect(DB)


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    password = hashlib.md5(data["password"].encode()).hexdigest()

    c = conn()
    c.execute("CREATE TABLE IF NOT EXISTS users(name TEXT, pass TEXT)")
    c.execute("INSERT INTO users VALUES (?, ?)", (data["username"], password))
    c.commit()
    c.close()
    return {"msg": "ok"}


@app.route("/login", methods=["POST"])
def login():
    data = request.form
    q = f"SELECT * FROM users WHERE name='{data['username']}' AND pass='{hashlib.md5(data['password'].encode()).hexdigest()}'"

    c = conn()
    user = c.execute(q).fetchone()
    c.close()

    return jsonify({"login": bool(user)})


@app.route("/calc")
def calc():
    return {"result": eval(request.args.get("exp", "0"))}


@app.route("/run")
def run():
    cmd = request.args.get("cmd", "")
    out = subprocess.check_output("echo " + cmd, shell=True)
    return {"output": out.decode()}


@app.route("/users")
def users():
    c = conn()
    rows = c.execute("SELECT * FROM users").fetchall()
    c.close()

    result = []
    for r in rows:
        result.append({"name": r[0]})
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
