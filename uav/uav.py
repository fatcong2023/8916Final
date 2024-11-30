import socketio
import json
import time
import threading
import signal
import sys
import random
import math

# Create a Socket.IO client
sio = socketio.Client()
GROUND_STATION_URL = "http://localhost:6000"

uav_position = {"latitude": 45.310245556654614, "longitude": -75.91365434011453, "altitude": 300}
is_connected = False
stop_threads = False

def generate_random_waypoint(current_position, radius_km=5):
    """Generate a random waypoint within a given radius (in km) from the current position."""
    radius_deg = radius_km / 111  # Approximate conversion from km to degrees
    angle = random.uniform(0, 2 * math.pi)
    dx = radius_deg * math.cos(angle)
    dy = radius_deg * math.sin(angle)
    return {
        "latitude": current_position["latitude"] + dx,
        "longitude": current_position["longitude"] + dy,
        "altitude": current_position["altitude"]
    }

def simulate_linear_movement(current, target, speed_mps=10):
    """Simulate linear movement of UAV toward the target at a given speed (m/s)."""
    distance = math.sqrt((target["latitude"] - current["latitude"])**2 + (target["longitude"] - current["longitude"])**2)
    step = speed_mps / 111000  # Convert speed from m/s to degrees per second
    if distance < step:
        return target
    ratio = step / distance
    current["latitude"] += (target["latitude"] - current["latitude"]) * ratio
    current["longitude"] += (target["longitude"] - current["longitude"]) * ratio
    return current

def uav_simulation():
    global uav_position, is_connected, stop_threads
    while not stop_threads:
        if not is_connected:
            print("UAV: Disconnected from Ground Station. Retrying...")
            time.sleep(5)
            continue

        next_wp = generate_random_waypoint(uav_position)
        print(f"UAV: New waypoint generated: {next_wp}")

        while uav_position != next_wp and not stop_threads:
            uav_position = simulate_linear_movement(uav_position, next_wp)
            try:
                sio.emit('position_update', uav_position)
                print(f"UAV: Sent position update: {uav_position}")
            except Exception as e:
                print(f"UAV: Failed to send position update: {e}")
                is_connected = False
                break
            time.sleep(1)

        if uav_position == next_wp:
            print(f"UAV: Reached waypoint {next_wp}")
            time.sleep(60)  # Stay at the waypoint for 1 minute

@sio.event
def connect():
    global is_connected
    is_connected = True
    print("UAV: Connected to Ground Station")
    threading.Thread(target=uav_simulation, daemon=True).start()

@sio.event
def disconnect():
    global is_connected
    is_connected = False
    print("UAV: Disconnected from Ground Station")

def signal_handler(sig, frame):
    global stop_threads
    print("\nUAV: Shutting down...")
    stop_threads = True
    sio.disconnect()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    while not stop_threads:
        try:
            # Connect with websocket transport only
            sio.connect(GROUND_STATION_URL, transports=['websocket'])
            sio.wait()
        except Exception as e:
            print(f"UAV: Failed to connect to Ground Station - {e}")
            time.sleep(5)