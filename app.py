from flask import Flask, request, jsonify
import requests
import time

app = Flask(__name__)

CREATE_VM_URL = "https://webhook-ec2-api.onrender.com/create-vm"
CREATE_CONNECTION_URL = "https://webhook-api-new-vm.onrender.com/create-connection"

@app.route('/create-vm-connection', methods=['POST'])
def create_vm_connection():
    data = request.json
    ami = data.get("ami")
    instance_type = data.get("instance_type")
    username = data.get("username")

    if not ami or not instance_type or not username:
        return jsonify({"error": "Missing required fields"}), 400

    # Étape 1 : Création de la VM
    vm_response = requests.post(CREATE_VM_URL, json={
        "ami": ami,
        "instance_type": instance_type,
        "username": username
    })

    if vm_response.status_code != 200:
        return jsonify({"error": "VM creation failed", "details": vm_response.text}), 500

    vm_data = vm_response.json()
    private_ip = vm_data.get("private_ip")
    private_key = vm_data.get("pem_key")

    if not private_ip or not private_key:
        return jsonify({"error": "Missing VM info"}), 500

    # Attente (si besoin, sinon à adapter dynamiquement)
    time.sleep(5)

    # Étape 2 : Création de la connexion Guacamole
    connection_payload = {
        "ip": private_ip,
        "private_key": private_key,
        "connection_protocol": "ssh",
        "connection_name": f"SSH - {private_ip}"
    }

    connection_response = requests.post(CREATE_CONNECTION_URL, json=connection_payload)

    if connection_response.status_code != 200:
        return jsonify({"error": "Connection creation failed", "details": connection_response.text}), 500

    return jsonify(connection_response.json())

if __name__ == '__main__':
    app.run(debug=True)
