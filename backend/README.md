# Kelasku — Backend (FastAPI + YOLO)

API deteksi objek ruang kelas: **Kursi/bangku, Meja, Papan tulis, Laptop, Lemari, Buku, Tas, Botol, Jam, Ponsel, Monitor, Keyboard, Mouse, Gunting**.

```
proyek/
├── backend/   <- folder ini
├── frontend/
└── dataset/   (dibuat otomatis oleh skrip jika belum ada)
```

## Menjalankan

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # opsional
uvicorn app.main:app --reload --port 8000
```

Dokumentasi interaktif: http://localhost:8000/docs

### Mode model
| Kondisi | Mode | Kelas yang bisa dikenali |
|---|---|---|
| `models/best.pt` **ada** (hasil training tim) | `custom` | semua 5 kelas |
| `models/best.pt` **belum ada** | `pretrained-coco` (`yolov8s.pt`, diunduh otomatis) | semua kecuali Papan tulis & Lemari |

Mode aktif dan kategori yang belum didukung terlihat di `GET /api/health`
(`missing_categories`), sehingga frontend bisa menampilkan peringatan.

## Endpoint

| Method | Path | Fungsi |
|---|---|---|
| GET | `/api/health` | status server + info model |
| GET | `/api/categories` | daftar kategori + warna (sama dengan frontend) |
| GET | `/api/stats` | total foto & objek yang pernah dianalisis |
| POST | `/api/detect` | unggah foto → hasil deteksi |
| GET | `/api/history` | riwayat (`?limit=&offset=`) |
| GET | `/api/history/{id}` | detail satu analisis |
| DELETE | `/api/history/{id}` | hapus analisis + file-nya |

`POST /api/detect` (multipart): `file` (wajib), `conf` (0.25), `iou` (0.45),
`categories` (mis. `Kursi,Meja`; kosong = semua), `save` (true).

Contoh respons:
```json
{
  "id": 1, "filename": "kelas.jpg", "width": 1280, "height": 720,
  "total": 3, "counts": {"Kursi": 2, "Laptop": 1},
  "detections": [{
    "label": "Kursi", "class_id": 0, "confidence": 0.91, "color": "#6478e8",
    "bbox": {"x1": 10, "y1": 20, "x2": 200, "y2": 300},
    "bbox_norm": {"x": 0.008, "y": 0.028, "w": 0.148, "h": 0.389}
  }],
  "original_url": "/files/uploads/ab12.jpg",
  "annotated_url": "/files/results/ab12.jpg",
  "inference_ms": 85.3,
  "model": {"mode": "custom", "name": "best.pt", "supported_categories": [], "missing_categories": []}
}
```
`bbox_norm` (0–1) memudahkan menggambar kotak overlay di atas `<img>` yang di-resize CSS.
URL file relatif terhadap server, mis. `http://localhost:8000` + `annotated_url`.

## Menyambungkan ke frontend (React)

```js
const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function detect(file, categories = []) {
  const form = new FormData();
  form.append("file", file);
  if (categories.length) form.append("categories", categories.join(","));
  const res = await fetch(`${API}/api/detect`, { method: "POST", body: form });
  if (!res.ok) throw new Error((await res.json()).detail);
  return res.json(); // { total, counts, detections, annotated_url, ... }
}
```
CORS sudah mengizinkan `http://localhost:5173` (Vite). Ubah lewat `CORS_ORIGINS` di `.env`.

## Dataset & training

```bash
python scripts/prepare_dataset.py auto     # dataset placeholder otomatis (COCO128)
python scripts/prepare_dataset.py check    # validasi dataset tim
python scripts/train.py --epochs 100       # train -> otomatis ke models/best.pt
```
Jika `dataset/` kosong, `train.py` menyiapkan dataset placeholder sendiri.
Detail format ada di `../dataset/README.md`. Setelah training, restart `uvicorn`.

## Struktur
```
app/
  main.py            aplikasi FastAPI, CORS, file statis
  config.py          pengaturan, kategori, pemetaan kelas COCO
  schemas.py         model respons
  routers/api.py     endpoint
  services/detector.py   load YOLO, prediksi, gambar kotak
  services/history.py    riwayat SQLite (storage/history.db)
scripts/             prepare_dataset.py, train.py
models/              taruh best.pt di sini
storage/             unggahan, hasil, dan database (diabaikan git)
```

## Menambah / mengubah kategori
Edit `CATEGORIES` (nama + warna) dan `COCO_ALIASES` di `app/config.py`.
Urutan `CATEGORIES` = id kelas pada dataset; `scripts/train.py` otomatis
menulis ulang `dataset/data.yaml` agar selalu sinkron. Jika urutan/kelas
berubah, dataset harus di-label ulang dan model di-train ulang.
