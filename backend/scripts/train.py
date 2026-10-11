"""Training YOLO untuk Kelasku.

  python scripts/train.py                      # pakai ../dataset (otomatis siapkan placeholder bila kosong)
  python scripts/train.py --epochs 100 --model yolov8s.pt --device 0

Hasil terbaik otomatis disalin ke models/best.pt dan langsung dipakai backend.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
DATASET = BACKEND.parent / "dataset"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).parent))

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def has_dataset() -> bool:
    d = DATASET / "images" / "train"
    return d.exists() and any(p.suffix.lower() in IMG_EXT for p in d.iterdir())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DATASET / "data.yaml"))
    ap.add_argument("--model", default="yolov8s.pt", help="bobot awal (transfer learning)")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--device", default=None, help="cpu, 0, 0,1, mps")
    ap.add_argument("--patience", type=int, default=20)
    ap.add_argument("--no-auto-dataset", action="store_true")
    args = ap.parse_args()

    import prepare_dataset

    prepare_dataset.write_data_yaml()  # sinkronkan nama kelas dengan backend

    if not has_dataset():
        if args.no_auto_dataset:
            sys.exit("Dataset kosong. Isi dataset/ atau jalankan: python scripts/prepare_dataset.py auto")
        print("Dataset tim belum ada -> menyiapkan dataset placeholder otomatis...")
        prepare_dataset.cmd_auto(argparse.Namespace(val_ratio=0.2))

    from ultralytics import YOLO

    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        patience=args.patience,
        project=str(BACKEND / "runs"),
        name="kelasku",
        exist_ok=True,
    )

    best = BACKEND / "runs" / "kelasku" / "weights" / "best.pt"
    if best.exists():
        target = BACKEND / "models" / "best.pt"
        target.parent.mkdir(exist_ok=True)
        shutil.copy2(best, target)
        print(f"\nModel disalin ke {target}. Restart backend untuk memakainya.")
    else:
        print("best.pt tidak ditemukan; cek folder runs/kelasku.")


if __name__ == "__main__":
    main()
