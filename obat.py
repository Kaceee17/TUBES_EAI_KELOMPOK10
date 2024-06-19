from flask import Flask, jsonify, request, render_template, url_for, redirect
from flask_mysqldb import MySQL
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'manajemen_obat'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def root():
    return 'Selamat datang di Pusat Informasi Obat'

@app.route('/obat', methods=['GET'])
def get_obat():
    nama = request.args.get('nama')
    kategori = request.args.get('kategori')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of items per page
    
    query = "SELECT COUNT(*) FROM obat"
    count_args = []
    if nama:
        query += " WHERE nama = %s"
        count_args.append(nama)
    elif kategori:
        query += " WHERE kategori = %s"
        count_args.append(kategori)

    cursor = mysql.connection.cursor()
    cursor.execute(query, count_args)
    total_items = cursor.fetchone()['COUNT(*)']
    
    offset = (page - 1) * per_page
    query = "SELECT * FROM obat"
    args = []
    if nama:
        query += " WHERE nama = %s"
        args.append(nama)
    elif kategori:
        query += " WHERE kategori = %s"
        args.append(kategori)
    query += " LIMIT %s OFFSET %s"
    args.extend([per_page, offset])
    
    cursor.execute(query, args)
    rows = cursor.fetchall()
    cursor.close()

    # Format date fields and currency
    data = []
    for row in rows:
        formatted_row = row.copy()
        if 'tanggal_kedaluwarsa' in row:
            formatted_row['tanggal_kedaluwarsa'] = row['tanggal_kedaluwarsa'].strftime('%d %b %Y')
        if 'harga' in row:
            formatted_row['harga'] = "{:,}".format(int(row['harga']))
        data.append(formatted_row)
    
    total_pages = (total_items + per_page - 1) // per_page  # Calculate total pages
    
    return render_template('ManageObat/obat.html', data=data, page=page, total_pages=total_pages)

@app.route('/addObat', methods=['GET', 'POST'])
def add_obat():
    if request.method == 'GET':
        return render_template('ManageObat/addobat.html')
    elif request.method == 'POST':
        data = request.form
        required_fields = ['nama', 'deskripsi', 'kategori', 'tanggal_kedaluwarsa', 'jumlah_stok', 'harga']

        if not all(data.get(field) for field in required_fields):
            return render_template('ManageObat/addobat.html', error="Data yang diperlukan tidak lengkap"), 400

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO obat (nama, deskripsi, kategori, tanggal_kedaluwarsa, jumlah_stok, harga) VALUES (%s, %s, %s, %s, %s, %s)",
                (data['nama'], data['deskripsi'], data['kategori'], data['tanggal_kedaluwarsa'], data['jumlah_stok'], data['harga'])
            )
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return render_template('ManageObat/addobat.html', error=str(e)), 500
        finally:
            cursor.close()

        return redirect(url_for('get_obat'))

@app.route('/editObat/<int:id>', methods=['GET', 'POST'])
def edit_obat(id):
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM obat WHERE id = %s", (id,))
        obat = cursor.fetchone()
        cursor.close()
        if not obat:
            return 'Obat tidak ditemukan', 404
        return render_template('ManageObat/edit_obat.html', obat=obat)
    
    elif request.method == 'POST':
        data = request.form
        required_fields = ['nama', 'deskripsi', 'kategori', 'tanggal_kedaluwarsa', 'jumlah_stok', 'harga']

        if not all(data.get(field) for field in required_fields):
            return render_template('ManageObat/edit_obat.html', error="Data yang diperlukan tidak lengkap", obat=data), 400

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "UPDATE obat SET nama = %s, deskripsi = %s, kategori = %s, tanggal_kedaluwarsa = %s, jumlah_stok = %s, harga = %s WHERE id = %s",
                (data['nama'], data['deskripsi'], data['kategori'], data['tanggal_kedaluwarsa'], data['jumlah_stok'], data['harga'], id)
            )
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return render_template('ManageObat/edit_obat.html', error=str(e), obat=data), 500
        finally:
            cursor.close()

        return redirect(url_for('get_obat'))

@app.route('/deleteObat/<int:id>', methods=['POST'])
def delete_obat(id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM obat WHERE id = %s", (id,))
        mysql.connection.commit()
        cursor.close()
    except Exception as e:
        mysql.connection.rollback()
        return str(e), 500
    return redirect(url_for('get_obat'))

if __name__ == '__main__':
    app.run(port=5001, debug=True)