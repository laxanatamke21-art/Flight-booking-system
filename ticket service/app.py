from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import uuid
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATABASE = "tickets.db"
PORT = 5005


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE NOT NULL,
            booking_id TEXT NOT NULL,

            passenger_name TEXT,
            flight_number TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            flight_date TEXT NOT NULL,

            seat_number TEXT,
            amount REAL NOT NULL,

            passenger_data TEXT,
            baggage_data TEXT,

            payment_id TEXT,
            payment_status TEXT,

            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "service": "Ticket Generation Service",
        "status": "Running",
        "port": PORT,
        "maximum_passengers": 4
    }), 200


# =========================================================
# GENERATE TICKET
# =========================================================

@app.route("/tickets", methods=["POST"])
@app.route("/ticket", methods=["POST"])
def generate_ticket():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400


        # -------------------------------------------------
        # BASIC REQUIRED FIELDS
        # -------------------------------------------------

        required = [
            "booking_id",
            "flight_number",
            "source",
            "destination",
            "flight_date",
            "amount"
        ]

        for field in required:

            if field not in data:

                return jsonify({
                    "success": False,
                    "error": f"{field} is required"
                }), 400


        # -------------------------------------------------
        # PASSENGERS
        # -------------------------------------------------

        passengers = data.get("passengers", [])


        # Compatibility with old single-passenger frontend
        if not passengers:

            passenger_name = data.get("passenger_name")

            seat_number = data.get("seat_number")

            if passenger_name:

                passengers = [{
                    "passenger_number": 1,
                    "passenger_name": passenger_name,
                    "name": passenger_name,
                    "age": data.get("age"),
                    "gender": data.get("gender"),
                    "seat_number": seat_number
                }]


        if not isinstance(passengers, list):

            return jsonify({
                "success": False,
                "error": "passengers must be an array"
            }), 400


        if len(passengers) == 0:

            return jsonify({
                "success": False,
                "error": "At least one passenger is required"
            }), 400


        if len(passengers) > 4:

            return jsonify({
                "success": False,
                "error": "Maximum 4 passengers are allowed"
            }), 400


        # -------------------------------------------------
        # VALIDATE PASSENGERS
        # -------------------------------------------------

        cleaned_passengers = []

        for index, passenger in enumerate(passengers):

            if not isinstance(passenger, dict):

                return jsonify({
                    "success": False,
                    "error": f"Passenger {index + 1} data is invalid"
                }), 400


            passenger_name = (
                passenger.get("passenger_name")
                or passenger.get("name")
            )

            seat_number = passenger.get("seat_number")


            if not passenger_name:

                return jsonify({
                    "success": False,
                    "error": f"passenger_name is required for passenger {index + 1}"
                }), 400


            if not seat_number:

                return jsonify({
                    "success": False,
                    "error": f"seat_number is required for passenger {index + 1}"
                }), 400


            cleaned_passenger = {
                "passenger_number": passenger.get(
                    "passenger_number",
                    index + 1
                ),

                "passenger_name": str(passenger_name).strip(),

                "name": str(passenger_name).strip(),

                "age": passenger.get("age"),

                "gender": passenger.get("gender"),

                "seat_number": str(seat_number).strip().upper()
            }

            cleaned_passengers.append(cleaned_passenger)


        # -------------------------------------------------
        # SEAT NUMBERS
        # -------------------------------------------------

        seat_numbers = data.get("seat_numbers", [])


        if not seat_numbers:

            seat_numbers = [
                passenger["seat_number"]
                for passenger in cleaned_passengers
            ]


        if not isinstance(seat_numbers, list):

            seat_numbers = [seat_numbers]


        seat_numbers = [
            str(seat).strip().upper()
            for seat in seat_numbers
        ]


        # -------------------------------------------------
        # BAGGAGE
        # -------------------------------------------------

        baggage = data.get("baggage", [])

        if not isinstance(baggage, list):
            baggage = []


        # -------------------------------------------------
        # PAYMENT INFORMATION
        # -------------------------------------------------

        payment_id = data.get("payment_id")

        payment_status = data.get(
            "payment_status",
            "SUCCESS"
        )


        # -------------------------------------------------
        # AMOUNT
        # -------------------------------------------------

        try:

            amount = float(data.get("amount"))

        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "error": "amount must be a number"
            }), 400


        if amount <= 0:

            return jsonify({
                "success": False,
                "error": "amount must be greater than 0"
            }), 400


        # -------------------------------------------------
        # TICKET NUMBER
        # -------------------------------------------------

        ticket_number = (
            "TKT-" +
            str(uuid.uuid4())[:8].upper()
        )


        created_at = datetime.now().isoformat()


        # -------------------------------------------------
        # STORE FIRST PASSENGER FOR COMPATIBILITY
        # -------------------------------------------------

        first_passenger = cleaned_passengers[0]

        first_passenger_name = first_passenger["passenger_name"]

        first_seat = first_passenger["seat_number"]


        # -------------------------------------------------
        # STORE DATA AS JSON
        # -------------------------------------------------

        passenger_data_json = json.dumps(
            cleaned_passengers
        )

        baggage_data_json = json.dumps(
            baggage
        )


        # -------------------------------------------------
        # INSERT TICKET
        # -------------------------------------------------

        conn = get_db()

        conn.execute("""
            INSERT INTO tickets
            (
                ticket_number,
                booking_id,
                passenger_name,
                flight_number,
                source,
                destination,
                flight_date,
                seat_number,
                amount,
                passenger_data,
                baggage_data,
                payment_id,
                payment_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            ticket_number,

            str(data["booking_id"]),

            first_passenger_name,

            str(data["flight_number"]),

            str(data["source"]),

            str(data["destination"]),

            str(data["flight_date"]),

            first_seat,

            amount,

            passenger_data_json,

            baggage_data_json,

            payment_id,

            payment_status,

            created_at
        ))


        conn.commit()


        # -------------------------------------------------
        # GET CREATED TICKET
        # -------------------------------------------------

        ticket = conn.execute("""
            SELECT *
            FROM tickets
            WHERE ticket_number = ?
        """, (ticket_number,)).fetchone()


        conn.close()


        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        ticket_dict = dict(ticket)


        # Convert JSON back to arrays for frontend
        try:
            ticket_dict["passengers"] = json.loads(
                ticket_dict.get("passenger_data") or "[]"
            )
        except:
            ticket_dict["passengers"] = []


        try:
            ticket_dict["baggage"] = json.loads(
                ticket_dict.get("baggage_data") or "[]"
            )
        except:
            ticket_dict["baggage"] = []


        return jsonify({

            "success": True,

            "message": "Ticket generated successfully",

            "ticket": ticket_dict

        }), 201


    except Exception as e:

        print("Ticket generation error:", str(e))

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# =========================================================
# GET TICKET BY BOOKING ID
# =========================================================

@app.route("/tickets/<booking_id>", methods=["GET"])
def get_ticket(booking_id):

    try:

        conn = get_db()

        tickets = conn.execute("""
            SELECT *
            FROM tickets
            WHERE booking_id = ?
            ORDER BY id ASC
        """, (booking_id,)).fetchall()

        conn.close()


        if not tickets:

            return jsonify({
                "success": False,
                "error": "Ticket not found"
            }), 404


        ticket_list = []


        for ticket in tickets:

            ticket_dict = dict(ticket)


            try:

                ticket_dict["passengers"] = json.loads(
                    ticket_dict.get("passenger_data") or "[]"
                )

            except:

                ticket_dict["passengers"] = []


            try:

                ticket_dict["baggage"] = json.loads(
                    ticket_dict.get("baggage_data") or "[]"
                )

            except:

                ticket_dict["baggage"] = []


            ticket_list.append(ticket_dict)


        # Return the first ticket plus complete passenger data
        first_ticket = ticket_list[0]

        all_passengers = []

        all_baggage = []


        for ticket in ticket_list:

            all_passengers.extend(
                ticket.get("passengers", [])
            )

            all_baggage.extend(
                ticket.get("baggage", [])
            )


        first_ticket["passengers"] = all_passengers

        first_ticket["baggage"] = all_baggage

        first_ticket["ticket_count"] = len(ticket_list)


        return jsonify({

            "success": True,

            "ticket": first_ticket,

            "tickets": ticket_list

        }), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# =========================================================
# GET ALL TICKETS
# =========================================================

@app.route("/tickets", methods=["GET"])
def get_all_tickets():

    try:

        conn = get_db()

        tickets = conn.execute("""
            SELECT *
            FROM tickets
            ORDER BY id DESC
        """).fetchall()

        conn.close()


        result = []


        for ticket in tickets:

            ticket_dict = dict(ticket)

            try:

                ticket_dict["passengers"] = json.loads(
                    ticket_dict.get("passenger_data") or "[]"
                )

            except:

                ticket_dict["passengers"] = []


            try:

                ticket_dict["baggage"] = json.loads(
                    ticket_dict.get("baggage_data") or "[]"
                )

            except:

                ticket_dict["baggage"] = []


            result.append(ticket_dict)


        return jsonify({

            "success": True,

            "tickets": result,

            "count": len(result)

        }), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    init_db()

    print("========================================")
    print("🎫 Ticket Generation Service")
    print("========================================")
    print("📡 Port: 5005")
    print("👥 Maximum Passengers: 4")
    print("🎟️ Multiple Seat Booking: ENABLED")
    print("🧳 Multiple Baggage: ENABLED")
    print("💳 Payment Information: ENABLED")
    print("========================================")

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )