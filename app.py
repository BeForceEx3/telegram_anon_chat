from flask import Flask, request, jsonify
from config import Config
from verifier import EmailVerification
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config.from_object(Config)

verifier = EmailVerification()

@app.route('/send_code', methods=['POST'])
def send_code(): ...

@app.route('/verify_code', methods=['POST'])
def verify_code(): ...

@app.route('/health', methods=['GET'])
def health(): ...

if __name__ == '__main__':
    app.run(debug=True)
