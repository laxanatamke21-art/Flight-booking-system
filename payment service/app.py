from flask import Flask, request, jsonify
from flask_cors import CORS

import sqlite3
import uuid
from datetime import datetime

from payment import (
    generate_client_token,
    process_payment
)


# =====================================================
# FLASK APP
# =====================================================

app = Flask(__name__)

CORS(app)


# =====================================================
# CONFIGURATION
# =====================================================

PORT = 5004

DATABASE = "payments.db"


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# =====================================================
# DATABASE INITIALIZATION
# =====================================================

def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            payment_id TEXT UNIQUE NOT NULL,

            booking_id TEXT NOT NULL,

            amount REAL NOT NULL,

            payment_method TEXT NOT NULL,

            status TEXT NOT NULL,

            created_at TEXT NOT NULL

        )
    """)

    conn.commit()

    conn.close()

    print("Payment database initialized.")


# =====================================================
# HOME
# =====================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({

        "service": "Payment Service",

        "status": "Running",

        "payment_gateway": "Braintree Sandbox",

        "port": PORT

    }), 200


# =====================================================
# BRAINTREE CLIENT TOKEN
# =====================================================

@app.route("/client-token", methods=["GET"])
def client_token():

    try:

        print()
        print("====================================")
        print("🔐 Generating Braintree Client Token")
        print("====================================")

        result = generate_client_token()

        print(
            "Braintree client token result:",
            result
        )

        if not result.get("success"):

            return jsonify({

                "success": False,

                "message":
                    result.get(
                        "message",
                        "Unable to generate client token"
                    )

            }), 500

        return jsonify(result), 200


    except Exception as e:

        print(
            "CLIENT TOKEN ERROR:",
            str(e)
        )

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# =====================================================
# MAKE PAYMENT
# =====================================================

@app.route("/payment", methods=["POST"])
def make_payment():

    try:

        # =================================================
        # GET REQUEST DATA
        # =================================================

        data = request.get_json()


        if not data:

            return jsonify({

                "success": False,

                "message":
                    "Request body is required"

            }), 400


        print()
        print("====================================")
        print("💳 NEW PAYMENT REQUEST")
        print("====================================")

        print(
            "Payment request:",
            data
        )


        # =================================================
        # GET BASIC PAYMENT DATA
        # =================================================

        booking_id = data.get(
            "booking_id"
        )


        amount = data.get(
            "amount"
        )


        payment_method_nonce = data.get(
            "payment_method_nonce"
        )


        device_data = data.get(
            "device_data"
        )


        # =================================================
        # GET MULTI-PASSENGER DATA
        # =================================================

        flight_id = data.get(
            "flight_id"
        )


        seat_numbers = data.get(
            "seat_numbers",
            []
        )


        passenger_count = data.get(
            "passenger_count",
            0
        )


        baggage_total = data.get(
            "baggage_total",
            0
        )


        # =================================================
        # VALIDATE BOOKING ID
        # =================================================

        if not booking_id:

            return jsonify({

                "success": False,

                "message":
                    "booking_id is required"

            }), 400


        # =================================================
        # VALIDATE AMOUNT
        # =================================================

        if amount is None:

            return jsonify({

                "success": False,

                "message":
                    "amount is required"

            }), 400


        try:

            amount = float(amount)

        except (
            ValueError,
            TypeError
        ):

            return jsonify({

                "success": False,

                "message":
                    "amount must be a number"

            }), 400


        if amount <= 0:

            return jsonify({

                "success": False,

                "message":
                    "amount must be greater than 0"

            }), 400


        # =================================================
        # VALIDATE NONCE
        # =================================================

        if not payment_method_nonce:

            return jsonify({

                "success": False,

                "message":
                    "Braintree payment nonce is required"

            }), 400


        # =================================================
        # VALIDATE PASSENGER COUNT
        # =================================================

        try:

            passenger_count = int(
                passenger_count
            )

        except (
            ValueError,
            TypeError
        ):

            passenger_count = 0


        if passenger_count <= 0:

            # Backward compatibility
            passenger_count = 1


        if passenger_count > 4:

            return jsonify({

                "success": False,

                "message":
                    "Maximum 4 passengers are allowed"

            }), 400


        # =================================================
        # VALIDATE SEATS
        # =================================================

        if not isinstance(
            seat_numbers,
            list
        ):

            seat_numbers = []


        if len(seat_numbers) > 4:

            return jsonify({

                "success": False,

                "message":
                    "Maximum 4 seats are allowed"

            }), 400


        # =================================================
        # VALIDATE BAGGAGE TOTAL
        # =================================================

        try:

            baggage_total = float(
                baggage_total or 0
            )

        except (
            ValueError,
            TypeError
        ):

            baggage_total = 0


        if baggage_total < 0:

            baggage_total = 0


        # =================================================
        # DISPLAY PAYMENT SUMMARY
        # =================================================

        print()
        print("-------- BOOKING SUMMARY --------")

        print(
            "Booking ID:",
            booking_id
        )

        print(
            "Flight ID:",
            flight_id
        )

        print(
            "Passengers:",
            passenger_count
        )

        print(
            "Seats:",
            seat_numbers
        )

        print(
            "Baggage Total:",
            baggage_total
        )

        print(
            "Total Amount:",
            amount
        )

        print("---------------------------------")
        print()


        # =================================================
        # PROCESS ONE BRAINTREE PAYMENT
        # =================================================

        print(
            "🔐 Processing Braintree payment..."
        )


        braintree_result = process_payment(

            amount=amount,

            payment_method_nonce=
                payment_method_nonce,

            booking_id=
                booking_id,

            device_data=
                device_data

        )


        # =================================================
        # BRAINTREE FAILED
        # =================================================

        if not braintree_result.get(
            "success"
        ):

            print(
                "❌ Braintree payment failed"
            )

            return jsonify({

                "success": False,

                "message":
                    braintree_result.get(
                        "message",
                        "Braintree payment failed"
                    ),

                "status":
                    "FAILED"

            }), 402


        # =================================================
        # BRAINTREE SUCCESS
        # =================================================

        print(
            "✅ Braintree payment successful"
        )


        transaction_id = (
            braintree_result.get(
                "transaction_id"
            )
        )


        braintree_status = (
            braintree_result.get(
                "status"
            )
        )


        # =================================================
        # CREATE OUR PAYMENT ID
        # =================================================

        payment_id = (

            "PAY-" +

            str(
                uuid.uuid4()
            )[:8].upper()

        )


        created_at = datetime.now().isoformat()


        # =================================================
        # SAVE PAYMENT
        # =================================================

        conn = get_db()


        conn.execute("""
            INSERT INTO payments
            (
                payment_id,
                booking_id,
                amount,
                payment_method,
                status,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?)

        """, (

            payment_id,

            booking_id,

            amount,

            "Braintree",

            "SUCCESS",

            created_at

        ))


        conn.commit()

        conn.close()


        # =================================================
        # SUCCESS RESPONSE
        # =================================================

        response_data = {

            "success": True,

            "message":
                "Payment successful",

            "payment_id":
                payment_id,

            "booking_id":
                booking_id,

            "amount":
                amount,

            "payment_method":
                "Braintree",

            "status":
                "SUCCESS",

            "braintree_transaction_id":
                transaction_id,

            "braintree_status":
                braintree_status,

            "flight_id":
                flight_id,

            "seat_numbers":
                seat_numbers,

            "passenger_count":
                passenger_count,

            "baggage_total":
                baggage_total,

            "created_at":
                created_at

        }


        print()
        print("====================================")
        print("✅ PAYMENT COMPLETED")
        print("====================================")

        print(
            "Payment ID:",
            payment_id
        )

        print(
            "Booking ID:",
            booking_id
        )

        print(
            "Amount:",
            amount
        )

        print(
            "Passengers:",
            passenger_count
        )

        print(
            "Seats:",
            seat_numbers
        )

        print(
            "Baggage:",
            baggage_total
        )

        print(
            "Transaction:",
            transaction_id
        )

        print("====================================")
        print()


        return jsonify(
            response_data
        ), 201


    # =====================================================
    # GENERAL ERROR
    # =====================================================

    except Exception as e:

        print()
        print(
            "❌ Payment API error:",
            str(e)
        )
        print()

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# =====================================================
# GET PAYMENT BY BOOKING ID
# =====================================================

@app.route(
    "/payment/<booking_id>",
    methods=["GET"]
)
def get_payment(booking_id):

    try:

        conn = get_db()


        payment = conn.execute("""
            SELECT *

            FROM payments

            WHERE booking_id = ?

            ORDER BY id DESC

            LIMIT 1

        """, (
            booking_id,
        )).fetchone()


        conn.close()


        if not payment:

            return jsonify({

                "success": False,

                "message":
                    "Payment not found"

            }), 404


        return jsonify({

            "success": True,

            "payment":
                dict(payment)

        }), 200


    except Exception as e:

        print(
            "Get payment error:",
            str(e)
        )


        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# =====================================================
# GET ALL PAYMENTS
# =====================================================

@app.route(
    "/payments",
    methods=["GET"]
)
def get_all_payments():

    try:

        conn = get_db()


        payments = conn.execute("""
            SELECT *

            FROM payments

            ORDER BY id DESC

        """).fetchall()


        conn.close()


        return jsonify({

            "success": True,

            "payments": [

                dict(payment)

                for payment in payments

            ]

        }), 200


    except Exception as e:

        print(
            "Get all payments error:",
            str(e)
        )


        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500


# =====================================================
# START PAYMENT SERVICE
# =====================================================

if __name__ == "__main__":

    init_db()


    print()
    print("====================================")
    print("💳 Braintree Payment Service")
    print("====================================")
    print("📡 Port: 5004")
    print("🔐 Environment: Sandbox")
    print("👥 Maximum Passengers: 4")
    print("💰 One Payment Per Booking")
    print("====================================")
    print()


    app.run(

        host="0.0.0.0",

        port=PORT,

        debug=False,

        use_reloader=False

    )