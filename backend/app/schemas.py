from __future__ import annotations

from pydantic import BaseModel


class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class BBoxNorm(BaseModel):
    """Koordinat relatif (0-1) agar mudah dipakai sebagai overlay CSS."""

    x: float
    y: float
    w: float
    h: float


class Detection(BaseModel):
    label: str
    class_id: int
    confidence: float
    color: str
    bbox: BBox
    bbox_norm: BBoxNorm


class ModelInfo(BaseModel):
    mode: str  # "custom" | "pretrained-coco"
    name: str
    supported_categories: list[str]
    missing_categories: list[str]


class DetectResponse(BaseModel):
    id: int | None
    filename: str
    width: int
    height: int
    total: int
    counts: dict[str, int]
    detections: list[Detection]
    original_url: str | None
    annotated_url: str | None
    inference_ms: float
    model: ModelInfo


class HistoryItem(BaseModel):
    id: int
    filename: str
    created_at: str
    total: int
    counts: dict[str, int]
    annotated_url: str | None
    model_mode: str


class HistoryList(BaseModel):
    items: list[HistoryItem]
    total: int
