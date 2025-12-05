from flask import Flask, request, jsonify, render_template_string
import os
from dotenv import load_dotenv
import smtplib, ssl, random, sqlite3, hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
app = Flask(__name__)

# ✅ Инициализация БД с тестовыми пользователями
def init_users_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor = conn.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        print("Создаем тестовых пользователей...")
        test_users = [
            ('test@example.com', 'DarkChat2025'),
            ('user@gmail.com', 'DarkChat2025'),
            ('demo@darkchat.com', 'DarkChat2025')
        ]
        password_hash = hashlib.sha256('DarkChat2025'.encode()).hexdigest()
        for email, _ in test_users:
            conn.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', 
                        (email, password_hash))
        conn.commit()
        print("✅ Тестовые пользователи созданы!")
    
    conn.commit()
    conn.close()

init_users_db()

class EmailAuth:
    def __init__(self):
        self.smtp_email = os.getenv('SMTP_EMAIL')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
    
    def send_password(self, email):
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return False, f"Пользователь {email} не найден"
        
        password = "DarkChat2025"
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_email
            msg['To'] = email
            msg['Subject'] = '🔑 Ваш пароль Dark Chat'
            
            body = f"""Добро пожаловать в Dark Chat!

📧 Ваш email: {email}
🔑 Ваш пароль: {password}

👉 Войдите на сайте с этими данными."""
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
                server.login(self.smtp_email, self.smtp_password)
                server.sendmail(self.smtp_email, email, msg.as_string())
            
            return True, f"✅ Пароль отправлен на {email}"
            
        except Exception as e:
            return False, f"❌ Ошибка отправки: {str(e)}"
    
    def login(self, email, password):
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return False, "Пользователь не найден"
        
        expected_hash = hashlib.sha256("DarkChat2025".encode()).hexdigest()
        if user[0] == expected_hash:
            return True, "✅ Успешный вход!"
        return False, "❌ Неверный пароль"

auth = EmailAuth()

# ✅ HTML_TEMPLATE (ОБЯЗАТЕЛЬНО!)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dark Chat - Вход</title>
    <style>
        body { 
            font-family: Arial; 
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
            color: #e0e0e0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .form-container {
            background: rgba(0, 0, 0, 0.9);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            min-width: 350px;
            text-align: center;
        }
        h2 { color: #00d4ff; margin-bottom: 30px; }
        input { 
            width: 100%; padding: 15px; margin: 10px 0; 
            background: rgba(255,255,255,0.05); 
            border: 2px solid rgba(255,255,255,0.1); 
            border-radius: 10px; 
            color: #fff; font-size: 16px;
        }
        input:focus { border-color: #00d4ff; outline: none; }
        button { 
            width: 100%; padding: 15px; margin: 10px 0; 
            background: linear-gradient(45deg, #00d4ff, #0099cc); 
            border: none; border-radius: 10px; color: white; 
            font-size: 16px; cursor: pointer;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,212,255,0.4); }
        .error { color: #ff4444; background: #ffe6e6; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { color: #44ff44; background: #e6ffe6; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .info { background: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0; }
        a { color: #00d4ff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="form-container">
        <h2>🌙 Dark Chat</h2>
        {% if success %}
            <div class="success">{{ success }}</div>
            <div class="info">Проверьте почту: <b>{{ email }}</b></div>
        {% elif error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST">
            <input type="email" name="email" placeholder="📧 Введите email" value="{{ email or '' }}" required>
            <button type="submit">📧 Отправить пароль</button>
        </form>
        
        <p><small><a href="/health">API Status</a> | <a href="/users">Тестовые пользователи</a></small></p>
    </div>
</body>
</html>
'''

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

@app.route('/users', methods=['GET'])
def list_users():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM users')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify({'users': users})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
