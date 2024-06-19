from flask import Flask, jsonify, request, redirect, url_for, render_template
from flask_cors import CORS
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

# MySQL configurations for rujukan
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'manajemen_rujukan_medis'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

def generate_response(status_code, message, data=None):
    response = {'status': status_code, 'message': message, 'timestamp': datetime.now().isoformat()}
    if data:
        response['data'] = data
    return jsonify(response), status_code

@app.route('/')
def root():
    return 'Selamat datang di Pusat Informasi Rujukan Medis'

@app.route('/add_rujukan', methods=['GET', 'POST'])
def add_rujukan():
    if request.method == 'POST':
        data = request.form
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("INSERT INTO rujukan (nama_pasien, rumah_sakit, tanggal) VALUES (%s, %s, %s)",
                           (data['nama_pasien'], data['rumah_sakit'], data['tanggal']))
            mysql.connection.commit()
            return redirect(url_for('list_rujukan'))
        except Exception as e:
            return str(e), 400
        finally:
            cursor.close()
    return render_template('addrujukan.html')

@app.route('/edit_rujukan/<int:id>', methods=['GET', 'POST'])
def edit_rujukan(id):
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        data = request.form
        try:
            cursor.execute("UPDATE rujukan SET nama_pasien = %s, rumah_sakit = %s, tanggal = %s WHERE id = %s",
                           (data['nama_pasien'], data['rumah_sakit'], data['tanggal'], id))
            mysql.connection.commit()
            return redirect(url_for('list_rujukan'))
        except Exception as e:
            return str(e), 400
        finally:
            cursor.close()
    else:
        cursor.execute("SELECT * FROM rujukan WHERE id = %s", [id])
        rujukan = cursor.fetchone()
        cursor.close()
        return render_template('edit_rujukan.html', rujukan=rujukan)

@app.route('/delete_rujukan/<int:id>', methods=['POST'])
def delete_rujukan(id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("DELETE FROM rujukan WHERE id = %s", [id])
        mysql.connection.commit()
        return redirect(url_for('list_rujukan'))
    except Exception as e:
        return str(e), 400
    finally:
        cursor.close()

@app.route('/rujukan', methods=['GET'])
def get_rujukan():
    cursor = mysql.connection.cursor()
    patient_id = request.args.get('patient_id')
    doctor_id = request.args.get('doctor_id')
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of items per page

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

    offset = (page - 1) * per_page
    query = "SELECT id, patient_id, doctor_id, referral_date, appointment_date, status, notes, created_at, updated_at FROM rujukan"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    column_names = [desc[0] for desc in cursor.description]
    result = [{col: (getattr(row[col], 'strftime', lambda fmt: row[col])('%d %b %Y') if col.endswith('_date') else row[col]) for col in column_names} for row in rows]
    
    cursor.close()

    total_pages = (total_items + per_page - 1) // per_page  # Calculate total pages

    return render_template('ManageRujukan/rujukan.html', result=result, page=page, total_pages=total_pages)

@app.route('/rujukan/<int:id>', methods=['GET'])
def get_single_rujukan(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM rujukan WHERE id = %s", (id,))
    row = cursor.fetchone()
    
    if not row:
        return generate_response(404, 'Referral not found')
    
    result = {desc[0]: (getattr(row[desc[0]], 'strftime', lambda fmt: row[desc[0]])('%Y-%m-%d %H:%M:%S') if desc[0].endswith('_date') else row[desc[0]]) for desc in cursor.description}
    
    cursor.close()
    return jsonify(result)

@app.route('/addrujukan', methods=['GET', 'POST'])
def addrujukan():
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
                "INSERT INTO rujukan (patient_id, doctor_id, referral_date, appointment_date, status, notes) VALUES (%s, %s, %s, %s, %s, %s)",
                (data['patient_id'], data['doctor_id'], data['referral_date'], data['appointment_date'], data['status'], data['notes'])
            )
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return render_template('ManageRujukan/addrujukan.html', error=str(e)), 500
        finally:
            cursor.close()

        return redirect(url_for('get_rujukan'))

@app.route('/edit_rujukan/<int:id>', methods=['GET', 'POST'])
def editrujukan(id):
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM rujukan WHERE id = %s", (id,))
        referral = cursor.fetchone()
        cursor.close()

        if not referral:
            return generate_response(404, 'Referral not found')

        return render_template('ManageRujukan/edit_rujukan.html', referral=referral)

    elif request.method == 'POST':
        data = request.form
        required_fields = ['patient_id', 'doctor_id', 'referral_date', 'appointment_date', 'status', 'notes']
        
        if not all(data.get(field) for field in required_fields):
            return render_template('ManageRujukan/edit_rujukan.html', error="Data yang diperlukan tidak lengkap", referral=data), 400

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "UPDATE rujukan SET patient_id = %s, doctor_id = %s, referral_date = %s, appointment_date = %s, status = %s, notes = %s WHERE id = %s",
                (data['patient_id'], data['doctor_id'], data['referral_date'], data['appointment_date'], data['status'], data['notes'], id)
            )
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return render_template('ManageRujukan/edit_rujukan.html', error=str(e), referral=data), 500
        finally:
            cursor.close()

        return redirect(url_for('get_rujukan'))


@app.route('/deleterujukan/<int:id>', methods=['POST'])
def deleterujukan(id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM rujukan WHERE id = %s", (id,))
        if cursor.rowcount == 0:
            return generate_response(404, 'Referral not found')
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        return generate_response(500, 'Failed to delete referral', str(e))
    finally:
        cursor.close()

    return redirect(url_for('get_rujukan'))

if __name__ == '__main__':
    app.run(port=5003, debug=True)
