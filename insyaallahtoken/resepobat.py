from flask import Blueprint, request, jsonify, render_template
from flask_mysqldb import MySQL
import MySQLdb.cursors  # Import this if using MySQLdb


resepobat_app = Blueprint('resepobat_app', __name__)

# Define the MySQL instance
mysql = MySQL()

def buat_respons_kesalahan(pesan, kode):
    return jsonify({'pesan': pesan}), kode

@resepobat_app.route('/resep', methods=['POST'])
def buat_resep():
    if request.content_type != 'application/json':
        return buat_respons_kesalahan('Content-Type harus application/json', 415)
    
    data = request.json
    id_pasien = data.get('id_pasien')
    id_obat = data.get('id_obat')
    jumlah_obat = data.get('jumlah_obat')
    keterangan_resep = data.get('keterangan_resep')
    
    if not all([id_pasien, id_obat, jumlah_obat, keterangan_resep]):
        return buat_respons_kesalahan('Semua field harus diisi', 400)

    cur = mysql.connection.cursor()
    # Corrected from "SELECT nama_obat FROM nama_obat WHERE id_obat = %s" to the line below
    cur.execute("SELECT nama FROM obat WHERE id = %s", (id_obat,))
    obat = cur.fetchone()
    
    if obat:
        nama_obat = obat['nama']  # Now you can access by key
        cur.execute("INSERT INTO resep_obat (id_pasien, id_obat, jumlah_obat, nama_obat, keterangan_resep) VALUES (%s, %s, %s, %s, %s)", 
                    (id_pasien, id_obat, jumlah_obat, nama_obat, keterangan_resep))
        mysql.connection.commit()
        cur.close()
        return jsonify({'pesan': 'Resep berhasil ditambahkan'}), 201
    else:
        cur.close()
        return buat_respons_kesalahan('ID Obat tidak ditemukan', 400)

@resepobat_app.route('/resepbaca', methods=['GET'])
def baca_resep():
    id_pasien = request.args.get('id_pasien')
    
    cur = mysql.connection.cursor()
    if id_pasien:
        cur.execute("SELECT * FROM resep_obat WHERE id_pasien = %s", (id_pasien,))
    else:
        cur.execute("SELECT * FROM resep_obat")
        
    baris = cur.fetchall()
    hasil = []
    for row in baris:
        hasil.append({
            'id_resepobat': row['id_resepobat'],  # Access by column name
            'id_pasien': row['id_pasien'],        # Access by column name
            'id_obat': row['id_obat'],            # Access by column name
            'jumlah_obat': row['jumlah_obat'],    # Access by column name
            'nama_obat': row['nama_obat'],        # Access by column name
            'keterangan_resep': row['keterangan_resep']  # Access by column name
        })
    cur.close()
    return render_template('/ManageResepObat/resepobat.html', hasil=hasil)

@resepobat_app.route('/resep/<int:id>', methods=['PUT'])
def ubah_resep(id):
    if request.content_type != 'application/json':
        return buat_respons_kesalahan('Content-Type harus application/json', 415)
    
    data = request.json
    id_pasien = data.get('id_pasien')
    id_obat = data.get('id_obat')
    jumlah_obat = data.get('jumlah_obat')
    keterangan_resep = data.get('keterangan_resep')
    
    if not all([id_pasien, id_obat, jumlah_obat, keterangan_resep]):
        return buat_respons_kesalahan('Semua field harus diisi', 400)

    cur = mysql.connection.cursor()
    cur.execute("SELECT nama FROM obat WHERE id = %s", (id_obat,))
    obat = cur.fetchone()
    
    if obat:
        nama_obat = obat['nama']  # Now you can access by key
        cur.execute("""
            UPDATE resep_obat 
            SET id_pasien = %s, id_obat = %s, jumlah_obat = %s, nama_obat = %s, keterangan_resep = %s 
            WHERE id_resepobat = %s
            """, (id_pasien, id_obat, jumlah_obat, nama_obat, keterangan_resep, id))
        if cur.rowcount == 0:
            return buat_respons_kesalahan('Resep tidak ditemukan', 404)
        mysql.connection.commit()
        cur.close()
        return jsonify({'pesan': 'Resep berhasil diperbarui'}), 200
    else:
        cur.close()
        return buat_respons_kesalahan('ID Obat tidak ditemukan', 400)
    
@resepobat_app.route('/resep/<int:id>', methods=['DELETE'])
def hapus_resep(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM resep_obat WHERE id_resepobat = %s", (id,))
    affected_rows = cur.rowcount
    mysql.connection.commit()
    cur.close()
    if affected_rows == 0:
        return jsonify({'pesan': 'Tidak ada resep yang dihapus'}), 404
    return jsonify({'pesan': 'Resep berhasil dihapus'}), 200
