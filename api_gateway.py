from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains and routes

SERVICE_MAP = {
    'users': 'http://localhost:5000',   # Assuming your user service is running on port 5000
    'medications': 'http://localhost:5001'  # Assuming your medications service is running on port 5001
}

@app.route('/<service_name>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def gateway(service_name, path):
    if service_name in SERVICE_MAP:
        service_url = f"{SERVICE_MAP[service_name]}/{path}"
        method = request.method
        resp = requests.request(method=method, url=service_url, headers=request.headers, params=request.args, json=request.json)
        return jsonify(resp.json()), resp.status_code
    else:
        return jsonify({'error': 'Service not found'}), 404

if __name__ == '__main__':
    app.run(port=5004, debug=True)
