import logging
import pika
from flask import Blueprint, abort, jsonify, request, render_template
from flask_mysqldb import MySQL
from datetime import datetime

obat_app = Blueprint('obat_app', __name__)

# Define the MySQL instance
mysql = MySQL()

# Error handler for 400 Bad Request
@obat_app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

# Error handler for 404 Not Found
@obat_app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

# Error handler for 500 Internal Server Error
@obat_app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Id Obat Tidak Ditemukan."}), 500

@obat_app.route('/')
def root():
    return 'Selamat datang di Pusat Informasi Obat'

@obat_app.route('/Obat', methods=['GET'])
def get_obat():
    nama = request.args.get('nama')
    kategori = request.args.get('kategori')
    query = "SELECT * FROM obat"
    args = []
    if nama:
        query += " WHERE nama = %s"
        args.append(nama)
    elif kategori:
        query += " WHERE kategori = %s"
        args.append(kategori)

    cursor = mysql.connection.cursor()
    cursor.execute(query, args)
    data = cursor.fetchall()
    cursor.close()
    return render_template('/ManageObat/obat.html', data=data)

@obat_app.route('/addObat', methods=['GET', 'POST'])
def add_obat():

    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters('127.0.0.1', 5672, '/', credentials)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare(queue='ReceiveNurse')

    if request.method == 'GET':
        # Display the form
        return render_template('ManageObat/addobat.html')
    
    elif request.method == 'POST':
        # Process the form submission
        data = request.form  # Accessing form data sent via POST
        required_fields = ['nama', 'deskripsi', 'kategori', 'tanggal_kedaluwarsa', 'jumlah_stok', 'harga']
        
        if not all(data.get(field) for field in required_fields):
            # Return error if any field is missing
            return render_template('ManageObat/addobat.html', error="Data yang diperlukan tidak lengkap"), 400

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO obat (nama, deskripsi, kategori, tanggal_kedaluwarsa, jumlah_stok, harga) VALUES (%s, %s, %s, %s, %s, %s)",
                (data['nama'], data['deskripsi'], data['kategori'], data['tanggal_kedaluwarsa'], data['jumlah_stok'], data['harga'])
            )
            mysql.connection.commit()

            channel.basic_publish(exchange='', routing_key='ReceiveNurse', body='Data obat telah ditambahkan!')
            print(" [x] Sent 'Data Obat telah Ditambahkan!'")   
        except Exception as e:
            mysql.connection.rollback()
            return render_template('ManageObat/addobat.html', error=str(e)), 500
        finally:
            cursor.close()

        # Fetch updated list of medications and show it
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM obat")
        meds = cursor.fetchall()
        cursor.close()
        return render_template('ManageObat/obat.html', data=meds)



@obat_app.route('/Update_Obat/<int:id>', methods=['POST'])
def update_obat(id):
    if request.form.get('_method') == 'PUT':
        data = request.form
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM obat WHERE id=%s", (id,))
        if cursor.fetchone() is None:
            cursor.close()
            abort(404, description="Data Obat tidak ditemukan.")

        try:
            cursor.execute(
                "UPDATE obat SET nama=%s, deskripsi=%s, kategori=%s, tanggal_kedaluwarsa=%s, jumlah_stok=%s, harga=%s WHERE id=%s",
                (data['nama'], data['deskripsi'], data['kategori'], data['tanggal_kedaluwarsa'], data['jumlah_stok'], data['harga'], id)
            )
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return str(e), 500
        finally:
            cursor.close()

        # Redirect to the obat list page
        return render_template('/ManageObat/obat.html', data=data)
    else:
        return jsonify({"error": "Invalid request"}), 400



@obat_app.route('/Delete_Obat/<int:id>', methods=['POST'])
def delete_obat(id):
    # Check if this is a simulated DELETE request
    if request.form.get('_method') == 'DELETE':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM obat WHERE id=%s", (id,))
        if cursor.fetchone() is None:
            cursor.close()
            return jsonify({"error": "Data Obat not found."}), 404

        cursor.execute("DELETE FROM obat WHERE id=%s", (id,))
        cursor.execute("SELECT * FROM obat")
        mysql.connection.commit()
        data = cursor.fetchall()
        cursor.close()

        # Redirect to a new URL or return a success message
        return render_template('/ManageObat/obat.html', data=data)
    else:
        return jsonify({"error": "Invalid request"}), 400
    
@obat_app.route('/Edit_Obat/<int:id>', methods=['GET'])
def edit_obat(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM obat WHERE id=%s", (id,))
    obat = cursor.fetchone()
    cursor.close()

    if obat is None:
        abort(404, description="Data Obat tidak ditemukan.")

    return render_template('ManageObat/edit_obat.html', obat=obat)



# @obat_app.route('/Obat', methods=['GET', 'POST'])
# def obat():
#     if request.method == 'GET':
#         nama = request.args.get('nama')
#         kategori = request.args.get('kategori')
#         query = "SELECT * FROM obat"
#         args = []
#         if nama:
#             query += " WHERE nama = %s"
#             args.append(nama)
#         elif kategori:
#             query += " WHERE kategori = %s"
#             args.append(kategori)

#         cursor = mysql.connection.cursor()
#         cursor.execute(query, args)
#         data = [dict(row) for row in cursor.fetchall()]
#         cursor.close()
#         return render_template('/ManageObat/obat.html', data=data)
#         # return render_template('patienthome.html', access_token=access_token, role=role, username=username)
    
#     elif request.method == 'POST':
#         data = request.get_json()
#         required_fields = ['nama', 'deskripsi', 'kategori', 'tanggal_kedaluwarsa', 'jumlah_stok', 'harga']
#         if not all(field in data for field in required_fields):
#             abort(400, description="Data yang diperlukan tidak lengkap")

#         try:
#             cursor = mysql.connection.cursor()
#             cursor.execute("INSERT INTO obat (nama, deskripsi, kategori, tanggal_kedaluwarsa, jumlah_stok, harga) VALUES (%s, %s, %s, %s, %s, %s)",
#                            (data['nama'], data['deskripsi'], data['kategori'], data['tanggal_kedaluwarsa'], data['jumlah_stok'], data['harga']))
#             mysql.connection.commit()
#         except Exception as e:
#             abort(500, description=str(e))
#         finally:
#             cursor.close()
#         return jsonify({'message': 'Data Obat Berhasil Ditambahkan'})