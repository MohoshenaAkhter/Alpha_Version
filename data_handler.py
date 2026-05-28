# Reads and writes the scene history CSV using pandas.

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
    """Append one scene to the CSV.

    The image_path argument is optional so that the function still works
    if image generation failed or was skipped — in that case the column is
    just left empty for this row.
    """
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

    # If a pre-beta CSV exists without the new image_path column, rewrite the
    # whole file once with the new layout so that future appends line up.
    if os.path.exists(DATA_FILE):
        existing = pd.read_csv(DATA_FILE)
        if "image_path" not in existing.columns:
            existing["image_path"] = ""
            existing.to_csv(DATA_FILE, index=False, columns=COLUMNS)

    df_new = pd.DataFrame([row], columns=COLUMNS)
    file_exists = os.path.exists(DATA_FILE)
    df_new.to_csv(DATA_FILE, mode="a", header=not file_exists, index=False)


def load_scenes():
    """Return the saved scenes as a DataFrame, or an empty one if no file."""
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(DATA_FILE)
    # Older CSVs may not have the image_path column yet; surface it as empty
    # rather than letting downstream code crash on a missing key.
    if "image_path" not in df.columns:
        df["image_path"] = ""
    return df
