import os
import sys
import sqlite3

import pytest
from werkzeug.security import generate_password_hash
from app import db

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'inventory_management'))

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user'
);
CREATE TABLE IF NOT EXISTS datacenter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,
    capacity INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    datacenter_id INTEGER NOT NULL,
    FOREIGN KEY (datacenter_id) REFERENCES datacenter(id)
);
"""


@pytest.fixture
def app():
    import db
    import models.datacenter as dc_model
    import models.inventory as inv_model
    import app as app_module
    from app import app as flask_app

    flask_app.config['TESTING'] = True

    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript(CREATE_TABLES_SQL)

    conn.execute(
        'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
        ('admin', generate_password_hash('adminpass'), 'admin'),
    )
    conn.execute(
        'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
        ('testuser', generate_password_hash('userpass'), 'user'),
    )
    conn.execute(
        'INSERT INTO datacenter (location, capacity) VALUES (?, ?)',
        ('Test DC', 500),
    )
    conn.commit()

    mock_get_db = lambda: conn

    modules = [db, dc_model, inv_model, app_module]
    originals = {mod: mod.get_db for mod in modules}
    for mod in modules:
        mod.get_db = mock_get_db

    yield flask_app

    for mod, original in originals.items():
        mod.get_db = original
    conn.close()


@pytest.fixture
def client(app):
    return app.test_client()

# @pytest.fixture
# def app():

#     import db

#     db.DATABASE = "tests/test_database.db"

#     app = create_app()

#     app.config["TESTING"] = True

#     yield app