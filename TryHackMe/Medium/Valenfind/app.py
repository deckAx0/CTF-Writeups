import os
import sqlite3
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session, send_file, g, flash, jsonify
from seeder import INITIAL_USERS

app = Flask(__name__)
app.secret_key = os.urandom(24)

ADMIN_API_KEY = "CUPID_MASTER_KEY_2024_XOXO"
DATABASE = 'cupid.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    if not os.path.exists(DATABASE):
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    real_name TEXT,
                    email TEXT,
                    phone_number TEXT,
                    address TEXT,
                    bio TEXT,
                    likes INTEGER DEFAULT 0,
                    avatar_image TEXT
                )
            ''')
            
            cursor.executemany('INSERT INTO users (username, password, real_name, email, phone_number, address, bio, likes, avatar_image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', INITIAL_USERS)
            db.commit()
            print("Database initialized successfully.")

@app.template_filter('avatar_color')
def avatar_color(username):
    hash_object = hashlib.md5(username.encode())
    return '#' + hash_object.hexdigest()[:6]

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        try:
            cursor = db.cursor()
            cursor.execute('INSERT INTO users (username, password, bio, real_name, email, avatar_image) VALUES (?, ?, ?, ?, ?, ?)', 
                       (username, password, "New to ValenFind!", "", "", "default.jpg"))
            db.commit()
            
            user_id = cursor.lastrowid
            session['user_id'] = user_id
            session['username'] = username
            session['liked'] = []
            
            flash("Account created! Please complete your profile.")
            return redirect(url_for('complete_profile'))
            
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Username already taken.")
    return render_template('register.html')

@app.route('/complete_profile', methods=['GET', 'POST'])
def complete_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        real_name = request.form['real_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        bio = request.form['bio']
        
        db = get_db()
        db.execute('''
            UPDATE users 
            SET real_name = ?, email = ?, phone_number = ?, address = ?, bio = ?
            WHERE id = ?
        ''', (real_name, email, phone, address, bio, session['user_id']))
        db.commit()
        
        flash("Profile setup complete! Time to find your match.")
        return redirect(url_for('dashboard'))
        
    return render_template('complete_profile.html')

@app.route('/my_profile', methods=['GET', 'POST'])
def my_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    
    if request.method == 'POST':
        real_name = request.form['real_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        bio = request.form['bio']
        
        db.execute('''
            UPDATE users 
            SET real_name = ?, email = ?, phone_number = ?, address = ?, bio = ?
            WHERE id = ?
        ''', (real_name, email, phone, address, bio, session['user_id']))
        db.commit()
        flash("Profile updated successfully! ✅")
        return redirect(url_for('my_profile'))
    
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('edit_profile.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['liked'] = [] 
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    profiles = db.execute('SELECT id, username, likes, bio, avatar_image FROM users WHERE id != ?', (session['user_id'],)).fetchall()
    return render_template('dashboard.html', profiles=profiles, user=session['username'])

@app.route('/profile/<username>')
def profile(username):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    profile_user = db.execute('SELECT id, username, bio, likes, avatar_image FROM users WHERE username = ?', (username,)).fetchone()
    
    if not profile_user:
        return "User not found", 404
        
    return render_template('profile.html', profile=profile_user)

@app.route('/api/fetch_layout')
def fetch_layout():
    layout_file = request.args.get('layout', 'theme_classic.html')
    
    if 'cupid.db' in layout_file or layout_file.endswith('.db'):
        return "Security Alert: Database file access is strictly prohibited."
    if 'seeder.py' in layout_file:
        return "Security Alert: Configuration file access is strictly prohibited."
    
    try:
        base_dir = os.path.join(os.getcwd(), 'templates', 'components')
        file_path = os.path.join(base_dir, layout_file)
        
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error loading theme layout: {str(e)}"

@app.route('/like/<int:user_id>', methods=['POST'])
def like_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'liked' not in session:
        session['liked'] = []
        
    if user_id in session['liked']:
        flash("You already liked this person! Don't be desperate. 😉")
        return redirect(request.referrer)

    db = get_db()
    db.execute('UPDATE users SET likes = likes + 1 WHERE id = ?', (user_id,))
    db.commit()
    
    session['liked'].append(user_id)
    session.modified = True
    
    flash("You sent a like! ❤️")
    return redirect(request.referrer)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('liked', None)
    return redirect(url_for('index'))

@app.route('/api/admin/export_db')
def export_db():
    auth_header = request.headers.get('X-Valentine-Token')
    
    if auth_header == ADMIN_API_KEY:
        try:
            return send_file(DATABASE, as_attachment=True, download_name='valenfind_leak.db')
        except Exception as e:
            return str(e)
    else:
        return jsonify({"error": "Forbidden", "message": "Missing or Invalid Admin Token"}), 403

if __name__ == '__main__':
    if not os.path.exists('templates/components'):
        os.makedirs('templates/components')
    
    with open('templates/components/theme_classic.html', 'w') as f:
        f.write('''
        <div class="bio-box" style="
            background: #ffffff; 
            border: 1px solid #e1e1e1; 
            padding: 20px; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
            text-align: left;">
            <h3 style="color: #2c3e50; border-bottom: 2px solid #ff4757; padding-bottom: 10px; display: inline-block;">__USERNAME__</h3>
            <p style="color: #7f8c8d; font-style: italic; line-height: 1.6;">"__BIO__"</p>
        </div>
        ''')
        
    with open('templates/components/theme_modern.html', 'w') as f:
        f.write('''
        <div class="bio-box modern" style="
            background: #2f3542; 
            color: #dfe4ea; 
            padding: 25px; 
            border-radius: 15px; 
            border-left: 5px solid #2ed573;
            font-family: 'Courier New', monospace;">
            <h3 style="color: #2ed573; text-transform: uppercase; letter-spacing: 2px; margin-top: 0;">__USERNAME__</h3>
            <p style="line-height: 1.5;">> __BIO__<span style="animation: blink 1s infinite;">_</span></p>
            <style>@keyframes blink { 50% { opacity: 0; } }</style>
        </div>
        ''')

    with open('templates/components/theme_romance.html', 'w') as f:
        f.write('''
        <div class="bio-box romance" style="
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%); 
            color: #c0392b; 
            padding: 30px; 
            border-radius: 50px 0 50px 0; 
            border: 2px dashed #ff6b81;
            text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 10px;">💖 💘 💖</div>
            <h3 style="font-family: 'Brush Script MT', cursive; font-size: 2.5rem; margin: 10px 0;">__USERNAME__</h3>
            <p style="font-weight: bold; font-size: 1.1rem;">✨ __BIO__ ✨</p>
            <div style="font-size: 1.5rem; margin-top: 15px;">💌</div>
        </div>
        ''')

    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)
