from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__)
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'manajemen_obat'
app.config['MYSQL_HOST'] = 'localhost'

mysql = MySQL(app)

@app.route('/')
def root():
    return 'Selamat datang di Pusat Informasi Obat'

@app.route('/Obat', methods=['GET', 'POST'])
def obat():
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM obat")

        column_names = [i[0] for i in cursor.description]

        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(column_names, row)))
        cursor.close()  
        return jsonify(data)
    
    elif request.method == 'POST':
        data = request.get_json()
        nama = data.get('nama')
        deskripsi = data.get('deskripsi')
        kategori = data.get('kategori')
        tanggal_kedaluwarsa = data.get('tanggal_kedaluwarsa')
        jumlah_stok = data.get('jumlah_stok')
        harga = data.get('harga')

        cursor = mysql.connection.cursor()
        sql = "INSERT INTO obat (nama, deskripsi, kategori, tanggal_kedaluwarsa, jumlah_stok, harga) VALUES (%s, %s, %s, %s, %s, %s)"
        val = (nama, deskripsi, kategori, tanggal_kedaluwarsa, jumlah_stok, harga)
        cursor.execute(sql, val)

        mysql.connection.commit()
        cursor.close()
        return jsonify({'message' : 'Data Obat Berhasil Ditambahkan'})

@app.route('/Obat/<int:id>', methods=['DELETE'])
def delete_obat(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM obat WHERE id=%s", (id,))
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": "Data Obat Berhasil Dihapus"})

@app.route('/Obat/<int:id>', methods=['PUT'])
def update_obat(id):
    data = request.get_json()
    nama = data.get('nama')
    deskripsi = data.get('deskripsi')
    kategori = data.get('kategori')
    tanggal_kedaluwarsa = data.get('tanggal_kedaluwarsa')
    jumlah_stok = data.get('jumlah_stok')
    harga = data.get('harga')

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE obat SET nama=%s, deskripsi=%s, kategori=%s, tanggal_kedaluwarsa=%s, jumlah_stok=%s, harga=%s WHERE id=%s", (nama, deskripsi, kategori, tanggal_kedaluwarsa, jumlah_stok, harga, id))
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": "Data Obat Berhasil Diubah"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6004, debug=True)