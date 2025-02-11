import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# Database setup
def init_db():
    conn = sqlite3.connect('carpool.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS rides
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, origin TEXT, destination TEXT, date TEXT, seats INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User authentication
def authenticate_user(username, password):
    conn = sqlite3.connect('carpool.db')
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user and user[1] == hash_password(password):
        return user[0]
    return None

# User registration
def register_user(username, password):
    conn = sqlite3.connect('carpool.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# Post a ride
def post_ride(user_id, origin, destination, date, seats):
    conn = sqlite3.connect('carpool.db')
    c = conn.cursor()
    c.execute("INSERT INTO rides (user_id, origin, destination, date, seats) VALUES (?, ?, ?, ?, ?)",
              (user_id, origin, destination, date, seats))
    conn.commit()
    conn.close()

# Get all rides
def get_all_rides():
    conn = sqlite3.connect('carpool.db')
    c = conn.cursor()
    c.execute("SELECT rides.id, users.username, rides.origin, rides.destination, rides.date, rides.seats FROM rides JOIN users ON rides.user_id = users.id")
    rides = c.fetchall()
    conn.close()
    return rides

# Get filtered rides
def get_filtered_rides(origin, destination, date):
    conn = sqlite3.connect('carpool.db')
    c = conn.cursor()
    query = "SELECT rides.id, users.username, rides.origin, rides.destination, rides.date, rides.seats FROM rides JOIN users ON rides.user_id = users.id WHERE 1=1"
    params = []
    if origin:
        query += " AND rides.origin = ?"
        params.append(origin)
    if destination:
        query += " AND rides.destination = ?"
        params.append(destination)
    if date:
        query += " AND rides.date = ?"
        params.append(date)
    c.execute(query, params)
    rides = c.fetchall()
    conn.close()
    return rides

# Streamlit app
def main():
    st.title("Car Pooling App")

    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    menu = ["Home", "Login", "Register", "Post a Ride", "View Rides"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Home")
        st.write("Welcome to the Car Pooling App!")

    elif choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user_id = authenticate_user(username, password)
            if user_id:
                st.session_state.user_id = user_id
                st.success("Logged in as {}".format(username))
            else:
                st.error("Invalid username or password")

    elif choice == "Register":
        st.subheader("Register")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if register_user(username, password):
                st.success("Registration successful! Please login.")
            else:
                st.error("Username already exists")

    elif choice == "Post a Ride":
        if st.session_state.user_id:
            st.subheader("Post a Ride")
            origin = st.text_input("Origin")
            destination = st.text_input("Destination")
            date = st.date_input("Date")
            seats = st.number_input("Seats available", min_value=1, max_value=10)
            if st.button("Post Ride"):
                post_ride(st.session_state.user_id, origin, destination, date.strftime('%Y-%m-%d'), seats)
                st.success("Ride posted successfully!")
        else:
            st.warning("Please login to post a ride")

    elif choice == "View Rides":
        st.subheader("View Rides")
        origin_filter = st.text_input("Filter by Origin")
        destination_filter = st.text_input("Filter by Destination")
        date_filter = st.date_input("Filter by Date")
        if st.button("Search Rides"):
            rides = get_filtered_rides(origin_filter, destination_filter, date_filter.strftime('%Y-%m-%d') if date_filter else None)
            if rides:
                st.write("### Available Rides")
                for ride in rides:
                    st.write(f"""
                    - **Ride ID**: {ride[0]}  
                    - **Posted by**: {ride[1]}  
                    - **From**: {ride[2]}  
                    - **To**: {ride[3]}  
                    - **Date**: {ride[4]}  
                    - **Seats Available**: {ride[5]}  
                    """)
            else:
                st.info("No rides match your filters.")
        else:
            rides = get_all_rides()
            if rides:
                st.write("### All Available Rides")
                for ride in rides:
                    st.write(f"""
                    - **Ride ID**: {ride[0]}  
                    - **Posted by**: {ride[1]}  
                    - **From**: {ride[2]}  
                    - **To**: {ride[3]}  
                    - **Date**: {ride[4]}  
                    - **Seats Available**: {ride[5]}  
                    """)
            else:
                st.info("No rides available at the moment.")

if __name__ == "__main__":
    main()