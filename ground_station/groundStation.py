from flask import Flask
from flask_socketio import SocketIO
import time
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', transport=['websocket'])

is_connected = False
uav_position = None
last_received_time = None

def wait_for_uav():
    global is_connected
    while not is_connected:
        print("Waiting for UAV...")
        time.sleep(2)

@socketio.on('connect')
def on_connect():
    global is_connected
    is_connected = True
    print("Ground Station: UAV connected")

@socketio.on('disconnect')
def on_disconnect():
    global is_connected
    is_connected = False
    print("Ground Station: UAV disconnected")
    threading.Thread(target=wait_for_uav, daemon=True).start()

@socketio.on('position_update')
def on_position_update(data):
    global uav_position, last_received_time
    uav_position = data
    last_received_time = time.time()
    print(f"Ground Station: Received position update: {uav_position}")

@app.route('/')
def index():
    return "Ground Station is running"

if __name__ == '__main__':
    threading.Thread(target=wait_for_uav, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=6000)