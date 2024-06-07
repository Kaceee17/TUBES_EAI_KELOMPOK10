from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from datetime import datetime
import pika

app = Flask (__name__)

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'pariwisata_user'

mysql = MySQL(app)

def generate_response(status_code, message, data=None):
    response = {'status_code': status_code, 'message': message, 'timestamp': datetime.now().isoformat()}
    if data:
        response['data'] = data
    return jsonify(response), status_code

@app.route('/')
def root():
    return 'Selamat datang di web pariwisata'


@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    name = data['name']
    email = data['email']
    
    cursor = mysql.connection.cursor()
    sql = "INSERT INTO user (name, email) VALUES (%s, %s)"
    val = (name, email)
    cursor.execute(sql, val)
    mysql.connection.commit()
    cursor.close()

    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters('127.0.0.1', 5672, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue='AdminTerima')
    channel.queue_declare(queue='CustomerTerima')

    channel.basic_publish(exchange='', routing_key='AdminTerima', body='Data telah dikirim ke Admin!')
    print(" [x] Sent 'Data Telah Ditambahkan ke Admin!'")    

    channel.basic_publish(exchange='', routing_key='CustomerTerima', body='Data telah dikirim ke Customer!')
    print(" [x] Sent 'Data Telah Ditambahkan ke Customer!'")

    connection.close()
    
    return generate_response(201, 'User added successfully')
    
    
    

@app.route('/detailuser', methods=['GET'])
def detailuser():
    if 'id' in request.args:
        cursor = mysql.connection.cursor()
        sql = "SELECT * FROM user WHERE user_id = %s"
        val = (request.args['id'],)
        cursor.execute(sql, val)

        #get column names from cursor.decription
        column_names = [i[0] for i in cursor.description]

        #fetch data and format into list of dictionaries
        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(column_names, row)))
            
        return jsonify(data)
        cursor.close()

@app.route('/updateuser', methods=['PUT'])
def updateuser():
    if 'id' in request.args:
        data = request.get_json()

        cursor = mysql.connection.cursor()
        sql = "UPDATE user SET name=%s, email=%s WHERE user_id=%s"
        val = (data['name'], data['email'], request.args['id'])
        cursor.execute(sql, val)
        mysql.connection.commit()

        return jsonify({'message': 'data updated successfully'})
    else:
        return jsonify({"error": "Pengguna tidak ditemukan"}), 404
    cursor.close()

    
@app.route('/deleteuser', methods=['DELETE'])
def deleteuser():
    if 'id' in request.args:
        cursor = mysql.connection.cursor()
        sql = "DELETE FROM user WHERE user_id=%s"
        val = (request.args['id'],)
        cursor.execute(sql, val)
        mysql.connection.commit()
        cursor.close()

        return generate_response(200, 'User deleted successfully')
    else:
        return generate_response(400, 'Could not delete user')

if __name__ == "__main__":
    app.run(debug=True, host ='0.0.0.0', port=5006)
