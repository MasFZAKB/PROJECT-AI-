from flask import Flask, request, jsonify
from flask_cors import CORS
from ultralytics import YOLO
import io
from PIL import Image

# Inisialisasi Aplikasi Flask
app = Flask(__name__)
CORS(app)

# 1. Muat (Load) Model YOLO Default
# Menggunakan 'yolov8n.pt' (YOLOv8 versi Nano yang paling ringan dan cepat).
# Saat dijalankan pertama kali, ia akan otomatis mendownload file yolov8n.pt dari internet.
MODEL_PATH = "yolov8n.pt" 
try:
    model = YOLO(MODEL_PATH)
    print(f"✅ Model YOLO '{MODEL_PATH}' (Default) berhasil dimuat!")
except Exception as e:
    print(f"❌ Error memuat model: {e}")
    model = None

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "aktif",
        "pesan": "Backend AI Kelasku siap menerima gambar!",
        "model_loaded": model is not None
    })

@app.route("/detect", methods=["POST"])
def detect_objects():
    if model is None:
        return jsonify({"error": "Model AI belum siap di server."}), 500
    
    if 'image' not in request.files:
        return jsonify({"error": "Tidak ada gambar yang dikirim."}), 400
        
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"error": "File gambar kosong."}), 400

    try:
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Lakukan prediksi (conf=0.25 agar hanya barang yg model yakin >25% yang ditampilkan)
        results = model.predict(image, conf=0.25) 
        
        detections = []
        
        for result in results:
             boxes = result.boxes
             for box in boxes:
                 x1, y1, x2, y2 = box.xyxy[0].tolist()
                 conf = round(box.conf[0].item(), 2)
                 
                 # Ambil nama kelas barang bawaan YOLO (Bahasa Inggris: chair, laptop, dll)
                 cls_id = int(box.cls[0].item())
                 class_name = model.names[cls_id]
                 
                 detections.append({
                     "barang": class_name,
                     "confidence": conf,
                     "box": {
                         "x1": round(x1), 
                         "y1": round(y1), 
                         "x2": round(x2), 
                         "y2": round(y2)
                     }
                 })
                 
        return jsonify({
            "status": "success",
            "jumlah_terdeteksi": len(detections),
            "data": detections
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Terjadi kesalahan: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
