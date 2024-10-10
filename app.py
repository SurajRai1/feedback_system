from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from collections import Counter
import json

app = Flask(__name__)
app.secret_key = 'secret-key'

# SQLite Database setup
def init_db():
    conn = sqlite3.connect('feedback.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    course_name TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comments TEXT
                )''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    name = request.form['name']
    email = request.form['email']
    course_name = request.form['course_name']
    rating = request.form['rating']
    comments = request.form['comments']

    if not name or not email or not course_name or not rating:
        flash('All fields are required!')
        return redirect(url_for('index'))

    conn = sqlite3.connect('feedback.db')
    c = conn.cursor()
    c.execute('INSERT INTO feedback (name, email, course_name, rating, comments) VALUES (?, ?, ?, ?, ?)', 
              (name, email, course_name, rating, comments))
    conn.commit()
    conn.close()

    flash('Feedback submitted successfully!')
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    conn = sqlite3.connect('feedback.db')
    c = conn.cursor()

    c.execute('SELECT course_name, AVG(rating) as avg_rating FROM feedback GROUP BY course_name')
    ratings = c.fetchall()

    c.execute('SELECT comments FROM feedback')
    comments = [row[0] for row in c.fetchall()]

    # Extract common themes in comments
    words = ' '.join(comments).split()
    common_themes = Counter(words).most_common(5)

    conn.close()

    return render_template('admin.html', ratings=ratings, common_themes=json.dumps(common_themes))

if __name__ == '__main__':
    app.run(debug=True)
