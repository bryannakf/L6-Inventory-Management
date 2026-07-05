from flask import Flask, current_app, render_template, request, jsonify, session, redirect, url_for, flash
from db import get_db, close_db, init_app
from models.inventory import *
from models.datacenter import add_datacenter, get_datacenters, update_datacenter, delete_datacenter
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)

app.config.from_mapping(
    DATABASE="/app/data/data.db"
)

app.secret_key = "your_secret_key"

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
    
def ensure_db():
    if not os.path.exists(app.config["DATABASE"]):
        with app.app_context():
            init_db()

@app.cli.command("initdb")
def initdb_command():
    init_db()
    print("Database initialized.")
    
# -------------------------
# ROUTES
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
        password = generate_password_hash(request.form["password"])
        role = request.form["role"]

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
def user():
    if not session.get("username"):
        return redirect(url_for("login"))
    return render_template("user.html")

@app.route("/inventory")
def inventory():
    return render_template("inventory.html")

@app.route("/datacenter")
def datacenter():
    return render_template("datacenter.html")

@app.route("/actionsAudit")
def actionsAudit():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("actionsAudit.html")

# -------------------------
# INVENTORY API
# -------------------------
@app.route("/api/item", methods=["POST"])
def api_add_item():
    data = request.get_json()

    add_item(
        data.get("item_name"),
        data.get("quantity"),
        data.get("datacenter_id")
    )

    return jsonify({"message": "Item added"}), 201


@app.route("/api/items")
def api_get_items():
    items = get_items()
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
def api_update_item(id):
    data = request.get_json()

    updated = update_item(
        id,
        data.get("quantity"),
        data.get("datacenter_id")
    )

    if updated == 0:
        return jsonify({"error": "Not found"}), 404

    return jsonify({"message": "Updated"})


@app.route("/api/item/<int:id>", methods=["DELETE"])
def api_delete_item(id):
    delete_item(id)
    return jsonify({"message": "Deleted"})


# -------------------------
# DATACENTER API
# -------------------------
@app.route("/api/datacenter", methods=["POST"])
def api_add_datacenter():
    data = request.get_json()

    add_datacenter(
        data.get("location"),
        data.get("capacity")
    )

    return jsonify({"message": "Datacenter added"}), 201


@app.route("/api/datacenters")
def api_get_datacenters():
    dcs = get_datacenters()
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
    data = request.get_json()

    update_datacenter(id, data.get("capacity"))
    return jsonify({"message": "Updated"})


@app.route("/api/datacenter/<int:id>", methods=["DELETE"])
def api_delete_datacenter(id):
    delete_datacenter(id)
    return jsonify({"message": "Deleted"})


# -------------------------
# AUDIT LOG
# -------------------------
@app.route("/api/actionsAudit")
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


application = app


if __name__ == "__main__":
    ensure_db()
    app.run(host="0.0.0.0", port=5000)