import cv2
import requests
import serial
import threading
import time
import netifaces as ni  # <-- Added to isolate the LAN card
from flask import Flask, Response, render_template_string, request as flask_request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------
# DYNAMIC LAN SELECTION (Forces application onto the wire)
# ---------------------------------------------------------
def get_lan_ip():
    try:
        # 'eth0' targets the physical copper Ethernet port on the Raspberry Pi
        ni.ifaddresses('eth0')
        ip = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
        return ip
    except (ValueError, KeyError, IndexError):
        print("⚠️ LAN Warning: Cable disconnected or static IP not assigned to eth0.")
        print("Falling back to localhost loopback for testing safety...")
        return "127.0.0.1"

PI_IP = get_lan_ip() 
print(f"🔒 [LAN LOCKED] Routing all motor data and dashboard traffic through: {PI_IP}")

# Arduino Serial Configuration
arduino_port = '/dev/ttyUSB0'  # Change to '/dev/ttyACM0' if needed
baud_rate = 9600

# Global variable to cache the latest line for the chart data engine
global_latest_line = "No data yet"

# ---------------------------------------------------------
# BACKGROUND SERIAL WORKER
# ---------------------------------------------------------
def serial_worker():
    global global_latest_line
    while True:
        try:
            print(f"[SERIAL] Connecting to Nano on {arduino_port}...")
            ser = serial.Serial(arduino_port, baud_rate, timeout=1)
            ser.reset_input_buffer()
            print("[SERIAL] Connected successfully!")
            while True:
                if ser.in_waiting > 0:
                    raw_line = ser.readline()
                    global_latest_line = raw_line.decode('utf-8', errors='ignore').rstrip()
                time.sleep(0.02)
        except Exception as e:
            global_latest_line = f"Serial Error: {e}"
            time.sleep(3)

# Spin up the background thread immediately
threading.Thread(target=serial_worker, daemon=True).start()
# ---------------------------------------------------------

# 2. TALK DIRECTLY TO THE LOCAL USB WEBCAM HARDWARE
print("\n[STARTING UPHUB] Accessing local Pi webcam hardware directly...")
cap = cv2.VideoCapture(0) 
print("[CONNECTED] Webcam hardware grabbed successfully!\n")

def generate_serial_stream():
    """Generates a live text loop back to the iframe log window"""
    last_seen = ""
    while True:
        if global_latest_line != last_seen:
            last_seen = global_latest_line
            yield f"{last_seen}<br>\n"
        time.sleep(0.1)

HTML_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>Robot Control Center</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #1e1e1e; color: white; margin: 0; padding: 20px; }
        .container { display: flex; flex-direction: column; align-items: center; gap: 20px; }
        img { border: 4px solid #333; border-radius: 8px; max-width: 640px; background: #000; width: 100%; }
        
        .dashboard-row {
            display: flex;
            flex-direction: column;
            gap: 20px;
            width: 100%;
            max-width: 640px;
        }
        .console-container, .chart-container {
            background: #0a0a0a;
            border: 2px solid #333;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            text-align: left;
            box-sizing: border-box;
            width: 100%;
        }
        .console-container h3, .chart-container h3 { 
            font-size: 16px; 
            color: #ffffff; 
            margin-top: 0; 
            margin-bottom: 10px; 
            border-bottom: 1px solid #333; 
            padding-bottom: 5px; 
        }
        iframe {
            width: 100%;
            height: 90px;
            border: none;
            background: transparent;
        }
        canvas {
            width: 100% !important;
            height: 220px !important;
        }

        .controls { display: grid; grid-template-columns: repeat(3, 80px); grid-template-rows: repeat(3, 80px); gap: 10px; justify-content: center; }
        button { background: #444; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }
        button:active { background: #00ff00; color: black; }
        .hidden { visibility: hidden; }
    </style>
</head>
<body>
    <h1>ML Video Feed & Robot Controls</h1>
    <div class="container">
        <img src="/video_feed" />
        
        <div class="dashboard-row">
            <div class="chart-container">
                <h3>[ Gas Concentration Timeline ]</h3>
                <canvas id="gasChart"></canvas>
            </div>

            <div class="console-container">
                <h3>[ Live Gas Telemetry Stream ]</h3>
                <iframe id="stream-frame" src=""></iframe>
            </div>
        </div>

        <h3>Control Pad</h3>
        <div class="controls">
            <button class="hidden"></button>
            <button onmousedown="sendCmd('forward')" onmouseup="sendCmd('stop')">▲</button>
            <button class="hidden"></button>
            <button onmousedown="sendCmd('left')" onmouseup="sendCmd('stop')">◀</button>
            <button onmousedown="sendCmd('stop')">■</button>
            <button onmousedown="sendCmd('right')" onmouseup="sendCmd('stop')">▶</button>
            <button class="hidden"></button>
            <button onmousedown="sendCmd('backward')" onmouseup="sendCmd('stop')">▼</button>
            <button class="hidden"></button>
        </div>
    </div>
    <script>
        function sendCmd(direction) {
            fetch('/move', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'direction=' + direction
            });
        }

        var currentIP = window.location.hostname;
        var currentPort = window.location.port;
        document.getElementById('stream-frame').src = "http://" + currentIP + ":" + currentPort + "/stream";

        // --- CHART.JS CONFIGURATION ---
        const ctx = document.getElementById('gasChart').getContext('2d');
        const maxDataPoints = 30; 
        
        const gasChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [], 
                datasets: [
                    { label: 'MQ-7 (CO)', data: [], borderColor: '#ff4444', borderWidth: 2, tension: 0.2, pointRadius: 0 },
                    { label: 'MQ-135 (Air Quality)', data: [], borderColor: '#33b5e5', borderWidth: 2, tension: 0.2, pointRadius: 0 },
                    { label: 'MQ-4 (Methane)', data: [], borderColor: '#ffbb33', borderWidth: 2, tension: 0.2, pointRadius: 0 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { color: '#222' }, ticks: { color: '#aaa' } },
                    y: { grid: { color: '#222' }, ticks: { color: '#aaa' }, beginAtZero: true }
                },
                plugins: {
                    legend: { labels: { color: 'white' } }
                }
            }
        });

        function queryChartData() {
            fetch('/sensor_json')
                .then(res => res.json())
                .then(data => {
                    let parts = data.raw.split('|');
                    
                    if (parts.length >= 3) {
                        let timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                        
                        let mq7Value   = parseFloat(parts[0].split(':').pop().trim());
                        let mq135Value = parseFloat(parts[1].split(':').pop().trim());
                        let mq4Value   = parseFloat(parts[2].split(':').pop().trim());

                        if (!isNaN(mq7Value) && !isNaN(mq135Value) && !isNaN(mq4Value)) {
                            gasChart.data.labels.push(timestamp);
                            gasChart.data.datasets[0].data.push(mq7Value);   
                            gasChart.data.datasets[1].data.push(mq135Value); 
                            gasChart.data.datasets[2].data.push(mq4Value);   
                            
                            if (gasChart.data.labels.length > maxDataPoints) {
                                gasChart.data.labels.shift();
                                gasChart.data.datasets[0].data.shift();
                                gasChart.data.datasets[1].data.shift();
                                gasChart.data.datasets[2].data.shift();
                            }
                            gasChart.update('none'); 
                        }
                    }
                })
                .catch(err => console.log("Chart sync skip"));
        }
        
        setInterval(queryChartData, 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/stream')
def stream():
    custom_white_css = "<style>body{color:#ffffff; font-family:'Courier New',monospace; font-size:14px; background:transparent; margin:0; line-height:1.4;}</style>"
    def streaming_wrapper():
        yield custom_white_css
        for data_line in generate_serial_stream():
            yield data_line
    return Response(streaming_wrapper(), mimetype='text/html')

@app.route('/sensor_json')
def sensor_json():
    return jsonify(raw=global_latest_line)

@app.route('/move', methods=['POST'])
def move_robot():
    direction = flask_request.form.get('direction')
    try:
        # Relies on the exact local static LAN address assigned above
        requests.post(f"http://{PI_IP}:8000/motor", data={'direction': direction}, timeout=0.1)
    except requests.exceptions.RequestException:
        pass 
    return "OK", 200

def gen_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        
        cv2.putText(frame, "ML Engine: Live (LAN Mode)", (15, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Flask is explicitly forced to use the LAN interface IP here instead of 0.0.0.0
    app.run(host=PI_IP, port=2712, threaded=True)
