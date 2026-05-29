# Sends the user's text to Groq and returns a dict containing emotion,
# scene, camera_style, lighting, a list of 3 hex colors and an image_prompt.

import json
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

# Inputs with this many words or fewer get a special prompt branch.
SHORT_INPUT_WORD_LIMIT = 2

SYSTEM_PROMPT = (
    "You are a cinematic director with a strong personal style. "
    "You translate emotions into specific, image-rich film scenes — not "
    "generic descriptions. Avoid clichés like 'a person sits alone in a "
    "dimly lit room' unless the input truly calls for it. Favour concrete "
    "subjects, places, weather, time of day, and small physical details. "
    "Always respond with valid JSON only, no markdown, no commentary."
)


def _build_user_prompt(text):
    is_short = len(text.split()) <= SHORT_INPUT_WORD_LIMIT

    instructions = (
        f'Analyse the emotional content of this text: "{text}"\n\n'
        "Respond with a JSON object with exactly these fields:\n"
        '- "emotion": the dominant emotion in 1-2 words\n'
        '- "scene": a vivid 2-3 sentence cinematic scene with a concrete '
        'subject, setting, and at least one small sensory detail\n'
        '- "camera_style": one camera technique (e.g. slow tracking shot, '
        'low-angle close-up, handheld follow)\n'
        '- "lighting": a lighting description (e.g. soft golden backlight, '
        'harsh fluorescent overhead, blue hour window light)\n'
        '- "colors": a list of exactly 3 hex colour codes that match the mood\n'
        '- "image_prompt": one sentence visual description of the scene, '
        'written for an image-generation model. Focus on subject, environment, '
        'mood and visual style. Do not mention camera brands or photographer '
        'names.\n\n'
    )

    if is_short:
        # Short inputs ("ok", "fine") don't carry enough signal — push the
        # model to invent rather than fall back to something generic.
        instructions += (
            "The input is very short and ambiguous. Interpret it generously: "
            "imagine the kind of moment a person who would type this short "
            "message might be living through, and build a specific scene "
            "around that. Do not ask the user for clarification — invent.\n\n"
        )

    instructions += "Respond with JSON only, no extra text."
    return instructions


def get_emotion_and_scene(text):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Add it to your environment variables.")

    client = Groq(api_key=GROQ_API_KEY)
    user_prompt = _build_user_prompt(text)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
        temperature=0.85,
    )

    raw = response.choices[0].message.content.strip()

    # Strip ```json ... ``` fences if the model wraps the response.
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)
