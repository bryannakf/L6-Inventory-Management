import os
import sys
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app as flask_app
from app import db

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    must_change_password INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS datacenter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,
    deleted_at DATETIME,
    capacity INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    datacenter_id INTEGER NOT NULL,
    deleted_at DATETIME,
    FOREIGN KEY (datacenter_id) REFERENCES datacenter(id)
);
CREATE TABLE IF NOT EXISTS actionsAudit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
        'INSERT INTO users (username, password, role, must_change_password) VALUES (?, ?, ?, ?)',
        ('admin', generate_password_hash('adminpass'), 'admin', 0),
    )
    conn.execute(
        'INSERT INTO users (username, password, role, must_change_password) VALUES (?, ?, ?, ?)',
        ('testuser', generate_password_hash('userpass'), 'user', 0),
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


@pytest.fixture(autouse=True)
def reset_rate_limiter_state():
    import app as app_module

    app_module.limiter.reset()