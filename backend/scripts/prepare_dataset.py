"""Utilitas dataset Kelasku.

  python scripts/prepare_dataset.py auto            # unduh & siapkan dataset placeholder (COCO128)
  python scripts/prepare_dataset.py split --src DIR # bagi folder gambar+label menjadi train/val
  python scripts/prepare_dataset.py check           # validasi struktur & label dataset/
"""
from __future__ import annotations

import argparse
import random
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
DATASET = BACKEND.parent / "dataset"
sys.path.insert(0, str(BACKEND))
from app.config import CATEGORIES  # noqa: E402

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
COCO128_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip"
# id COCO -> id Kelasku (urutan = CATEGORIES di app/config.py)
COCO_TO_KELASKU = {
    56: 0, 13: 0,   # chair, bench -> Kursi
    60: 1,          # dining table -> Meja
    63: 3,          # laptop
    73: 5,          # book -> Buku
    24: 6,          # backpack -> Tas
    39: 7,          # bottle -> Botol
    74: 8,          # clock -> Jam
    67: 9,          # cell phone -> Ponsel
    62: 10,         # tv -> Monitor
    66: 11,         # keyboard
    64: 12,         # mouse
    76: 13,         # scissors -> Gunting
}


def write_data_yaml() -> None:
    """Buat dataset/data.yaml dari CATEGORIES agar selalu sinkron dengan backend."""
    DATASET.mkdir(parents=True, exist_ok=True)
    lines = ["path: .", "train: images/train", "val: images/val", "", "names:"]
    lines += [f"  {i}: {c['name']}" for i, c in enumerate(CATEGORIES)]
    (DATASET / "data.yaml").write_text("\n".join(lines) + "\n")


def _clear_dataset() -> None:
    write_data_yaml()
    for sub in ("images", "labels"):
        for split in ("train", "val"):
            d = DATASET / sub / split
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True)
            (d / ".gitkeep").touch()


def _write_pairs(pairs: list[tuple[Path, Path | None]], val_ratio: float, seed: int = 42) -> None:
    random.Random(seed).shuffle(pairs)
    n_val = max(1, int(len(pairs) * val_ratio)) if len(pairs) > 1 else 0
    for i, (img, lbl) in enumerate(pairs):
        split = "val" if i < n_val else "train"
        shutil.copy2(img, DATASET / "images" / split / img.name)
        if lbl is not None:
            shutil.copy2(lbl, DATASET / "labels" / split / (img.stem + ".txt"))
    print(f"Selesai: {len(pairs) - n_val} train, {n_val} val -> {DATASET}")


def cmd_auto(args: argparse.Namespace) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "coco128.zip"
        print(f"Mengunduh {COCO128_URL} ...")
        urllib.request.urlretrieve(COCO128_URL, zpath)
        with zipfile.ZipFile(zpath) as z:
            z.extractall(tmp)
        root = Path(tmp) / "coco128"
        pairs: list[tuple[Path, Path | None]] = []
        remapped_dir = Path(tmp) / "remapped"
        remapped_dir.mkdir()
        for img in sorted((root / "images" / "train2017").iterdir()):
            lbl = root / "labels" / "train2017" / (img.stem + ".txt")
            if img.suffix.lower() not in IMG_EXT or not lbl.exists():
                continue
            lines = []
            for line in lbl.read_text().splitlines():
                parts = line.split()
                if parts and int(parts[0]) in COCO_TO_KELASKU:
                    lines.append(" ".join([str(COCO_TO_KELASKU[int(parts[0])]), *parts[1:]]))
            if lines:  # hanya gambar yang berisi kelas yang relevan
                out = remapped_dir / lbl.name
                out.write_text("\n".join(lines) + "\n")
                pairs.append((img, out))
        if not pairs:
            sys.exit("Tidak ada gambar relevan ditemukan.")
        _clear_dataset()
        _write_pairs(pairs, args.val_ratio)
    print("CATATAN: ini dataset placeholder dari COCO; Papan tulis & Lemari belum punya contoh.")


def cmd_split(args: argparse.Namespace) -> None:
    src = Path(args.src).resolve()
    pairs = []
    for img in sorted(src.rglob("*")):
        if img.suffix.lower() in IMG_EXT:
            lbl = img.with_suffix(".txt")
            if not lbl.exists():
                lbl = src / "labels" / (img.stem + ".txt")
            pairs.append((img, lbl if lbl.exists() else None))
    if not pairs:
        sys.exit(f"Tidak ada gambar di {src}")
    _clear_dataset()
    _write_pairs(pairs, args.val_ratio)


def cmd_check(_: argparse.Namespace) -> int:
    n_classes = len(CATEGORIES)
    problems = 0
    totals = [0] * n_classes
    for split in ("train", "val"):
        imgs = [p for p in (DATASET / "images" / split).glob("*") if p.suffix.lower() in IMG_EXT]
        print(f"[{split}] {len(imgs)} gambar")
        for img in imgs:
            lbl = DATASET / "labels" / split / (img.stem + ".txt")
            if not lbl.exists():
                print(f"  - tanpa label (dianggap background): {img.name}")
                continue
            for ln, line in enumerate(lbl.read_text().splitlines(), 1):
                p = line.split()
                try:
                    cid, vals = int(p[0]), [float(v) for v in p[1:]]
                    assert len(vals) == 4 and all(0 <= v <= 1 for v in vals)
                    assert 0 <= cid < n_classes
                    totals[cid] += 1
                except Exception:
                    problems += 1
                    print(f"  ! format salah {lbl.name}:{ln}: {line!r}")
    print("\nJumlah objek per kelas:")
    for c, n in zip(CATEGORIES, totals):
        warn = "  <-- belum ada contoh" if n == 0 else ("  <-- terlalu sedikit (<50)" if n < 50 else "")
        print(f"  {c['name']:<12} {n}{warn}")
    print("\nOK" if not problems else f"\n{problems} masalah ditemukan")
    return 1 if problems else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("auto"); a.add_argument("--val-ratio", type=float, default=0.2)
    s = sub.add_parser("split"); s.add_argument("--src", required=True); s.add_argument("--val-ratio", type=float, default=0.2)
    sub.add_parser("check")
    args = ap.parse_args()
    if args.cmd == "check":
        sys.exit(cmd_check(args))
    {"auto": cmd_auto, "split": cmd_split}[args.cmd](args)


if __name__ == "__main__":
    main()
