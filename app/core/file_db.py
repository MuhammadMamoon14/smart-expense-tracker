"""
file_db.py — Central JSON file storage service.
All reads/writes go through this module.
"""

import json
import uuid
from pathlib import Path
from typing import Any
from threading import Lock

from app.core.config import settings

# Per-file locks to prevent race conditions
_locks: dict[str, Lock] = {}


def _get_lock(filepath: Path) -> Lock:
    key = str(filepath)
    if key not in _locks:
        _locks[key] = Lock()
    return _locks[key]


# ---------------------------------------------------------------------------
# File path helpers
# ---------------------------------------------------------------------------

def _resolve(filename: str) -> Path:
    path = settings.data_path / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


DB_FILES = {
    "users":      "users.json",
    "expenses":   "expenses.json",
    "income":     "income.json",
    "savings":    "savings.json",
    "bills":      "bills.json",
    "categories": "categories.json",
}


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def read_json(filename: str) -> list[dict[str, Any]]:
    """Read a JSON file and return its contents as a list. Auto-creates if missing."""
    path = _resolve(filename)
    lock = _get_lock(path)
    with lock:
        if not path.exists():
            path.write_text("[]", encoding="utf-8")
            return []
        try:
            content = path.read_text(encoding="utf-8").strip()
            if not content:
                return []
            data = json.loads(content)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            # Corrupt file — reset it
            path.write_text("[]", encoding="utf-8")
            return []


def write_json(filename: str, data: list[dict[str, Any]]) -> None:
    """Safely write a list of dicts to a JSON file (atomic write)."""
    path = _resolve(filename)
    lock = _get_lock(path)
    tmp = path.with_suffix(".tmp")
    with lock:
        tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        tmp.replace(path)


def generate_id() -> str:
    """Generate a unique string ID."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Initialise all data files on startup
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Ensure all required JSON files exist."""
    for filename in DB_FILES.values():
        path = _resolve(filename)
        if not path.exists():
            path.write_text("[]", encoding="utf-8")

    # Seed default categories if empty
    cats = read_json(DB_FILES["categories"])
    if not cats:
        default_categories = [
            {"id": generate_id(), "name": "Food & Dining", "icon": "🍔", "budget_limit": None},
            {"id": generate_id(), "name": "Transport",     "icon": "🚗", "budget_limit": None},
            {"id": generate_id(), "name": "Housing",       "icon": "🏠", "budget_limit": None},
            {"id": generate_id(), "name": "Health",        "icon": "💊", "budget_limit": None},
            {"id": generate_id(), "name": "Education",     "icon": "📚", "budget_limit": None},
            {"id": generate_id(), "name": "Entertainment", "icon": "🎮", "budget_limit": None},
            {"id": generate_id(), "name": "Shopping",      "icon": "🛍️", "budget_limit": None},
            {"id": generate_id(), "name": "Travel",        "icon": "✈️", "budget_limit": None},
            {"id": generate_id(), "name": "Utilities",     "icon": "💡", "budget_limit": None},
            {"id": generate_id(), "name": "Other",         "icon": "📌", "budget_limit": None},
        ]
        write_json(DB_FILES["categories"], default_categories)
