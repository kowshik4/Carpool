import streamlit as st
import sqlite3
import pandas as pd
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
        driver_name TEXT NOT NULL,
        pickup_location TEXT NOT NULL,
        dropoff_location TEXT NOT NULL,
        ride_date DATE NOT NULL,
        ride_time TIME NOT NULL,
        seats_available INTEGER NOT NULL,
        price INTEGER NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    )
    """)
    # Create bookings table
    c.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ride_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        FOREIGN KEY (ride_id) REFERENCES rides (id),
        FOREIGN KEY (username) REFERENCES users (username)
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
def post_ride(username, pickup, dropoff, datetime_str, seats_available, price):
    try:
        # Convert datetime string to date and time
        ride_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        ride_date = ride_datetime.date().strftime("%Y-%m-%d")  # YYYY-MM-DD
        ride_time = ride_datetime.time().strftime("%H:%M:%S")  # HH:MM:SS

        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO rides (driver_name, pickup_location, dropoff_location, ride_date, ride_time, seats_available, price, active) 
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (username, pickup, dropoff, ride_date, ride_time, seats_available, price))
            conn.commit()

        st.success("✅ Ride posted successfully!")
        st.write(f"Debug: Ride details - {username}, {pickup}, {dropoff}, {ride_date}, {ride_time}, {seats_available}, {price}")

    except ValueError:
        st.error("❌ Invalid date format! Please use YYYY-MM-DD HH:MM.")
        st.write(f"Debug: ValueError - {datetime_str}")

    except sqlite3.Error as e:
        st.error(f"❌ Database error: {e}")
        st.write(f"Debug: sqlite3.Error - {e}")

# Search for rides
def search_rides(search_pickup, search_dropoff):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT driver_name, pickup_location, dropoff_location, ride_date, ride_time, seats_available, price FROM rides
        WHERE pickup_location LIKE ? AND dropoff_location LIKE ? AND active = 1
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
    with st.form("post_ride_form"):
        driver_name = st.text_input("Driver Name")
        pickup_location = st.text_input("Pickup Location")
        dropoff_location = st.text_input("Dropoff Location")
        ride_date = st.date_input("Ride Date")
        ride_time = st.time_input("Ride Time")
        seats_available = st.number_input("Seats Available", min_value=1, max_value=10, step=1)
        price = st.number_input("Price ($)", min_value=1, step=1)

        submit_button = st.form_submit_button("Post Ride")
    
    if submit_button:
        if driver_name and pickup_location and dropoff_location:
            save_ride(driver_name, pickup_location, dropoff_location, ride_date, ride_time, seats_available, price)
            st.success("Ride posted successfully!")
        else:
            st.error("Please fill in all required fields.")

# Function to save ride to the database
def save_ride(driver_name, pickup_location, dropoff_location, ride_date, ride_time, seats_available, price):
    conn = sqlite3.connect("carpooling.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO rides (driver_name, pickup_location, dropoff_location, ride_date, ride_time, seats_available, price, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (driver_name, pickup_location, dropoff_location, ride_date, ride_time.strftime("%H:%M:%S"), seats_available, price))
        conn.commit()
        st.write(f"Debug: Ride saved - {driver_name}, {pickup_location}, {dropoff_location}, {ride_date}, {ride_time.strftime('%H:%M:%S')}, {seats_available}, {price}")
    except sqlite3.Error as e:
        st.error(f"❌ Database error: {e}")
        st.write(f"Debug: sqlite3.Error - {e}")
    finally:
        conn.close()

# Function to get all rides
def get_all_rides():
    conn = sqlite3.connect(DB_FILE)
    query = """
    SELECT 
        id AS "Ride ID", 
        driver_name AS "Driver", 
        pickup_location AS "Pickup Location", 
        dropoff_location AS "Dropoff Location", 
        ride_date AS "Date", 
        ride_time AS "Time", 
        seats_available AS "Seats Available", 
        price AS "Price ($)"
    FROM rides
    WHERE active = 1
    """
    rides_df = pd.read_sql_query(query, conn)
    conn.close()
    return rides_df

# Function to display all rides
def display_all_rides_ui():
    st.subheader("Available Rides")
    rides_df = get_all_rides()
    if not rides_df.empty:
        st.dataframe(rides_df, use_container_width=True)
    else:
        st.info("No rides available at the moment.")

# Function to search for rides (Stub)
def search_rides_ui():
    st.subheader("Search for Rides")

    # User input fields for filtering rides
    pickup = st.text_input("Enter Pickup Location:")
    dropoff = st.text_input("Enter Dropoff Location:")
    ride_date = st.date_input("Select Ride Date:")

    if st.button("Search Rides"):
        conn = sqlite3.connect("carpooling.db")
        query = """
        SELECT 
            id AS "Ride ID", 
            driver_name AS "Driver", 
            pickup_location AS "Pickup Location", 
            dropoff_location AS "Dropoff Location", 
            ride_date AS "Date", 
            ride_time AS "Time", 
            seats_available AS "Seats Available", 
            price AS "Price ($)"
        FROM rides 
        WHERE pickup_location LIKE ? 
        AND dropoff_location LIKE ? 
        AND ride_date = ?
        """

        # Execute query with parameters
        df = pd.read_sql_query(query, conn, params=('%' + pickup + '%', '%' + dropoff + '%', ride_date))
        conn.close()

        # Display results
        if not df.empty:
            st.write("### Available Rides:")
            st.dataframe(df)
        else:
            st.warning("No rides found for the given search criteria.")

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

# Function to book a ride
def book_ride(ride_id, username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Check if there are available seats
        cursor.execute("SELECT seats_available FROM rides WHERE id = ?", (ride_id,))
        seats_available = cursor.fetchone()[0]
        if seats_available > 0:
            # Insert booking
            cursor.execute("INSERT INTO bookings (ride_id, username) VALUES (?, ?)", (ride_id, username))
            # Update seats available
            cursor.execute("UPDATE rides SET seats_available = seats_available - 1 WHERE id = ?", (ride_id,))
            conn.commit()

            # Check if seats are now zero and set the ride as inactive if so
            cursor.execute("SELECT seats_available FROM rides WHERE id = ?", (ride_id,))
            seats_available = cursor.fetchone()[0]
            if seats_available == 0:
                cursor.execute("UPDATE rides SET active = 0 WHERE id = ?", (ride_id,))
                conn.commit()

            st.success("Ride booked successfully!")
        else:
            st.error("No seats available for this ride.")
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
    finally:
        conn.close()

def book_ride_ui():
    st.subheader("Book a Ride")
    ride_id = st.number_input("Enter Ride ID", min_value=1, step=1)
    if st.button("Book Ride"):
        if "username" in st.session_state and st.session_state["username"]:
            book_ride(ride_id, st.session_state["username"])
        else:
            st.error("You need to be logged in to book a ride.")

def get_user_rides(username):
    conn = sqlite3.connect(DB_FILE)
    query = """
    SELECT 
        id AS "Ride ID", 
        driver_name AS "Driver", 
        pickup_location AS "Pickup Location", 
        dropoff_location AS "Dropoff Location", 
        ride_date AS "Date", 
        ride_time AS "Time", 
        seats_available AS "Seats Available", 
        price AS "Price ($)"
    FROM rides
    WHERE driver_name = ?
    """
    rides_df = pd.read_sql_query(query, conn, params=(username,))
    conn.close()
    return rides_df

def get_user_bookings(username):
    conn = sqlite3.connect(DB_FILE)
    query = """
    SELECT 
        b.id AS "Booking ID", 
        r.id AS "Ride ID", 
        r.driver_name AS "Driver", 
        r.pickup_location AS "Pickup Location", 
        r.dropoff_location AS "Dropoff Location", 
        r.ride_date AS "Date", 
        r.ride_time AS "Time", 
        r.price AS "Price ($)"
    FROM bookings b
    JOIN rides r ON b.ride_id = r.id
    WHERE b.username = ?
    """
    bookings_df = pd.read_sql_query(query, conn, params=(username,))
    conn.close()
    return bookings_df

def ride_history_ui():
    st.subheader("Your Ride History")
    
    if "username" in st.session_state and st.session_state["username"]:
        username = st.session_state["username"]
        
        st.write("### Your Posted Rides")
        user_rides_df = get_user_rides(username)
        if not user_rides_df.empty:
            st.dataframe(user_rides_df, use_container_width=True)
        else:
            st.info("You have not posted any rides.")
        
        st.write("### Your Booked Rides")
        user_bookings_df = get_user_bookings(username)
        if not user_bookings_df.empty:
            st.dataframe(user_bookings_df, use_container_width=True)
        else:
            st.info("You have not booked any rides.")
    else:
        st.error("You need to be logged in to view your ride history.")

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

        st.sidebar.title("Menu")
        menu_options = ["View Rides", "Post Ride", "Search Rides", "Book Ride", "Ride History"]
        choice = st.sidebar.radio("Select an action:", menu_options)

        # Display the selected action
        if choice == "View Rides":
            display_all_rides_ui()
        elif choice == "Post Ride":
            post_ride_ui()
        elif choice == "Search Rides":
            search_rides_ui()
        elif choice == "Book Ride":
            book_ride_ui()
        elif choice == "Ride History":
            ride_history_ui()
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