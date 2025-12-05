from flask import Flask, request, jsonify, render_template_string
import os
from dotenv import load_dotenv
import sqlite3, hashlib, random
from datetime import datetime, timedelta
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

load_dotenv()
app = Flask(__name__)

sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
FROM_EMAIL = os.getenv('SMTP_EMAIL', 'noreply@darkchat.com')

def init_codes_db():
    conn = sqlite3.connect('codes.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS codes (
        id INTEGER PRIMARY KEY,
        email_hash TEXT UNIQUE NOT NULL,
        code TEXT NOT NULL,
        is_valid INTEGER DEFAULT 1,
        attempts INTEGER DEFAULT 0,
        expires_at TEXT
    )''')
    conn.commit()
    conn.close()

init_codes_db()

class SimpleEmailAuth:
    def generate_code(self):
        return str(random.randint(100000, 999999))
    
    def hash_email(self, email):
        return hashlib.sha256(email.lower().encode()).hexdigest()
    
    def send_code(self, email):
        code = self.generate_code()
        email_hash = self.hash_email(email)
        expires_at = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect('codes.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO codes (email_hash, code, expires_at, attempts)
            VALUES (?, ?, ?, 0)
        ''', (email_hash, code, expires_at))
        conn.commit()
        conn.close()
        
        try:
            message = Mail(
                from_email=Email(FROM_EMAIL),
                to_emails=To(email),
                subject='🔐 Код авторизации Dark Chat',
                plain_text_content=Content(
                    f"Ваш код авторизации Dark Chat:\n\n🔢 Код: {code}\n\n⏰ Действует 10 минут"
                )
            )
            response = sg.send(message)
            return True, "Код отправлен!"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def verify_code(self, email, code):
        email_hash = self.hash_email(email)
        conn = sqlite3.connect('codes.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT code, is_valid, attempts, expires_at FROM codes WHERE email_hash = ?', (email_hash,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False, "Код не найден"
        
        stored_code, is_valid, attempts, expires_at = result
        
        if datetime.now() > datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S'):
            return False, "Код истек"
        
        if stored_code != code:
            return False, "Неверный код"
        
        cursor.execute('UPDATE codes SET is_valid = 0 WHERE email_hash = ?', (email_hash,))
        conn.commit()
        conn.close()
        return True, "✅ Добро пожаловать!"

auth = SimpleEmailAuth()

HTML_TEMPLATE = '''<!DOCTYPE html>
<html><head><title>Dark Chat</title>
<style>
body { font-family: Arial; background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%); color: #e0e0e0; height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
.form { background: rgba(0,0,0,0.95); padding: 40px; border-radius: 25px; min-width: 380px; text-align: center; box-shadow: 0 25px 50px rgba(0,0,0,0.8); }
h2 { color: #00d4ff; margin-bottom: 30px; }
input { width: 100%; padding: 18px; margin: 15px 0; background: rgba(255,255,255,0.08); border: 2px solid rgba(255,255,255,0.15); border-radius: 15px; color: #fff; font-size: 20px; text-align: center; }
button { width: 100%; padding: 18px; margin: 15px 0; background: linear-gradient(45deg, #00d4ff, #0099cc); border: none; border-radius: 15px; color: white; font-size: 18px; cursor: pointer; }
.error { color: #ff6b6b; background: rgba(255,107,107,0.15); padding: 15px; border-radius: 10px; margin: 15px 0; }
.success { color: #51cf66; background: rgba(81,207,102,0.15); padding: 15px; border-radius: 10px; margin: 15px 0; }
</style></head>
<body>
<div class="form">
<h2>🌙 Dark Chat</h2>
{% if step == "code" %}
<div class="success">✅ Код отправлен на <b>{{ email }}</b></div>
<form method="POST">
<input type="hidden" name="email" value="{{ email }}">
<input type="text" name="code" placeholder="🔢 6-значный код" maxlength="6" required autofocus>
<button>✅ Войти</button>
</form>
{% else %}
<form method="POST">
<input type="email" name="email" placeholder="📧 Любой email" required autofocus>
<button>📧 Отправить код</button>
</form>{% endif %}
{% if error %}<div class="error">{{ error }}</div>{% endif %}
</div>
<script>
document.addEventListener("DOMContentLoaded", function() {
    document.querySelector("input").focus();
    document.querySelector("input").addEventListener("keypress", function(e) {
        if (e.key === "Enter") this.form.submit();
    });
});
</script>
</body></html>'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        code = request.form.get('code', '').strip()
        
        if code:
            success, message = auth.verify_code(email, code)
            return render_template_string(HTML_TEMPLATE, 
                success=message if success else None,
                error=message if not success else None,
                step='code', email=email)
        else:
            success, message = auth.send_code(email)
            return render_template_string(HTML_TEMPLATE, step='code', email=email)
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
