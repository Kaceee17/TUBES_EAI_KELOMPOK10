import logging
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

@obat_app.route('/addObat', methods=['POST'])
def add_obat():
    data = request.form  # Change to request.form to get data from the form
    required_fields = ['nama', 'deskripsi', 'kategori', 'tanggal_kedaluwarsa', 'jumlah_stok', 'harga']
    if not all(field in data for field in required_fields):
        abort(400, description="Data yang diperlukan tidak lengkap")

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO obat (nama, deskripsi, kategori, tanggal_kedaluwarsa, jumlah_stok, harga) VALUES (%s, %s, %s, %s, %s, %s)",
                       (data['nama'], data['deskripsi'], data['kategori'], data['tanggal_kedaluwarsa'], data['jumlah_stok'], data['harga']))
        mysql.connection.commit()
    except Exception as e:
        abort(500, description=str(e))
    finally:
        cursor.close()
    return render_template('ManageObat/addobat.html', message="Obat berhasil ditambahkan")
    # return jsonify({'message': 'Data Obat Berhasil Ditambahkan'})

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

@obat_app.route('/Update_Obat/<int:id>', methods=['PUT'])
def update_obat(id):
    data = request.get_json()
    if not all(key in data for key in ['nama', 'deskripsi', 'kategori', 'tanggal_kedaluwarsa', 'jumlah_stok', 'harga']):
        abort(400, description="Data yang diterima tidak lengkap")

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM obat WHERE id=%s", (id,))
    if cursor.fetchone() is None:
        cursor.close()
        abort(404, description="Data Obat tidak ditemukan.")

    cursor.execute("UPDATE obat SET nama=%s, deskripsi=%s, kategori=%s, tanggal_kedaluwarsa=%s, jumlah_stok=%s, harga=%s WHERE id=%s",
                   (data['nama'], data['deskripsi'], data['kategori'], data['tanggal_kedaluwarsa'], data['jumlah_stok'], data['harga'], id))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Data Obat Berhasil Diubah"})

@obat_app.route('/Delete_Obat/<int:id>', methods=['DELETE'])
def delete_obat(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM obat WHERE id=%s", (id,))
    if cursor.fetchone() is None:
        cursor.close()
        abort(404, description="Data Obat not found.")

    cursor.execute("DELETE FROM obat WHERE id=%s", (id,))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Data Obat Berhasil Dihapus"})
