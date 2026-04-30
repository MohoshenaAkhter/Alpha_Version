import os

# Model used for generating cinematic scenes
GROQ_MODEL = "llama-3.3-70b-versatile"

# CSV file to store saved scenes
DATA_FILE = "scenes.csv"

# API key loaded from environment variable
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
