import tkinter as tk
from tkinter import Label, Button, ttk
import gps
import folium
import webbrowser
import sqlite3
from math import radians, cos, sin, sqrt, atan2
import threading
import time

# Database Setup
DB_FILE = "golf_holes.db"

def get_holes():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, lat, lon FROM holes")
    holes = cursor.fetchall()
    conn.close()
    return holes

# Haversine Formula for Distance Calculation
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c * 1000  # Convert to meters

# Get GPS Data
def get_gps_data():
    session = gps.gps(mode=gps.WATCH_ENABLE)
    while True:
        session.next()
        if session.fix.mode >= 2:  # 2D Fix (Lat/Lon available)
            return session.fix.latitude, session.fix.longitude

# Generate Map and Update Distance
def update_distance():
    global selected_hole
    lat, lon = get_gps_data()

    # Get selected hole details
    hole_id = hole_var.get()
    hole_lat, hole_lon = next((h[2], h[3]) for h in get_holes() if h[0] == hole_id)

    distance = haversine(lat, lon, hole_lat, hole_lon)

    # Create a map centered on player's position
    golf_map = folium.Map(location=[lat, lon], zoom_start=18, tiles="Stamen Terrain")

    # Add player marker
    folium.Marker([lat, lon], tooltip="You", icon=folium.Icon(color="blue")).add_to(golf_map)

    # Add hole marker
    folium.Marker([hole_lat, hole_lon], tooltip="Hole", icon=folium.Icon(color="red")).add_to(golf_map)

    # Save and open the map
    map_path = "/tmp/golf_map.html"
    golf_map.save(map_path)
    webbrowser.open("file://" + map_path)

    # Update Distance in GUI
    distance_label.config(text=f"Distance to {selected_hole.get()}: {distance:.2f} meters")

# Auto Refresh Every 5 Seconds
def auto_refresh():
    while True:
        update_distance()
        time.sleep(5)

# GUI Setup
root = tk.Tk()
root.title("Golf GPS Distance Tracker")

Label(root, text="Golf GPS Tracker", font=("Arial", 16)).pack(pady=10)

# Dropdown for hole selection
holes = get_holes()
hole_var = tk.IntVar()
hole_var.set(holes[0][0])  # Default to first hole

selected_hole = ttk.Combobox(root, values=[h[1] for h in holes], state="readonly")
selected_hole.pack(pady=10)

# Distance label
distance_label = Label(root, text="Distance to Hole: Calculating...", font=("Arial", 14))
distance_label.pack(pady=10)

# Update button
Button(root, text="Update Now", command=update_distance, font=("Arial", 12)).pack(pady=10)

# Start Auto-Refresh in Background
threading.Thread(target=auto_refresh, daemon=True).start()

root.mainloop()
