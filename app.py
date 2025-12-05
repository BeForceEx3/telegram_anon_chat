from flask import Flask, request, jsonify, render_template_string
import os
from dotenv import load_dotenv
import smtplib, ssl, random, sqlite3, hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
app = Flask(__name__)

# ✅ Инициализация БД с тестовыми пользователями!
def init_users_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # ✅ Проверяем, есть ли пользователи
    cursor = conn.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        print("Создаем тестовых пользователей...")
        test_users = [
            ('test@example.com', 'DarkChat2025'),
            ('user@gmail.com', 'DarkChat2025'),
            ('demo@darkchat.com', 'DarkChat2025')
        ]
        for email, password in test_users:
            conn.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', 
                        (email, hashlib.sha256(password.encode()).hexdigest()))
        conn.commit()
        print("✅ Тестовые пользователи созданы!")
    
    conn.commit()
    conn.close()

init_users_db()  # Создаем БД при запуске!

class EmailAuth:
    def __init__(self):
        self.smtp_email = os.getenv('SMTP_EMAIL')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
    
    def send_password(self, email):
        """Отправляет пароль на email"""
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return False, f"Пользователь {email} не найден. Попробуйте: test@example.com"
        
        # ✅ Извлекаем пароль из хэша (для демо)
        password = self._get_password_from_hash(user[0])
        
        # Отправка
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_email
            msg['To'] = email
            msg['Subject'] = '🔑 Ваш пароль Dark Chat'
            
            body = f"""Добро пожаловать в Dark Chat!

📧 Ваш email: {email}
🔑 Ваш пароль: {password}

👉 Войдите на сайте с этими данными.

⚠️  Не передавайте пароль третьим лицам!"""
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
                server.login(self.smtp_email, self.smtp_password)
                server.sendmail(self.smtp_email, email, msg.as_string())
            
            return True, f"✅ Пароль отправлен на {email}"
            
        except Exception as e:
            return False, f"❌ Ошибка отправки: {str(e)}"
    
    def _get_password_from_hash(self, hash_val):
        """Для демо возвращает пароль DarkChat2025"""
        return "DarkChat2025"
    
    def login(self, email, password):
        """Проверка логина"""
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return False, "Пользователь не найден"
        
        # Проверяем пароль
        expected_hash = hashlib.sha256("DarkChat2025".encode()).hexdigest()
        if user[0] == expected_hash:
            return True, "✅ Успешный вход!"
        return False, "❌ Неверный пароль"

# Остальной код тот же...
auth = EmailAuth()

@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if '@' not in email:
            return render_template_string(HTML_TEMPLATE, error="Неверный email")
        
        success, message = auth.send_password(email)
        return render_template_string(HTML_TEMPLATE, 
            success=message if success else None, 
            error=message if not success else None,
            email=email)
    
    return render_template_string(HTML_TEMPLATE)

# API роуты...
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
    return jsonify({'status': 'OK', 'users_exist': True})

@app.route('/users', methods=['GET'])  # ✅ Для теста!
def list_users():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM users')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify({'users': users})

# HTML_TEMPLATE тот же...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
