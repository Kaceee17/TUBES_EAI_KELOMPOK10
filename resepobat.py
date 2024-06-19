import pika
from flask import abort, jsonify, redirect, request, render_template, url_for, Flask
from flask_mysqldb import MySQL
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'manajemen_resep'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Define the MySQL instance
mysql = MySQL(app)

@app.route('/')
def root():
    return 'Selamat datang di Pusat Informasi Resep Obat'

def buat_respons_kesalahan(pesan, kode):
    return jsonify({'pesan': pesan}), kode

@app.route('/addresep', methods=['GET', 'POST'])
def buat_resep():
    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters('127.0.0.1', 5672, '/', credentials)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(queue='ReceiveNurse')

    if request.method == 'GET':
        return render_template('ManageResepObat/addresep.html')
    
    elif request.method == 'POST':
        data = request.form
        id_pasien = data.get('id_pasien')
        id_obat = data.get('id_obat')
        jumlah_obat = data.get('jumlah_obat')
        keterangan_resep = data.get('keterangan_resep')
        
        if not all([id_pasien, id_obat, jumlah_obat, keterangan_resep]):
            return render_template('ManageResepObat/addresep.html', error="Semua field harus diisi"), 400

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
                return render_template('ManageResepObat/addresep.html', error=str(e)), 500
            finally:
                cursor.close()

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM resep_obat")
            resep = cursor.fetchall()
            cursor.close()
            return render_template('ManageResepObat/resepobat.html', hasil=resep, page=1, total_pages=1)  # Set page and total_pages
        else:
            cursor.close()
            return render_template('ManageResepObat/addresep.html', error="ID Obat tidak ditemukan"), 400



@app.route('/resep', methods=['GET'])
def baca_resep():
    try:
        id_pasien = request.args.get('id_pasien')
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Number of items per page

        cur = mysql.connection.cursor()

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
        hasil = []
        for row in rows:
            hasil.append({
                'id_resepobat': row['id_resepobat'],
                'id_pasien': row['id_pasien'],
                'id_obat': row['id_obat'],
                'jumlah_obat': row['jumlah_obat'],
                'nama_obat': row['nama_obat'],
                'keterangan_resep': row['keterangan_resep']
            })
        cur.close()

        total_pages = (total_items + per_page - 1) // per_page  # Calculate total pages

        return render_template('ManageResepObat/resepobat.html', hasil=hasil, page=page, total_pages=total_pages)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/ubahResep/<int:id>', methods=['GET', 'POST'])
def ubah_resep(id):
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM resep_obat WHERE id_resepobat = %s", (id,))
        resep = cursor.fetchone()
        cursor.close()
        if not resep:
            return 'Resep tidak ditemukan', 404
        return render_template('ManageResepObat/edit_resep.html', resep=resep)
    
    elif request.method == 'POST':
        data = request.form
        required_fields = ['id_pasien', 'id_obat', 'jumlah_obat', 'keterangan_resep']

        if not all(data.get(field) for field in required_fields):
            return render_template('ManageResepObat/edit_resep.html', error="Data yang diperlukan tidak lengkap", resep=data), 400

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "UPDATE resep_obat SET id_pasien = %s, id_obat = %s, jumlah_obat = %s, keterangan_resep = %s WHERE id_resepobat = %s",
                (data['id_pasien'], data['id_obat'], data['jumlah_obat'], data['keterangan_resep'], id)
            )
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return render_template('ManageResepObat/edit_resep.html', error=str(e), resep=data), 500
        finally:
            cursor.close()

        return redirect(url_for('baca_resep'))

        
@app.route('/resep/delete/<int:id>', methods=['POST'])
def hapus_resep(id):
    # Check if this is a simulated DELETE request
    if request.form.get('_method') == 'DELETE':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM resep_obat WHERE id_resepobat = %s", (id,))
        if cur.fetchone() is None:
            cur.close()
            return jsonify({"error": "Data Resep not found."}), 404

        cur.execute("DELETE FROM resep_obat WHERE id_resepobat = %s", (id,))
        mysql.connection.commit()

        # Fetch the updated list of prescriptions
        cur.execute("SELECT COUNT(*) FROM resep_obat")
        total_items = cur.fetchone()['COUNT(*)']
        cur.execute("SELECT * FROM resep_obat")
        data = cur.fetchall()
        cur.close()

        # Calculate total pages and set the current page
        per_page = 10
        total_pages = (total_items + per_page - 1) // per_page
        page = 1  # Assuming page 1 after deletion for simplicity

        # Redirect to a new URL or return a success message
        return render_template('ManageResepObat/resepobat.html', hasil=data, page=page, total_pages=total_pages)
    else:
        return jsonify({"error": "Invalid request"}), 400

if __name__ == '__main__':
    app.run(port=5002, debug=True)
