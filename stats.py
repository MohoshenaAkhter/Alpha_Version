# Bar chart of how often each emotion has been generated.

import matplotlib.pyplot as plt
from data_handler import load_scenes


def show_emotion_chart():
    df = load_scenes()
    if df.empty or "emotion" not in df.columns:
        print("No scenes saved yet.")
        return

    counts = df["emotion"].value_counts()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(counts.index, counts.values, color="#e94560", edgecolor="#1a1a2e")
    ax.set_title("Your Emotion History", fontsize=14, pad=15)
    ax.set_xlabel("Emotion")
    ax.set_ylabel("Times used")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    plt.show()
