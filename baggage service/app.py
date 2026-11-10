from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DATABASE = "baggage.db"


# =====================================================
# DATABASE
# =====================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS baggage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id TEXT NOT NULL,
            seat_number TEXT NOT NULL,
            baggage_type TEXT NOT NULL,
            weight INTEGER NOT NULL,
            price INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    return jsonify({
        "message": "Baggage Service is running",
        "port": 5003
    })


# =====================================================
# BAGGAGE OPTIONS
# =====================================================

@app.route("/baggage/options", methods=["GET"])
def baggage_options():

    options = [

        {
            "type": "No Baggage",
            "weight": 0,
            "price": 0
        },

        {
            "type": "Cabin Baggage",
            "weight": 7,
            "price": 0
        },

        {
            "type": "Checked Baggage",
            "weight": 15,
            "price": 800
        },

        {
            "type": "Extra Baggage",
            "weight": 25,
            "price": 1500
        }

    ]

    return jsonify(options)


# =====================================================
# ADD BAGGAGE
# =====================================================

@app.route("/baggage", methods=["POST"])
def add_baggage():

    data = request.get_json()

    flight_id = data.get("flight_id")
    seat_number = data.get("seat_number")
    baggage_type = data.get("baggage_type")
    weight = data.get("weight")
    price = data.get("price")

    if not flight_id:
        return jsonify({
            "message": "flight_id is required"
        }), 400

    if not seat_number:
        return jsonify({
            "message": "seat_number is required"
        }), 400

    if not baggage_type:
        return jsonify({
            "message": "baggage_type is required"
        }), 400

    if weight is None:
        return jsonify({
            "message": "weight is required"
        }), 400

    if price is None:
        return jsonify({
            "message": "price is required"
        }), 400

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO baggage
        (
            flight_id,
            seat_number,
            baggage_type,
            weight,
            price
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        flight_id,
        seat_number,
        baggage_type,
        weight,
        price
    ))

    baggage_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Baggage added successfully",
        "baggage_id": baggage_id,
        "flight_id": flight_id,
        "seat_number": seat_number,
        "baggage_type": baggage_type,
        "weight": weight,
        "price": price
    }), 201


# =====================================================
# GET BAGGAGE FOR FLIGHT
# =====================================================

@app.route("/baggage/<flight_id>", methods=["GET"])
def get_baggage(flight_id):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM baggage
        WHERE flight_id = ?
    """, (flight_id,))

    rows = cursor.fetchall()

    conn.close()

    baggage = []

    for row in rows:

        baggage.append({
            "id": row["id"],
            "flight_id": row["flight_id"],
            "seat_number": row["seat_number"],
            "baggage_type": row["baggage_type"],
            "weight": row["weight"],
            "price": row["price"]
        })

    return jsonify(baggage)


# =====================================================
# DELETE BAGGAGE
# =====================================================

@app.route("/baggage/<int:baggage_id>", methods=["DELETE"])
def delete_baggage(baggage_id):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM baggage
        WHERE id = ?
    """, (baggage_id,))

    conn.commit()

    deleted = cursor.rowcount

    conn.close()

    if deleted == 0:

        return jsonify({
            "message": "Baggage not found"
        }), 404

    return jsonify({
        "message": "Baggage deleted successfully"
    })


# =====================================================
# START SERVICE
# =====================================================

if __name__ == "__main__":

    init_db()

    print("====================================")
    print("🧳 Baggage Service Running")
    print("📡 Port: 5003")
    print("====================================")

    app.run(
        host="0.0.0.0",
        port=5003,
        debug=False,
        use_reloader=False
    )