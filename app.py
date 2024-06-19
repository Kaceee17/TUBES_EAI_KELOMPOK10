import MySQLdb
from flask import Flask, jsonify, request, redirect, url_for, session, render_template
from flask_cors import CORS
from flask_mysqldb import MySQL
import bcrypt, jwt, time
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'manajemen_user'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

JWT_SECRET = 'your_jwt_secret'
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRES_IN = 1000
REFRESH_TOKEN_EXPIRES_IN = 3600

tokens = {}

def generate_token(user_id, name, expires_in, token_type='access'):
    payload = {
        'user_id': user_id,
        'name': name,
        'exp': time.time() + expires_in,
        'type': token_type
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_access_token(user_id, name):
    return generate_token(user_id, name, ACCESS_TOKEN_EXPIRES_IN, 'access')

def generate_refresh_token(user_id, name):
    return generate_token(user_id, name, REFRESH_TOKEN_EXPIRES_IN, 'refresh')

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
        name = decoded['name']
        access_token = generate_access_token(user_id, name)
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

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error"}), 500

@app.route('/')
def landingpage():
    return render_template('landingpage.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, name) VALUES (%s, %s, %s)", 
                           (username, hashed_password, name))
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

        if user:
            logger.debug(f"User found: {user}")
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                logger.debug("Password matches")
                user_id = user['id']
                name = user['name']
                access_token = generate_access_token(user_id, name)
                refresh_token = generate_refresh_token(user_id, name)
                tokens[user_id] = {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'name': name,
                    'expires_at': time.time() + ACCESS_TOKEN_EXPIRES_IN
                }
                session['user_id'] = user_id
                return redirect(url_for('index', access_token=access_token))
            else:
                logger.debug("Password does not match")
                return 'Invalid username or password', 401
        else:
            logger.debug("User not found")
            return 'Invalid username or password', 401
        
    return render_template('login.html')

@app.route('/index')
def index():
    try:
        user_id = session.get('user_id')
        if not user_id:
            logger.debug(f"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
            return redirect(url_for('login'))

        access_token = get_valid_access_token(user_id)
        if not access_token:
            return "Access Denied. Please log in again.", 403

        decoded_token = decode_token(access_token)
        if not decoded_token:
            return "Invalid access token.", 403

        name = decoded_token.get('name')

        # cursor = mysql.connection.cursor()
        # cursor.execute("SELECT * FROM obat")
        # rows = cursor.fetchall()
        # cursor.close()

        # data = []
        # for row in rows:
        #     formatted_row = row.copy()
        #     if 'tanggal_kedaluwarsa' in row:
        #         formatted_row['tanggal_kedaluwarsa'] = row['tanggal_kedaluwarsa'].strftime('%d %b %Y')
        #     data.append(formatted_row)

        # for row in data:
        #     row['harga'] = "{:,}".format(row['harga'])

        return render_template('index.html', name=name, access_token=access_token)
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return "Internal Server Error", 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landingpage'))

if __name__ == '__main__':
    app.run(port=5000, debug=True)