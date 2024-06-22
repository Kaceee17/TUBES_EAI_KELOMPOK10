from flask import Flask, jsonify, request, render_template, url_for, redirect
from flask_mysqldb import MySQL
from flask_cors import CORS
from datetime import datetime
import bcrypt, jwt, time
import logging

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:5000"}})

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

JWT_SECRET = 'your_jwt_secret'
JWT_ALGORITHM = 'HS256'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'manajemen_user'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

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
    return 'Selamat datang di Pusat Informasi Resep Obat'

@app.route('/api/total_resep', methods=['GET'])
def total_resep():
    token, response, status = verify_jwt()
    if response:
       return response, status

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM resep_obat")
    total_resep = cursor.fetchone()['total']
    cursor.close()
    return jsonify({'total_resep': total_resep})


def buat_respons_kesalahan(pesan, kode):
    return jsonify({'pesan': pesan}), kode

@app.route('/api/addresep', methods=['GET', 'POST'])
def buat_resep():

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status

    import pika
    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters('127.0.0.1', 5672, '/', credentials)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(queue='ReceiveNurse')

    if request.method == 'GET':
        return jsonify({"message": "Use POST method to add resep."})
    
    elif request.method == 'POST':
        data = request.get_json()
        id_pasien = data.get('id_pasien')
        id_obat = data.get('id_obat')
        jumlah_obat = data.get('jumlah_obat')
        keterangan_resep = data.get('keterangan_resep')
        
        if not all([id_pasien, id_obat, jumlah_obat, keterangan_resep]):
            return jsonify({"error": "Semua field harus diisi"}), 400

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT nama FROM manajemen_obat.obat WHERE id = %s", (id_obat,))
        obat = cursor.fetchone()
        
        if obat:
            nama_obat = obat['nama']
            try:
                cursor.execute("INSERT INTO resep_obat (id_pasien, id_obat, jumlah_obat, nama_obat, keterangan_resep) VALUES (%s, %s, %s, %s, %s)", 
                            (id_pasien, id_obat, jumlah_obat, nama_obat, keterangan_resep))
                mysql.connection.commit()

                channel.basic_publish(exchange='', routing_key='ReceiveNurse', body='Data resep telah ditambahkan!')
                print(" [x] Sent 'Data Resep telah Ditambahkan!'")   
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({"error": str(e)}), 500
            finally:
                cursor.close()

            return jsonify({"message": "Resep added successfully"})
        else:
            cursor.close()
            return jsonify({"error": "ID Obat tidak ditemukan"}), 400





@app.route('/api/resep', methods=['GET'])
def baca_resep():

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status

    try:
        id_pasien = request.args.get('id_pasien')
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Number of items per page

        cur = mysql.connection.cursor()

        # Conditional query based on whether an ID is provided
        if id_pasien:
            cur.execute("SELECT COUNT(*) FROM resep_obat WHERE id_pasien = %s", (id_pasien,))
            total_items = cur.fetchone()['COUNT(*)']
            offset = (page - 1) * per_page
            cur.execute("SELECT * FROM resep_obat WHERE id_pasien = %s LIMIT %s OFFSET %s", (id_pasien, per_page, offset))
        else:
            cur.execute("SELECT COUNT(*) FROM resep_obat")
            total_items = cur.fetchone()['COUNT(*)']
            offset = (page - 1) * per_page
            cur.execute("SELECT * FROM resep_obat LIMIT %s OFFSET %s", (per_page, offset))

        rows = cur.fetchall()
        prescriptions = []
        for row in rows:
            prescriptions.append({
                'id_resepobat': row['id_resepobat'],
                'id_pasien': row['id_pasien'],
                'id_obat': row['id_obat'],
                'jumlah_obat': row['jumlah_obat'],
                'nama_obat': row['nama_obat'],
                'keterangan_resep': row['keterangan_resep']
            })
        cur.close()

        total_pages = (total_items + per_page - 1) // per_page  # Calculate total pages

        # Return data as JSON
        return jsonify({
            'hasil': prescriptions,
            'page': page,
            'total_pages': total_pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ubahResep/<int:id>', methods=['GET', 'POST'])
def ubah_resep(id):

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status

    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM resep_obat WHERE id_resepobat = %s", (id,))
        resep = cursor.fetchone()
        cursor.close()
        if not resep:
            return jsonify({'error': 'Resep tidak ditemukan'}), 404
        return jsonify(resep)
    
    elif request.method == 'POST':
        data = request.get_json()
        required_fields = ['id_pasien', 'id_obat', 'jumlah_obat', 'keterangan_resep']

        if not all(data.get(field) for field in required_fields):
            return jsonify({'error': 'Data yang diperlukan tidak lengkap'}), 400

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "UPDATE resep_obat SET id_pasien = %s, id_obat = %s, jumlah_obat = %s, keterangan_resep = %s WHERE id_resepobat = %s",
                (data['id_pasien'], data['id_obat'], data['jumlah_obat'], data['keterangan_resep'], id)
            )
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()

        return jsonify({'message': 'Resep updated successfully'})


        
@app.route('/api/resep/delete/<int:id>', methods=['DELETE'])
def hapus_resep(id):

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM resep_obat WHERE id_resepobat = %s", (id,))
        if cur.fetchone() is None:
            cur.close()
            return jsonify({"error": "Data Resep not found."}), 404

        cur.execute("DELETE FROM resep_obat WHERE id_resepobat = %s", (id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Resep deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5002, debug=True)