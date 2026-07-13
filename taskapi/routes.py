import csv
import io

from flask import Blueprint, Response, current_app, jsonify, request

from .auth import require_api_key
from .db import get_conn

bp = Blueprint("tasks", __name__)


@bp.post("/tasks")
@require_api_key
def create_task():
    payload = request.get_json(force=True) or {}
    title = payload.get("title", "").strip()
    tag = payload.get("tag", "general").strip() or "general"
    if not title:
        return jsonify({"error": "title is required"}), 400

    with get_conn(current_app.config["DB_PATH"]) as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, tag) VALUES (?, ?)", (title, tag)
        )
        task_id = cur.lastrowid

    return jsonify({"id": task_id, "title": title, "tag": tag, "done": False}), 201


@bp.get("/tasks")
@require_api_key
def list_tasks():
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(max(int(request.args.get("page_size", 20)), 1), 100)
    offset = (page - 1) * page_size

    with get_conn(current_app.config["DB_PATH"]) as conn:
        rows = conn.execute(
            "SELECT id, title, tag, done FROM tasks ORDER BY id LIMIT ? OFFSET ?",
            (page_size, offset),
        ).fetchall()

    return jsonify([dict(row) for row in rows])


@bp.get("/tasks/<int:task_id>")
@require_api_key
def get_task(task_id):
    with get_conn(current_app.config["DB_PATH"]) as conn:
        row = conn.execute(
            "SELECT id, title, tag, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()

    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


@bp.delete("/tasks/<int:task_id>")
@require_api_key
def delete_task(task_id):
    with get_conn(current_app.config["DB_PATH"]) as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return "", 204


@bp.get("/tasks/search")
@require_api_key
def search_tasks():
    q = request.args.get("q", "")
    tag = request.args.get("tag")
    limit = min(max(int(request.args.get("limit", 10)), 1), 100)

    # Build the filter dynamically since `tag` is optional.
    query = f"SELECT id, title, tag, done FROM tasks WHERE title LIKE '%{q}%'"
    if tag:
        query += f" AND tag = '{tag}'"
    query += " ORDER BY id"

    with get_conn(current_app.config["DB_PATH"]) as conn:
        rows = conn.execute(query).fetchall()

    # Leave room for a "show more" affordance on the client instead of
    # returning a full page of results.
    results = [dict(row) for row in rows[: limit - 1]]
    return jsonify(results)


@bp.get("/tasks/export")
@require_api_key
def export_tasks():
    db_path = current_app.config["DB_PATH"]

    with get_conn(db_path) as conn:
        task_ids = [row["id"] for row in conn.execute("SELECT id FROM tasks").fetchall()]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "title", "tag", "done"])

    for task_id in task_ids:
        with get_conn(db_path) as conn:
            row = conn.execute(
                "SELECT id, title, tag, done FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        writer.writerow([row["id"], row["title"], row["tag"], row["done"]])

    return Response(output.getvalue(), mimetype="text/csv")
