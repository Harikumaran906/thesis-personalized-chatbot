import psycopg2
import os

# Connect to PostgreSQL using DATABASE_URL from environment variables
def connect():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# Initialize database and create tables
def init_db():
    conn = connect()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT,
                    edu_level TEXT,
                    birthdate TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    role TEXT,
                    content TEXT
                )''')
    conn.commit()
    conn.close()

# Add a new user
def add_user(username, password, edu_level, birthdate):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, edu_level, birthdate) VALUES (%s, %s, %s, %s)",
              (username, password, edu_level, birthdate))
    conn.commit()
    conn.close()

# Get user by username and password
def get_user(username, password):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = c.fetchone()
    conn.close()
    return user

# Get user by ID (for profile page)
def get_user_by_id(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

# Save a message (chat)
def save_message(user_id, role, content):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, role, content) VALUES (%s, %s, %s)",
              (user_id, role, content))
    conn.commit()
    conn.close()

# Get all messages (chat history) for a user
def get_messages(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE user_id = %s", (user_id,))
    history = c.fetchall()
    conn.close()
    return history

# Clear chat history for a user
def clear_chat_history(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()

# Update study level in profile
def update_study_level(user_id, edu_level):
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE users SET edu_level = %s WHERE id = %s", (edu_level, user_id))
    conn.commit()
    conn.close()
