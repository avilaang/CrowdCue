import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.0-flash")

def get_engagement_suggestions(slide_text: str, dominant_engagement: str = None) -> str:
    prompt = f"""
    The following text is from a presentation slide:

    "{slide_text}"
    "The dominant audience engagement state is: {dominant_engagement}" 

    As an AI helper for a live presenter, provide:
    - 1 audience engagement idea (questions, polls, short and relevant joke, a surprising statistic or fact)

    Keep the suggestions concise and naturally speakable and based on the audince state. Do not include any additional headings or how the audience is feeling.
    """

    response = model.generate_content(prompt)
    return response.text
