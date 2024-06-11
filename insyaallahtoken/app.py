from flask import Flask, jsonify, request, redirect, url_for, session, render_template, session
from datetime import datetime
import requests
import time
import jwt
from flask_cors import CORS
from flask_mysqldb import MySQL
import bcrypt
import pika


app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'manajemen_user'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

from rujukan import rujukan_app
from obat import obat_app
from resepobat import resepobat_app

mysql = MySQL(app)

JWT_SECRET = 'your_jwt_secret'
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRES_IN = 1000  # 30 seconds for demo
REFRESH_TOKEN_EXPIRES_IN = 3600  # 1 hour

tokens = {}  # In-memory store for tokens

app.register_blueprint(rujukan_app, url_prefix='/api/rujukan')
app.register_blueprint(obat_app, url_prefix='/api/Obat')
app.register_blueprint(resepobat_app, url_prefix='/api/resepobat')


def generate_token(user_id, role, name, expires_in, token_type='access'):
    payload = {
        'user_id': user_id,
        'role': role,
        'name': name,
        'exp': time.time() + expires_in,
        'type': token_type
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_access_token(user_id, role, name):
    return generate_token(user_id, role, name, ACCESS_TOKEN_EXPIRES_IN, 'access')

def generate_refresh_token(user_id, role, name):
    return generate_token(user_id, role, name, REFRESH_TOKEN_EXPIRES_IN, 'refresh')

def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def refresh_access_token(user_id):
    refresh_token = tokens[user_id]['refresh_token']
    decoded = decode_token(refresh_token)
    if decoded and decoded['type'] == 'refresh':
        role = decoded['role']
        name = decoded['name']
        access_token = generate_access_token(user_id, role, name)
        tokens[user_id]['access_token'] = access_token
        tokens[user_id]['expires_at'] = time.time() + ACCESS_TOKEN_EXPIRES_IN
        return access_token
    else:
        raise Exception("Invalid or expired refresh token")
    
def get_valid_access_token(user_id):
    if user_id in tokens:
        if time.time() >= tokens[user_id]['expires_at']:
            return refresh_access_token(user_id)
        return tokens[user_id]['access_token']
    return None

@app.route('/api/refresh_token')
def api_refresh_token():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401

    try:
        new_access_token = refresh_access_token(user_id)
        return jsonify({'access_token': new_access_token}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 403

# Register the rujukan blueprint with the main Flask app instance

# Error handler for 400 Bad Request
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

# Error handler for 404 Not Found
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

# Error handler for 500 Internal Server Error
@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Id Obat Tidak Ditemukan."}), 500



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        name = request.form['name']
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, role, name) VALUES (%s, %s, %s, %s)", 
                           (username, hashed_password, role, name))
            mysql.connection.commit()
        except Exception as e:
            return str(e), 400
        finally:
            cursor.close()

        return redirect(url_for('login'))
        
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            user_id = user['id']
            role = user['role']
            name = user['name']  # Fetching name from user data
            access_token = generate_access_token(user_id, role, name)
            refresh_token = generate_refresh_token(user_id, role, name)
            tokens[user_id] = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'role': role,
                'name': name,  # Storing name in tokens dictionary
                'expires_at': time.time() + ACCESS_TOKEN_EXPIRES_IN
            }
            session['user_id'] = user_id
            
            if 'patient' in role:
                return redirect(url_for('patient_home', access_token=access_token))
            elif 'nurse' in role:
                return redirect(url_for('nurse_home', access_token=access_token))
            else:
                return 'Invalid role', 403
        else:
            return 'Invalid username or password', 401
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id in tokens:
        tokens.pop(user_id)
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    access_token = get_valid_access_token(user_id)
    return redirect(url_for('static', filename='dashboard.html'))

@app.route('/api/resource', methods=['GET'])
def protected_resource():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    access_token = get_valid_access_token(user_id)
    resource_url = 'https://api.github.com/user'  # GitHub API endpoint to get user info
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(resource_url, headers=headers)
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'error': 'Failed to fetch resource'}), response.status_code

def get_username(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT username FROM users WHERE id = %s", [user_id])
    user = cursor.fetchone()
    cursor.close()
    return user['username'] if user else None

@app.route('/patienthome')
def patient_home():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    access_token = get_valid_access_token(user_id)
    role = tokens[user_id]['role']
    username = get_username(user_id)

    return render_template('patienthome.html', access_token=access_token, role=role, username=username)

@app.route('/nursehome')
def nurse_home():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    access_token = get_valid_access_token(user_id)
    if not access_token:
        return "Access Denied. Please log in again.", 403

    role = tokens[user_id]['role']
    username = get_username(user_id)

    return render_template('nursehome.html', access_token=access_token, role=role, username=username)






# @app.route('/obat/addObat', methods=['POST'])
# def add_obat_page():
#     return render_template('ManageObat/addobat.html')

@app.route('/add_obat', methods=['GET'])
def show_add_obat_form():
    return render_template('ManageObat/addobat.html')

if __name__ == '__main__':
    app.run(debug=True)
