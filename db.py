"""
Program: L6 Inventory Management Web Application
Filename: db.py
Author: Student Project Team
Course: Software Engineering
Version: 1.0
Date: 09/07/2026

Disclaimer:
The following source code is the sole work of the author(s) unless otherwise stated.

References:
[1] Flask Documentation (2026) [online] Available from: https://flask.palletsprojects.com/
    [Accessed 09/07/2026].
[2] Python sqlite3 Documentation (2026) [online] Available from:
    https://docs.python.org/3/library/sqlite3.html
    [Accessed 09/07/2026].
"""

import os
import sqlite3
from flask import g

def get_db():
    if "db" not in g:
        db_path = os.environ.get(
            "DATABASE_PATH",
            os.path.join(os.getcwd(), "instance", "data.db")
        )
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