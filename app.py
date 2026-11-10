from flask import Flask, send_from_directory, redirect
import os
import sys
import time
import subprocess
import threading
import webbrowser
import socket


# =====================================================
# MAIN APPLICATION
# =====================================================

app = Flask(
    __name__,
    static_folder="frontend"
)


# =====================================================
# PROJECT BASE DIRECTORY
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# =====================================================
# CHECK IF PORT IS ALREADY RUNNING
# =====================================================

def is_port_in_use(port):

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    ) as sock:

        return sock.connect_ex(
            ("127.0.0.1", port)
        ) == 0


# =====================================================
# MICROSERVICES
# =====================================================

services = [

    {
        "name": "Flight Service",
        "folder": "flight service",
        "port": 5001
    },

    {
        "name": "Seat Service",
        "folder": "seat service",
        "port": 5002
    },

    {
        "name": "Baggage Service",
        "folder": "baggage service",
        "port": 5003
    },

    {
        "name": "Payment Service",
        "folder": "payment service",
        "port": 5004
    },

    {
        "name": "Ticket Service",
        "folder": "ticket service",
        "port": 5005
    },

    {
        "name": "User Service",
        "folder": "user service",
        "port": 5006
    }

]


# Store running processes

service_processes = []


# =====================================================
# START MICROSERVICES
# =====================================================

def start_microservices():

    print()
    print("==========================================")
    print("STARTING FLIGHT BOOKING MICROSERVICES")
    print("==========================================")

    for service in services:

        service_name = service["name"]

        service_folder = os.path.join(
            BASE_DIR,
            service["folder"]
        )

        port = service["port"]

        service_app = os.path.join(
            service_folder,
            "app.py"
        )


        # Check folder and app.py

        if not os.path.exists(service_app):

            print(
                f"⚠️ {service_name} app.py not found"
            )

            print(
                f"   Expected: {service_app}"
            )

            continue


        # Check if service already running

        if is_port_in_use(port):

            print(
                f"⚠️ {service_name} already running on port {port}"
            )

            continue


        try:

            print(
                f"🚀 Starting {service_name}..."
            )

            process = subprocess.Popen(

                [
                    sys.executable,
                    "app.py"
                ],

                cwd=service_folder

            )


            service_processes.append(
                process
            )


            print(
                f"   Started on port {port}"
            )


            # Small delay between services

            time.sleep(1)


        except Exception as error:

            print(
                f"❌ Could not start {service_name}"
            )

            print(error)


    print()
    print("==========================================")
    print("ALL MICROSERVICES STARTED")
    print("==========================================")
    print()


# =====================================================
# FRONTEND ROUTES
# =====================================================

@app.route("/")
def home():

    # First page when project starts

    return redirect("/register.html")


# =====================================================
# SERVE FRONTEND FILES
# =====================================================

@app.route("/<path:filename>")
def frontend_files(filename):

    frontend_path = os.path.join(
        BASE_DIR,
        "frontend"
    )

    return send_from_directory(
        frontend_path,
        filename
    )


# =====================================================
# OPEN BROWSER AUTOMATICALLY
# =====================================================

def open_browser():

    time.sleep(2)

    webbrowser.open(
        "http://127.0.0.1:5000/"
    )


# =====================================================
# START APPLICATION
# =====================================================

if __name__ == "__main__":

    # Start all backend services

    start_microservices()


    # Open browser automatically

    browser_thread = threading.Thread(
        target=open_browser
    )

    browser_thread.daemon = True

    browser_thread.start()


    print("==========================================")
    print("✈️ SKYBOOK FLIGHT BOOKING SYSTEM")
    print("==========================================")
    print()
    print("Frontend Server Running")
    print()
    print("🌐 Open:")
    print("http://127.0.0.1:5000")
    print()
    print("First Page:")
    print("Register Page")
    print()
    print("Press CTRL + C to stop the project")
    print("==========================================")
    print()


    try:

        app.run(
            host="0.0.0.0",
            port=5000,
            debug=False,
            use_reloader=False
        )

    except KeyboardInterrupt:

        print()
        print("Stopping Flight Booking System...")


        for process in service_processes:

            try:

                process.terminate()

            except Exception:

                pass


        print("All services stopped.")