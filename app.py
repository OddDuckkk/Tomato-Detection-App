from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Initialize counters
counters = {
    'fresh': 0,
    'rotten': 0,
    'last_reset': datetime.now().date()
}

# Lock for thread-safe counter updates
counter_lock = threading.Lock()

def reset_counters():
    global counters
    while True:
        now = datetime.now()
        if now.date() != counters['last_reset']:
            with counter_lock:
                counters['fresh'] = 0
                counters['rotten'] = 0
                counters['last_reset'] = now.date()
        # Sleep for a short period to reduce CPU usage
        time.sleep(60)

@app.route('/update', methods=['POST'])
def update_counter():
    global counters
    # Simulated detection result
    detection_result = request.json  # {'type': 'fresh'} or {'type': 'rotten'}
    
    with counter_lock:
        if detection_result['type'] == 'fresh':
            counters['fresh'] += 1
        elif detection_result['type'] == 'rotten':
            counters['rotten'] += 1

    return jsonify(success=True)

@app.route('/count', methods=['GET'])
def get_count():
    global counters
    return jsonify(counters)

if __name__ == '__main__':
    app.run(debug=True)
    # Start the reset counters thread
    reset_thread = threading.Thread(target=reset_counters, daemon=True)
    reset_thread.start()
    app.run(host='0.0.0.0', port=5000)
