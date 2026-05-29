# Bar chart of how often each emotion has been generated.

import io
import base64
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — safe for both tkinter and Flask
import matplotlib.pyplot as plt
from data_handler import load_scenes


def show_emotion_chart():
    """For tkinter — opens chart in a window."""
    df = load_scenes()
    if df.empty or "emotion" not in df.columns:
        print("No scenes saved yet.")
        return

    counts = df["emotion"].value_counts()
    fig, ax = _build_chart(counts)
    plt.show()


def get_emotion_chart_base64():
    """For Flask — returns chart as a base64 image string."""
    df = load_scenes()
    if df.empty or "emotion" not in df.columns:
        return None

    counts = df["emotion"].value_counts()
    fig, ax = _build_chart(counts)

    # Convert chart to base64 string
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_base64


def _build_chart(counts):
    """Shared chart builder used by both functions."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(counts.index, counts.values, color="#e94560", edgecolor="#1a1a2e")
    ax.set_title("Your Emotion History", fontsize=14, pad=15)
    ax.set_xlabel("Emotion")
    ax.set_ylabel("Times used")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return fig, ax