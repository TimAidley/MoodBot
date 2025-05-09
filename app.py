from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
from datetime import datetime
import csv
import os

app = Flask(__name__)

# Ensure the instance folder exists
os.makedirs(app.instance_path, exist_ok=True)
DB_PATH = os.path.join(app.instance_path, 'moods.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS moods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mood TEXT NOT NULL,
        timestamp DATETIME NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

@app.route('/')
def index():
    # Get the list of moods from the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT mood FROM moods ORDER BY mood")
    existing_moods = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Default moods if none exist yet
    default_moods = ['happy', 'sleeping', 'angry', 'grumpy', 'excited', 'calm']
    
    # Combine existing and default moods, removing duplicates
    all_moods = list(set(existing_moods + default_moods))
    all_moods.sort()
    
    return render_template('index.html', moods=all_moods)

@app.route('/record', methods=['POST'])
def record_mood():
    mood = request.form.get('mood')
    timestamp = datetime.now()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO moods (mood, timestamp) VALUES (?, ?)", 
                  (mood, timestamp))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/history')
def history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT mood, timestamp FROM moods ORDER BY timestamp DESC LIMIT 100")
    moods = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return render_template('history.html', moods=moods)

@app.route('/export')
def export_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT mood, timestamp FROM moods ORDER BY timestamp")
    rows = cursor.fetchall()
    conn.close()
    
    # Create a CSV file
    export_path = os.path.join(app.instance_path, 'mood_export.csv')
    with open(export_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Mood', 'Timestamp'])  # Header
        writer.writerows(rows)
    
    return send_file(export_path, as_attachment=True, 
                     download_name='mood_export.csv',
                     mimetype='text/csv')

@app.route('/add_mood', methods=['POST'])
def add_mood():
    new_mood = request.form.get('new_mood')
    if new_mood and new_mood.strip():
        # No need to store in a separate table, just record it
        timestamp = datetime.now()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO moods (mood, timestamp) VALUES (?, ?)", 
                      (new_mood.strip(), timestamp))
        conn.commit()
        conn.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
