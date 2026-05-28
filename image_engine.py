# Generates a cinematic image for the scene using Pollinations.ai.
# Pollinations is free and needs no API key, and each result is cached on
# disk by a hash of its prompt so the same prompt isn't refetched.

import hashlib
import os
import urllib.parse

import requests

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/"
CACHE_DIR = os.path.join("scenes", "images")
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 512
DEFAULT_MODEL = "flux"
REQUEST_TIMEOUT = 60


class ImageGenerationError(Exception):
    pass


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(prompt, width, height, model):
    # Same prompt at a different size really is a different image, so the
    # cache key has to include the rendering parameters too.
    key = f"{model}|{width}x{height}|{prompt}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{digest}.jpg")


def build_image_prompt(scene_dict):
    # Prefer the model-written image_prompt; fall back to stitching scene,
    # camera and lighting if it isn't there.
    image_prompt = (scene_dict.get("image_prompt") or "").strip()
    if image_prompt:
        return f"{image_prompt} Cinematic, film still, high detail."

    scene = (scene_dict.get("scene") or "").strip()
    camera = (scene_dict.get("camera_style") or "").strip()
    lighting = (scene_dict.get("lighting") or "").strip()

    if not scene:
        raise ImageGenerationError("Scene description is empty, nothing to render.")

    parts = [scene]
    if camera:
        parts.append(f"Camera: {camera}.")
    if lighting:
        parts.append(f"Lighting: {lighting}.")
    parts.append("Cinematic, film still, high detail, photorealistic.")
    return " ".join(parts)


def generate_image(prompt, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, model=DEFAULT_MODEL):
    if not prompt or not prompt.strip():
        raise ImageGenerationError("Empty image prompt.")

    _ensure_cache_dir()
    path = _cache_path(prompt, width, height, model)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path

    encoded = urllib.parse.quote(prompt, safe="")
    url = (
        f"{POLLINATIONS_URL}{encoded}"
        f"?width={width}&height={height}&model={model}&nologo=true"
    )

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.Timeout as exc:
        raise ImageGenerationError("Image generation timed out. Try again in a moment.") from exc
    except requests.ConnectionError as exc:
        raise ImageGenerationError("Could not reach the image service. Check your connection.") from exc
    except requests.RequestException as exc:
        raise ImageGenerationError(f"Image request failed: {exc}") from exc

    if response.status_code != 200:
        raise ImageGenerationError(
            f"Image service returned status {response.status_code}."
        )

    # Pollinations occasionally returns an empty body under load.
    if not response.content or len(response.content) < 1024:
        raise ImageGenerationError("Image service returned an empty or invalid image.")

    with open(path, "wb") as f:
        f.write(response.content)
    return path
