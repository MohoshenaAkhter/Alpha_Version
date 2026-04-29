import tkinter as tk
from tkinter import font
from ai_engine import get_emotion_and_scene

def generate_scene():
    user_input = input_box.get("1.0", tk.END).strip()

    if not user_input:
        output_box.config(state="normal")
        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, "⚠️ Please type something first.")
        output_box.config(state="disabled")
        return

    result = get_emotion_and_scene(user_input)
    emotion = result["emotion"]
    scene = result["scene"]

    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, f"🎭 Emotion: {emotion}\n\n🎬 Scene:\n{scene}")
    output_box.config(state="disabled")

# --- Window Setup ---
root = tk.Tk()
root.title("Emotion-Driven Cinematic Scene Engine")
root.geometry("700x550")
root.configure(bg="#1a1a2e")

# --- Input Label ---
tk.Label(root, text="How are you feeling?",
         bg="#1a1a2e", fg="white", font=("Georgia", 13)).pack(pady=(20, 5))

# --- Input Box ---
input_box = tk.Text(root, height=5, width=65,
                    font=("Courier", 11), bg="#16213e", fg="white",
                    insertbackground="white", relief="flat", padx=10, pady=10)
input_box.pack(pady=5)

# --- Button ---
tk.Button(root, text="✨ Generate Scene",
          command=generate_scene,
          bg="#e94560", fg="white",
          font=("Georgia", 12, "bold"),
          relief="flat", padx=20, pady=8,
          cursor="hand2").pack(pady=15)

# --- Output Label ---
tk.Label(root, text="Your Cinematic Scene:",
         bg="#1a1a2e", fg="white", font=("Georgia", 13)).pack(pady=(5, 5))

# --- Output Box ---
output_box = tk.Text(root, height=10, width=65,
                     font=("Courier", 11), bg="#16213e", fg="#e0e0e0",
                     relief="flat", padx=10, pady=10, state="disabled",
                     wrap="word")
output_box.pack(pady=5)

root.mainloop()