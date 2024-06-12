from flask import Flask, jsonify, request, render_template, url_for, redirect
from flask_mysqldb import MySQL
from flask_cors import CORS
from datetime import datetime
import bcrypt, jwt, time
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:5000"}})

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# MySQL configurations for rujukan
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'manajemen_user'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

JWT_SECRET = 'your_jwt_secret'
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRES_IN = 60  # 16.6 minutes
REFRESH_TOKEN_EXPIRES_IN = 3600  # 1 hour

mysql = MySQL(app)

def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.error("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.error("Invalid token")
        return None
    
def verify_jwt():
    accessToken = request.headers.get('Authorization')
    if not accessToken:
        return None, jsonify({'error': 'JWT not found'}), 401

    try:
        tokenSplit = accessToken.split(' ')[1]
    except IndexError:
        return None, jsonify({'error': 'JWT format error'}), 401

    token = decode_token(tokenSplit)
    if token is None:
        return None, jsonify({'error': 'Token is invalid or expired'}), 401

    if token['exp'] <= time.time():
        return None, jsonify({'error': 'Token has expired'}), 401

    return token, None, None

@app.route('/')
def root():
    return 'Selamat datang di Pusat Informasi Rujukan Medis'

@app.route('/api/total_rujukan', methods=['GET'])
def total_rujukan():
    token, response, status = verify_jwt()
    if response:
        return response, status
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM rujukan")
    total_rujukan = cursor.fetchone()['total']
    cursor.close()
    return jsonify({'total_rujukan': total_rujukan})

@app.route('/add_rujukan', methods=['POST'])
def add_rujukan():

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status
    
    if request.method == 'POST':
        data = request.get_json()
        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO rujukan (patient_id, doctor_id, referral_date, appointment_date, status, notes, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (data['patient_id'], data['doctor_id'], data['referral_date'], data['appointment_date'], data['status'], data['notes'], datetime.now(), datetime.now())
            )
            mysql.connection.commit()
            return jsonify({"message": "Rujukan added successfully"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        finally:
            cursor.close()
    return jsonify({"message": "Use POST method to add rujukan"}), 405

@app.route('/delete_rujukan/<int:id>', methods=['DELETE'])
def delete_rujukan(id):

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("DELETE FROM rujukan WHERE id = %s", [id])
        if cursor.rowcount == 0:
            return jsonify({"error": "Rujukan not found"}), 404
        mysql.connection.commit()
        return jsonify({"message": "Rujukan deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()

@app.route('/rujukan', methods=['GET'])
def get_rujukan():

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status
    
    cursor = mysql.connection.cursor()
    patient_id = request.args.get('patient_id')
    doctor_id = request.args.get('doctor_id')
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of items per page

    # Build the query dynamically based on filters
    query = "SELECT COUNT(*) FROM rujukan"
    conditions = []
    params = []
    if patient_id:
        conditions.append("patient_id = %s")
        params.append(patient_id)
    if doctor_id:
        conditions.append("doctor_id = %s")
        params.append(doctor_id)
    if status:
        conditions.append("status = %s")
        params.append(status)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    cursor.execute(query, params)
    total_items = cursor.fetchone()['COUNT(*)']

    # Calculate offset for pagination
    offset = (page - 1) * per_page
    query = "SELECT id, patient_id, doctor_id, referral_date, appointment_date, status, notes, created_at, updated_at FROM rujukan"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Get column names for the result dictionary
    column_names = [desc[0] for desc in cursor.description]
    result = [{
        col: (getattr(row[col], 'strftime', lambda fmt: row[col])('%Y-%m-%d %H:%M:%S') if col.endswith('_date') else row[col])
        for col in column_names
    } for row in rows]
    
    cursor.close()

    total_pages = (total_items + per_page - 1) // per_page  # Calculate total pages

    # Return data as JSON instead of rendering a template
    return jsonify({
        'result': result,
        'page': page,
        'total_pages': total_pages
    })

@app.route('/rujukan/<int:id>', methods=['GET'])
def get_single_rujukan(id):

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM rujukan WHERE id = %s", (id,))
    row = cursor.fetchone()
    
    if not row:
        return jsonify({"error": "Referral not found"}), 404
    
    result = {desc[0]: (getattr(row[desc[0]], 'strftime', lambda fmt: row[desc[0]])('%Y-%m-%d %H:%M:%S') if desc[0].endswith('_date') else row[desc[0]]) for desc in cursor.description}
    
    cursor.close()
    return jsonify(result)

@app.route('/addrujukan', methods=['GET', 'POST'])
def addrujukan():

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status
    
    if request.method == 'GET':
        return render_template('ManageRujukan/addrujukan.html')
    
    elif request.method == 'POST':
        data = request.form
        required_fields = ['patient_id', 'doctor_id', 'referral_date', 'appointment_date', 'status', 'notes']
        
        if not all(data.get(field) for field in required_fields):
            return render_template('ManageRujukan/addrujukan.html', error="Data yang diperlukan tidak lengkap"), 400

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO rujukan (patient_id, doctor_id, referral_date, appointment_date, status, notes, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (data['patient_id'], data['doctor_id'], data['referral_date'], data['appointment_date'], data['status'], data['notes'], datetime.now(), datetime.now())
            )
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return render_template('ManageRujukan/addrujukan.html', error=str(e)), 500
        finally:
            cursor.close()

        return redirect(url_for('get_rujukan'))

@app.route('/edit_rujukan/<int:id>', methods=['GET', 'POST'])
def edit_rujukan(id):

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status
    
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM rujukan WHERE id = %s", (id,))
        referral = cursor.fetchone()
        cursor.close()

        if not referral:
            return jsonify({"error": "Referral not found"}), 404

        return jsonify(referral)

    elif request.method == 'POST':
        data = request.get_json()
        required_fields = ['patient_id', 'doctor_id', 'referral_date', 'appointment_date', 'status', 'notes']
        
        if not all(data.get(field) for field in required_fields):
            return jsonify({"error": "Data yang diperlukan tidak lengkap"}), 400

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "UPDATE rujukan SET patient_id = %s, doctor_id = %s, referral_date = %s, appointment_date = %s, status = %s, notes = %s, updated_at = %s WHERE id = %s",
                (data['patient_id'], data['doctor_id'], data['referral_date'], data['appointment_date'], data['status'], data['notes'], datetime.now(), id)
            )
            mysql.connection.commit()
            return jsonify({"message": "Rujukan updated successfully"})
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            cursor.close()

if __name__ == '__main__':
    app.run(port=5003, debug=True)