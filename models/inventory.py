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

# def delete_item(item_id):
#     db = get_db()
#     db.execute("DELETE FROM inventory WHERE id=?", (item_id,))
#     db.execute(
#         "INSERT INTO actionsAudit (username, action) VALUES (?, ?)",
#         ("system", f"Deleted item {item_id}")
#     )
#     print("🔥 INVENTORY DELETE CALLED", item_id)
#     db.commit()