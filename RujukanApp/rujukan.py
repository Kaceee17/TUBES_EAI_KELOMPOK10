from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__)

# Konfigurasi database MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'manajemen_rujukan_medis'

mysql = MySQL(app)

def generate_response(status_code, message, data=None):
    response = {'status_code': status_code, 'message': message, 'timestamp': datetime.now().isoformat()}
    if data:
        response['data'] = data
    return jsonify(response), status_code

@app.route('/')
def root():
    return 'Selamat datang di halaman rujukan'

@app.route('/rujukan', methods=['GET'])
def get_rujukan():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, patient_id, doctor_id, referral_date, appointment_date, status, notes, created_at, updated_at FROM referrals")
    rows = cursor.fetchall()
    
    column_names = [desc[0] for desc in cursor.description]
    
    result = []
    for row in rows:
        referral_data = dict(zip(column_names, row))
        referral_data['referral_date'] = referral_data['referral_date'].strftime('%Y-%m-%d')
        referral_data['appointment_date'] = referral_data['appointment_date'].strftime('%Y-%m-%d') if referral_data['appointment_date'] else None
        referral_data['created_at'] = referral_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        referral_data['updated_at'] = referral_data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        result.append(referral_data)
    
    cursor.close()
    return jsonify(result)

@app.route('/rujukan/<int:id>', methods=['GET'])
def get_single_rujukan(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, patient_id, doctor_id, referral_date, appointment_date, status, notes, created_at, updated_at FROM referrals WHERE id = %s", (id,))
    row = cursor.fetchone()
    
    if row is None:
        return generate_response(404, 'Rujukan tidak ditemukan')
    
    column_names = [desc[0] for desc in cursor.description]
    referral_data = dict(zip(column_names, row))
    referral_data['referral_date'] = referral_data['referral_date'].strftime('%Y-%m-%d')
    referral_data['appointment_date'] = referral_data['appointment_date'].strftime('%Y-%m-%d') if referral_data['appointment_date'] else None
    referral_data['created_at'] = referral_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    referral_data['updated_at'] = referral_data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.close()
    return jsonify(referral_data)

@app.route('/addrujukan', methods=['POST'])
def addrujukan():
    data = request.json
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')
    referral_date = data.get('referral_date')
    appointment_date = data.get('appointment_date')
    status = data.get('status')
    notes = data.get('notes')

    # Validation checks
    if not str(patient_id).startswith('1') or len(str(patient_id)) != 3:
        return generate_response(400, 'Patient ID does not meet requirements')
    if not str(doctor_id).startswith('2') or len(str(doctor_id)) != 3:
        return generate_response(400, 'Doctor ID does not meet requirements')

    cursor = mysql.connection.cursor()
    sql = "INSERT INTO referrals (patient_id, doctor_id, referral_date, appointment_date, status, notes) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (patient_id, doctor_id, referral_date, appointment_date, status, notes)
    
    cursor.execute(sql, val)
    mysql.connection.commit()
    cursor.close()
    return generate_response(201, 'Referral added successfully')

@app.route('/update_referral/<int:id>', methods=['PUT'])
def update_referral(id):
    data = request.json
    patient_id = data.get('patient_id')
    doctor_id = data.get('doctor_id')
    referral_date = data.get('referral_date')
    appointment_date = data.get('appointment_date')
    status = data.get('status')
    notes = data.get('notes')

    cursor = mysql.connection.cursor()
    sql = "UPDATE referrals SET patient_id = %s, doctor_id = %s, referral_date = %s, appointment_date = %s, status = %s, notes = %s WHERE id = %s"
    val = (patient_id, doctor_id, referral_date, appointment_date, status, notes, id)
    
    cursor.execute(sql, val)
    mysql.connection.commit()
    cursor.close()
    return generate_response(200, f'Referral with id {id} updated successfully')

@app.route('/delete_referral/<int:id>', methods=['DELETE'])
def delete_referral(id):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("DELETE FROM referrals WHERE id = %s", (id,))
        mysql.connection.commit()
        cursor.close()
        return generate_response(200, f'Referral with id {id} deleted successfully')
    except Exception as e:
        cursor.close()
        return generate_response(500, f'Error occurred while deleting referral with id {id}: {str(e)}')

if __name__ == '__main__':
    app.run(debug=True, port=6001)
