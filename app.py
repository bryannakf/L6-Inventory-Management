from flask import Flask, current_app, render_template, request, jsonify, session, redirect, url_for, flash
from db import get_db, close_db, init_app
import db
from models.inventory import *
from models.datacenter import add_datacenter, get_datacenters, update_datacenter, delete_datacenter
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app)

app.config.from_mapping(
    DATABASE="/app/data/data.db"
)

app.secret_key = os.getenv("SECRET_KEY")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

init_app(app)

# -------------------------
# DB INITIALISATION
# -------------------------
def init_db():
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

    with open(schema_path, "r", encoding="utf-8") as f:
        db.executescript(f.read())

    db.commit()


# def ensure_db():
#     if not os.path.exists(app.config["DATABASE"]):
#         with app.app_context():
#             init_db()
def ensure_db():
    with app.app_context():
        db = get_db()
        db.executescript(open(os.path.join(os.path.dirname(__file__), "schema.sql")).read())
        db.commit()

@app.cli.command("initdb")
def initdb_command():
    init_db()
    print("Database initialized.")

# -------------------------
# LOGIN REQUIRED
# -------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return wrapper

# -------------------------
# HOME
# -------------------------
@app.route("/")
def index():
    return redirect(url_for("register"))

# -------------------------
# REGISTER
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    db = get_db()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("register"))

        if not re.search(r"[A-Z]", password):
            flash("Password needs one uppercase letter.")
            return redirect(url_for("register"))

        if not re.search(r"\d", password):
            flash("Password needs one number.")
            return redirect(url_for("register"))

        password = generate_password_hash(password)
        role = "user"  # Default role is 'user'

        try:
            db.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            db.commit()

            flash("Registration successful! Please log in.")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Username already exists.")
            return redirect(url_for("register"))

    return render_template("register.html")

# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per minute")
def login():
    db = get_db()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(url_for("admin" if user["role"] == "admin" else "user"))

        flash("Invalid credentials")
        return redirect(url_for("login"))

    return render_template("login.html")

# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------------
# PAGES
# -------------------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("admin.html")

@app.route("/user")
@login_required
def user():
    return render_template("user.html")

@app.route("/inventory")
@login_required
def inventory():
    return render_template("inventory.html")

@app.route("/datacenter")
@login_required
def datacenter():
    return render_template("datacenter.html")

@app.route("/actionsAudit")
@login_required
@admin_required
def actionsAudit():
    #return redirect(url_for("login"))
    return render_template("actionsAudit.html")

# -------------------------
# INVENTORY API
# -------------------------
#add item

@app.route("/api/item", methods=["POST"])
@login_required
def api_add_item():
    data = request.get_json()

    add_item(
        data["item_name"],
        data["quantity"],
        data["datacenter_id"]
    )

    db = get_db()

    db.execute(
        """
        INSERT INTO actionsAudit(username, action)
        VALUES (?, ?)
        """,
        (
            session["username"],
            f"Added item '{data['item_name']}' "
            f"(Qty {data['quantity']}) "
            f"to datacenter {data['datacenter_id']}"
        )
    )

    db.commit()

    return jsonify({"message": "Item added"}), 201


# 🔥 FIXED: excludes soft-deleted items
@app.route("/api/items")
@login_required
def api_get_items():
    db = get_db()

    items = db.execute("""
        SELECT *
        FROM inventory
        WHERE deleted_at IS NULL
    """).fetchall()

    return jsonify([
        {
            "id": i["id"],
            "item_name": i["item_name"],
            "quantity": i["quantity"],
            "datacenter_id": i["datacenter_id"]
        }
        for i in items
    ])


@app.route("/api/item/<int:id>", methods=["PUT"])
@login_required
def api_update_item(id):
    data = request.get_json()

    updated = update_item(
        id,
        data.get("quantity"),
        data.get("datacenter_id")
    )
    if updated:
        db = get_db()
        db.execute(
            """
            INSERT INTO actionsAudit(username, action)
            VALUES (?, ?)
            """,
            (
                session["username"],
                f"Updated item {id} "
                f"(Qty={data['quantity']}, Datacenter={data['datacenter_id']})"
            )
        )
        db.commit()


    if updated == 0:
        return jsonify({"error": "Not found"}), 404

    return jsonify({"message": "Updated"})


@app.route("/api/item/<int:id>", methods=["DELETE"])
@login_required
def api_delete_item(id):
    db = get_db()

    updated = db.execute("""
        UPDATE inventory
        SET deleted_at = CURRENT_TIMESTAMP
        WHERE id = ?
        AND deleted_at IS NULL
    """, (id,)).rowcount

    if updated == 0:
        return jsonify({
            "error": "Item already deleted or not found"
        }), 404

    db.execute(
        "INSERT INTO actionsAudit(username, action) VALUES (?, ?)",
        (session["username"], f"Soft deleted item {id}")
    )

    db.commit()

    return jsonify({"message": "Item moved to recycle bin"})

@app.route("/api/item/restore/<int:id>", methods=["POST"])
@login_required
@admin_required
def restore_item(id):
    db = get_db()

    restored = db.execute(
        "UPDATE inventory SET deleted_at = NULL WHERE id = ?",
        (id,)
    ).rowcount

    # Add audit log
    if restored:
        db.execute(
            "INSERT INTO actionsAudit (username, action) VALUES (?, ?)",
            (session["username"], f"Restored item {id}")
        )

    db.commit()

    if restored == 0:
        return jsonify({"error": "Item not found"}), 404

    return jsonify({"message": "Item restored"})

@app.route("/api/items/deleted")
@login_required
@admin_required
def get_deleted_items():
    db = get_db()

    items = db.execute("""
        SELECT *
        FROM inventory
        WHERE deleted_at IS NOT NULL
    """).fetchall()

    return jsonify([
        {
            "id": i["id"],
            "item_name": i["item_name"],
            "deleted_at": i["deleted_at"]
        }
        for i in items
    ])
    
@app.route("/api/item/hard-delete/<int:id>", methods=["DELETE"])
@login_required
@admin_required
def hard_delete_item(id):
    db = get_db()

    deleted = db.execute(
        "DELETE FROM inventory WHERE id = ?",
        (id,)
    ).rowcount

    if deleted:
        db.execute(
            "INSERT INTO actionsAudit(username, action) VALUES (?, ?)",
            (session["username"], f"Hard deleted item {id}")
        )

    db.commit()

    if deleted == 0:
        return jsonify({"error": "Item not found"}), 404

    return jsonify({"message": "Item permanently deleted"})
# -------------------------
# DATACENTER API
# -------------------------
        
@app.route("/api/datacenter", methods=["POST"])
@login_required
def api_add_datacenter():

    data = request.get_json()

    add_datacenter(
        data["location"],
        data["capacity"]
    )

    db = get_db()

    db.execute(
        """
        INSERT INTO actionsAudit(username, action)
        VALUES (?, ?)
        """,
        (
            session["username"],
            f"Added datacenter '{data['location']}' "
            f"with capacity {data['capacity']}"
        )
    )

    db.commit()

    return jsonify({"message":"Datacenter added"}), 201

# 🔥 FIXED: excludes soft-deleted items
@app.route("/api/datacenters")
@login_required
def api_get_datacenters():
    db = get_db()

    dcs = db.execute("""
        SELECT *
        FROM datacenter
        WHERE deleted_at IS NULL
    """).fetchall()

    return jsonify([
        {
            "id": d["id"],
            "location": d["location"],
            "capacity": d["capacity"]
        }
        for d in dcs
    ])


@app.route("/api/datacenter/<int:id>", methods=["PUT"])
@login_required
def api_update_datacenter(id):
    data = request.get_json()

    updated = update_datacenter(
        id,
        data.get("capacity")
    )

    if updated == 0:
        return jsonify({"error": "Not found"}), 404

    if updated:
        db = get_db()

        db.execute(
            """
            INSERT INTO actionsAudit(username, action)
            VALUES (?, ?)
            """,
            (
                session["username"],
                f"Updated datacenter {id} "
                f"(Capacity={data['capacity']})"
            )
        )

        db.commit()
        return jsonify({"message": "Updated"})


@app.route("/api/datacenter/<int:id>", methods=["DELETE"])
@login_required
def api_delete_datacenter(id):
    db = get_db()

    updated = db.execute("""
        UPDATE datacenter
        SET deleted_at = CURRENT_TIMESTAMP
        WHERE id = ?
        AND deleted_at IS NULL
    """, (id,)).rowcount

    if updated == 0:
        return jsonify({
            "error": "Datacenter already deleted or not found"
        }), 404

    db.execute(
        "INSERT INTO actionsAudit(username, action) VALUES (?, ?)",
        (session["username"], f"Soft deleted datacenter {id}")
    )

    db.commit()

    return jsonify({"message": "Datacenter moved to recycle bin"})

@app.route("/api/datacenters/deleted")
@login_required
@admin_required
def get_deleted_datacenters():
    db = get_db()

    dcs = db.execute("""
        SELECT *
        FROM datacenter
        WHERE deleted_at IS NOT NULL
    """).fetchall()

    return jsonify([
        {
            "id": d["id"],
            "location": d["location"],
            "deleted_at": d["deleted_at"]
        }
        for d in dcs
    ])

@app.route("/api/datacenter/restore/<int:id>", methods=["POST"])
@login_required
@admin_required
def restore_datacenter(id):
    db = get_db()

    restored = db.execute(
        "UPDATE datacenter SET deleted_at = NULL WHERE id = ?",
        (id,)
    ).rowcount

    # Add audit log
    if restored:
        db.execute(
            "INSERT INTO actionsAudit (username, action) VALUES (?, ?)",
            (session["username"], f"Restored datacenter {id}")
        )

    db.commit()

    if restored == 0:
        return jsonify({"error": "Datacenter not found"}), 404

    return jsonify({"message": "Datacenter restored"})

@app.route("/api/datacenter/hard-delete/<int:id>", methods=["DELETE"])
@login_required
@admin_required
def hard_delete_datacenter(id):
    db = get_db()

    deleted = db.execute(
        "DELETE FROM datacenter WHERE id = ?",
        (id,)
    ).rowcount

    if deleted:
        db.execute(
            "INSERT INTO actionsAudit(username, action) VALUES (?, ?)",
            (session["username"], f"Hard deleted datacenter {id}")
        )

    db.commit()

    if deleted == 0:
        return jsonify({"error": "Datacenter not found"}), 404

    return jsonify({"message": "Datacenter permanently deleted"})

# -------------------------
# AUDIT LOG
# -------------------------
@app.route("/api/actionsAudit")
@login_required
def api_actions():
    db = get_db()

    rows = db.execute(
        "SELECT * FROM actionsAudit ORDER BY timestamp DESC"
    ).fetchall()

    return jsonify([
        {
            "id": r["id"],
            "user": r["username"],
            "action": r["action"],
            "timestamp": r["timestamp"]
        }
        for r in rows
    ])

#create user


application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    
with app.app_context():
    ensure_db()