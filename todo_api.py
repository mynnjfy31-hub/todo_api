from flask import Flask, request, jsonify
import sqlite3
import hashlib
import datetime

app = Flask(__name__)

# ===== اتصال به دیتابیس =====
def get_db():
    conn = sqlite3.connect('todo.db')
    conn.row_factory = sqlite3.Row
    return conn

# ===== هش کردن رمز =====
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ===== ساخت دیتابیس =====
def create_db():
    conn = sqlite3.connect('todo.db')
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            due_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ دیتابیس todo.db ساخته شد!")

# ==================== کاربران ====================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({"error": "نام، ایمیل و رمز الزامی است"}), 400

    hashed = hash_password(password)
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                    (name, email, hashed))
        db.commit()
        user_id = cur.lastrowid
        db.close()
        return jsonify({"id": user_id, "message": "ثبت‌نام موفق!"}), 201
    except sqlite3.IntegrityError:
        db.close()
        return jsonify({"error": "این ایمیل قبلاً ثبت شده است"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "ایمیل و رمز الزامی است"}), 400

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    db.close()

    if user and user['password'] == hash_password(password):
        return jsonify({
            "message": "خوش آمدی!",
            "user_id": user['id'],
            "name": user['name']
        }), 200

    return jsonify({"error": "ایمیل یا رمز اشتباه است"}), 401

# ==================== دسته‌بندی‌ها ====================

@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.get_json()
    name = data.get('name')
    user_id = data.get('user_id')

    if not name or not user_id:
        return jsonify({"error": "نام و user_id الزامی است"}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute('INSERT INTO categories (name, user_id) VALUES (?, ?)', (name, user_id))
    db.commit()
    cat_id = cur.lastrowid
    db.close()
    return jsonify({"id": cat_id, "message": "دسته اضافه شد"}), 201

@app.route('/api/categories/<int:user_id>', methods=['GET'])
def get_categories(user_id):
    db = get_db()
    cats = db.execute('SELECT * FROM categories WHERE user_id = ?', (user_id,)).fetchall()
    db.close()
    return jsonify([dict(c) for c in cats])

# ==================== تسک‌ها ====================

@app.route('/api/tasks/<int:user_id>', methods=['GET'])
def get_tasks(user_id):
    db = get_db()
    tasks = db.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
    db.close()
    return jsonify([dict(t) for t in tasks])

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    title = data.get('title')
    user_id = data.get('user_id')

    if not title or not user_id:
        return jsonify({"error": "عنوان و user_id الزامی است"}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute('''
        INSERT INTO tasks (title, description, status, priority, due_date, user_id, category_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        title,
        data.get('description'),
        data.get('status', 'pending'),
        data.get('priority', 'medium'),
        data.get('due_date'),
        user_id,
        data.get('category_id')
    ))
    db.commit()
    task_id = cur.lastrowid
    db.close()
    return jsonify({"id": task_id, "message": "تسک اضافه شد"}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    db = get_db()
    cur = db.cursor()

    existing = cur.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({"error": "تسک پیدا نشد"}), 404

    if data.get('title'):
        cur.execute('UPDATE tasks SET title = ? WHERE id = ?', (data['title'], task_id))
    if data.get('description'):
        cur.execute('UPDATE tasks SET description = ? WHERE id = ?', (data['description'], task_id))
    if data.get('status'):
        cur.execute('UPDATE tasks SET status = ? WHERE id = ?', (data['status'], task_id))
    if data.get('priority'):
        cur.execute('UPDATE tasks SET priority = ? WHERE id = ?', (data['priority'], task_id))
    if data.get('due_date'):
        cur.execute('UPDATE tasks SET due_date = ? WHERE id = ?', (data['due_date'], task_id))
    if data.get('category_id'):
        cur.execute('UPDATE tasks SET category_id = ? WHERE id = ?', (data['category_id'], task_id))

    db.commit()
    db.close()
    return jsonify({"message": f"تسک {task_id} به‌روز شد"}), 200

@app.route('/api/tasks/<int:task_id>/complete', methods=['PUT'])
def complete_task(task_id):
    db = get_db()
    cur = db.cursor()
    existing = cur.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({"error": "تسک پیدا نشد"}), 404

    cur.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (task_id,))
    db.commit()
    db.close()
    return jsonify({"message": f"تسک {task_id} انجام شد"}), 200

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    db = get_db()
    cur = db.cursor()
    existing = cur.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if not existing:
        db.close()
        return jsonify({"error": "تسک پیدا نشد"}), 404

    cur.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    db.commit()
    db.close()
    return jsonify({"message": f"تسک {task_id} حذف شد"}), 200

# ===== اجرا =====
if __name__ == '__main__':
    create_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
