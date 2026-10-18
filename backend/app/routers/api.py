from __future__ import annotations
import uuid
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from PIL import UnidentifiedImageError
from .. import config, schemas
from ..services import history
from ..services.detector import detector, draw_detections, load_image
router = APIRouter(prefix="/api")

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

def _url(kind: str, filename: str | None) -> str | None:
    return f"/files/{kind}/{filename}" if filename else None

@router.get("/health")
def health():
    return {"status": "ok", "model_loaded": detector.loaded, "model": detector.info()}

@router.get("/categories")
def categories():
    return {"categories": config.CATEGORIES, "model": detector.info()}

@router.get("/stats")
def stats():
    return history.stats()

@router.post("/detect", response_model=schemas.DetectResponse)
def detect(
    file: UploadFile = File(..., description="Foto JPG/PNG/WEBP, maks. 10 MB"),
    conf: float = Form(config.DEFAULT_CONF, ge=0.01, le=1.0),
    iou: float = Form(config.DEFAULT_IOU, ge=0.01, le=1.0),
    categories: str = Form("", description="Filter, pisahkan koma. Contoh: Kursi,Meja"),
    save: bool = Form(True, description="Simpan ke riwayat"),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Format tidak didukung. Gunakan JPG, PNG, atau WEBP.")

    data = file.file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"Ukuran foto maksimal {config.MAX_UPLOAD_BYTES // 1024 // 1024} MB.")

    try:
        image = load_image(data)
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "File bukan gambar yang valid.")

    wanted = {c.strip() for c in categories.split(",") if c.strip()}
    valid = {c["name"] for c in config.CATEGORIES}
    if wanted - valid:
        raise HTTPException(422, f"Kategori tidak dikenal: {sorted(wanted - valid)}")

    if not detector.loaded:
        raise HTTPException(503, "Model belum siap, coba lagi sebentar.")
    raw, ms = detector.predict(image, conf=conf, iou=iou, categories=wanted or None)

    w, h = image.size
    detections = [
        schemas.Detection(
            label=d.label,
            class_id=d.class_id,
            confidence=round(d.confidence, 4),
            color=next(c["color"] for c in config.CATEGORIES if c["name"] == d.label),
            bbox=schemas.BBox(x1=d.x1, y1=d.y1, x2=d.x2, y2=d.y2),
            bbox_norm=schemas.BBoxNorm(x=d.x1 / w, y=d.y1 / h, w=(d.x2 - d.x1) / w, h=(d.y2 - d.y1) / h),
        )
        for d in raw
    ]
    counts: dict[str, int] = {}
    for d in detections:
        counts[d.label] = counts.get(d.label, 0) + 1

    token = uuid.uuid4().hex
    orig_name = ann_name = None
    if save:
        orig_name, ann_name = f"{token}.jpg", f"{token}.jpg"
        image.save(config.UPLOAD_DIR / orig_name, quality=92)
        draw_detections(image, raw).save(config.RESULT_DIR / ann_name, quality=92)

    row_id = None
    if save:
        row_id = history.add(
            filename=file.filename or "foto",
            width=w, height=h,
            total=len(detections),
            counts=counts,
            detections=[d.model_dump() for d in detections],
            original_file=orig_name,
            annotated_file=ann_name,
            model_mode=detector.mode,
            inference_ms=round(ms, 1),
        )

    return schemas.DetectResponse(
        id=row_id,
        filename=file.filename or "foto",
        width=w, height=h,
        total=len(detections),
        counts=counts,
        detections=detections,
        original_url=_url("uploads", orig_name),
        annotated_url=_url("results", ann_name),
        inference_ms=round(ms, 1),
        model=schemas.ModelInfo(**detector.info()),
    )


@router.get("/history", response_model=schemas.HistoryList)
def list_history(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    rows, total = history.list_(limit, offset)
    items = [
        schemas.HistoryItem(
            id=r["id"], filename=r["filename"], created_at=r["created_at"],
            total=r["total"], counts=r["counts"],
            annotated_url=_url("results", r["annotated_file"]),
            model_mode=r["model_mode"] or "",
        )
        for r in rows
    ]
    return schemas.HistoryList(items=items, total=total)


@router.get("/history/{analysis_id}", response_model=schemas.DetectResponse)
def get_history(analysis_id: int):
    r = history.get(analysis_id)
    if not r:
        raise HTTPException(404, "Riwayat tidak ditemukan.")
    return schemas.DetectResponse(
        id=r["id"], filename=r["filename"], width=r["width"], height=r["height"],
        total=r["total"], counts=r["counts"], detections=r["detections"],
        original_url=_url("uploads", r["original_file"]),
        annotated_url=_url("results", r["annotated_file"]),
        inference_ms=r["inference_ms"] or 0,
        model=schemas.ModelInfo(**detector.info()),
    )


@router.delete("/history/{analysis_id}", status_code=204)
def delete_history(analysis_id: int):
    r = history.delete(analysis_id)
    if not r:
        raise HTTPException(404, "Riwayat tidak ditemukan.")
    for folder, key in ((config.UPLOAD_DIR, "original_file"), (config.RESULT_DIR, "annotated_file")):
        if r[key]:
            (folder / r[key]).unlink(missing_ok=True)
