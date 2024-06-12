from flask import Flask, jsonify, request, render_template, url_for, redirect
from flask_mysqldb import MySQL
from flask_cors import CORS
from datetime import datetime
import bcrypt, jwt, time
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:5000"}})

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'manajemen_user'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

JWT_SECRET = 'your_jwt_secret'
JWT_ALGORITHM = 'HS256'
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
    return 'Selamat datang di Pusat Informasi Obat'

@app.route('/api/total_obat', methods=['GET'])
def total_obat():
    token, response, status = verify_jwt()
    if response:
        return response, status
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM obat")
    total_obat = cursor.fetchone()['total']
    cursor.close()
    return jsonify({'total_obat': total_obat})

@app.route('/dashboard')
def dashboard():
    token, response, status = verify_jwt()
    if response:
        return response, status
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM obat")
    total_obat = cursor.fetchone()['total']
    cursor.close()

    return render_template('dashboard.html', total_obat=total_obat)

@app.route('/obat', methods=['GET'])
def get_obat():
    
    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status

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
        formatted_row = {key: value for key, value in row.items()}
        if 'tanggal_kedaluwarsa' in row:
            formatted_row['tanggal_kedaluwarsa'] = row['tanggal_kedaluwarsa'].strftime('%d %b %Y')
        if 'harga' in row:
            formatted_row['harga'] = "{:,}".format(int(row['harga']))
        data.append(formatted_row)
    
    total_pages = (total_items + per_page - 1) // per_page  # Calculate total pages
    
    # Return data as JSON
    return jsonify({
        'data': data,
        'page': page,
        'total_pages': total_pages
    })

@app.route('/addObat', methods=['GET', 'POST'])
def add_obat():

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status

    if request.method == 'GET':
        return render_template('ManageObat/addobat.html')
    elif request.method == 'POST':
        data = request.get_json()
        required_fields = ['nama', 'deskripsi', 'kategori', 'tanggal_kedaluwarsa', 'jumlah_stok', 'harga']

        if not all(data.get(field) for field in required_fields):
            return jsonify({'error': 'Data yang diperlukan tidak lengkap'}), 400

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO obat (nama, deskripsi, kategori, tanggal_kedaluwarsa, jumlah_stok, harga) VALUES (%s, %s, %s, %s, %s, %s)",
                (data['nama'], data['deskripsi'], data['kategori'], data['tanggal_kedaluwarsa'], data['jumlah_stok'], data['harga'])
            )
            mysql.connection.commit()
            cursor.close()
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 500

        return jsonify({'message': 'Obat added successfully'})


@app.route('/editObat/<int:id>', methods=['GET', 'POST'])
def edit_obat(id):

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status
    
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM obat WHERE id = %s", (id,))
        obat = cursor.fetchone()
        cursor.close()
        if not obat:
            return jsonify({'error': 'Obat tidak ditemukan'}), 404
        return jsonify(obat)
    
    elif request.method == 'POST':
        data = request.get_json()
        required_fields = ['nama', 'deskripsi', 'kategori', 'tanggal_kedaluwarsa', 'jumlah_stok', 'harga']

        if not all(data.get(field) for field in required_fields):
            return jsonify({'error': 'Data yang diperlukan tidak lengkap'}), 400

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "UPDATE obat SET nama = %s, deskripsi = %s, kategori = %s, tanggal_kedaluwarsa = %s, jumlah_stok = %s, harga = %s WHERE id = %s",
                (data['nama'], data['deskripsi'], data['kategori'], data['tanggal_kedaluwarsa'], data['jumlah_stok'], data['harga'], id)
            )
            mysql.connection.commit()
            cursor.close()
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 500

        return jsonify({'message': 'Obat updated successfully'})


@app.route('/deleteObat/<int:id>', methods=['DELETE'])
def delete_obat(id):

    # untuk validate dia punya akses token atau ga
    token, response, status = verify_jwt()
    if response:
        return response, status

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM obat WHERE id = %s", (id,))
        mysql.connection.commit()
        cursor.close()
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500
    return jsonify({'message': 'Obat deleted successfully'})

if __name__ == '__main__':
    app.run(port=5001, debug=True)