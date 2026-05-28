# Calls the Groq API with the user's text and returns a dict containing
# emotion, scene, camera_style, lighting, a list of 3 hex colors, and an
# image_prompt suitable for feeding into an image-generation model.

import json
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL


def get_emotion_and_scene(text):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Add it to your environment variables.")

    client = Groq(api_key=GROQ_API_KEY)

    # Asking for a strict JSON response keeps parsing simple.
    prompt = (
        f'Analyse the emotional content of this text: "{text}"\n\n'
        "Respond with a JSON object with exactly these fields:\n"
        '- "emotion": dominant emotion in 1-2 words\n'
        '- "scene": vivid 2-3 sentence cinematic scene\n'
        '- "camera_style": camera technique (e.g. slow tracking shot)\n'
        '- "lighting": lighting description (e.g. soft golden backlight)\n'
        '- "colors": list of 3 hex colour codes\n'
        '- "image_prompt": one sentence visual description of the scene, '
        'written for an image-generation model. Focus on subject, environment, '
        'mood and visual style. Do not mention camera brands or photographer names.\n\n'
        "Respond with JSON only, no extra text."
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a creative cinematic director. Always respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1024,
        temperature=0.8,
    )

    raw = response.choices[0].message.content.strip()

    # The model sometimes wraps the JSON in ```json ... ``` fences, strip them.
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)
