from flask import Flask, jsonify, request
from flask_cors import CORS

from database import (
    create_table,
    generate_flights,
    get_all_flights,
    get_flight_by_id,
    search_flights,
    search_by_date,
    search_return_flights,
    search_round_trip,
    search_between_dates,
    get_route_flights,
    get_cities,
    get_available_seats_count,
    update_available_seats,
    decrease_available_seats,
    increase_available_seats
)


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

CORS(app)


# =========================================================
# STARTUP
# =========================================================

create_table()

generate_flights()


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({

        "service": "SkyBook Flight Service",

        "status": "running",

        "message": "Flight Service is working",

        "port": 5001,

        "features": [
            "One Way Flight Search",
            "Round Trip Flight Search",
            "Return Flight Search",
            "Date Wise Search",
            "Route Search",
            "Flight Schedule",
            "Seat Availability"
        ]

    }), 200


# =========================================================
# GET ALL FLIGHTS
# =========================================================

@app.route("/flights", methods=["GET"])
def all_flights():

    flights = get_all_flights()

    return jsonify({

        "success": True,

        "count": len(flights),

        "flights": [
            dict(flight)
            for flight in flights
        ]

    }), 200


# =========================================================
# GET FLIGHT BY ID
# =========================================================

@app.route(
    "/flights/<int:flight_id>",
    methods=["GET"]
)
def get_flight(flight_id):

    flight = get_flight_by_id(
        flight_id
    )

    if not flight:

        return jsonify({

            "success": False,

            "message": "Flight not found"

        }), 404

    return jsonify({

        "success": True,

        "flight": dict(flight)

    }), 200


# =========================================================
# ONE-WAY FLIGHT SEARCH
# =========================================================
#
# Example:
#
# /flights/search
# ?source=Mumbai
# &destination=Delhi
# &date=2026-09-20
#
# =========================================================

@app.route(
    "/flights/search",
    methods=["GET"]
)
def search():

    source = request.args.get(
        "source",
        ""
    ).strip()

    destination = request.args.get(
        "destination",
        ""
    ).strip()

    flight_date = request.args.get(
        "date",
        ""
    ).strip()


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not source:

        return jsonify({

            "success": False,

            "message": "Source is required"

        }), 400


    if not destination:

        return jsonify({

            "success": False,

            "message": "Destination is required"

        }), 400


    if not flight_date:

        return jsonify({

            "success": False,

            "message": "Date is required"

        }), 400


    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    flights = search_flights(

        source,

        destination,

        flight_date

    )


    return jsonify({

        "success": True,

        "trip_type": "one_way",

        "source": source,

        "destination": destination,

        "date": flight_date,

        "count": len(flights),

        "flights": [

            dict(flight)

            for flight in flights

        ]

    }), 200


# =========================================================
# ROUND TRIP SEARCH
# =========================================================
#
# Example:
#
# /flights/round-trip
#
# ?source=Mumbai
# &destination=Delhi
# &departure_date=2026-09-20
# &return_date=2026-09-25
#
# =========================================================

@app.route(
    "/flights/round-trip",
    methods=["GET"]
)
def round_trip():

    source = request.args.get(
        "source",
        ""
    ).strip()

    destination = request.args.get(
        "destination",
        ""
    ).strip()

    departure_date = request.args.get(
        "departure_date",
        ""
    ).strip()

    return_date = request.args.get(
        "return_date",
        ""
    ).strip()


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not source:

        return jsonify({

            "success": False,

            "message": "Source is required"

        }), 400


    if not destination:

        return jsonify({

            "success": False,

            "message": "Destination is required"

        }), 400


    if not departure_date:

        return jsonify({

            "success": False,

            "message": "Departure date is required"

        }), 400


    if not return_date:

        return jsonify({

            "success": False,

            "message": "Return date is required"

        }), 400


    # -----------------------------------------------------
    # CHECK DATE ORDER
    # -----------------------------------------------------

    if return_date < departure_date:

        return jsonify({

            "success": False,

            "message":
                "Return date must be after departure date"

        }), 400


    # -----------------------------------------------------
    # SEARCH OUTBOUND + RETURN
    # -----------------------------------------------------

    result = search_round_trip(

        source,

        destination,

        departure_date,

        return_date

    )


    outbound = result["outbound"]

    return_flights = result["return"]


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return jsonify({

        "success": True,

        "trip_type": "round_trip",

        "source": source,

        "destination": destination,

        "departure_date": departure_date,

        "return_date": return_date,

        "outbound_count": len(outbound),

        "return_count": len(return_flights),

        "outbound": [

            dict(flight)

            for flight in outbound

        ],

        "return": [

            dict(flight)

            for flight in return_flights

        ]

    }), 200


# =========================================================
# RETURN FLIGHTS ONLY
# =========================================================
#
# Example:
#
# Mumbai -> Delhi
#
# Return:
# Delhi -> Mumbai
#
# =========================================================

@app.route(
    "/flights/return",
    methods=["GET"]
)
def return_flights():

    source = request.args.get(
        "source",
        ""
    ).strip()

    destination = request.args.get(
        "destination",
        ""
    ).strip()

    return_date = request.args.get(
        "return_date",
        ""
    ).strip()


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not source:

        return jsonify({

            "success": False,

            "message": "Source is required"

        }), 400


    if not destination:

        return jsonify({

            "success": False,

            "message": "Destination is required"

        }), 400


    if not return_date:

        return jsonify({

            "success": False,

            "message": "Return date is required"

        }), 400


    # -----------------------------------------------------
    # SEARCH REVERSE ROUTE
    # -----------------------------------------------------

    flights = search_return_flights(

        destination,

        source,

        return_date

    )


    return jsonify({

        "success": True,

        "trip_type": "return",

        "source": destination,

        "destination": source,

        "date": return_date,

        "count": len(flights),

        "flights": [

            dict(flight)

            for flight in flights

        ]

    }), 200


# =========================================================
# SEARCH ONLY BY DATE
# =========================================================

@app.route(
    "/flights/date/<flight_date>",
    methods=["GET"]
)
def flights_by_date(flight_date):

    flights = search_by_date(
        flight_date
    )

    return jsonify({

        "success": True,

        "date": flight_date,

        "count": len(flights),

        "flights": [

            dict(flight)

            for flight in flights

        ]

    }), 200


# =========================================================
# SEARCH FLIGHTS BETWEEN TWO DATES
# =========================================================

@app.route(
    "/flights/between",
    methods=["GET"]
)
def flights_between_dates():

    source = request.args.get(
        "source",
        ""
    ).strip()

    destination = request.args.get(
        "destination",
        ""
    ).strip()

    start_date = request.args.get(
        "start_date",
        ""
    ).strip()

    end_date = request.args.get(
        "end_date",
        ""
    ).strip()


    if not source:

        return jsonify({

            "success": False,

            "message": "Source is required"

        }), 400


    if not destination:

        return jsonify({

            "success": False,

            "message": "Destination is required"

        }), 400


    if not start_date:

        return jsonify({

            "success": False,

            "message": "Start date is required"

        }), 400


    if not end_date:

        return jsonify({

            "success": False,

            "message": "End date is required"

        }), 400


    flights = search_between_dates(

        source,

        destination,

        start_date,

        end_date

    )


    return jsonify({

        "success": True,

        "source": source,

        "destination": destination,

        "start_date": start_date,

        "end_date": end_date,

        "count": len(flights),

        "flights": [

            dict(flight)

            for flight in flights

        ]

    }), 200


# =========================================================
# GET FLIGHTS FOR A ROUTE
# =========================================================

@app.route(
    "/flights/route",
    methods=["GET"]
)
def route_flights():

    source = request.args.get(
        "source",
        ""
    ).strip()

    destination = request.args.get(
        "destination",
        ""
    ).strip()


    if not source:

        return jsonify({

            "success": False,

            "message": "Source is required"

        }), 400


    if not destination:

        return jsonify({

            "success": False,

            "message": "Destination is required"

        }), 400


    flights = get_route_flights(

        source,

        destination

    )


    return jsonify({

        "success": True,

        "source": source,

        "destination": destination,

        "count": len(flights),

        "flights": [

            dict(flight)

            for flight in flights

        ]

    }), 200


# =========================================================
# GET AVAILABLE CITIES
# =========================================================

@app.route(
    "/cities",
    methods=["GET"]
)
def cities():

    city_list = get_cities()


    return jsonify({

        "success": True,

        "count": len(city_list),

        "cities": city_list

    }), 200


# =========================================================
# CHECK AVAILABLE SEATS
# =========================================================

@app.route(
    "/flights/<int:flight_id>/seats",
    methods=["GET"]
)
def available_seats(flight_id):

    flight = get_flight_by_id(
        flight_id
    )


    if not flight:

        return jsonify({

            "success": False,

            "message": "Flight not found"

        }), 404


    seats = get_available_seats_count(
        flight_id
    )


    return jsonify({

        "success": True,

        "flight_id": flight_id,

        "available_seats": seats

    }), 200


# =========================================================
# UPDATE AVAILABLE SEATS
# =========================================================

@app.route(
    "/flights/<int:flight_id>/seats",
    methods=["PUT"]
)
def update_seats(flight_id):

    data = request.get_json()


    if not data:

        return jsonify({

            "success": False,

            "message": "Request body is required"

        }), 400


    new_count = data.get(
        "available_seats"
    )


    if new_count is None:

        return jsonify({

            "success": False,

            "message":
                "available_seats is required"

        }), 400


    try:

        new_count = int(new_count)

    except (ValueError, TypeError):

        return jsonify({

            "success": False,

            "message":
                "available_seats must be a number"

        }), 400


    if new_count < 0:

        return jsonify({

            "success": False,

            "message":
                "available_seats cannot be negative"

        }), 400


    updated = update_available_seats(

        flight_id,

        new_count

    )


    if updated == 0:

        return jsonify({

            "success": False,

            "message":
                "Flight not found or no change made"

        }), 404


    return jsonify({

        "success": True,

        "message":
            "Available seats updated",

        "flight_id": flight_id,

        "available_seats": new_count

    }), 200


# =========================================================
# DECREASE AVAILABLE SEATS
# =========================================================
#
# Used for multi-passenger booking.
#
# Example:
#
# Available = 60
# Passengers = 3
#
# New Available = 57
# =========================================================

@app.route(
    "/flights/<int:flight_id>/seats/decrease",
    methods=["PUT"]
)
def decrease_seats(flight_id):

    data = request.get_json()


    if not data:

        return jsonify({

            "success": False,

            "message":
                "Request body is required"

        }), 400


    passenger_count = data.get(
        "passenger_count"
    )


    if passenger_count is None:

        return jsonify({

            "success": False,

            "message":
                "passenger_count is required"

        }), 400


    try:

        passenger_count = int(
            passenger_count
        )

    except (ValueError, TypeError):

        return jsonify({

            "success": False,

            "message":
                "passenger_count must be a number"

        }), 400


    if passenger_count <= 0:

        return jsonify({

            "success": False,

            "message":
                "passenger_count must be greater than 0"

        }), 400


    if passenger_count > 4:

        return jsonify({

            "success": False,

            "message":
                "Maximum 4 passengers allowed"

        }), 400


    updated = decrease_available_seats(

        flight_id,

        passenger_count

    )


    if updated == 0:

        return jsonify({

            "success": False,

            "message":
                "Not enough available seats or flight not found"

        }), 409


    new_count = get_available_seats_count(
        flight_id
    )


    return jsonify({

        "success": True,

        "message":
            "Available seats decreased",

        "flight_id": flight_id,

        "booked_seats": passenger_count,

        "available_seats": new_count

    }), 200


# =========================================================
# INCREASE AVAILABLE SEATS
# =========================================================
#
# Used when a booking is cancelled.
# =========================================================

@app.route(
    "/flights/<int:flight_id>/seats/increase",
    methods=["PUT"]
)
def increase_seats(flight_id):

    data = request.get_json()


    if not data:

        return jsonify({

            "success": False,

            "message":
                "Request body is required"

        }), 400


    passenger_count = data.get(
        "passenger_count"
    )


    if passenger_count is None:

        return jsonify({

            "success": False,

            "message":
                "passenger_count is required"

        }), 400


    try:

        passenger_count = int(
            passenger_count
        )

    except (ValueError, TypeError):

        return jsonify({

            "success": False,

            "message":
                "passenger_count must be a number"

        }), 400


    if passenger_count <= 0:

        return jsonify({

            "success": False,

            "message":
                "passenger_count must be greater than 0"

        }), 400


    updated = increase_available_seats(

        flight_id,

        passenger_count

    )


    if updated == 0:

        return jsonify({

            "success": False,

            "message":
                "Flight not found"

        }), 404


    new_count = get_available_seats_count(
        flight_id
    )


    return jsonify({

        "success": True,

        "message":
            "Available seats increased",

        "flight_id": flight_id,

        "added_seats": passenger_count,

        "available_seats": new_count

    }), 200


# =========================================================
# AIRLINES
# =========================================================

@app.route(
    "/airlines",
    methods=["GET"]
)
def airlines():

    return jsonify({

        "success": True,

        "airlines": [

            "Air India",

            "IndiGo",

            "Vistara",

            "SpiceJet",

            "Akasa Air",

            "Emirates"

        ]

    }), 200


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    print("=" * 60)

    print("✈️ SkyBook Flight Service")

    print("🚀 Running on port 5001")

    print("📅 Automatic schedules enabled")

    print("🔄 One Way + Round Trip enabled")

    print("🛫 Return flight search enabled")

    print("👥 Multi-passenger booking supported")

    print("=" * 60)


    app.run(

        host="0.0.0.0",

        port=5001,

        debug=True

    )