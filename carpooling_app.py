import streamlit as st
import sqlite3
from datetime import datetime

# Database setup
DB_FILE = "carpooling.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Create users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    # Create rides table
    c.execute("""
        CREATE TABLE IF NOT EXISTS rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            pickup TEXT NOT NULL,
            dropoff TEXT NOT NULL,
            datetime TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)
    conn.commit()
    conn.close()

# Register a new user
def register_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        st.success("User registered successfully. You can now log in.")
    except sqlite3.IntegrityError:
        st.error("Username already exists. Please choose a different one.")
    conn.close()

# Authenticate user
def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

# Post a ride
def post_ride(username, pickup, dropoff, datetime_str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO rides (username, pickup, dropoff, datetime) VALUES (?, ?, ?, ?)",
              (username, pickup, dropoff, datetime_str))
    conn.commit()
    conn.close()
    st.success("Ride posted successfully!")

# Search for rides
def search_rides(search_pickup, search_dropoff):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT username, pickup, dropoff, datetime FROM rides
        WHERE pickup LIKE ? AND dropoff LIKE ?
    """, (f"%{search_pickup}%", f"%{search_dropoff}%"))
    results = c.fetchall()
    conn.close()
    return results

# Log in an existing user
def login_user():
    if "username" in st.session_state and st.session_state["username"]:
        st.success(f"Welcome, {st.session_state['username']}!")
        return

    st.subheader("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if authenticate_user(username, password):
            # Save the logged-in user's information in session state
            st.session_state["username"] = username
            st.session_state["logged_in"] = True  # Set the flag
        else:
            st.error("Invalid username or password.")

    # Trigger a UI refresh if the login state changed
    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        st.session_state["logged_in"] = False  # Reset the flag
        st.experimental_set_query_params()  # Clear URL params
        st.rerun()  # Simulate refresh

# Register a new user
def register_user_ui():
    st.subheader("Register")
    username = st.text_input("Username", key="reg_username")
    password = st.text_input("Password", type="password", key="reg_password")
    if st.button("Register"):
        register_user(username, password)

# Post a ride
def post_ride_ui():
    st.subheader("Post a Ride")
    pickup = st.text_input("Pickup Location")
    dropoff = st.text_input("Drop-off Location")
    date = st.date_input("Date")
    time = st.time_input("Time")
    if st.button("Post Ride"):
        datetime_str = datetime.combine(date, time).isoformat()
        post_ride(st.session_state["username"], pickup, dropoff, datetime_str)

# Search for rides
def search_rides_ui():
    st.subheader("Search for Rides")
    search_pickup = st.text_input("Enter Pickup Location")
    search_dropoff = st.text_input("Enter Drop-off Location")
    if st.button("Search"):
        results = search_rides(search_pickup, search_dropoff)
        if results:
            st.write("Matching Rides:")
            for ride in results:
                st.write(f"Driver: {ride[0]}, Pickup: {ride[1]}, Drop-off: {ride[2]}, Date & Time: {ride[3]}")
        else:
            st.warning("No matching rides found.")

# Log out a user
def logout_user():
    if st.sidebar.button("Logout"):
        # Clear the username and set a flag to trigger a refresh
        st.session_state["username"] = None
        st.session_state["logged_out"] = True  # Set the flag

    # Trigger a UI refresh if the logout state changed
    if "logged_out" in st.session_state and st.session_state["logged_out"]:
        st.session_state["logged_out"] = False  # Reset the flag
        st.experimental_set_query_params()  # Clear URL params
        st.rerun()  # Simulate refresh

# Main application logic
def main():
    st.title("Carpool")
    init_db()

    # Initialize session state variables if not set
    if "username" not in st.session_state:
        st.session_state["username"] = None

    if st.session_state["username"]:
        # Show logged-in content
        st.sidebar.write(f"Logged in as: {st.session_state['username']}")
        logout_user()
        action = st.sidebar.selectbox("Choose an Action", ["Post a Ride", "Search for Rides"])
        if action == "Post a Ride":
            post_ride_ui()
        elif action == "Search for Rides":
            search_rides_ui()
    else:
        # Show login or registration page
        st.sidebar.title("Navigation")
        action = st.sidebar.selectbox("Choose an Action", ["Login", "Register"])
        if action == "Login":
            login_user()
        elif action == "Register":
            register_user_ui()

if __name__ == "__main__":
    main()