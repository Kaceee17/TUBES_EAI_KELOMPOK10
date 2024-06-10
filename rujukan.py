from flask import Blueprint, jsonify, request, render_template
from flask_mysqldb import MySQL
from datetime import datetime

# Create a blueprint instance
rujukan_app = Blueprint('rujukan_app', __name__)

def generate_response(status_code, message, data=None):
    response = {'status': status_code, 'message': message, 'timestamp': datetime.now().isoformat()}
    if data:
        response['data'] = data
    return jsonify(response), status_code

# Define the MySQL instance
mysql = MySQL()

@rujukan_app.route('/rujukan', methods=['GET'])
def get_rujukan():
    cursor = mysql.connection.cursor()
    # Extract query parameters
    patient_id = request.args.get('patient_id')
    doctor_id = request.args.get('doctor_id')
    status = request.args.get('status')

    query = "SELECT id, patient_id, doctor_id, referral_date, appointment_date, status, notes, created_at, updated_at FROM referrals"
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
    rows = cursor.fetchall()
    
    column_names = [desc[0] for desc in cursor.description]
    result = [{col: (getattr(row[col], 'strftime', lambda fmt: row[col])('%Y-%m-%d %H:%M:%S') if col.endswith('_date') else row[col]) for col in column_names} for row in rows]
    
    cursor.close()
    return render_template('/ManageRujukan/rujukan.html', result=result)

@rujukan_app.route('/rujukan/<int:id>', methods=['GET'])
def get_single_rujukan(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM referrals WHERE id = %s", (id,))
    row = cursor.fetchone()
    
    if not row:
        return generate_response(404, 'Referral not found')
    
    result = {desc[0]: (getattr(row[desc[0]], 'strftime', lambda fmt: row[desc[0]])('%Y-%m-%d %H:%M:%S') if desc[0].endswith('_date') else row[desc[0]]) for desc in cursor.description}
    
    cursor.close()
    return jsonify(result)

@rujukan_app.route('/addrujukan', methods=['POST'])
def addrujukan():
    data = request.json
    required_fields = ['patient_id', 'doctor_id', 'referral_date', 'appointment_date', 'status', 'notes']
    if not all(data.get(field) for field in required_fields):
        return generate_response(400, 'Missing required fields')

    try:
        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO referrals (patient_id, doctor_id, referral_date, appointment_date, status, notes) VALUES (%s, %s, %s, %s, %s, %s)",
            (data['patient_id'], data['doctor_id'], data['referral_date'], data['appointment_date'], data['status'], data['notes'])
        )
        mysql.connection.commit()
        cursor.close()
        return generate_response(201, 'Referral added successfully')
    except Exception as e:
        mysql.connection.rollback()
        return generate_response(500, 'Failed to add referral', str(e))

@rujukan_app.route('/update_referral/<int:id>', methods=['PUT'])
def update_referral(id):
    data = request.json
    if not all(data.get(key) for key in ['patient_id', 'doctor_id', 'referral_date', 'appointment_date', 'status', 'notes']):
        return generate_response(400, 'Missing required fields')

    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            "UPDATE referrals SET patient_id = %s, doctor_id = %s, referral_date = %s, appointment_date = %s, status = %s, notes = %s WHERE id = %s",
            (data['patient_id'], data['doctor_id'], data['referral_date'], data['appointment_date'], data['status'], data['notes'], id)
        )
        if cursor.rowcount == 0:
            return generate_response(404, 'Referral not found')
        mysql.connection.commit()
        return generate_response(200, 'Referral updated successfully')
    except Exception as e:
        mysql.connection.rollback()
        return generate_response(500, 'Failed to update referral', str(e))
    finally:
        cursor.close()

@rujukan_app.route('/delete_referral/<int:id>', methods=['DELETE'])
def delete_referral(id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("DELETE FROM referrals WHERE id = %s", (id,))
        if cursor.rowcount == 0:
            return generate_response(404, 'Referral not found')
        mysql.connection.commit()
        return generate_response(200, 'Referral deleted successfully')
    except Exception as e:
        mysql.connection.rollback()
        return generate_response(500, 'Failed to delete referral', str(e))
    finally:
        cursor.close()
