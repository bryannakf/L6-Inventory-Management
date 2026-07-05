import os
import sqlite3
from flask import g

def get_db():
    if "db" not in g:
        db_path = os.environ.get("DATABASE_PATH", "/app/data/data.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)