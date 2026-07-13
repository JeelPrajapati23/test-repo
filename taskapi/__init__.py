from flask import Flask

from .db import init_db


def create_app(db_path: str = "tasks.db") -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path
    init_db(db_path)

    from .routes import bp as tasks_bp

    app.register_blueprint(tasks_bp)

    return app
