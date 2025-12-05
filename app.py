from flask import Flask, request, jsonify, render_template_string
import os
from dotenv import load_dotenv
import smtplib, ssl, random, sqlite3, hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
app = Flask(__name__)

# SQLite Users DB (логин + хэш пароля)
def init_users_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

init_users_db()

class EmailAuth:
    def __init__(self):
        self.smtp_email = os.getenv('SMTP_EMAIL')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
    
    def send_password(self, email):
        """Отправляет текущий пароль на email"""
        # Проверяем существует ли пользователь
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return False, "Пользователь не найден"
        
        password = self._hash_to_plain(user[0])  # В реальности храните plain или расшифруйте
        
        # Отправка пароля
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_email
            msg['To'] = email
            msg['Subject'] = 'Ваш пароль Dark Chat'
            
            body = f"""Ваш пароль для входа в Dark Chat:

📧 Email: {email}
🔑 Пароль: {password}

Войдите на сайте и используйте эти данные."""
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
                server.login(self.smtp_email, self.smtp_password)
                server.sendmail(self.smtp_email, email, msg.as_string())
            
            return True, "Пароль отправлен на email"
            
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def _hash_to_plain(self, hash_val):
        """Демо: конвертирует хэш обратно в пароль (в реальности храните plain)"""
        # Для демо возвращаем простой пароль
        return "DarkChat2025"
    
    def login(self, email, password):
        """Проверка логина/пароля"""
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and self._hash_to_plain(user[0]) == password:
            return True, "Успешный вход"
        return False, "Неверный пароль"

auth = EmailAuth()

# ✅ Главная страница с формой!
@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if '@' not in email:
            return render_template_string(HTML_TEMPLATE, error="Неверный email")
        
        success, message = auth.send_password(email)
        if success:
            return render_template_string(HTML_TEMPLATE, 
                success="Пароль отправлен на вашу почту!", email=email)
        else:
            return render_template_string(HTML_TEMPLATE, error=message)
    
    return render_template_string(HTML_TEMPLATE)

# ✅ API для мобильного/JS
@app.route('/send_password', methods=['POST'])
def send_password_api():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    
    if not email or '@' not in email:
        return jsonify({'error': 'Неверный email'}), 400
    
    success, message = auth.send_password(email)
    return jsonify({'success': success, 'message': message})

@app.route('/login', methods=['POST'])
def login_api():
    data = request.get_json() or {}
    success, message = auth.login(data.get('email'), data.get('password'))
    return jsonify({'success': success, 'message': message})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK'})

# HTML форма для браузера
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dark Chat - Вход</title>
    <style>
        body { font-family: Arial; max-width: 400px; margin: 100px auto; padding: 20px; }
        input[type="email"] { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { width: 100%; padding: 12px; background: #4285f4; color: white; border: none; border-radius: 5px; font-size: 16px; }
        .error { color: red; background: #ffe6e6; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { color: green; background: #e6ffe6; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .info { background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <h2>🔐 Dark Chat - Получить пароль</h2>
    {% if success %}
        <div class="success">{{ success }}</div>
        <div class="info">Проверьте почту: <b>{{ email }}</b></div>
        <p><small>Пароль отправлен! Войдите с полученными данными.</small></p>
    {% elif error %}
        <div class="error">{{ error }}</div>
    {% endif %}
    
    <form method="POST">
        <input type="email" name="email" placeholder="Введите email" required>
        <button type="submit">📧 Отправить пароль на почту</button>
    </form>
    
    <p><small><a href="/health">API Status</a></small></p>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
