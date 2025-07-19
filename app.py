from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# URLs des autres services
CREATE_VM_URL = "https://webhook-ec2-api.onrender.com/create-vm"
CREATE_USER_URL = "https://webservice-guacservice.onrender.com/create-user"
CREATE_CONNECTION_URL = "https://webhook-api-new-vm.onrender.com/create-connection"
FINAL_LOGIN_URL = "https://webhook-api-generate-url.onrender.com/api/final-login"

@app.route("/create-full-vm", methods=["POST"])
def create_full_vm():
    try:
        data = request.get_json()
        ami = data.get("ami")
        instance_type = data.get("instance_type")
        username = data.get("username")

        if not all([ami, instance_type, username]):
            return jsonify({"error": "Missing ami, instance_type or username"}), 400

        # Étape 1 - Créer la VM
        vm_payload = {
            "ami": ami,
            "instance_type": instance_type,
            "username": username
        }
        vm_response = requests.post(CREATE_VM_URL, json=vm_payload)
        vm_data = vm_response.json()

        if vm_response.status_code != 200:
            return jsonify({"error": "EC2 creation failed", "details": vm_data}), 500

        public_ip = vm_data["public_ip"]
        private_key = vm_data["pem_key"]

        # Étape 2 - Créer l'utilisateur Guacamole
        user_payload = {"email": username}
        user_response = requests.post(CREATE_USER_URL, json=user_payload)
        user_data = user_response.json()

        if user_response.status_code != 200 or not user_data.get("username"):
            return jsonify({"error": "Guacamole user creation failed", "details": user_data}), 500

        guac_username = user_data["username"]

        # Étape 3 - Créer la connexion Guacamole
        conn_payload = {
            "ip": public_ip,
            "private_key": private_key,
            "connection_protocol": "ssh",
            "connection_name": f"SSH - {public_ip}",
            "username": guac_username
        }
        conn_response = requests.post(CREATE_CONNECTION_URL, json=conn_payload)
        conn_data = conn_response.json()

        if conn_response.status_code != 201 or not conn_data.get("connection_id"):
            return jsonify({"error": "Guacamole connection failed", "details": conn_data}), 500

        connection_id = conn_data["connection_id"]

        # Étape 4 - Générer l'URL finale
        login_payload = {
            "username": guac_username,
            "connection_id": str(connection_id)
        }
        login_response = requests.post(FINAL_LOGIN_URL, json=login_payload)
        login_data = login_response.json()

        if login_response.status_code != 200 or not login_data.get("redirect_url"):
            return jsonify({"error": "Final login URL generation failed", "details": login_data}), 500

        return jsonify({
            "username": guac_username,
            "connection_id": connection_id,
            "redirect_url": login_data["redirect_url"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
