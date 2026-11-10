import sqlite3

DATABASE = "seats.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# CREATE TABLE
# =========================================================

def create_table():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seats (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            flight_id INTEGER NOT NULL,

            seat_number TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'Available',

            UNIQUE(
                flight_id,
                seat_number
            )
        )
    """)

    conn.commit()

    conn.close()


# =========================================================
# CREATE SEATS FOR FLIGHT
# =========================================================

def create_seats_for_flight(
    flight_id
):

    conn = get_db()

    cursor = conn.cursor()

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

            seat_number = (
                f"{row}{letter}"
            )

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

    conn.close()


# =========================================================
# GET SEATS
# =========================================================

def get_seats(flight_id):

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

        ORDER BY id
    """, (flight_id,))

    seats = cursor.fetchall()

    conn.close()

    return seats


# =========================================================
# BOOK SEAT
# =========================================================

def book_seat(
    flight_id,
    seat_number
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM seats

        WHERE flight_id = ?

        AND seat_number = ?
    """, (
        flight_id,
        seat_number
    ))

    seat = cursor.fetchone()

    if not seat:

        conn.close()

        return {
            "success": False,
            "message": "Seat not found"
        }

    if seat["status"].lower() == "booked":

        conn.close()

        return {
            "success": False,
            "message": "Seat is already booked"
        }

    cursor.execute("""
        UPDATE seats

        SET status = 'Booked'

        WHERE flight_id = ?

        AND seat_number = ?

        AND status = 'Available'
    """, (
        flight_id,
        seat_number
    ))

    if cursor.rowcount == 0:

        conn.rollback()
        conn.close()

        return {
            "success": False,
            "message": "Seat was just booked by another user"
        }

    conn.commit()

    conn.close()

    return {
        "success": True,
        "message": "Seat booked successfully",
        "flight_id": flight_id,
        "seat_number": seat_number,
        "status": "Booked"
    }