import sqlite3
from datetime import date, timedelta


DATABASE = "flights.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# CREATE TABLE
# =========================================================

def create_table():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flights (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            flight_number TEXT NOT NULL,

            airline TEXT NOT NULL,

            source TEXT NOT NULL,

            destination TEXT NOT NULL,

            departure_time TEXT NOT NULL,

            arrival_time TEXT NOT NULL,

            date TEXT NOT NULL,

            price REAL NOT NULL,

            available_seats INTEGER NOT NULL DEFAULT 60,

            UNIQUE(flight_number, date)
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# AIRLINES
# =========================================================

AIRLINES = [

    {
        "name": "Air India",
        "code": "AI",
        "base_price": 5500
    },

    {
        "name": "IndiGo",
        "code": "6E",
        "base_price": 4500
    },

    {
        "name": "Vistara",
        "code": "UK",
        "base_price": 6000
    },

    {
        "name": "SpiceJet",
        "code": "SG",
        "base_price": 4200
    },

    {
        "name": "Akasa Air",
        "code": "QP",
        "base_price": 4000
    },

    {
        "name": "Emirates",
        "code": "EK",
        "base_price": 12000
    }

]


# =========================================================
# ROUTES
# =========================================================
# Both directions are included.
#
# Example:
# Mumbai -> Delhi
# Delhi  -> Mumbai
#
# Therefore Round Trip can find a return flight.
# =========================================================

ROUTES = [

    # Mumbai <-> Delhi
    ("Mumbai", "Delhi", 2.10),
    ("Delhi", "Mumbai", 2.15),

    # Mumbai <-> Bangalore
    ("Mumbai", "Bangalore", 1.45),
    ("Bangalore", "Mumbai", 1.50),

    # Delhi <-> Bangalore
    ("Delhi", "Bangalore", 2.40),
    ("Bangalore", "Delhi", 2.45),

    # Mumbai <-> Hyderabad
    ("Mumbai", "Hyderabad", 1.35),
    ("Hyderabad", "Mumbai", 1.40),

    # Delhi <-> Hyderabad
    ("Delhi", "Hyderabad", 2.10),
    ("Hyderabad", "Delhi", 2.15),

    # Mumbai <-> Chennai
    ("Mumbai", "Chennai", 1.55),
    ("Chennai", "Mumbai", 2.00),

    # Delhi <-> Kolkata
    ("Delhi", "Kolkata", 2.20),
    ("Kolkata", "Delhi", 2.25),

    # Bangalore <-> Chennai
    ("Bangalore", "Chennai", 1.00),
    ("Chennai", "Bangalore", 1.05),

    # Pune <-> Delhi
    ("Pune", "Delhi", 2.05),
    ("Delhi", "Pune", 2.10),

    # Pune <-> Bangalore
    ("Pune", "Bangalore", 1.30),
    ("Bangalore", "Pune", 1.35),

    # Mumbai <-> Goa
    ("Mumbai", "Goa", 1.15),
    ("Goa", "Mumbai", 1.20)

]


# =========================================================
# DEPARTURE / ARRIVAL TIMES
# =========================================================

FLIGHT_TIMES = [

    ("05:30", "07:45"),
    ("06:15", "09:00"),
    ("08:00", "10:45"),
    ("10:30", "12:45"),
    ("13:00", "15:30"),
    ("16:00", "18:15"),
    ("18:30", "20:45"),
    ("21:00", "23:15")

]


# =========================================================
# GENERATE FLIGHTS
# =========================================================

def generate_flights():

    conn = get_db()
    cursor = conn.cursor()

    start_date = date(2026, 9, 1)
    end_date = date(2027, 10, 31)
    current_date = start_date

    while current_date <= end_date:

        date_string = current_date.strftime("%Y-%m-%d")

        for airline in AIRLINES:

            for route_index, route in enumerate(ROUTES):

                source = route[0]

                destination = route[1]

                duration = route[2]

                # -----------------------------------------
                # Select different departure times
                # -----------------------------------------

                time_index = (
                    route_index
                    + current_date.toordinal()
                    + len(airline["code"])
                ) % len(FLIGHT_TIMES)

                departure, arrival = FLIGHT_TIMES[time_index]

                # -----------------------------------------
                # Price variation
                # -----------------------------------------

                price_variation = (
                    route_index * 150
                    + current_date.day * 10
                )

                price = (
                    airline["base_price"]
                    + price_variation
                )

                # -----------------------------------------
                # Flight number
                # -----------------------------------------

                flight_number = (
                    f"{airline['code']}"
                    f"{route_index + 1:02d}"
                    f"{current_date.day:02d}"
                )

                # -----------------------------------------
                # Insert flight
                # -----------------------------------------

                try:

                    cursor.execute("""
                        INSERT OR IGNORE INTO flights
                        (
                            flight_number,
                            airline,
                            source,
                            destination,
                            departure_time,
                            arrival_time,
                            date,
                            price,
                            available_seats
                        )

                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

                    """, (

                        flight_number,
                        airline["name"],
                        source,
                        destination,
                        departure,
                        arrival,
                        date_string,
                        price,
                        60

                    ))

                except sqlite3.Error as error:

                    print(
                        "Flight insert error:",
                        error
                    )

        current_date += timedelta(days=1)

    conn.commit()

    conn.close()

    print(
        "=============================================="
    )

    print(
        "✈️ Flight schedules generated successfully"
    )

    print(
        f"📅 From: {start_date}"
    )

    print(
        f"📅 Until: {end_date}"
    )

    print(
        f"🛫 Routes: {len(ROUTES)}"
    )

    print(
        f"🏢 Airlines: {len(AIRLINES)}"
    )

    print(
        "🔄 One Way + Round Trip supported"
    )

    print(
        "=============================================="
    )


# =========================================================
# GET ALL FLIGHTS
# =========================================================

def get_all_flights():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM flights
        ORDER BY date, departure_time
    """)

    flights = cursor.fetchall()

    conn.close()

    return flights


# =========================================================
# GET FLIGHT BY ID
# =========================================================

def get_flight_by_id(flight_id):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM flights
        WHERE id = ?
    """, (flight_id,))

    flight = cursor.fetchone()

    conn.close()

    return flight


# =========================================================
# SEARCH FLIGHTS
# =========================================================
# Used for ONE-WAY flight search.
#
# Example:
# Mumbai -> Delhi
# 2026-09-20
# =========================================================

def search_flights(
    source,
    destination,
    flight_date
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM flights

        WHERE LOWER(source) = LOWER(?)

        AND LOWER(destination) = LOWER(?)

        AND date = ?

        AND available_seats > 0

        ORDER BY departure_time
    """, (
        source,
        destination,
        flight_date
    ))

    flights = cursor.fetchall()

    conn.close()

    return flights


# =========================================================
# SEARCH RETURN FLIGHTS
# =========================================================
# Used for ROUND TRIP.
#
# Example:
#
# Outbound:
# Mumbai -> Delhi
# 2026-09-20
#
# Return:
# Delhi -> Mumbai
# 2026-09-25
#
# The return flight is searched independently.
# =========================================================

def search_return_flights(
    source,
    destination,
    return_date
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM flights

        WHERE LOWER(source) = LOWER(?)

        AND LOWER(destination) = LOWER(?)

        AND date = ?

        AND available_seats > 0

        ORDER BY departure_time
    """, (
        source,
        destination,
        return_date
    ))

    flights = cursor.fetchall()

    conn.close()

    return flights


# =========================================================
# SEARCH ROUND TRIP
# =========================================================
# This function returns both outbound and return flights.
#
# outbound:
# Mumbai -> Delhi
#
# return:
# Delhi -> Mumbai
# =========================================================

def search_round_trip(
    source,
    destination,
    departure_date,
    return_date
):

    conn = get_db()

    cursor = conn.cursor()

    # -----------------------------------------
    # OUTBOUND FLIGHTS
    # -----------------------------------------

    cursor.execute("""
        SELECT *
        FROM flights

        WHERE LOWER(source) = LOWER(?)

        AND LOWER(destination) = LOWER(?)

        AND date = ?

        AND available_seats > 0

        ORDER BY departure_time
    """, (
        source,
        destination,
        departure_date
    ))

    outbound = cursor.fetchall()

    # -----------------------------------------
    # RETURN FLIGHTS
    # -----------------------------------------

    cursor.execute("""
        SELECT *
        FROM flights

        WHERE LOWER(source) = LOWER(?)

        AND LOWER(destination) = LOWER(?)

        AND date = ?

        AND available_seats > 0

        ORDER BY departure_time
    """, (
        destination,
        source,
        return_date
    ))

    return_flights = cursor.fetchall()

    conn.close()

    return {
        "outbound": outbound,
        "return": return_flights
    }


# =========================================================
# SEARCH BY DATE
# =========================================================

def search_by_date(flight_date):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM flights

        WHERE date = ?

        AND available_seats > 0

        ORDER BY departure_time
    """, (flight_date,))

    flights = cursor.fetchall()

    conn.close()

    return flights


# =========================================================
# SEARCH AVAILABLE FLIGHTS BETWEEN DATES
# =========================================================

def search_between_dates(
    source,
    destination,
    start_date,
    end_date
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM flights

        WHERE LOWER(source) = LOWER(?)

        AND LOWER(destination) = LOWER(?)

        AND date BETWEEN ? AND ?

        AND available_seats > 0

        ORDER BY date, departure_time
    """, (
        source,
        destination,
        start_date,
        end_date
    ))

    flights = cursor.fetchall()

    conn.close()

    return flights


# =========================================================
# GET AVAILABLE SEATS COUNT
# =========================================================

def get_available_seats_count(flight_id):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT available_seats
        FROM flights
        WHERE id = ?
    """, (flight_id,))

    result = cursor.fetchone()

    conn.close()

    if result:

        return result["available_seats"]

    return 0


# =========================================================
# UPDATE AVAILABLE SEATS
# =========================================================

def update_available_seats(
    flight_id,
    new_count
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE flights

        SET available_seats = ?

        WHERE id = ?

    """, (
        new_count,
        flight_id
    ))

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    return updated


# =========================================================
# DECREASE AVAILABLE SEATS
# =========================================================
# Useful when multiple passengers book together.
#
# Example:
# 60 seats
# 3 passengers book
# Result = 57
# =========================================================

def decrease_available_seats(
    flight_id,
    passenger_count
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE flights

        SET available_seats =
            available_seats - ?

        WHERE id = ?

        AND available_seats >= ?

    """, (
        passenger_count,
        flight_id,
        passenger_count
    ))

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    return updated


# =========================================================
# INCREASE AVAILABLE SEATS
# =========================================================
# Useful if a booking is cancelled.
# =========================================================

def increase_available_seats(
    flight_id,
    passenger_count
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE flights

        SET available_seats =
            available_seats + ?

        WHERE id = ?

    """, (
        passenger_count,
        flight_id
    ))

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    return updated


# =========================================================
# GET FLIGHTS FOR A ROUTE
# =========================================================

def get_route_flights(
    source,
    destination
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM flights

        WHERE LOWER(source) = LOWER(?)

        AND LOWER(destination) = LOWER(?)

        AND available_seats > 0

        ORDER BY date, departure_time

    """, (
        source,
        destination
    ))

    flights = cursor.fetchall()

    conn.close()

    return flights


# =========================================================
# GET AVAILABLE CITIES
# =========================================================

def get_cities():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT source AS city
        FROM flights

        UNION

        SELECT destination AS city
        FROM flights

        ORDER BY city
    """)

    cities = cursor.fetchall()

    conn.close()

    return [row["city"] for row in cities]


# =========================================================
# INITIALIZE DATABASE
# =========================================================

if __name__ == "__main__":

    create_table()

    generate_flights()

    print(
        "Flight database is ready."
    )