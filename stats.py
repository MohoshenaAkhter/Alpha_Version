"""Statistics and visualization for saved scenes."""

import matplotlib.pyplot as plt
from data_handler import load_scenes


def get_emotion_counts():
    """Return how many times each emotion appears in saved scenes.

    Returns:
        pd.Series: Emotion counts sorted by frequency.
    """
    df = load_scenes()
    if df.empty or "emotion" not in df.columns:
        return None
    return df["emotion"].value_counts()


def show_emotion_chart():
    """Open a bar chart showing the user's emotion history."""
    counts = get_emotion_counts()
    if counts is None:
        print("No scenes saved yet.")
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(counts.index, counts.values, color="#e94560", edgecolor="#1a1a2e")
    ax.set_title("Your Emotion History", fontsize=14, pad=15)
    ax.set_xlabel("Emotion")
    ax.set_ylabel("Times used")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    plt.show()
