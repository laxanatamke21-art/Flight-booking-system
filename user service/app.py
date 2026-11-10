from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import hashlib

app = Flask(__name__)
CORS(app)

DATABASE = "users.db"


def get_db():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    return conn


def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():

    return jsonify({
        "service": "User Service",
        "status": "Running"
    })


@app.route("/register", methods=["POST"])
def register():

    data = request.json

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:

        return jsonify({
            "error": "All fields are required"
        }), 400

    conn = get_db()

    existing = conn.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (email,)).fetchone()

    if existing:

        conn.close()

        return jsonify({
            "error": "Email already registered"
        }), 409

    conn.execute("""
        INSERT INTO users
        (
            name,
            email,
            password
        )
        VALUES (?, ?, ?)
    """, (
        name,
        email,
        hash_password(password)
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Registration successful"
    }), 201


@app.route("/login", methods=["POST"])
def login():

    data = request.json

    email = data.get("email")
    password = data.get("password")

    conn = get_db()

    user = conn.execute("""
        SELECT id, name, email
        FROM users
        WHERE email = ?
        AND password = ?
    """, (
        email,
        hash_password(password)
    )).fetchone()

    conn.close()

    if not user:

        return jsonify({
            "error": "Invalid email or password"
        }), 401

    return jsonify({
        "message": "Login successful",
        "user": dict(user)
    })


if __name__ == "__main__":

    init_db()

    print("👤 User Service running on port 5006")

    app.run(
        host="0.0.0.0",
        port=5006,
        debug=False,
        use_reloader=False
    )