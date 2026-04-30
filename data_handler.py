"""Handles saving and loading scene records using pandas."""

import os
from datetime import datetime

import pandas as pd

from config import DATA_FILE

COLUMNS = ["timestamp", "user_input", "emotion", "scene", "camera_style", "lighting", "colors"]


def save_scene(user_input, result):
    """Save a generated scene to the CSV file.

    Args:
        user_input (str): The text the user typed.
        result (dict): The scene data returned by ai_engine.
    """
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user_input": user_input,
        "emotion": result.get("emotion", ""),
        "scene": result.get("scene", ""),
        "camera_style": result.get("camera_style", ""),
        "lighting": result.get("lighting", ""),
        "colors": str(result.get("colors", [])),
    }

    df_new = pd.DataFrame([row], columns=COLUMNS)
    file_exists = os.path.exists(DATA_FILE)
    df_new.to_csv(DATA_FILE, mode="a", header=not file_exists, index=False)


def load_scenes():
    """Load all saved scenes from the CSV file.

    Returns:
        pd.DataFrame: All saved records, or empty DataFrame if none exist.
    """
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(DATA_FILE)
