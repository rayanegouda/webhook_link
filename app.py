from flask import Flask, request, jsonify
import requests
import time

app = Flask(__name__)  # ✅ Cette ligne doit venir AVANT le @app.route

# 🔧 URLs de vos services backend
CREATE_VM_URL = "https://webhook-ec2-api.onrender.com/create-vm"  # À adapter
CREATE_CONNECTION_URL = "https://webhook-api-new-vm.onrender.com/create-connection"  # À adapter


@app.route('/create-vm-connection', methods=['POST'])
def create_vm_connection():
    try:
        data = request.json
        print("[INFO] Requête reçue :", data)

        ami = data.get("ami")
        instance_type = data.get("instance_type")
        username = data.get("username")

        if not ami or not instance_type or not username:
            print("[ERROR] Champs manquants")
            return jsonify({"error": "Missing required fields"}), 400

        print("[INFO] Création de la VM en cours...")

        vm_response = requests.post(CREATE_VM_URL, json={
            "ami": ami,
            "instance_type": instance_type,
            "username": username
        })

        print("[INFO] Statut VM :", vm_response.status_code)
        print("[INFO] Réponse VM :", vm_response.text)

        if vm_response.status_code != 200:
            return jsonify({"error": "VM creation failed", "details": vm_response.text}), 500

        vm_data = vm_response.json()
        public_ip = vm_data.get("public_ip")
        private_key = vm_data.get("pem_key")

        if not public_ip or not private_key:
            print("[ERROR] IP ou clé privée manquante")
            return jsonify({"error": "Missing VM info"}), 500

        print("[INFO] Délai d’attente avant connexion Guacamole...")
        time.sleep(5)

        print("[INFO] Connexion Guacamole en cours...")

        connection_payload = {
            "ip": public_ip,
            "private_key": private_key,
            "connection_protocol": "ssh",
            "connection_name": f"SSH - {public_ip}"
        }

        connection_response = requests.post(CREATE_CONNECTION_URL, json=connection_payload, timeout=30)

        print("[INFO] Statut Guacamole :", connection_response.status_code)
        print("[INFO] Réponse Guacamole :", connection_response.text)

        if connection_response.status_code not in [200, 201]:
            return jsonify({"error": "Connection creation failed", "details": connection_response.text}), 500

        print("[SUCCESS] Connexion établie")
		#return jsonify({"status": "success","vm_details": vm_data,"guacamole_connection": connection_response.json()}), 200
        return jsonify(connection_response.json())

    except Exception as e:
        import traceback
        print("[EXCEPTION]", str(e))
        traceback.print_exc()
        return jsonify({"error": "Unexpected error occurred"}), 500
