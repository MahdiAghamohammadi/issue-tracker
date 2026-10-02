from pathlib import Path
import json
import os
import tempfile

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_FILE = DATA_DIR / "issues.json"


def load_data():
    if DATA_FILE.exists():
        with DATA_FILE.open("r", encoding="utf-8") as file:
            content = file.read()
        if content.strip():
            return json.loads(content)
    return []


def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=DATA_DIR, delete=False
        ) as file:
            temporary_path = Path(file.name)
            json.dump(data, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, DATA_FILE)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
