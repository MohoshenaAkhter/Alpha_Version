import os
from flask import Flask, render_template, request, jsonify, send_from_directory

from ai_engine import get_emotion_and_scene
from image_engine import build_image_prompt, generate_image, ImageGenerationError
from data_handler import save_scene, load_scenes
from stats import get_emotion_chart_base64

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    user_input = data.get("text", "").strip()
    if not user_input:
        return jsonify({"error": "Empty input"}), 400

    try:
        result = get_emotion_and_scene(user_input)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    try:
        image_prompt = build_image_prompt(result)
        image_path = generate_image(image_prompt)
        result["image_path"] = image_path
        result["image_url"] = "/" + image_path.replace("\\", "/")
        result["image_error"] = None
    except ImageGenerationError as exc:
        result["image_path"] = None
        result["image_url"] = None
        result["image_error"] = str(exc)
    except Exception as exc:
        result["image_path"] = None
        result["image_url"] = None
        result["image_error"] = f"Unexpected error: {exc}"

    return jsonify(result)


@app.route("/save", methods=["POST"])
def save():
    data = request.get_json() or {}
    result = {
        "emotion": data.get("emotion", ""),
        "scene": data.get("scene", ""),
        "camera_style": data.get("camera_style", ""),
        "lighting": data.get("lighting", ""),
        "colors": data.get("colors", []),
    }
    save_scene(data.get("input", ""), result, image_path=data.get("image_path"))
    return jsonify({"status": "saved"})


@app.route("/history")
def history():
    entries = load_scenes().to_dict(orient="records")
    chart = get_emotion_chart_base64()
    return render_template("history.html", entries=entries, chart=chart)


@app.route("/scenes/images/<filename>")
def serve_image(filename):
    return send_from_directory(
        os.path.join(os.getcwd(), "scenes", "images"), filename
    )


if __name__ == "__main__":
    app.run(debug=True)
