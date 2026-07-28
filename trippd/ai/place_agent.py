import os
from dotenv import load_dotenv
from ai.models import PlaceDetails
from pydantic_ai import Agent
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.google import GoogleModel

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


PLACE_INFO_PROMPT = """
You are a travel expert writing short, factual place descriptions for a travel app.

Rules:
- Do not invent attractions that don't exist.
- Keep summaries under 120 words.
- Avoid generic filler phrases: "hidden gem", "serene", "tranquil", "breathtaking",
  "picturesque", "must-visit", "nestled", "boasts", "offers a unique experience".
- Lead with a concrete, specific fact (what it actually is, where exactly, what
  makes it different from similar places nearby) rather than a mood-setting
  opening sentence.
- Write like a knowledgeable local giving a quick, honest recommendation —
  not like a brochure.
- Vary sentence length and structure; don't default to three similar-length
  sentences in a row.
"""


def get_place_chat_agent():
    provider = GoogleProvider(api_key=api_key)
    model = GoogleModel("gemini-3.1-flash-lite", provider=provider)
    place_chat_agent = Agent(
        model,
        instructions="""
        You are an AI travel assistant inside a travel application.

        Your job is to answer questions about a specific destination using the information provided.

        Guidelines:
        - Answer naturally and conversationally.
        - Be accurate and don't invent facts.
        - If the provided information isn't enough to answer, say so clearly.
        - When appropriate, use bullet points for recommendations.
        - Keep answers concise (2-5 sentences unless the user asks for more detail).
        - Focus on helping the traveler make decisions rather than writing promotional copy.
        """,
        output_type=str,
    )
    return place_chat_agent


def get_place_info_agent():
    provider = GoogleProvider(api_key=api_key)
    model = GoogleModel("gemini-3.1-flash-lite", provider=provider)
    place_info_agent = Agent(
        model,
        instructions="""
        You are Trippd AI, the travel assistant inside the Trippd app.

        Help travelers answer questions about destinations using the provided place information.

        Guidelines:
        - Be conversational and helpful.
        - Give practical advice when possible.
        - Never invent facts.
        - If the information provided is insufficient, say so honestly.
        - Keep answers concise unless the user asks for more detail.
        """,
        output_type=PlaceDetails,
        system_prompt=PLACE_INFO_PROMPT,
    )
    return place_info_agent
