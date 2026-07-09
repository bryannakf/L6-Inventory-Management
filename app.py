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

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "test-secret-key-for-development"
)

app.secret_key = os.environ.get("SECRET_KEY")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

init_app(app)


# DB INITIALISATION

def init_db():

    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

    db.commit()



@app.route("/debug-users")
def debug_users():
    db = get_db()
    rows = db.execute("SELECT username FROM users").fetchall()
    return {"users": [r["username"] for r in rows]}

def ensure_db():
    with app.app_context():
        db = get_db()
        db.executescript(open(os.path.join(os.path.dirname(__file__), "schema.sql")).read())
        db.commit()

@app.cli.command("initdb")
def initdb_command():
    init_db()
    print("Database initialized.")

#create default admin user if not exists
@app.cli.command("create-admin")
def create_admin():

    username = input("Admin username: ")
    password = input("Admin password: ")


    db = get_db()

    db.execute(
        """
        INSERT INTO users
        (username,password,role,must_change_password)
        VALUES (?, ?, ?, ?)
        """,

        (
            username,
            generate_password_hash(password),
            "admin",
            1
        )
    )

    db.commit()

    print("Administrator created")

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session and "username" not in session:
            flash("Access denied")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def audit_username():
    return session.get("username", "system")

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
    return redirect(url_for("login"))

@app.route('/register', methods=["GET", "POST"])
def register():
    db = get_db()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form.get("role", "user")

        try:
            db.execute(
                "INSERT INTO users (username, password, role, must_change_password) VALUES (?, ?, ?, ?)",
                (username, generate_password_hash(password), role, 0),
            )
            db.commit()
            flash("Registration successful! Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists")

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

        # Look up the user
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        
        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            must_change_password = user["must_change_password"] if "must_change_password" in user.keys() else 0
            if must_change_password == 1:
                flash("You must change your temporary password before continuing.")
                return redirect(url_for("change_password"))

           # flash("Login successful!")

            # Redirect based on role
            if user["role"] == "admin":
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("user"))

        # Invalid login
        flash("Invalid username or password.")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        new_password = request.form["password"]
        confirm = request.form["confirm_password"]

        if new_password != confirm:
            flash("Passwords do not match.")
            return redirect(url_for("change_password"))

        db = get_db()

        db.execute(
            """
            UPDATE users
            SET password = ?,
                must_change_password = 0
            WHERE id = ?
            """,
            (
                generate_password_hash(new_password),
                session["user_id"]
            )
        )

        db.commit()

        flash("Password updated successfully.")

        return redirect(
            url_for("admin" if session["role"] == "admin" else "user")
        )

    return render_template("change_password.html")
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
        flash("Access denied")
        return redirect(url_for("login"))

    if "user_id" not in session:
        return render_template("admin.html")

    db = get_db()

    user = db.execute(
        "SELECT must_change_password FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if user and user["must_change_password"] == 1:
        return redirect(url_for("change_password"))

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
def api_add_item():
    data = request.get_json() or {}
    item_name = data.get("item_name") or data.get("itemName")
    quantity = data.get("quantity")
    datacenter_id = data.get("datacenter_id")

    if item_name is None or quantity is None or datacenter_id is None:
        return jsonify({"error": "Missing required fields"}), 400

    add_item(
        item_name,
        quantity,
        datacenter_id
    )

    db = get_db()

    db.execute(
        """
        INSERT INTO actionsAudit(username, action)
        VALUES (?, ?)
        """,
        (
            audit_username(),
            f"Added item '{item_name}' "
            f"(Qty {quantity}) "
            f"to datacenter {datacenter_id}"
        )
    )

    db.commit()

    return jsonify({"message": "Item added successfully"}), 201


# 🔥 FIXED: excludes soft-deleted items
@app.route("/api/items")
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


@app.route("/api/item", methods=["PUT"])
@app.route("/api/item/<int:id>", methods=["PUT"])
def api_update_item(id=None):
    data = request.get_json() or {}
    quantity = data.get("quantity")

    if quantity is None:
        return jsonify({"error": "Missing required fields"}), 400

    db = get_db()

    if id is None:
        item_name = data.get("item_name") or data.get("itemName")
        if not item_name:
            return jsonify({"error": "Missing required fields"}), 400

        existing = db.execute(
            "SELECT id, datacenter_id FROM inventory WHERE item_name = ? AND deleted_at IS NULL ORDER BY id DESC LIMIT 1",
            (item_name,),
        ).fetchone()
    else:
        existing = db.execute(
            "SELECT id, datacenter_id FROM inventory WHERE id = ? AND deleted_at IS NULL",
            (id,),
        ).fetchone()

    if not existing:
        return jsonify({"error": "Not found"}), 404

    id = existing["id"]
    datacenter_id = data.get("datacenter_id", existing["datacenter_id"])

    updated = update_item(id, quantity, datacenter_id)
    if updated:
        db.execute(
            """
            INSERT INTO actionsAudit(username, action)
            VALUES (?, ?)
            """,
            (
                audit_username(),
                f"Updated item {id} "
                f"(Qty={quantity}, Datacenter={datacenter_id})"
            )
        )
        db.commit()


    if updated == 0:
        return jsonify({"error": "Not found"}), 404

    return jsonify({"message": "Item updated successfully"})


@app.route("/api/item/<int:id>", methods=["DELETE"])
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
        (audit_username(), f"Soft deleted item {id}")
    )

    db.commit()

    return jsonify({"message": "Item deleted successfully"})

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
def api_add_datacenter():
    data = request.get_json() or {}

    if data.get("location") is None or data.get("capacity") is None:
        return jsonify({"error": "Missing required fields"}), 400

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
            audit_username(),
            f"Added datacenter '{data['location']}' "
            f"with capacity {data['capacity']}"
        )
    )

    db.commit()

    return jsonify({"message": "Data Center added successfully"}), 201

# 🔥 FIXED: excludes soft-deleted items
@app.route("/api/datacenters")
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
def api_update_datacenter(id):
    data = request.get_json() or {}

    if data.get("capacity") is None:
        return jsonify({"error": "Missing required fields"}), 400

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
                audit_username(),
                f"Updated datacenter {id} "
                f"(Capacity={data['capacity']})"
            )
        )

        db.commit()
        return jsonify({"message": "Data Center updated successfully"})


@app.route("/api/datacenter/<int:id>", methods=["DELETE"])
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
        (audit_username(), f"Soft deleted datacenter {id}")
    )

    db.commit()

    return jsonify({"message": "Data Center deleted successfully"})

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
@app.route("/admin/create-user", methods=["GET", "POST"])
@login_required
@admin_required
def create_user():
    db = get_db()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect(url_for("create_user"))

        if not re.search(r"[A-Z]", password):
            flash("Password needs one uppercase letter.")
            return redirect(url_for("create_user"))

        if not re.search(r"\d", password):
            flash("Password needs one number.")
            return redirect(url_for("create_user"))


        hashed_password = generate_password_hash(password)

        try:
            db.execute(
                """
                INSERT INTO users
                (username, password, role, must_change_password)
                VALUES (?, ?, ?, ?)
                """,
                (username, hashed_password, role, 1)
                )

            db.execute(
                "INSERT INTO actionsAudit (username, action) VALUES (?, ?)",
                (session["username"], f"Created user {username} with role {role}")
            )

            db.commit()

            flash("User created successfully")
            return redirect(url_for("create_user"))

        except sqlite3.IntegrityError:
            flash("Username already exists")

    return render_template("create_user.html")



application = app

if __name__ == "__main__":
    with app.app_context():
        ensure_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )