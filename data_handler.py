# Reads and writes the scene history CSV (one row per saved scene).

import os
from datetime import datetime
import pandas as pd
from config import DATA_FILE

COLUMNS = [
    "timestamp",
    "user_input",
    "emotion",
    "scene",
    "camera_style",
    "lighting",
    "colors",
    "image_path",
]


def save_scene(user_input, result, image_path=None):
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user_input": user_input,
        "emotion": result.get("emotion", ""),
        "scene": result.get("scene", ""),
        "camera_style": result.get("camera_style", ""),
        "lighting": result.get("lighting", ""),
        "colors": str(result.get("colors", [])),
        "image_path": image_path or "",
    }

    # Migrate older CSVs (alpha) that don't have the image_path column yet.
    if os.path.exists(DATA_FILE):
        existing = pd.read_csv(DATA_FILE)
        if "image_path" not in existing.columns:
            existing["image_path"] = ""
            existing.to_csv(DATA_FILE, index=False, columns=COLUMNS)

    # Append mode; the header is only written if the file is new.
    df_new = pd.DataFrame([row], columns=COLUMNS)
    file_exists = os.path.exists(DATA_FILE)
    df_new.to_csv(DATA_FILE, mode="a", header=not file_exists, index=False)


def load_scenes():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(DATA_FILE)
    if "image_path" not in df.columns:
        df["image_path"] = ""
    return df
