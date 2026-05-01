# Tkinter UI for the cinematic scene engine. The API call runs in a
# background thread so the window stays responsive while waiting.

import json
import threading
import tkinter as tk

import groq

from ai_engine import get_emotion_and_scene
from data_handler import save_scene, load_scenes
from stats import show_emotion_chart

# Theme colors used across the window.
BG_DARK = "#1a1a2e"
BG_MID = "#16213e"
ACCENT = "#e94560"
FG_MAIN = "#e0e0e0"

# The most recently generated scene, kept so Save can write it to CSV.
last_input = None
last_result = None


def set_output(text):
    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, text)
    output_box.config(state="disabled")


def darken(hex_color):
    # Used to give buttons a subtle hover effect.
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r, g, b = max(0, r - 25), max(0, g - 25), max(0, b - 25)
    return f"#{r:02x}{g:02x}{b:02x}"


def make_btn(parent, text, command, bg, fg, font, padx=20, pady=8):
    # tk.Button ignores bg/fg colors on macOS, so a Label with click bindings
    # is used instead to keep the look consistent across platforms.
    btn = tk.Label(parent, text=text, bg=bg, fg=fg, font=font,
                   padx=padx, pady=pady, cursor="hand2")
    btn.bind("<Button-1>", lambda e: command())
    btn.bind("<Enter>", lambda e: btn.config(bg=darken(bg)))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def show_result(user_input, result):
    global last_input, last_result
    last_input = user_input
    last_result = result

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

    # Fill the three swatch canvases with the returned hex colors.
    for i, canvas in enumerate(color_swatches):
        color = colors[i] if i < len(colors) else BG_MID
        canvas.config(bg=color)
        swatch_labels[i].config(text=colors[i] if i < len(colors) else "")

    generate_btn.config(text="✨ Generate Scene", fg="white")
    save_btn.pack(side="left", padx=5)
    status_label.config(text="", fg="#52b788")


def call_api(user_input):
    # Runs in a background thread. Errors are classified so the user gets
    # a more useful message than a raw stack trace. Results are pushed back
    # to the main thread via root.after, which is the safe way to update Tk.
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
        # Raised by ai_engine when the API key is missing.
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

    threading.Thread(target=call_api, args=(user_input,), daemon=True).start()


def save_current_scene():
    if last_result is None:
        return
    save_scene(last_input, last_result)
    status_label.config(text="✓ Scene saved!", fg="#52b788")
    save_btn.config(fg="#888888")


def view_history():
    # Check first whether there is any saved data, so we can give visible
    # feedback in the window itself rather than only in the terminal.
    df = load_scenes()
    if df.empty or "emotion" not in df.columns:
        status_label.config(text="No scenes saved yet — generate and save one first.",
                            fg="#e94560")
        return
    status_label.config(text="", fg="#52b788")
    show_emotion_chart()


def run():
    # Build the window and start the Tk main loop. Wrapping this in a
    # function keeps import-time side effects out of ui.py, so the module
    # can be imported (e.g. for testing) without launching the UI.
    global root, input_box, output_box
    global generate_btn, save_btn, status_label
    global color_swatches, swatch_labels

    root = tk.Tk()
    root.title("Emotion-Driven Cinematic Scene Engine")
    root.geometry("780x820")
    root.configure(bg=BG_DARK)

    tk.Label(root, text="🎬 Cinematic Scene Engine",
             bg=BG_DARK, fg="white",
             font=("Georgia", 18, "bold")).pack(pady=(20, 2))

    tk.Label(root, text="Type how you feel & Get a cinematic scene",
             bg=BG_DARK, fg="#888888",
             font=("Georgia", 10)).pack(pady=(0, 10))

    tk.Label(root, text="How are you feeling?",
             bg=BG_DARK, fg="white", font=("Georgia", 13)).pack(pady=(10, 5))

    input_box = tk.Text(root, height=5, width=65,
                        font=("Courier", 11), bg=BG_MID, fg="white",
                        insertbackground="white", relief="flat", padx=10, pady=10)
    input_box.pack(pady=5)

    generate_btn = make_btn(root, text="✨ Generate Scene",
                            command=generate_scene,
                            bg=ACCENT, fg="white",
                            font=("Georgia", 12, "bold"),
                            padx=20, pady=8)
    generate_btn.pack(pady=15)

    tk.Label(root, text="Your Cinematic Scene:",
             bg=BG_DARK, fg="white", font=("Georgia", 13)).pack(pady=(5, 5))

    output_box = tk.Text(root, height=12, width=65,
                         font=("Courier", 11), bg=BG_MID, fg=FG_MAIN,
                         relief="flat", padx=10, pady=10,
                         state="disabled", wrap="word")
    output_box.pack(pady=5)

    tk.Label(root, text="Color Palette:",
             bg=BG_DARK, fg="white", font=("Georgia", 12)).pack(anchor="w", padx=60, pady=(10, 5))

    swatch_frame = tk.Frame(root, bg=BG_DARK)
    swatch_frame.pack(anchor="w", padx=60, pady=(0, 10))

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

    # Save and history buttons sit side by side under the swatches.
    button_row = tk.Frame(root, bg=BG_DARK)
    button_row.pack(pady=(10, 0))

    history_btn = make_btn(button_row, text="📊 View History",
                           command=view_history,
                           bg="#3d5a80", fg="white",
                           font=("Georgia", 11, "bold"),
                           padx=15, pady=6)
    history_btn.pack(side="left", padx=5)

    # Save button is created but not packed yet — it appears only after a
    # scene is generated (see show_result).
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
