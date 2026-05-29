# Tkinter UI for the cinematic scene engine. Both the Groq call and the
# image fetch run on background threads so the window stays responsive.

import json
import os
import threading
import tkinter as tk

import groq
from PIL import Image, ImageTk

from ai_engine import get_emotion_and_scene
from data_handler import save_scene, load_scenes
from image_engine import build_image_prompt, generate_image, ImageGenerationError
from stats import show_emotion_chart

# Theme colors used across the window.
BG_DARK = "#1a1a2e"
BG_MID = "#16213e"
ACCENT = "#e94560"
FG_MAIN = "#e0e0e0"

THUMB_WIDTH = 300
THUMB_HEIGHT = 300

# The most recently generated scene, kept so Save knows what to write.
last_input = None
last_result = None
last_image_path = None

# PhotoImage gets GC'd if nothing holds a reference.
thumbnail_photo = None


def set_output(text):
    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, text)
    output_box.see("1.0")
    output_box.config(state="disabled")


def darken(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r, g, b = max(0, r - 25), max(0, g - 25), max(0, b - 25)
    return f"#{r:02x}{g:02x}{b:02x}"


def make_btn(parent, text, command, bg, fg, font, padx=20, pady=8):
    btn = tk.Label(parent, text=text, bg=bg, fg=fg, font=font,
                   padx=padx, pady=pady, cursor="hand2")
    btn.bind("<Button-1>", lambda e: command())
    btn.bind("<Enter>", lambda e: btn.config(bg=darken(bg)))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def reset_image_area(message="No image yet."):
    global thumbnail_photo
    thumbnail_photo = None
    image_panel.config(image="", text=message, cursor="")
    image_panel.image = None


def show_thumbnail(path):
    global thumbnail_photo
    try:
        img = Image.open(path)
    except (OSError, FileNotFoundError) as exc:
        reset_image_area(f"Could not open image:\n{exc}")
        return

    img.thumbnail((THUMB_WIDTH, THUMB_HEIGHT))
    thumbnail_photo = ImageTk.PhotoImage(img)
    image_panel.config(image=thumbnail_photo, text="", cursor="hand2")
    image_panel.image = thumbnail_photo


def open_image_fullsize(_event=None):
    if not last_image_path or not os.path.exists(last_image_path):
        return

    top = tk.Toplevel(root)
    top.title("Scene Image")
    top.configure(bg=BG_DARK)

    img = Image.open(last_image_path)
    img.thumbnail((1100, 800))
    photo = ImageTk.PhotoImage(img)
    label = tk.Label(top, image=photo, bg=BG_DARK)
    label.image = photo
    label.pack(padx=20, pady=20)

    top.bind("<Escape>", lambda e: top.destroy())


def show_result(user_input, result):
    global last_input, last_result, last_image_path
    last_input = user_input
    last_result = result
    last_image_path = None

    emotion = result.get("emotion", "")
    scene = result.get("scene", "")
    camera = result.get("camera_style", "")
    lighting = result.get("lighting", "")
    colors = result.get("colors", [])

    output_text = (
        f"🎭  Emotion:       {emotion}\n\n"
        f"🎬  Scene:\n{scene}\n\n"
        f"🎥  Camera Style:  {camera}\n\n"
        f"💡  Lighting:      {lighting}"
    )
    set_output(output_text)

    for i, canvas in enumerate(color_swatches):
        color = colors[i] if i < len(colors) else BG_MID
        canvas.config(bg=color)
        swatch_labels[i].config(text=colors[i] if i < len(colors) else "")

    generate_btn.config(text="✨ Generate Scene", fg="white")
    save_btn.pack(side="left", padx=5)
    status_label.config(text="", fg="#52b788")

    reset_image_area("Generating image…")
    threading.Thread(target=fetch_image, args=(result,), daemon=True).start()


def fetch_image(result):
    try:
        prompt = build_image_prompt(result)
        path = generate_image(prompt)
    except ImageGenerationError as exc:
        msg = str(exc)
        root.after(0, lambda: reset_image_area(f"Image unavailable:\n{msg}"))
        return
    except Exception as exc:
        msg = str(exc)
        root.after(0, lambda: reset_image_area(f"Image unavailable:\n{msg}"))
        return

    def display():
        global last_image_path
        last_image_path = path
        show_thumbnail(path)

    root.after(0, display)


def call_api(user_input):
    try:
        result = get_emotion_and_scene(user_input)
        root.after(0, lambda: show_result(user_input, result))
        return
    except groq.AuthenticationError:
        msg = "Authentication failed. Please check your GROQ_API_KEY."
    except groq.RateLimitError:
        msg = "Rate limit reached. Please wait a moment and try again."
    except groq.APIConnectionError:
        msg = "Could not reach the Groq service. Check your internet connection."
    except groq.APIError as exc:
        msg = f"API error: {exc}"
    except json.JSONDecodeError:
        msg = "The model returned a response that could not be parsed as JSON."
    except ValueError as exc:
        msg = str(exc)
    except Exception as exc:
        msg = f"Unexpected error: {exc}"

    root.after(0, lambda: set_output(f"Something went wrong:\n{msg}"))
    root.after(0, lambda: generate_btn.config(text="✨ Generate Scene", fg="white"))


def generate_scene():
    user_input = input_box.get("1.0", tk.END).strip()
    if not user_input:
        set_output("Please type something first.")
        return

    generate_btn.config(text="Generating...", fg="#888888")
    save_btn.pack_forget()
    status_label.config(text="")
    set_output("Analyzing your emotion...")
    reset_image_area("No image yet.")

    threading.Thread(target=call_api, args=(user_input,), daemon=True).start()


def save_current_scene():
    if last_result is None:
        return
    save_scene(last_input, last_result, image_path=last_image_path)
    status_label.config(text="✓ Scene saved!", fg="#52b788")
    save_btn.config(fg="#888888")


def view_history():
    df = load_scenes()
    if df.empty or "emotion" not in df.columns:
        set_output("No scenes saved yet — generate and save one first.")
        status_label.config(text="")
        return
    status_label.config(text="")
    show_emotion_chart()


def run():
    global root, input_box, output_box
    global generate_btn, save_btn, status_label
    global color_swatches, swatch_labels
    global image_panel

    root = tk.Tk()
    root.title("Emotion-Driven Cinematic Scene Engine")
    root.geometry("760x900")
    root.configure(bg=BG_DARK)

    tk.Label(root, text="🎬 Cinematic Scene Engine",
             bg=BG_DARK, fg="white",
             font=("Georgia", 17, "bold")).pack(pady=(12, 2))

    tk.Label(root, text="Type how you feel & Get a cinematic scene",
             bg=BG_DARK, fg="#888888",
             font=("Georgia", 10)).pack(pady=(0, 8))

    tk.Label(root, text="How are you feeling?",
             bg=BG_DARK, fg="white", font=("Georgia", 12)).pack(pady=(4, 4))

    input_box = tk.Text(root, height=3, width=60,
                        font=("Courier", 11), bg=BG_MID, fg="white",
                        insertbackground="white", relief="flat", padx=10, pady=8)
    input_box.pack(pady=4)

    generate_btn = make_btn(root, text="✨ Generate Scene",
                            command=generate_scene,
                            bg=ACCENT, fg="white",
                            font=("Georgia", 12, "bold"),
                            padx=20, pady=6)
    generate_btn.pack(pady=8)

    tk.Label(root, text="Your Cinematic Scene:",
             bg=BG_DARK, fg="white", font=("Georgia", 13)).pack(pady=(4, 4))

    output_box = tk.Text(root, height=7, width=60,
                         font=("Courier", 10), bg=BG_MID, fg=FG_MAIN,
                         relief="flat", padx=10, pady=8,
                         state="disabled", wrap="word")
    output_box.pack(pady=4)

    tk.Label(root, text="Color Palette:",
             bg=BG_DARK, fg="white", font=("Georgia", 12)).pack(anchor="w", padx=60, pady=(6, 4))

    swatch_frame = tk.Frame(root, bg=BG_DARK)
    swatch_frame.pack(anchor="w", padx=60, pady=(0, 6))

    color_swatches = []
    swatch_labels = []
    for _ in range(3):
        col_frame = tk.Frame(swatch_frame, bg=BG_DARK)
        col_frame.pack(side="left", padx=(0, 15))

        canvas = tk.Canvas(col_frame, width=80, height=40,
                           bg=BG_MID, highlightthickness=1,
                           highlightbackground="#333333")
        canvas.pack()

        label = tk.Label(col_frame, text="", bg=BG_DARK, fg="#888888",
                         font=("Courier", 9))
        label.pack(pady=(3, 0))

        color_swatches.append(canvas)
        swatch_labels.append(label)

    tk.Label(root, text="Scene Image (Click to enlarge):",
             bg=BG_DARK, fg="white", font=("Georgia", 12)).pack(pady=(6, 4))

    # Without pack_propagate(False) a placeholder text would blow up the panel
    # because Label width/height are character/line counts, not pixels.
    image_frame = tk.Frame(root, bg=BG_MID,
                           width=THUMB_WIDTH, height=THUMB_HEIGHT)
    image_frame.pack(pady=(0, 8))
    image_frame.pack_propagate(False)

    image_panel = tk.Label(image_frame, text="No image yet.",
                           bg=BG_MID, fg="#888888",
                           font=("Georgia", 10),
                           wraplength=THUMB_WIDTH - 20)
    image_panel.pack(fill="both", expand=True)
    image_panel.bind("<Button-1>", open_image_fullsize)

    button_row = tk.Frame(root, bg=BG_DARK)
    button_row.pack(pady=(2, 0))

    history_btn = make_btn(button_row, text="📊 View History",
                           command=view_history,
                           bg="#3d5a80", fg="white",
                           font=("Georgia", 11, "bold"),
                           padx=15, pady=6)
    history_btn.pack(side="left", padx=5)

    save_btn = make_btn(button_row, text="💾 Save Scene",
                        command=save_current_scene,
                        bg="#2d6a4f", fg="white",
                        font=("Georgia", 11, "bold"),
                        padx=15, pady=6)

    status_label = tk.Label(root, text="", bg=BG_DARK, fg="#52b788",
                            font=("Georgia", 11))
    status_label.pack(pady=(8, 10))

    root.mainloop()


if __name__ == "__main__":
    run()
