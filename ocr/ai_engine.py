import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.0-flash")

def get_engagement_suggestions(slide_text: str):
    prompt = f"""
    The following text is from a presentation slide:

    "{slide_text}"

    As an AI helper for a live presenter, provide:
    - 2 short, relevant jokes
    - 2 surprising statistics or facts
    - 2 audience engagement ideas (questions, polls, etc.)

    Keep the suggestions concise and naturally speakable.
    """

    response = model.generate_content(prompt)
    return response.text
