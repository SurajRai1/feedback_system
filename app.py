from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from collections import Counter
import json
import os
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Ensure the instance folder exists
INSTANCE_PATH = Path(__file__).parent / 'instance'
INSTANCE_PATH.mkdir(exist_ok=True)

# Database path
DB_PATH = INSTANCE_PATH / 'feedback.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# SQLite Database setup
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    course_name TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comments TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    name = request.form['name']
    email = request.form['email']
    course_name = request.form['course_name']
    rating = request.form['rating']
    comments = request.form['comments']

    if not name or not email or not course_name or not rating:
        flash('All fields are required!', 'error')
        return redirect(url_for('index'))

    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO feedback (name, email, course_name, rating, comments) VALUES (?, ?, ?, ?, ?)', 
                (name, email, course_name, rating, comments))
        conn.commit()
        conn.close()
        return redirect(url_for('thank_you'))
    except Exception as e:
        app.logger.error(f"Database error: {str(e)}")
        flash('An error occurred while submitting your feedback. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/admin')
def admin():
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get course ratings
        c.execute('''
            SELECT course_name, 
                   AVG(rating) as avg_rating,
                   COUNT(*) as total_ratings
            FROM feedback 
            GROUP BY course_name
            ORDER BY avg_rating DESC
        ''')
        ratings = c.fetchall()

        # Get recent comments
        c.execute('SELECT comments FROM feedback WHERE comments IS NOT NULL AND comments != ""')
        comments = [row[0] for row in c.fetchall()]

        # Extract common themes in comments
        words = ' '.join(comments).split()
        common_themes = Counter(words).most_common(5)

        conn.close()

        return render_template('admin.html', 
                            ratings=[(r[0], float(r[1])) for r in ratings],
                            common_themes=json.dumps(common_themes))
    except Exception as e:
        app.logger.error(f"Admin dashboard error: {str(e)}")
        return "Error loading dashboard", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
