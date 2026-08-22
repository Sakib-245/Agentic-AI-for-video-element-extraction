"""
Stage 4: AI Tagging

Sends the thumbnail plus the numeric CV features already extracted (palette,
motion) to Claude, and asks for a small structured JSON tag back. Grounding
the prompt in real measurements -- not just the raw image -- means the model
isn't guessing "warm cinematic grade" from vibes; it's reading it off actual
RGB values you computed yourself.

Requires ANTHROPIC_API_KEY to be set in the environment (see .env.example).
"""
import base64
import json
import os

from google import genai
from google.genai import types


_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai()  # reads ANTHROPIC_API_KEY from env
    return _client


TAG_PROMPT_TEMPLATE = """This video shot has:
- dominant colors (RGB): {palette}
- motion vector (dx, dy): {motion}
- on-screen text detected: {has_text}

Based on the image and these measurements, respond with ONLY a JSON object
(no other text, no markdown fences) in this exact shape:
{{"style": "...", "content": "...", "mood": "..."}}

- style: visual/technical style, e.g. "handheld documentary", "static wide shot", "cinematic slow pan"
- content: what's in frame, e.g. "close-up interview", "cityscape establishing shot", "product on table"
- mood: emotional register, e.g. "tense", "warm and nostalgic", "energetic"
"""

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def tag_shot(thumbnail_path, palette, motion):
    with open(thumbnail_path, "rb") as f:
        image_bytes = f.read()

    prompt = (
        f"This video shot has dominant colors {palette} and motion vector {motion}. "
        f"Analyze the image and describe its style, content, and mood."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "object",
                "properties": {
                    "style": {"type": "string"},
                    "content": {"type": "string"},
                    "mood": {"type": "string"}
                },
                "required": ["style", "content", "mood"]
            }
        )
    )
    return json.loads(response.text)