"""
Program: L6 Inventory Management Web Application
Filename: models/datacenter.py
Author: Student Project Team
Course: Software Engineering
Version: 1.0
Date: 09/07/2026

Disclaimer:
The following source code is the sole work of the author(s) unless otherwise stated.

References:
[1] Python sqlite3 Documentation (2026) [online] Available from:
    https://docs.python.org/3/library/sqlite3.html
    [Accessed 09/07/2026].
"""

from db import get_db

def add_datacenter(location, capacity):
    db = get_db()
    db.execute(
        "INSERT INTO datacenter (location, capacity) VALUES (?, ?)",
        (location, capacity)
    )
    db.commit()


def get_datacenters():
    db = get_db()
    return db.execute("SELECT * FROM datacenter WHERE deleted_at IS NULL").fetchall()

def update_datacenter(datacenter_id, capacity):
    db = get_db()

    cur = db.execute("""
        UPDATE datacenter
        SET capacity = ?
        WHERE id = ?
        AND deleted_at IS NULL
    """, (capacity, datacenter_id))

    db.commit()
    return cur.rowcount

def delete_datacenter(datacenter_id):
    db = get_db()
    db.execute("DELETE FROM datacenter WHERE id = ?", (datacenter_id,))
    db.commit()
    
