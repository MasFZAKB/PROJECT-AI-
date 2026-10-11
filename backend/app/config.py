"""Konfigurasi backend Kelasku (dibaca dari environment / file .env)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
DATASET_DIR = ROOT_DIR / "dataset"

load_dotenv(BACKEND_DIR / ".env")


def _path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (BACKEND_DIR / p)


# Kategori objek yang dirancang di frontend (urutan = class id pada dataset).
CATEGORIES: list[dict[str, str]] = [
    {"name": "Kursi", "color": "#6478e8"},
    {"name": "Meja", "color": "#d69b42"},
    {"name": "Papan tulis", "color": "#299c83"},
    {"name": "Laptop", "color": "#bc78d4"},
    {"name": "Lemari", "color": "#dc7777"},
    {"name": "Buku", "color": "#e0679a"},
    {"name": "Tas", "color": "#4aa3c9"},
    {"name": "Botol", "color": "#7cb342"},
    {"name": "Jam", "color": "#f0883e"},
    {"name": "Ponsel", "color": "#8e7cc3"},
    {"name": "Monitor", "color": "#3f8f8f"},
    {"name": "Keyboard", "color": "#a1887f"},
    {"name": "Mouse", "color": "#c0a030"},
    {"name": "Gunting", "color": "#d1495b"},
]

# Nama kelas bawaan model COCO -> kategori Kelasku. Dipakai saat model
# kustom belum ada (COCO tidak punya "papan tulis" dan "lemari").
COCO_ALIASES: dict[str, str] = {
    "chair": "Kursi", "bench": "Kursi", "couch": "Kursi",
    "dining table": "Meja", "desk": "Meja", "table": "Meja",
    "laptop": "Laptop",
    "whiteboard": "Papan tulis", "blackboard": "Papan tulis",
    "cabinet": "Lemari", "wardrobe": "Lemari", "closet": "Lemari",
    "book": "Buku",
    "backpack": "Tas", "handbag": "Tas",
    "bottle": "Botol",
    "clock": "Jam",
    "cell phone": "Ponsel",
    "tv": "Monitor", "monitor": "Monitor",
    "keyboard": "Keyboard",
    "mouse": "Mouse",
    "scissors": "Gunting",
}

MODEL_PATH = _path(os.getenv("MODEL_PATH", "models/best.pt"))
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "yolov8s.pt")
DEFAULT_CONF = float(os.getenv("DEFAULT_CONF", "0.25"))
DEFAULT_IOU = float(os.getenv("DEFAULT_IOU", "0.45"))
IMGSZ = int(os.getenv("IMGSZ", "640"))
DEVICE = os.getenv("DEVICE") or None
MAX_UPLOAD_BYTES = int(float(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024)
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if o.strip()
]

STORAGE_DIR = BACKEND_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
RESULT_DIR = STORAGE_DIR / "results"
DB_PATH = STORAGE_DIR / "history.db"
for _d in (UPLOAD_DIR, RESULT_DIR):
    _d.mkdir(parents=True, exist_ok=True)
