from db import get_db

def add_datacenter(location, capacity):
    db = get_db()
    db.execute(
        "INSERT INTO datacenter (location, capacity) VALUES (?, ?)",
        (location, capacity)
    )
    db.execute(
        "INSERT INTO actionsAudit (username, action) VALUES (?, ?)",
        ("admin", f"Added datacenter at {location} with capacity {capacity}")
    )
    db.commit()


def get_datacenters():
    db = get_db()
    return db.execute("SELECT * FROM datacenter").fetchall()


def update_datacenter(datacenter_id, capacity):
    db = get_db()
    db.execute(
        "UPDATE datacenter SET capacity = ? WHERE id = ?",
        (capacity, datacenter_id)
    )
    db.execute(
        "INSERT INTO actionsAudit (username, action) VALUES (?, ?)",
        ("admin", f"Updated datacenter {datacenter_id}")
    )
    db.commit()


def delete_datacenter(datacenter_id):
    db = get_db()
    db.execute("DELETE FROM datacenter WHERE id = ?", (datacenter_id,))
    db.execute(
        "INSERT INTO actionsAudit (username, action) VALUES (?, ?)",
        ("admin", f"Deleted datacenter {datacenter_id}")
    )
    db.commit()
    
