from flask import Flask, render_template, request, redirect, session, url_for
from database import init_db, add_user, get_user, get_user_by_id, save_message, get_messages, clear_chat_history, update_study_level

from openai_srvr import get_ai_answer
import os

app = Flask(__name__, static_folder="../static", template_folder="templates")
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    if 'user_id' in session:
        history = get_messages(session['user_id'])
        return render_template('index.html', username=session['username'], history=history, edu_level=session.get('edu_level', 'elementary'))
    return redirect(url_for('login'))

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data['user_input']
    edu_level = data['edu_level']
    course = data.get('course', '')
    ai_answer = get_ai_answer(user_input, edu_level, course)
    save_message(session['user_id'], 'user', user_input)
    save_message(session['user_id'], 'bot', ai_answer)
    return {'ai_answer': ai_answer}



@app.route('/clear')
def clear():
    clear_chat_history(session['user_id'])
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        edu_level = request.form['edu_level']
        birthdate = request.form['birthdate']
        add_user(username, password, edu_level, birthdate)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username, password)
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['edu_level'] = user[3]
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        edu_level = request.form['edu_level']
        update_study_level(session['user_id'], edu_level)
        session['edu_level'] = edu_level

    user = get_user_by_id(session['user_id'])
    return render_template('profile.html', username=user[1], edu_level=user[3], birthdate=user[4])


if __name__ == "__main__":
    init_db()
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

