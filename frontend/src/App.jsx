import { useEffect, useRef, useState } from "react";
import "./index.css";
import "./App.css";

const defaultCategories = [
  { name: "Kursi", color: "#6478e8" },
  { name: "Meja", color: "#d69b42" },
  { name: "Papan tulis", color: "#299c83" },
  { name: "Laptop", color: "#bc78d4" },
  { name: "Lemari", color: "#dc7777" },
];

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function Icon({ name, size = 20 }) {
  const paths = {
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </>
    ),
    image: (
      <>
        <rect x="3" y="3" width="18" height="18" rx="3" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <path d="m21 15-5-5L5 21" />
      </>
    ),
    history: (
      <>
        <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
        <path d="M3 3v5h5" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path
          d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.6a8 8 0 0 1-1.6.9l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.6-.9l-1.7.6-1.4-2.4 1.4-1.1a8 8 0 0 1 0-1.9l-1.4-1.1 1.4-2.4 1.7.6a8 8 0 0 1 1.6-.9l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.6.9l1.7-.6 1.4 2.4-1.4 1.1a8 8 0 0 1-.1 1.8Z"
          transform="translate(-1 -1)"
        />
      </>
    ),
    upload: (
      <>
        <path d="M12 16V4m-5 5 5-5 5 5" />
        <path d="M20 16v4H4v-4" />
      </>
    ),
    sun: (
      <>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" />
      </>
    ),
    moon: <path d="M20.9 13A9 9 0 0 1 11 3.1 9 9 0 1 0 20.9 13Z" />,
    close: (
      <>
        <path d="m18 6-12 12M6 6l12 12" />
      </>
    ),
    arrow: (
      <>
        <path d="M7 17 17 7M7 7h10v10" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    file: (
      <>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
        <path d="M14 2v6h6M8 13h8m-8 4h8" />
      </>
    ),
    chevron: <path d="m9 18 6-6-6-6" />,
  };

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}

function readSavedTheme() {
  try {
    return localStorage.getItem("kelasku-theme") === "dark";
  } catch {
    return false;
  }
}

export default function App() {
  const [dark, setDark] = useState(readSavedTheme);
  const [image, setImage] = useState(null);
  const [fileName, setFileName] = useState("");
  const [activeCategory, setActiveCategory] = useState("Semua objek");
  const [dragging, setDragging] = useState(false);
  const [categories, setCategories] = useState(defaultCategories);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [online, setOnline] = useState(false);
  const fileInput = useRef(null);
  const requestId = useRef(0);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";

    try {
      localStorage.setItem("kelasku-theme", dark ? "dark" : "light");
    } catch {
      // Tema tetap berfungsi meskipun penyimpanan browser tidak tersedia.
    }
  }, [dark]);

  useEffect(() => {
    return () => {
      if (image) URL.revokeObjectURL(image);
    };
  }, [image]);

  useEffect(() => {
    fetch(`${API}/api/categories`)
      .then((response) => response.json())
      .then((data) => {
        setCategories(data.categories);
        setOnline(true);
      })
      .catch(() => setOnline(false)); // pakai daftar bawaan jika backend mati
  }, []);

  async function analyze(file) {
    const id = ++requestId.current;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const form = new FormData();
      form.append("file", file);
      const response = await fetch(`${API}/api/detect`, {
        method: "POST",
        body: form,
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || "Gagal menganalisis foto.");
      }
      const data = await response.json();
      if (id === requestId.current) setResult(data);
    } catch (err) {
      if (id !== requestId.current) return;
      setError(
        err instanceof TypeError
          ? `Backend tidak terjangkau. Pastikan server berjalan di ${API}`
          : err.message,
      );
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }

  function handleFile(file) {
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      alert("Pilih file gambar seperti JPG, PNG, atau WEBP.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert("Ukuran foto maksimal 10 MB.");
      return;
    }

    setImage(URL.createObjectURL(file));
    setFileName(file.name);
    setActiveCategory("Semua objek");
    analyze(file);
  }

  function removeImage() {
    requestId.current++; // batalkan hasil analisis yang masih berjalan
    setResult(null);
    setError("");
    setLoading(false);
    setImage(null);
    setFileName("");
    if (fileInput.current) fileInput.current.value = "";
  }

  const colorOf = (name) =>
    categories.find((category) => category.name === name)?.color ?? "#999";
  const visibleCounts = result
    ? Object.entries(result.counts).filter(
        ([name]) => activeCategory === "Semua objek" || name === activeCategory,
      )
    : [];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" aria-label="Kelasku beranda">
          <span className="brand-mark">K</span>
          <span className="brand-name">
            kelasku<span>.</span>
          </span>
        </a>

        <div className="sidebar-section">
          <p className="sidebar-label">WORKSPACE</p>
          <nav className="navigation">
            <a href="#dashboard" className="nav-link active">
              <Icon name="grid" />
              <span>Dashboard</span>
            </a>
            <a href="#analisis" className="nav-link">
              <Icon name="image" />
              <span>Analisis gambar</span>
            </a>
            <a href="#riwayat" className="nav-link">
              <Icon name="history" />
              <span>Riwayat analisis</span>
              <span className="nav-soon">Segera</span>
            </a>
          </nav>
        </div>

        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <span className="note-indicator" />
            <div>
              <strong>Mode pengembangan</strong>
              <p>
                {online ? "Backend AI terhubung" : "Backend belum terhubung"}
              </p>
            </div>
          </div>
          <div className="profile">
            <div className="avatar">K</div>
            <div className="profile-info">
              <strong>Kelasku Workspace</strong>
              <span>Proyek kelompok</span>
            </div>
            <button
              className="icon-button"
              title={dark ? "Aktifkan mode terang" : "Aktifkan mode gelap"}
              aria-label={dark ? "Aktifkan mode terang" : "Aktifkan mode gelap"}
              onClick={() => setDark((value) => !value)}
            >
              <Icon name={dark ? "sun" : "moon"} size={18} />
            </button>
          </div>
        </div>
      </aside>

      <main className="main-content" id="dashboard">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <Icon name="chevron" size={15} />
            <span>Dashboard</span>
          </div>
          <div className="topbar-actions">
            <span className="environment">
              <span /> Prototype
            </span>
            <button
              className="theme-button"
              onClick={() => setDark((value) => !value)}
              aria-label={dark ? "Gunakan mode terang" : "Gunakan mode gelap"}
              title={dark ? "Mode terang" : "Mode gelap"}
            >
              <Icon name={dark ? "sun" : "moon"} size={18} />
              <span>{dark ? "Mode terang" : "Mode gelap"}</span>
            </button>
          </div>
        </header>

        <div className="page-content">
          <section className="welcome-row">
            <div>
              <p className="eyebrow">RUANG KELAS · COMPUTER VISION</p>
              <h1>Dashboard</h1>
              <p className="welcome-description">
                Kenali dan hitung objek di ruang kelas melalui satu foto.
              </p>
            </div>
            <div className="date-chip">
              <span className="date-dot" />
              Prototipe aktif
            </div>
          </section>

          <section className="stats-grid" aria-label="Ringkasan aplikasi">
            <article className="stat-card">
              <div className="stat-top">
                <span className="stat-label">Foto diunggah</span>
                <span className="stat-icon">
                  <Icon name="image" size={18} />
                </span>
              </div>
              <div className="stat-value">{image ? "01" : "00"}</div>
              <p className="stat-caption">
                {image ? "Foto siap ditinjau" : "Belum ada foto pada sesi ini"}
              </p>
            </article>
            <article className="stat-card">
              <div className="stat-top">
                <span className="stat-label">Objek terdeteksi</span>
                <span className="stat-icon">
                  <Icon name="grid" size={18} />
                </span>
              </div>
              <div className="stat-value">
                {result ? String(result.total).padStart(2, "0") : "—"}
              </div>
              <p className="stat-caption">
                {loading
                  ? "Menganalisis foto…"
                  : result
                    ? `Selesai dalam ${Math.round(result.inference_ms)} ms`
                    : "Menunggu foto"}
              </p>
            </article>
            <article className="stat-card">
              <div className="stat-top">
                <span className="stat-label">Kategori objek</span>
                <span className="stat-icon">
                  <Icon name="file" size={18} />
                </span>
              </div>
              <div className="stat-value">
                {String(categories.length).padStart(2, "0")}
              </div>
              <p className="stat-caption">Kategori objek yang dikenali</p>
            </article>
          </section>

          <section className="workspace-grid" id="analisis">
            <article className="panel upload-panel">
              <div className="panel-heading">
                <div>
                  <p className="panel-kicker">LANGKAH 01</p>
                  <h2>Foto ruang kelas</h2>
                  <p className="panel-description">
                    Unggah gambar sebagai bahan analisis.
                  </p>
                </div>
                {image && (
                  <button className="text-button" onClick={removeImage}>
                    <Icon name="close" size={15} /> Hapus foto
                  </button>
                )}
              </div>

              <input
                ref={fileInput}
                className="visually-hidden"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={(event) => handleFile(event.target.files?.[0])}
              />

              {image ? (
                <div className="image-preview">
                  <img src={image} alt="Pratinjau ruang kelas yang diunggah" />
                  <div className="preview-overlay">
                    <div className="preview-file">
                      <Icon name="image" size={16} />
                      <span title={fileName}>{fileName}</span>
                    </div>
                    <button
                      className="preview-change"
                      onClick={() => fileInput.current?.click()}
                    >
                      Ganti foto
                    </button>
                  </div>
                </div>
              ) : (
                <div
                  className={`dropzone ${dragging ? "dragging" : ""}`}
                  onDragOver={(event) => {
                    event.preventDefault();
                    setDragging(true);
                  }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={(event) => {
                    event.preventDefault();
                    setDragging(false);
                    handleFile(event.dataTransfer.files?.[0]);
                  }}
                >
                  <div className="upload-icon">
                    <Icon name="upload" size={23} />
                  </div>
                  <h3>Mulai dengan foto kelas</h3>
                  <p>Seret gambar ke sini, atau pilih file dari perangkatmu.</p>
                  <button
                    className="primary-button"
                    onClick={() => fileInput.current?.click()}
                  >
                    <Icon name="upload" size={17} />
                    Pilih foto
                  </button>
                  <span className="file-hint">
                    JPG, PNG atau WEBP · Maks. 10 MB
                  </span>
                </div>
              )}

              <div className="upload-footer">
                <div className="footer-status">
                  <span
                    className={`status-indicator ${image ? "ready" : ""}`}
                  />
                  {image ? "Foto berhasil dimuat" : "Menunggu unggahan"}
                </div>
                <span>Foto dikirim ke backend lokal untuk dianalisis</span>
              </div>
            </article>

            <article className="panel results-panel">
              <div className="panel-heading">
                <div>
                  <p className="panel-kicker">LANGKAH 02</p>
                  <h2>Hasil deteksi</h2>
                  <p className="panel-description">
                    Ringkasan objek dari model computer vision.
                  </p>
                </div>
                <span className="coming-badge">
                  {loading
                    ? "Memproses…"
                    : result
                      ? `${result.total} objek`
                      : online
                        ? "Siap"
                        : "Belum terhubung"}
                </span>
              </div>

              {loading ? (
                <div className="results-empty">
                  <div className="spinner" />
                  <h3>Menganalisis foto…</h3>
                  <p>Model YOLO sedang mengenali objek di foto kelas.</p>
                </div>
              ) : error ? (
                <div className="results-empty">
                  <h3>Terjadi kendala</h3>
                  <p>{error}</p>
                </div>
              ) : result ? (
                <div className="results-body">
                  <img
                    className="results-image"
                    src={`${API}${result.annotated_url}`}
                    alt="Foto dengan kotak deteksi"
                  />
                  {visibleCounts.length === 0 ? (
                    <p className="results-none">
                      {result.total === 0
                        ? "Tidak ada objek terdeteksi. Coba foto yang lebih jelas."
                        : `Tidak ada "${activeCategory}" pada foto ini.`}
                    </p>
                  ) : (
                    <ul className="results-counts">
                      {visibleCounts.map(([name, count]) => (
                        <li key={name}>
                          <span
                            className="category-dot"
                            style={{ backgroundColor: colorOf(name) }}
                          />
                          <span className="count-name">{name}</span>
                          <strong>{count}</strong>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : (
                <div className="results-empty">
                  <div className="empty-illustration">
                    <div className="empty-frame">
                      <Icon name="image" size={29} />
                      <span className="frame-corner corner-tl" />
                      <span className="frame-corner corner-tr" />
                      <span className="frame-corner corner-bl" />
                      <span className="frame-corner corner-br" />
                    </div>
                  </div>
                  <h3>Hasil akan muncul di sini</h3>
                  <p>
                    Unggah foto kelas, lalu jumlah objek dan kotak deteksi akan
                    ditampilkan pada bagian ini.
                  </p>
                </div>
              )}

              <div className="results-footer">
                <span>Model</span>
                <span className="model-value">
                  YOLO ·{" "}
                  {result
                    ? result.model.mode === "custom"
                      ? "Model kustom"
                      : "COCO pretrained"
                    : "Siap menganalisis"}
                </span>
              </div>
            </article>
          </section>

          <section className="panel category-panel">
            <div className="category-heading">
              <div>
                <p className="panel-kicker">REFERENSI ANALISIS</p>
                <h2>Kategori objek</h2>
                <p className="panel-description">
                  Pilih kategori untuk memfilter hasil deteksi.
                </p>
              </div>
              <span className="category-count">
                {String(categories.length).padStart(2, "0")} kategori
              </span>
            </div>

            <div className="category-list">
              <button
                className={`category-item ${activeCategory === "Semua objek" ? "selected" : ""}`}
                onClick={() => setActiveCategory("Semua objek")}
              >
                <span className="category-dot all-dot" />
                <span>Semua objek</span>
                <span className="category-arrow">
                  <Icon name="chevron" size={16} />
                </span>
              </button>
              {categories.map((category) => (
                <button
                  className={`category-item ${activeCategory === category.name ? "selected" : ""}`}
                  key={category.name}
                  onClick={() => setActiveCategory(category.name)}
                >
                  <span
                    className="category-dot"
                    style={{ backgroundColor: category.color }}
                  />
                  <span>{category.name}</span>
                  <span className="category-arrow">
                    <Icon name="chevron" size={16} />
                  </span>
                </button>
              ))}
            </div>

            <div className="category-note">
              <Icon name="file" size={17} />
              <p>
                <strong>{activeCategory}</strong>
                {result
                  ? activeCategory === "Semua objek"
                    ? ` — ${result.total} objek terdeteksi pada foto.`
                    : ` — ${result.counts[activeCategory] ?? 0} terdeteksi pada foto.`
                  : image
                    ? " dipilih. Hasil akan tampil setelah analisis selesai."
                    : " — unggah foto terlebih dahulu untuk melihat jumlah objek."}
              </p>
            </div>
          </section>

          <footer className="page-footer">
            <span>
              Kelasku <span className="footer-dot">·</span> Kenali lebih dalam
              kelasmu.
            </span>
            <span></span>
          </footer>
        </div>
      </main>
    </div>
  );
}
