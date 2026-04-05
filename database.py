import sqlite3

def init_db():
    conn = sqlite3.connect("study_bot.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    conn.commit()
    conn.close()

def add_user_if_not_exists(user_id):
    conn = sqlite3.connect("study_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def add_task(user_id, text):
    conn = sqlite3.connect("study_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (user_id, text) VALUES (?, ?)", (user_id, text))
    conn.commit()
    conn.close()

def get_tasks(user_id):
    conn = sqlite3.connect("study_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, text FROM tasks WHERE user_id = ?", (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def delete_task(task_id):
    conn = sqlite3.connect("study_bot.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def update_xp(user_id, amount):
    conn = sqlite3.connect("study_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET xp = xp + ? WHERE user_id = ?", (amount, user_id))
    cursor.execute("SELECT xp FROM users WHERE user_id = ?", (user_id,))
    xp = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return xp