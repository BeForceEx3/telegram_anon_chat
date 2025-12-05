from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import smtplib, ssl, random, sqlite3, hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
app = Flask(__name__)

# ✅ Обязательный роут для Render!
@app.route('/')
def home():
    return jsonify({"status": "Dark Chat Verification API", "endpoints": ["/send_code", "/verify_code", "/health"]})

class EmailVerification:
    # ... (тот же код verifier.py)
    pass

verifier = EmailVerification()

@app.route('/send_code', methods=['POST'])
def send_code():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    
    if not email or '@' not in email:
        return jsonify({'error': 'Неверный email'}), 400
    
    success, message = verifier.send_code(email)
    return jsonify({'message': message}), 200 if success else 500

@app.route('/verify_code', methods=['POST'])
def verify_code():
    data = request.get_json() or {}
    success, message = verifier.verify_code(data.get('email'), data.get('code'))
    return jsonify({'success': success, 'message': message})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
