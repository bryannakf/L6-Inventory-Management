"""
Program: L6 Inventory Management Web Application
Filename: models/inventory.py
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

def add_item(item_name, quantity, datacenter_id):
    db = get_db()
    db.execute(
        "INSERT INTO inventory (item_name, quantity, datacenter_id) VALUES (?, ?, ?)",
        (item_name, quantity, datacenter_id)
    )
    db.commit()


def get_items():
    db = get_db()
    return db.execute(
        "SELECT id, item_name, quantity, datacenter_id FROM inventory"
    ).fetchall()


def update_item(id, quantity, datacenter_id):
    db = get_db()

    cur = db.execute("""
        UPDATE inventory
        SET quantity = ?, datacenter_id = ?
        WHERE id = ?
        AND deleted_at IS NULL
    """, (quantity, datacenter_id, id))

    db.commit()
    return cur.rowcount

def delete_item(item_id):
    db = get_db()
    db.execute("DELETE FROM inventory WHERE id=?", (item_id,))
    db.commit()
