from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# ============================================================
# CONFIGURATION
# ============================================================

PORT = 5002

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "seats.db")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id INTEGER NOT NULL,
            seat_number TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Available',
            UNIQUE(flight_id, seat_number)
        )
    """)

    conn.commit()
    conn.close()

    print("Seat database initialized successfully.")


# ============================================================
# CREATE SEATS FOR A FLIGHT
# ============================================================

def create_seats_for_flight(flight_id):

    conn = get_db()
    cursor = conn.cursor()

    try:

        # Check whether seats already exist
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM seats
            WHERE flight_id = ?
        """, (flight_id,))

        result = cursor.fetchone()

        total = result["total"]

        # Seats already exist
        if total > 0:
            return

        print(
            f"Creating seats automatically for Flight ID: {flight_id}"
        )

        # ====================================================
        # AIRCRAFT LAYOUT
        #
        # A B C | D E F
        #
        # 10 rows x 6 seats
        # Total = 60 seats
        # ====================================================

        seat_letters = [
            "A",
            "B",
            "C",
            "D",
            "E",
            "F"
        ]

        for row in range(1, 11):

            for letter in seat_letters:

                seat_number = f"{row}{letter}"

                cursor.execute("""
                    INSERT OR IGNORE INTO seats
                    (
                        flight_id,
                        seat_number,
                        status
                    )
                    VALUES (?, ?, 'Available')
                """, (
                    flight_id,
                    seat_number
                ))

        conn.commit()

        print(
            f"60 seats created successfully for Flight ID: {flight_id}"
        )

    except Exception as e:

        conn.rollback()

        print(
            "Error creating seats:",
            str(e)
        )

        raise

    finally:

        conn.close()


# ============================================================
# CONVERT DATABASE ROW TO JSON
# ============================================================

def seat_to_dict(seat):

    return {
        "id": seat["id"],
        "flight_id": seat["flight_id"],
        "seat_number": seat["seat_number"],
        "status": seat["status"]
    }


# ============================================================
# GET ALL SEATS
# ============================================================
#
# IMPORTANT:
# This endpoint returns a DIRECT ARRAY.
#
# Example:
#
# [
#   {
#       "id": 1,
#       "flight_id": 20,
#       "seat_number": "1A",
#       "status": "Available"
#   }
# ]
#
# This matches your seats.html code.
# ============================================================

@app.route("/seats/<int:flight_id>", methods=["GET"])
def get_seats(flight_id):

    try:

        print(
            f"Loading seats for Flight ID: {flight_id}"
        )

        # Automatically create seats
        create_seats_for_flight(flight_id)

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                flight_id,
                seat_number,
                status
            FROM seats
            WHERE flight_id = ?
            ORDER BY
                CAST(
                    SUBSTR(
                        seat_number,
                        1,
                        LENGTH(seat_number) - 1
                    ) AS INTEGER
                ),
                seat_number
        """, (flight_id,))

        rows = cursor.fetchall()

        conn.close()

        seats = []

        for seat in rows:
            seats.append(
                seat_to_dict(seat)
            )

        print(
            f"Total seats returned: {len(seats)}"
        )

        # IMPORTANT:
        # Return array directly
        return jsonify(seats), 200

    except Exception as e:

        print(
            "Get seats error:",
            str(e)
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# GET AVAILABLE SEATS
# ============================================================

@app.route(
    "/seats/<int:flight_id>/available",
    methods=["GET"]
)
def get_available_seats(flight_id):

    try:

        create_seats_for_flight(flight_id)

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                flight_id,
                seat_number,
                status
            FROM seats
            WHERE flight_id = ?
            AND LOWER(status) = 'available'
            ORDER BY
                CAST(
                    SUBSTR(
                        seat_number,
                        1,
                        LENGTH(seat_number) - 1
                    ) AS INTEGER
                ),
                seat_number
        """, (flight_id,))

        rows = cursor.fetchall()

        conn.close()

        seats = []

        for seat in rows:

            seats.append(
                seat_to_dict(seat)
            )

        return jsonify(seats), 200

    except Exception as e:

        print(
            "Available seats error:",
            str(e)
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# GET SINGLE SEAT
# ============================================================

@app.route(
    "/seats/<int:flight_id>/<seat_number>",
    methods=["GET"]
)
def get_single_seat(flight_id, seat_number):

    try:

        create_seats_for_flight(flight_id)

        seat_number = seat_number.upper()

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                flight_id,
                seat_number,
                status
            FROM seats
            WHERE flight_id = ?
            AND UPPER(seat_number) = ?
        """, (
            flight_id,
            seat_number
        ))

        seat = cursor.fetchone()

        conn.close()

        if not seat:

            return jsonify({
                "success": False,
                "message": "Seat not found"
            }), 404

        return jsonify({
            "success": True,
            "seat": seat_to_dict(seat)
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# BOOK SEAT USING PUT
# ============================================================
#
# URL:
#
# PUT
# /seats/20/10C
#
# This is the API your seats.html is currently using.
# ============================================================

@app.route(
    "/seats/<int:flight_id>/<seat_number>",
    methods=["PUT"]
)
def book_seat_by_url(flight_id, seat_number):

    conn = None

    try:

        seat_number = seat_number.upper().strip()

        print(
            "================================================"
        )

        print(
            f"BOOKING REQUEST"
        )

        print(
            f"Flight ID  : {flight_id}"
        )

        print(
            f"Seat       : {seat_number}"
        )

        print(
            "================================================"
        )

        # Make sure seats exist
        create_seats_for_flight(flight_id)

        conn = get_db()
        cursor = conn.cursor()

        # ====================================================
        # ATOMIC BOOKING
        # ====================================================
        #
        # Only update if seat is still Available.
        #
        # This prevents two users from booking
        # the same seat at exactly the same time.
        # ====================================================

        cursor.execute("""
            UPDATE seats
            SET status = 'Booked'
            WHERE flight_id = ?
            AND UPPER(seat_number) = ?
            AND LOWER(status) = 'available'
        """, (
            flight_id,
            seat_number
        ))

        updated = cursor.rowcount

        # ====================================================
        # SEAT WAS NOT BOOKED
        # ====================================================

        if updated == 0:

            # Check whether seat exists
            cursor.execute("""
                SELECT
                    id,
                    flight_id,
                    seat_number,
                    status
                FROM seats
                WHERE flight_id = ?
                AND UPPER(seat_number) = ?
            """, (
                flight_id,
                seat_number
            ))

            seat = cursor.fetchone()

            if not seat:

                conn.rollback()

                return jsonify({
                    "success": False,
                    "message": "Seat not found"
                }), 404

            # Seat already booked
            if seat["status"].lower() == "booked":

                conn.rollback()

                return jsonify({
                    "success": False,
                    "message": "Seat is already booked"
                }), 409

            conn.rollback()

            return jsonify({
                "success": False,
                "message": "Seat cannot be booked"
            }), 409

        # ====================================================
        # COMMIT BOOKING
        # ====================================================

        conn.commit()

        # Get updated seat
        cursor.execute("""
            SELECT
                id,
                flight_id,
                seat_number,
                status
            FROM seats
            WHERE flight_id = ?
            AND UPPER(seat_number) = ?
        """, (
            flight_id,
            seat_number
        ))

        seat = cursor.fetchone()

        conn.close()
        conn = None

        print(
            f"Seat {seat_number} booked successfully."
        )

        return jsonify({
            "success": True,
            "message": "Seat booked successfully",
            "flight_id": flight_id,
            "seat_number": seat_number,
            "status": "Booked",
            "seat": seat_to_dict(seat)
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()
            conn.close()

        print(
            "PUT booking error:",
            str(e)
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# BOOK SEAT USING POST
# ============================================================

@app.route(
    "/seats/book",
    methods=["POST"]
)
def book_seat():

    conn = None

    try:

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "success": False,
                "message": "JSON data is required."
            }), 400

        flight_id = data.get("flight_id")
        seat_number = data.get("seat_number")

        # ====================================================
        # VALIDATION
        # ====================================================

        if flight_id is None:

            return jsonify({
                "success": False,
                "message": "Flight ID is required."
            }), 400

        if not seat_number:

            return jsonify({
                "success": False,
                "message": "Seat number is required."
            }), 400

        try:

            flight_id = int(flight_id)

        except ValueError:

            return jsonify({
                "success": False,
                "message": "Flight ID must be a number."
            }), 400

        seat_number = str(
            seat_number
        ).upper().strip()

        # ====================================================
        # CREATE SEATS
        # ====================================================

        create_seats_for_flight(flight_id)

        conn = get_db()
        cursor = conn.cursor()

        # ====================================================
        # ATOMIC BOOKING
        # ====================================================

        cursor.execute("""
            UPDATE seats
            SET status = 'Booked'
            WHERE flight_id = ?
            AND UPPER(seat_number) = ?
            AND LOWER(status) = 'available'
        """, (
            flight_id,
            seat_number
        ))

        updated = cursor.rowcount

        # ====================================================
        # BOOKING FAILED
        # ====================================================

        if updated == 0:

            cursor.execute("""
                SELECT
                    id,
                    flight_id,
                    seat_number,
                    status
                FROM seats
                WHERE flight_id = ?
                AND UPPER(seat_number) = ?
            """, (
                flight_id,
                seat_number
            ))

            seat = cursor.fetchone()

            if not seat:

                conn.rollback()
                conn.close()

                return jsonify({
                    "success": False,
                    "message": "Seat does not exist."
                }), 404

            if seat["status"].lower() == "booked":

                conn.rollback()
                conn.close()

                return jsonify({
                    "success": False,
                    "message": "Seat is already booked."
                }), 409

            conn.rollback()
            conn.close()

            return jsonify({
                "success": False,
                "message": "Unable to book seat."
            }), 409

        # ====================================================
        # SAVE
        # ====================================================

        conn.commit()

        conn.close()
        conn = None

        return jsonify({
            "success": True,
            "message": "Seat booked successfully.",
            "flight_id": flight_id,
            "seat_number": seat_number,
            "status": "Booked"
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()
            conn.close()

        print(
            "POST booking error:",
            str(e)
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# CANCEL / RELEASE SEAT
# ============================================================

@app.route(
    "/seats/cancel",
    methods=["POST"]
)
def cancel_seat():

    try:

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "success": False,
                "message": "JSON data is required."
            }), 400

        flight_id = data.get("flight_id")
        seat_number = data.get("seat_number")

        if flight_id is None or not seat_number:

            return jsonify({
                "success": False,
                "message":
                    "Flight ID and seat number are required."
            }), 400

        seat_number = str(
            seat_number
        ).upper().strip()

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE seats
            SET status = 'Available'
            WHERE flight_id = ?
            AND UPPER(seat_number) = ?
        """, (
            flight_id,
            seat_number
        ))

        updated = cursor.rowcount

        conn.commit()
        conn.close()

        if updated == 0:

            return jsonify({
                "success": False,
                "message": "Seat not found."
            }), 404

        print(
            f"Seat {seat_number} released for Flight {flight_id}"
        )

        return jsonify({
            "success": True,
            "message": "Seat cancelled successfully.",
            "flight_id": flight_id,
            "seat_number": seat_number,
            "status": "Available"
        }), 200

    except Exception as e:

        print(
            "Cancel seat error:",
            str(e)
        )

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# SEAT STATISTICS
# ============================================================

@app.route(
    "/seats/<int:flight_id>/stats",
    methods=["GET"]
)
def seat_statistics(flight_id):

    try:

        create_seats_for_flight(flight_id)

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(
                    CASE
                        WHEN LOWER(status) = 'available'
                        THEN 1
                        ELSE 0
                    END
                ) AS available,
                SUM(
                    CASE
                        WHEN LOWER(status) = 'booked'
                        THEN 1
                        ELSE 0
                    END
                ) AS booked
            FROM seats
            WHERE flight_id = ?
        """, (flight_id,))

        result = cursor.fetchone()

        conn.close()

        total = result["total"] or 0
        available = result["available"] or 0
        booked = result["booked"] or 0

        return jsonify({
            "success": True,
            "flight_id": flight_id,
            "total_seats": total,
            "available_seats": available,
            "booked_seats": booked,
            "occupancy_percentage":
                round(
                    (booked / total) * 100,
                    2
                ) if total > 0 else 0
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# RESET ALL SEATS FOR A FLIGHT
# ============================================================
#
# Useful for testing.
#
# POST:
# /seats/20/reset
#
# ============================================================

@app.route(
    "/seats/<int:flight_id>/reset",
    methods=["POST"]
)
def reset_seats(flight_id):

    try:

        create_seats_for_flight(flight_id)

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE seats
            SET status = 'Available'
            WHERE flight_id = ?
        """, (flight_id,))

        updated = cursor.rowcount

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "All seats reset successfully.",
            "flight_id": flight_id,
            "seats_reset": updated
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return jsonify({
        "service": "Seat Service",
        "status": "running",
        "port": PORT,
        "database": DATABASE,
        "features": [
            "Automatic seat creation",
            "Seat selection",
            "Live seat booking",
            "Seat cancellation",
            "Seat statistics",
            "Concurrent booking protection"
        ]
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    init_db()

    print("")
    print("========================================")
    print("       ✈️ SKYBOOK SEAT SERVICE")
    print("========================================")
    print("Service : Seat Service")
    print("Port    : 5002")
    print("URL     : http://localhost:5002")
    print("Database:", DATABASE)
    print("========================================")
    print("Features:")
    print("✓ Automatic 60 seats per flight")
    print("✓ A B C | D E F layout")
    print("✓ Live seat booking")
    print("✓ Prevent double booking")
    print("✓ Seat cancellation")
    print("✓ Seat statistics")
    print("✓ Automatic seat creation")
    print("========================================")
    print("")

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=True
    )