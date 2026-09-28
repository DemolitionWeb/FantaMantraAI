import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SPORTMONKS_API_TOKEN = os.getenv("SPORTMONKS_API_TOKEN")
BBS_API_KEY = os.getenv("BBS_API_KEY")

RUOLI_MANTRA = [
    "POR",
    "DC",
    "DD",
    "DS",
    "B",
    "E",
    "M",
    "C",
    "W",
    "T",
    "A",
    "PC",
]