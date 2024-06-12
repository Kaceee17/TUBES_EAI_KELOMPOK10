import MySQLdb
from flask import Flask, jsonify, request, redirect, url_for, session, render_template, make_response
from flask_cors import CORS
from flask_mysqldb import MySQL
import bcrypt, jwt, time, logging, requests

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
ACCESS_TOKEN_EXPIRES_IN = 3600  # 16.6 minutes
REFRESH_TOKEN_EXPIRES_IN = 3600  # 1 hour

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
    return generate_token(user_id, name, ACCESS_TOKEN_EXPIRES_IN)

def generate_refresh_token(user_id, name):
    return generate_token(user_id, name, REFRESH_TOKEN_EXPIRES_IN)

def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.error("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.error("Invalid token")
        return None

@app.route('/refresh_token', methods=['POST'])
def refresh_token():
    refresh_token = request.json.get('refresh_token')
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE refresh_token = %s", [refresh_token])
        user = cursor.fetchone()

        if user:
            user_id = user['id']
            name = user['name']
            new_access_token = generate_access_token(user_id, name)
            new_refresh_token = generate_refresh_token(user_id, name)

            cursor.execute("UPDATE users SET refresh_token = %s WHERE id = %s", (new_refresh_token, user_id))
            mysql.connection.commit()

            return jsonify({
                'access_token': new_access_token,
                'refresh_token': new_refresh_token
            }), 200
    finally:
        cursor.close()  # Close cursor to avoid leakage
    return jsonify({'error': 'Invalid refresh token'}), 403



def get_valid_access_token(user_id):
    logger.error(f"tokens :", tokens)
    if user_id in tokens:
        if time.time() >= tokens[user_id]['expires_at']:
            return refresh_token(user_id)
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
            logger.error("Failed to register user: {}".format(e))
            return str(e), 400
        finally:
            cursor.close()

        return redirect(url_for('login'))
        
    return render_template('register.html')

from flask import jsonify  # Import jsonify for creating JSON responses

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", [username])
            user = cursor.fetchone()

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                user_id = user['id']
                name = user['name']
                access_token = generate_access_token(user_id, name)
                refresh_token = generate_refresh_token(user_id, name)

                cursor.execute("UPDATE users SET refresh_token = %s WHERE id = %s", (refresh_token, user_id))
                mysql.connection.commit()
                session['user_id'] = user_id

                response = make_response(jsonify({
                    'redirect_url': url_for('index'),
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'name': name
                }))
                response.set_cookie('access_token', access_token, httponly=True)
                return response
        finally:
            cursor.close()
        return jsonify({'error': 'Invalid username or password'}), 401
        
    return render_template('login.html')

@app.route('/index')
def index():
    token = request.cookies.get('access_token')
    if token:
        decoded = decode_token(token)
        if decoded:
            # API call to obat.py to get total_obat
            try:
                obat_response = requests.get('http://127.0.0.1:5001/api/total_obat', headers={'Authorization': 'Bearer ' + token})
                total_obat = obat_response.json().get('total_obat', 'Unavailable')
            except requests.RequestException as e:
                total_obat = 'Unavailable'
                logger.error("Failed to fetch total_obat: {}".format(e))

            try:
                resep_response = requests.get('http://127.0.0.1:5002/api/total_resep', headers={'Authorization': 'Bearer ' + token})
                total_resep = resep_response.json().get('total_resep', 'Unavailable')
            except requests.RequestException as e:
                total_resep = 'Unavailable'
                logger.error("Failed to fetch total_resep: {}".format(e))

            try:
                rujukan_response = requests.get('http://127.0.0.1:5003/api/total_rujukan', headers={'Authorization': 'Bearer ' + token})
                total_rujukan = rujukan_response.json().get('total_rujukan', 'Unavailable')
            except requests.RequestException as e:
                total_rujukan = 'Unavailable'
                logger.error("Failed to fetch total_rujukan: {}".format(e))

            return render_template('index.html', name=decoded['name'], total_resep=total_resep, total_obat = total_obat, total_rujukan=total_rujukan)
        else:
            response = make_response("Token is invalid or expired. Please login again.", 403)
            response.delete_cookie('access_token')  # Remove the invalid cookie
            return response
        
    return redirect(url_for('login'))


# @app.route('/index')
# def index():
#     token = request.cookies.get('access_token')  # Adjust based on how you're passing the token (headers, cookies, etc.)
#     if token:
#         decoded = decode_token(token)
#         if decoded:
#             return render_template('index.html', name=decoded['name'])
#         else:
#             response = make_response("Token is invalid or expired. Please login again.", 403)
#             response.delete_cookie('access_token')  # Remove the invalid cookie
#             return response
        
#     return redirect(url_for('login'))

    # return render_template('index.html', name=session.get('name'))
    # user_id = session.get('user_id')
    # if not user_id:
    #     return redirect(url_for('login'))

    # if not user_id:
    #     logger.error("User ID not found in session")
    #     return redirect(url_for('login'))

    # access_token = get_valid_access_token(user_id)
    # if not access_token:
    #     logger.error("Access token invalid or expired")
    #     return "Access Denied. Please log in again.", 403

    # decoded_token = decode_token(access_token)
    # if not decoded_token:
    #     logger.error("Failed to decode access token") 
    #     return "Invalid access token.", 403

    # name = decoded_token.get('name')
    # return render_template('index.html', name=name, access_token=access_token)
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('name', None)
    return redirect(url_for('landingpage'))

if __name__ == '__main__':
    app.run(port=5000, debug=True)
