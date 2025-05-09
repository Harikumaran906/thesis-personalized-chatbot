import os
import psycopg2
from urllib.parse import urlparse

def connect():
    result = urlparse(os.getenv("DATABASE_URL"))
    return psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )

def init_db():
    conn = connect()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            birthdate TEXT,
            answer_length TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            role TEXT,
            content TEXT,
            topic TEXT,
            is_confused INTEGER DEFAULT 0,
            source TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS topic_scores (
            user_id INTEGER,
            topic TEXT,
            score INTEGER,
            status TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id SERIAL PRIMARY KEY,
            title TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS subtopics (
            id SERIAL PRIMARY KEY,
            topic_id INTEGER,
            title TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id INTEGER,
            topic_id INTEGER,
            subtopic_id INTEGER,
            status TEXT,
            PRIMARY KEY (user_id, subtopic_id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_difficulty (
            user_id INTEGER,
            topic TEXT,
            level TEXT,
            PRIMARY KEY (user_id, topic)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            current_topic_id INTEGER
        )
    ''')

    conn.commit()
    conn.close()

def add_user(username, password, birthdate, answer_length):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (username, password, birthdate, answer_length)
        VALUES (%s, %s, %s, %s)
    ''', (username, password, birthdate, answer_length))
    conn.commit()
    conn.close()

def get_user(username, password):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_answer_length(user_id, new_length):
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE users SET answer_length = %s WHERE id = %s", (new_length, user_id))
    conn.commit()
    conn.close()

def save_message(user_id, role, content, topic=None, source=None, is_confused=0):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        INSERT INTO messages (user_id, role, content, topic, is_confused, source)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (user_id, role, content, topic, is_confused, source))
    conn.commit()
    conn.close()

def get_full_chat(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        SELECT role, content, topic, source, timestamp
        FROM messages
        WHERE user_id = %s
        ORDER BY id
    ''', (user_id,))
    all_chat = c.fetchall()
    conn.close()
    return all_chat

def save_score(user_id, topic, score, status):
    conn = connect()
    c = conn.cursor()
    c.execute('SELECT * FROM topic_scores WHERE user_id = %s AND topic = %s', (user_id, topic))
    existing = c.fetchone()
    if existing:
        c.execute('''
            UPDATE topic_scores
            SET score = %s, status = %s
            WHERE user_id = %s AND topic = %s
        ''', (score, status, user_id, topic))
    else:
        c.execute('''
            INSERT INTO topic_scores (user_id, topic, score, status)
            VALUES (%s, %s, %s, %s)
        ''', (user_id, topic, score, status))
    conn.commit()
    conn.close()

def get_completed_topic_scores(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        SELECT topic, score, status
        FROM topic_scores
        WHERE user_id = %s
    ''', (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_topics():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, title FROM topics")
    topics = c.fetchall()
    conn.close()
    return topics

def get_subtopics_by_topic(topic_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, title FROM subtopics WHERE topic_id = %s", (topic_id,))
    subtopics = c.fetchall()
    conn.close()
    return subtopics

def get_next_subtopic(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        SELECT s.id, s.title, t.id, t.title
        FROM subtopics s
        JOIN topics t ON s.topic_id = t.id
        WHERE NOT EXISTS (
            SELECT 1 FROM user_progress
            WHERE user_id = %s AND subtopic_id = s.id AND status = 'completed'
        )
        ORDER BY s.id ASC
        LIMIT 1
    ''', (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def mark_subtopic_completed(user_id, topic_id, subtopic_id):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        INSERT INTO user_progress (user_id, topic_id, subtopic_id, status)
        VALUES (%s, %s, %s, 'completed')
        ON CONFLICT (user_id, subtopic_id) DO UPDATE SET status = EXCLUDED.status
    ''', (user_id, topic_id, subtopic_id))
    conn.commit()
    conn.close()

def is_subtopic_completed(user_id, subtopic_id):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        SELECT 1 FROM user_progress
        WHERE user_id = %s AND subtopic_id = %s AND status = 'completed'
    ''', (user_id, subtopic_id))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_topic_title(topic_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT title FROM topics WHERE id = %s", (topic_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_first_subtopic(topic_id):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        SELECT s.id, s.title, t.id, t.title
        FROM subtopics s
        JOIN topics t ON s.topic_id = t.id
        WHERE t.id = %s
        ORDER BY s.id ASC
        LIMIT 1
    ''', (topic_id,))
    result = c.fetchone()
    conn.close()
    return result

def save_difficulty(user_id, topic, level):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        INSERT INTO user_difficulty (user_id, topic, level)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, topic) DO UPDATE SET level = EXCLUDED.level
    ''', (user_id, topic, level))
    conn.commit()
    conn.close()

def get_difficulty_levels(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        SELECT topic, level
        FROM user_difficulty
        WHERE user_id = %s
    ''', (user_id,))
    difficulty_map = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return difficulty_map

def reset_subtopics(user_id, topic_id):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        DELETE FROM user_progress
        WHERE user_id = %s AND topic_id = %s
    ''', (user_id, topic_id))
    conn.commit()
    conn.close()

def set_current_topic(user_id, topic_id):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        INSERT INTO user_settings (user_id, current_topic_id)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET current_topic_id = EXCLUDED.current_topic_id
    ''', (user_id, topic_id))
    conn.commit()
    conn.close()

def get_completed_subtopic_ids(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute('''
        SELECT subtopic_id
        FROM user_progress
        WHERE user_id = %s AND status = 'completed'
    ''', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]
