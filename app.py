from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import threading
import time
import pytz
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tomato_counts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the model for daily counts
class TomatoCount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    fresh_count = db.Column(db.Integer, nullable=False)
    rotten_count = db.Column(db.Integer, nullable=False)

#Define Timezone
timezone = 'Asia/Makassar'
local_tz = pytz.timezone(timezone)

# Initialize counters
time_init = datetime.now(local_tz)
counters = {
    'fresh': 0,
    'rotten': 0,
    'last_reset': time_init.date()
}

# Lock for thread-safe counter updates
counter_lock = threading.Lock()

def reset_counters():
    global counters
    while True:
        now = datetime.now(local_tz)
        print(f"Current time: {now}")
        print(f"Last reset: {counters['last_reset']}")
        now = datetime.now(local_tz)
        if now.date() != counters['last_reset']:
            with counter_lock:
                # Save the counts to the database before resetting
                new_record = TomatoCount(
                    date=counters['last_reset'],
                    fresh_count=counters['fresh'],
                    rotten_count=counters['rotten']
                )
                db.session.add(new_record)
                db.session.commit()

                # Reset the counters
                counters['fresh'] = 0
                counters['rotten'] = 0
                counters['last_reset'] = now.date()
        # Sleep for a short period to reduce CPU usage
        time.sleep(60)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update', methods=['POST'])
def update_counter():
    global counters
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
    # Ensure the database and table are created
    with app.app_context():
        db.create_all()

    # Start the reset counters thread
    reset_thread = threading.Thread(target=reset_counters, daemon=True)
    reset_thread.start()

    # Run the Flask application
    app.run(host='0.0.0.0', port=5000)
