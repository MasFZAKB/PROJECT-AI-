"""Layanan deteksi objek berbasis YOLO (Ultralytics)."""
from __future__ import annotations

import io
import logging
import threading
import time
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageOps

from .. import config

log = logging.getLogger("kelasku.detector")

COLOR_BY_NAME = {c["name"]: c["color"] for c in config.CATEGORIES}
ID_BY_NAME = {c["name"]: i for i, c in enumerate(config.CATEGORIES)}
_NAME_LOOKUP = {c["name"].lower(): c["name"] for c in config.CATEGORIES}


def to_category(model_class_name: str) -> str | None:
    """Petakan nama kelas model ke kategori Kelasku (None = abaikan)."""
    key = model_class_name.strip().lower().replace("_", " ")
    return _NAME_LOOKUP.get(key) or config.COCO_ALIASES.get(key)


def _hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return b, g, r


@dataclass
class RawDetection:
    label: str
    class_id: int
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class Detector:
    def __init__(self) -> None:
        self._model = None
        self._lock = threading.Lock()
        self.mode = "not-loaded"
        self.model_name = ""
        self._class_map: dict[int, str] = {}

    # ------------------------------------------------------------------ load
    def load(self) -> None:
        from ultralytics import YOLO  # import lambat -> ditunda

        if config.MODEL_PATH.exists():
            log.info("Memuat model kustom: %s", config.MODEL_PATH)
            self._model = YOLO(str(config.MODEL_PATH))
            self.mode = "custom"
            self.model_name = config.MODEL_PATH.name
        else:
            log.warning(
                "Model kustom %s belum ada -> memakai model COCO pretrained (%s). "
                "Hanya Kursi, Meja, dan Laptop yang bisa dikenali sampai tim "
                "selesai training.",
                config.MODEL_PATH,
                config.FALLBACK_MODEL,
            )
            self._model = YOLO(config.FALLBACK_MODEL)  # diunduh otomatis
            self.mode = "pretrained-coco"
            self.model_name = config.FALLBACK_MODEL

        names = self._model.names  # {id: name}
        self._class_map = {
            i: cat for i, n in names.items() if (cat := to_category(n)) is not None
        }
        log.info("Kelas yang dipetakan: %s", self._class_map)

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def info(self) -> dict:
        supported = sorted(set(self._class_map.values()), key=ID_BY_NAME.get)
        return {
            "mode": self.mode,
            "name": self.model_name,
            "supported_categories": supported,
            "missing_categories": [
                c["name"] for c in config.CATEGORIES if c["name"] not in supported
            ],
        }

    # --------------------------------------------------------------- predict
    def predict(
        self,
        image: Image.Image,
        conf: float | None = None,
        iou: float | None = None,
        categories: set[str] | None = None,
    ) -> tuple[list[RawDetection], float]:
        if not self.loaded:
            raise RuntimeError("Model belum dimuat")

        arr = np.asarray(image.convert("RGB"))
        start = time.perf_counter()
        with self._lock:  # model Ultralytics tidak dijamin thread-safe
            results = self._model.predict(
                arr[:, :, ::-1],  # Ultralytics mengharapkan BGR untuk ndarray
                conf=conf if conf is not None else config.DEFAULT_CONF,
                iou=iou if iou is not None else config.DEFAULT_IOU,
                imgsz=config.IMGSZ,
                device=config.DEVICE,
                verbose=False,
            )
        elapsed = (time.perf_counter() - start) * 1000

        out: list[RawDetection] = []
        boxes = results[0].boxes
        for xyxy, score, cls in zip(
            boxes.xyxy.cpu().numpy(), boxes.conf.cpu().numpy(), boxes.cls.cpu().numpy()
        ):
            label = self._class_map.get(int(cls))
            if label is None or (categories and label not in categories):
                continue
            x1, y1, x2, y2 = (float(v) for v in xyxy)
            out.append(
                RawDetection(label, ID_BY_NAME[label], float(score), x1, y1, x2, y2)
            )
        out.sort(key=lambda d: d.confidence, reverse=True)
        return out, elapsed


# --------------------------------------------------------------------- utils
def load_image(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img)  # hormati rotasi foto dari HP
    return img.convert("RGB")


def draw_detections(image: Image.Image, dets: list[RawDetection]) -> Image.Image:
    """Gambar kotak + label pada salinan gambar."""
    canvas = np.asarray(image.convert("RGB")).copy()[:, :, ::-1].copy()
    h, w = canvas.shape[:2]
    thick = max(2, round(max(h, w) / 400))
    scale = max(0.5, max(h, w) / 1400)

    for d in dets:
        color = _hex_to_bgr(COLOR_BY_NAME[d.label])
        p1, p2 = (int(d.x1), int(d.y1)), (int(d.x2), int(d.y2))
        cv2.rectangle(canvas, p1, p2, color, thick, cv2.LINE_AA)

        text = f"{d.label} {d.confidence:.0%}"
        (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
        top = max(p1[1] - th - base - 4, 0)
        cv2.rectangle(canvas, (p1[0], top), (p1[0] + tw + 6, top + th + base + 4), color, -1)
        cv2.putText(
            canvas, text, (p1[0] + 3, top + th + 1),
            cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1, cv2.LINE_AA,
        )
    return Image.fromarray(canvas[:, :, ::-1])


detector = Detector()
