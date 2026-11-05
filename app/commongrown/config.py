import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("COMMONGROWN_DATA", ROOT / ".data")).resolve()


def read_json(path):
    path = Path(path)
    if path.stat().st_size > 100000:
        raise ValueError("JSON input exceeds 100 KB")
    with path.open() as stream:
        return json.load(stream)


def private_path(company, data=DATA):
    from .models import digest
    return Path(data) / "companies" / digest(company) / "private.json"
