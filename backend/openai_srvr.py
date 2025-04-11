import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_ai_answer(prompt, edu_level, course):
    full_prompt = f"You are a tutor for a {edu_level} student studying {course}. Answer this question that is understandable by him:\n{prompt}"
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": full_prompt}
        ]
    )
    return response.choices[0].message.content.strip()
