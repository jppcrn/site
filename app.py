from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/log', methods=['POST'])
def log_data():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent')
    data = request.get_json()

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print("\n===== NOVO ACESSO =====")
    print("Data/Hora:", agora)
    print("IP:", ip)
    print("User-Agent:", user_agent)
    print("Latitude:", latitude)
    print("Longitude:", longitude)
    print("=======================\n")

    return jsonify({
        "status": "ok",
        "data_hora": agora,
        "ip": ip,
        "user_agent": user_agent,
        "latitude": latitude,
        "longitude": longitude
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
