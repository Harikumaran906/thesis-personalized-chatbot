import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def doubt_answer(doubt, answer_length, topic, subtopic_title, ref_explanation):
    prompt = f"""Doubt Explanation Context
                Topic: {topic}
                Subtopic: {subtopic_title or 'N/A'}
                Explanation Style: {answer_length}
                Explanation: {ref_explanation}
                Doubt: {doubt}
                """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an educational AI tutor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content.strip()



def guided_answer(topic, subtopic_title, answer_length, difficulty):
    prompt = f"You are teaching a {difficulty.lower()} level student. Explain the subtopic '{subtopic_title}' from the topic '{topic}' in a {answer_length} way with both theory and example."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an educational AI tutor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content.strip()


def initial_tst_qn():
    categories = ["AI Basics", "Machine Learning", "Neural Networks", "Search Algorithms", "Expert Systems"]
    questions = []

    for category in categories:
        prompt = f"Generate 5 beginner-level multiple-choice questions to categorize the basic understanding of {category} in an AI course. Each question must have 4 options labeled A-D and end with 'Answer: <letter>'.\n\nFormat:\nQ1: ...\nA) ...\nB) ...\nC) ...\nD) ...\nAnswer: <letter>"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI tutor generating MCQs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=800
        )

        lines = response.choices[0].message.content.strip().split('\n')
        q = {}
        for line in lines:
            line = line.strip()
            if line.startswith("Q"):
                if q:
                    q["category"] = category
                    questions.append(q)
                    q = {}
                q["question"] = line.split(":", 1)[1].strip()
                q["options"] = []
            elif line[:2] in ["A)", "B)", "C)", "D)"]:
                q["options"].append(line)
            elif line.startswith("Answer:"):
                q["answer"] = line.split(":", 1)[1].strip()
        if q:
            q["category"] = category
            questions.append(q)

    return questions[:25]

def grade_initial_tst(questions):
    category_scores = {
        "AI Basics": 0,
        "Machine Learning": 0,
        "Neural Networks": 0,
        "Search Algorithms": 0,
        "Expert Systems": 0
    }
    counts = {cat: 0 for cat in category_scores}

    for q in questions:
        cat = q["category"]
        if q["selected"] == q["correct"]:
            category_scores[cat] += 1
        counts[cat] += 1
    difficulty_map = {}
    for cat in category_scores:
        correct = category_scores[cat]
        if correct >= 4:
            level = "Advanced"
        elif correct >= 2:
            level = "Intermediate"
        else:
            level = "Beginner"
        difficulty_map[cat] = level
    return difficulty_map

def generate_quiz_qn(topic, explanation_text=None):
    context = f"Based on the topic '{topic}' in an AI course,"
    if explanation_text:
        context += f" and the following explanation:\n\n{explanation_text}\n\n"
    prompt = context + """generate 5 multiple-choice questions to test the student's understanding.
                           Each question must have 4 options labeled A-D and end with 'Answer: <letter>'.
                            Format:
                            Q1: ...
                            A) ...
                            B) ...
                            C) ...
                            D) ...
                            Answer: <letter>"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI tutor generating MCQ quizzes."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=800
    )
    lines = response.choices[0].message.content.strip().split('\n')
    questions = []
    q = {}
    for line in lines:
        line = line.strip()
        if line.startswith("Q"):
            if q:
                questions.append(q)
                q = {}
            q["question"] = line.split(":", 1)[1].strip()
            q["options"] = []
        elif line[:2] in ["A)", "B)", "C)", "D)"]:
            q["options"].append(line)
        elif line.startswith("Answer:"):
            q["answer"] = line.split(":", 1)[1].strip()
    if q:
        questions.append(q)
    return questions[:5]

def grade_quiz(questions_and_user_answers):
    prompt = "You are a university AI teacher. Grade this student's MCQ quiz. Each question has 4 choices (A–D). Compare the user's selected answer with the correct one and give a total score from 0 to 5.\n\n"

    for i, qa in enumerate(questions_and_user_answers, 1):
        prompt += f"Q{i}: {qa['question']}\nCorrect Answer: {qa['correct']}\nStudent Answer: {qa['selected']}\n\n"

    prompt += "Now just respond with the total score only (0 to 5), nothing else."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert grader for an AI course."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=10
    )
    score_text = response.choices[0].message.content.strip()
    score = int(''.join(filter(str.isdigit, score_text)))
    return min(max(score, 0), 5)
