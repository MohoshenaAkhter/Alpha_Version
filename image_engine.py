import base64
import hashlib
import os

import requests

CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")
MODEL = "@cf/black-forest-labs/flux-1-schnell"
CACHE_DIR = os.path.join("scenes", "images")
REQUEST_TIMEOUT = 60


class ImageGenerationError(Exception):
    pass


def _cache_path(prompt):
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{digest}.jpg")


def build_image_prompt(scene_dict):
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


def generate_image(prompt):
    if not prompt or not prompt.strip():
        raise ImageGenerationError("Empty image prompt.")

    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        raise ImageGenerationError(
            "Cloudflare credentials are not set. Add CLOUDFLARE_ACCOUNT_ID "
            "and CLOUDFLARE_API_TOKEN to your environment."
        )

    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(prompt)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{CLOUDFLARE_ACCOUNT_ID}/ai/run/{MODEL}"
    )
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {"prompt": prompt, "steps": 8}

    try:
        response = requests.post(url, headers=headers, json=body, timeout=REQUEST_TIMEOUT)
    except requests.Timeout as exc:
        raise ImageGenerationError("Image generation timed out. Try again in a moment.") from exc
    except requests.ConnectionError as exc:
        raise ImageGenerationError("Could not reach the image service. Check your connection.") from exc
    except requests.RequestException as exc:
        raise ImageGenerationError(f"Image request failed: {exc}") from exc

    if response.status_code == 401 or response.status_code == 403:
        raise ImageGenerationError(
            "Cloudflare authentication failed. Check CLOUDFLARE_API_TOKEN."
        )
    if response.status_code == 429:
        raise ImageGenerationError("Daily Cloudflare AI quota reached. Try again tomorrow.")
    if response.status_code != 200:
        raise ImageGenerationError(
            f"Image service returned status {response.status_code}: {response.text[:200]}"
        )

    payload = response.json()
    if not payload.get("success"):
        errors = payload.get("errors") or []
        msg = errors[0].get("message") if errors else "Unknown error."
        raise ImageGenerationError(f"Cloudflare AI error: {msg}")

    image_b64 = payload.get("result", {}).get("image")
    if not image_b64:
        raise ImageGenerationError("Cloudflare AI returned no image.")

    image_bytes = base64.b64decode(image_b64)
    with open(path, "wb") as f:
        f.write(image_bytes)
    return path
