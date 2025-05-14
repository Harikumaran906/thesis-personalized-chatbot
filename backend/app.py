import markdown
from flask import Flask, render_template, request, redirect, session, jsonify
from backend.database import *
from backend.openai_srvr import (doubt_answer, guided_answer, generate_quiz_qn, grade_quiz, initial_tst_qn, grade_initial_tst)

app = Flask(__name__, static_folder='../static', template_folder='templates')
app.secret_key = 'Kumaran@123'

def categorize_topic(title):
    if "ARTIFICIAL INTELLIGENCE" in title:
        return "AI Basics"
    elif "MACHINE LEARNING" in title:
        return "Machine Learning"
    elif "NEURAL NETWORK" in title:
        return "Neural Networks"
    elif "SEARCH" in title or "STATE SPACE" in title:
        return "Search Algorithms"
    elif "KNOWLEDGE REPRESENTATION" in title:
        return "Expert Systems"

@app.route('/')
def home():
    session.clear()
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        birthdate = request.form['birthdate']
        answer_length = request.form['answer_length']
        if get_user(username, password):
            return render_template('register.html', error="Username already exists. Choose a different one.")

        add_user(username, password, birthdate, answer_length)
        user = get_user(username, password)
        session['user_id'] = user[0]
        session['username'] = user[1]
        return redirect('/main')
    return render_template('register.html')


@app.route('/diagnostic', methods=['POST'])
def diagnostic():
    user_id = session['user_id']
    user = get_user_by_id(user_id)

    if 'q1' in request.form:
        questions = []
        for i in range(1, 26):
            q = request.form.get(f'q{i}')
            selected = request.form.get(f'selected{i}')
            correct = request.form.get(f'correct{i}')
            category = request.form.get(f'category{i}')
            if q and selected and correct and category:
                questions.append({
                    "question": q,
                    "selected": selected,
                    "correct": correct,
                    "category": category
                })

        difficulty_map = grade_initial_tst(questions)
        all_topics = dict(get_all_topics())
        selected_ids = get_pref_topic(user_id)
        for tid in selected_ids:
            title = all_topics[tid]
            category = categorize_topic(title)
            level = difficulty_map.get(category, "Beginner")
            save_difficulty(user_id, title, level)

        session['username'] = user[1]
        return redirect('/main')

    selected_ids = get_pref_topic(user_id)
    all_topics = dict(get_all_topics())
    selected_titles = [all_topics[tid] for tid in selected_ids if tid in all_topics]
    selected_categories = set()
    for title in selected_titles:
        cat = categorize_topic(title)
        if cat:
            selected_categories.add(cat)

    all_questions = initial_tst_qn()
    questions = [q for q in all_questions if q["category"] in selected_categories][:25]

    return render_template('diagnostic.html',
                           diagnostic_questions=questions,
                           username=user[1])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = get_user(request.form['username'], request.form['password'])
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/main')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/main')
def main():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    selected_topics = get_pref_topic(user_id)
    if not selected_topics:
        return redirect('/select_topics')
    return render_template('menu.html', username=session['username'])


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    if request.method == 'POST':
        new_length = request.form['answer_length']
        update_answer_length(user[0], new_length)
        return redirect('/profile')

    all_topics = get_all_topics()
    completed_scores = get_completed_topic_scores(user_id)
    difficulty_levels = get_difficulty_levels(user_id)
    completed_ids = set(get_completed_subtopic_ids(user_id))
    score_map = {}
    for topic_id, topic_title in all_topics:
        all_subs = get_subtopics_by_topic(topic_id) or []
        total = len(all_subs)
        completed = sum(1 for sub in all_subs if sub[0] in completed_ids)
        score_map[topic_title] = {
            "topic_id": topic_id,
            "score": "Not attempted",
            "progress": f"{completed}/{total}",
            "difficulty": difficulty_levels.get(topic_title, "N/A")
        }
    for topic, score, _ in completed_scores:
        if topic in score_map:
            score_map[topic]["score"] = f"{score}/5"
    return render_template('profile.html',
                           username=user[1],
                           birthdate=user[3],
                           answer_length=user[6],
                           topic_scores=score_map)

@app.route('/set_current_topic/<int:topic_id>', methods=['POST'])
def handle_set_current_topic(topic_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    reset_subtopics(user_id, topic_id)
    set_current_topic(user_id, topic_id)
    return redirect('/profile')


@app.route('/chat', methods=['GET'])
def chat_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html',
                           username=session['username'],
                           guided_response=None,
                           current_topic=None,
                           current_subtopic_title=None,
                           current_subtopic_id=None,
                           current_subtopic_index=None,
                           total_subtopics=None,
                           show_next_button=False,
                           message=None)

@app.route('/chat', methods=['POST'])
def handle_chat():
    data = request.get_json()
    doubt = data['doubt']

    user_id = session['user_id']
    user = get_user_by_id(user_id)
    answer_length = user[6]  # short / medium / detailed

    conn = connect()
    c = conn.cursor()
    c.execute('''
        SELECT topic, content
        FROM messages
        WHERE user_id = %s AND role = 'user' AND source = 'guided'
        ORDER BY id DESC
        LIMIT 1
    ''', (user_id,))
    row = c.fetchone()
    conn.close()

    topic = "General"
    subtopic_title = None
    ref_explanation = ""
    if row:
        topic, guided_msg = row
        if "–" in guided_msg:
            subtopic_title = guided_msg.split("–", 1)[1].strip()
            ref_explanation = guided_answer(topic, subtopic_title, answer_length)

    prompt = f"""Doubt Explanation Context
Topic: {topic}
Subtopic: {subtopic_title or 'N/A'}
Explanation Style: {answer_length}

Explanation:
{ref_explanation}

Doubt:
{doubt}
"""

    raw = doubt_answer(prompt, answer_length, topic, subtopic_title)
    answer = markdown.markdown(raw)

    save_message(user_id, 'user', doubt, topic=topic, source='doubt')
    save_message(user_id, 'bot', answer, topic=topic, source='doubt')
    return jsonify({'ai_answer': answer})

@app.route('/start_guided', methods=['GET', 'POST'])
def start_guided():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    user = get_user_by_id(user_id)
    next_sub = get_next_subtopic(user_id)

    if not next_sub:
        return render_template('index.html',
                               username=session['username'],
                               guided_response="You've completed all available subtopics!",
                               current_subtopic=None,
                               current_topic=None,
                               current_subtopic_title=None,
                               current_subtopic_id=None,
                               current_subtopic_index=None,
                               total_subtopics=None,
                               show_next_button=False,
                               message=None)

    subtopic_id, subtopic_title, topic_id, topic = next_sub
    raw = guided_answer(topic, subtopic_title, user[6])
    explanation = markdown.markdown(raw)

    save_message(user_id, 'user', f"{topic} – {subtopic_title}", topic=topic, source='guided')
    save_message(user_id, 'bot', explanation, topic=topic, source='guided')

    subtopics = get_subtopics_by_topic(topic_id)
    tot_st = len(subtopics)
    subtopic_num = next(i for i, s in enumerate(subtopics, 1) if s[0] == subtopic_id)

    return render_template('index.html',
                           username=session['username'],
                           guided_response=explanation,
                           current_subtopic_id=subtopic_id,
                           current_subtopic_title=subtopic_title,
                           current_topic=topic,
                           current_subtopic_index=subtopic_num,
                           total_subtopics=tot_st,
                           show_next_button=False,
                           message=None)

@app.route('/mark_done', methods=['POST'])
def mark_done():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    subtopic_id = int(request.form['subtopic_id'])

    conn = connect()
    c = conn.cursor()
    c.execute("SELECT topic_id FROM subtopics WHERE id = %s", (subtopic_id,))
    row = c.fetchone()
    conn.close()

    if row:
        topic_id = row[0]
        mark_subtopic_completed(user_id, topic_id, subtopic_id)

        subtopics = get_subtopics_by_topic(topic_id)
        completed = [s[0] for s in subtopics if is_subtopic_completed(user_id, s[0])]
        if len(completed) == len(subtopics):
            topic = get_topic_title(topic_id)
            save_score(user_id, topic, 0, "Completed")
            remaining = [tid for tid in get_pref_topic(user_id) if tid != topic_id]
            if remaining:
                set_current_topic(user_id, remaining[0])

    return render_template('index.html',
                           username=session['username'],
                           guided_response="Subtopic marked as completed!",
                           current_subtopic=None,
                           current_topic=None,
                           current_subtopic_title=None,
                           current_subtopic_id=None,
                           current_subtopic_index=None,
                           total_subtopics=None,
                           show_next_button=True,
                           message="Subtopic marked as completed. Click below to continue.")

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    user_id = session['user_id']

    if request.method == 'POST':
        topic = request.form.get('topic')
        questions = []
        for i in range(1, 6):
            q = request.form.get(f'q{i}')
            a = request.form.get(f'selected{i}')
            c = request.form.get(f'correct{i}')
            if q and a and c:
                questions.append({'question': q, 'selected': a, 'correct': c})

        score = grade_quiz(questions)
        save_score(user_id, topic, score, "Completed")
        if score <= 2:
            level = "Beginner"
        elif score == 3:
            level = "Intermediate"
        else:
            level = "Advanced"
        save_difficulty(user_id, topic, level)
        return redirect('/profile')

    topic = request.args.get('topic')
    if not topic:
        return redirect('/profile')
    conn = connect()
    c = conn.cursor()
    c.execute('''
        SELECT content FROM messages
        WHERE user_id = %s AND topic = %s AND role = 'bot' AND source = 'guided'
        ORDER BY id
    ''', (user_id, topic))
    rows = c.fetchall()
    conn.close()

    explanation_text = "\n\n".join([r[0] for r in rows])
    questions = generate_quiz_qn(topic, explanation_text)

    return render_template('quiz.html',
                           username=session['username'],
                           quiz_questions=questions,
                           topic=topic)


@app.route('/chat_history')
def chat_history():
    user_id = session['user_id']
    all_chat = get_full_chat(user_id)

    all_chat_converted = []
    for role, content, topic, source, timestamp in all_chat:
        if role == 'bot':
            content = markdown.markdown(content)
        all_chat_converted.append((role, content, topic, source, timestamp))

    return render_template('history.html',
                           username=session['username'],
                           all_messages=all_chat_converted)

@app.route('/select_topics', methods=['GET', 'POST'])
def select_topics():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    all_categories = ['AI Basics', 'Machine Learning', 'Neural Networks', 'Search Algorithms', 'Expert Systems']
    if request.method == 'POST':
        selected_categories = request.form.getlist('categories')
        previously_selected_ids = get_pref_topic(user_id)
        all_topics = get_all_topics()
        prev_titles = [title for tid, title in all_topics if tid in previously_selected_ids]
        previously_selected_categories = set(categorize_topic(title) for title in prev_titles)
        new_categories = [cat for cat in selected_categories if cat not in previously_selected_categories]
        new_topic_ids = []
        for tid, title in all_topics:
            if categorize_topic(title) in new_categories:
                new_topic_ids.append(tid)
        save_pref_topics(user_id, previously_selected_ids + new_topic_ids)
        if new_topic_ids:
            set_current_topic(user_id, new_topic_ids[0])
        user = get_user_by_id(user_id)
        all_questions = initial_tst_qn()
        questions = [q for q in all_questions if q["category"] in new_categories][:25]
        return render_template('diagnostic.html',
                               diagnostic_questions=questions,
                               username=user[1],
                               password=user[2],
                               birthdate=user[3],
                               answer_length=user[4])
    all_topics = get_all_topics()
    selected_topic_ids = get_pref_topic(user_id)
    selected_titles = [title for tid, title in all_topics if tid in selected_topic_ids]
    selected_categories = list(set(categorize_topic(title) for title in selected_titles))
    return render_template('pref_topic.html',
                           username=session['username'],
                           all_categories=all_categories,
                           selected_categories=selected_categories)


if __name__ == '__main__':
    app.run(debug=True)
