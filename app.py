"""
GiziSiKecil – WHO Growth, Permenkes, PDF, EduParenting
------------------------------------------------------
FastAPI + Gradio app for child growth monitoring:

- Z-score WHO (WAZ, HAZ, WHZ, BAZ, HCZ)
- Dual classification WHO + Permenkes
- Growth curves (BB/U, TB/U, LK/U, BB/TB)
- Monthly checklist & KPSP
- EduParenting & motivational quotes
- PDF report export

Run (e.g. on Render):
    uvicorn app:app --host 0.0.0.0 --port $PORT
"""

import os
import math
import random
from datetime import datetime, date
from typing import Optional, Dict, Any, Tuple

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pygrowup import Calculator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import gradio as gr

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from functools import lru_cache

# -------------------------------------------------
# Global config & folders
# -------------------------------------------------
APP_VERSION = "2.3.0"
APP_TITLE = "GiziSiKecil - Monitor Pertumbuhan Anak (Full)"

BASE_URL = os.getenv("BASE_URL", "https://anthrohpk-app.onrender.com")
STATIC_DIR = "static"
OUTPUTS_DIR = "outputs"
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# -------------------------------------------------
# EduParenting: Video & Motivational Quotes
# -------------------------------------------------
YOUTUBE_VIDEOS = {
    "mpasi_6bln": {
        "title": "🥕 Resep MPASI 6 Bulan Pertama",
        "url": "https://www.youtube.com/watch?v=7Zg3L2J5HfE",
        "thumbnail": "https://img.youtube.com/vi/7Zg3L2J5HfE/hqdefault.jpg",
    },
    "motorik_6bln": {
        "title": "🤸 Stimulasi Motorik Kasar 6-9 Bulan",
        "url": "https://www.youtube.com/watch?v=9Y9n1A6d7Kk",
        "thumbnail": "https://img.youtube.com/vi/9Y9n1A6d7Kk/hqdefault.jpg",
    },
    "mpasi_9bln": {
        "title": "🍚 MPASI 9 Bulan: Tekstur Kasar",
        "url": "https://www.youtube.com/watch?v=Q0X3Y2Z1x0o",
        "thumbnail": "https://img.youtube.com/vi/Q0X3Y2Z1x0o/hqdefault.jpg",
    },
    "bahasa_12bln": {
        "title": "🗣️ Stimulasi Bahasa 12-15 Bulan",
        "url": "https://www.youtube.com/watch?v=2W3X4Y5Z6A7",
        "thumbnail": "https://img.youtube.com/vi/2W3X4Y5Z6A7/hqdefault.jpg",
    },
    "imunisasi": {
        "title": "💉 Jadwal Imunisasi Bayi Lengkap",
        "url": "https://www.youtube.com/watch?v=5X6Y7Z8A9B0",
        "thumbnail": "https://img.youtube.com/vi/5X6Y7Z8A9B0/hqdefault.jpg",
    },
}

MOM_QUOTES = [
    "💕 'Seorang ibu adalah penjelajah yang tak pernah lelah, selalu menemukan jalan cinta untuk anaknya.'",
    "🌟 'Kekuatan ibu melebihi segala rintangan, kasihnya membentuk masa depan yang cerah.'",
    "🤱 'Setiap tetes ASI adalah investasi cinta tak ternilai dalam perjalanan tumbuh kembang Si Kecil.'",
    "💪 'Kamu kuat, kamu cukup, dan kamu melakukan yang terbaik untuk Si Kecil! Jangan menyerah, Ibu hebat!'",
    "🌈 'Pertumbuhan anak bukan kompetisi, tapi perjalanan cinta bersama. Setiap langkah kecil adalah pencapaian besar.'",
    "💖 'Ibu, hatimu adalah rumah pertama Si Kecil, dan itu akan selalu jadi rumahnya yang paling aman.'",
]

# -------------------------------------------------
# WHO Calculator
# -------------------------------------------------
try:
    calc = Calculator(
        adjust_height_data=False,
        adjust_weight_scores=False,
        include_cdc=False,
        logger_name="pygrowup",
        log_level="ERROR",
    )
    print("✅ WHO Calculator (pygrowup) loaded")
except Exception as e:
    print("❌ ERROR init Calculator:", e)
    calc = None

# -------------------------------------------------
# Helper functions: parsing & age
# -------------------------------------------------
def as_float(x) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).replace(",", ".").strip())
    except Exception:
        return None


def parse_date(s: str) -> Optional[date]:
    """Terima format: YYYY-MM-DD atau DD/MM/YYYY."""
    if not s:
        return None
    s = s.strip()
    # Format 1: YYYY-MM-DD
    try:
        y, m, d = [int(p) for p in s.split("-")]
        return date(y, m, d)
    except Exception:
        pass
    # Format 2: DD/MM/YYYY
    try:
        d, m, y = [int(p) for p in s.split("/")]
        return date(y, m, d)
    except Exception:
        return None


def age_months_from_dates(dob: date, dom: date) -> Optional[float]:
    if not dob or not dom or dom < dob:
        return None
    days = (dom - dob).days
    if days < 0:
        return None
    return days / 30.4375  # rata-rata hari per bulan (365.25 / 12)


def z_to_percentile(z: Optional[float]) -> Optional[float]:
    if z is None or math.isnan(z):
        return None
    p = 0.5 * (1 + math.erf(z / math.sqrt(2))) * 100
    return round(p, 1)

# -------------------------------------------------
# WHO Z-scores & Permenkes classification
# -------------------------------------------------
def compute_zscores(
    sex_label: str,
    age_months: Optional[float],
    w_kg: Optional[float],
    h_cm: Optional[float],
    hc_cm: Optional[float],
) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {k: None for k in ("waz", "haz", "whz", "baz", "hcz")}
    if calc is None or age_months is None:
        return out

    sex = "M" if sex_label.lower().startswith("l") else "F"

    try:
        if w_kg is not None:
            out["waz"] = calc.wfa(w_kg, age_months, sex)
        if h_cm is not None:
            out["haz"] = calc.lhfa(h_cm, age_months, sex)
        if w_kg is not None and h_cm is not None:
            out["whz"] = calc.wfl(w_kg, age_months, sex, h_cm)
            try:
                bmi = w_kg / ((h_cm / 100) ** 2)
                out["baz"] = calc.bmifa(bmi, age_months, sex)
            except Exception:
                out["baz"] = None
        if hc_cm is not None:
            out["hcz"] = calc.hcfa(hc_cm, age_months, sex)
    except Exception:
        # Jangan biarkan satu error menjatuhkan seluruh analisis
        pass

    # sanitasi
    for k, v in list(out.items()):
        try:
            if v is not None:
                v = float(v)
                if math.isinf(v) or math.isnan(v):
                    out[k] = None
                else:
                    out[k] = round(v, 2)
        except Exception:
            out[k] = None
    return out


def classify_permenkes_waz(z: Optional[float]) -> str:
    if z is None:
        return "Tidak diketahui"
    if z < -3:
        return "Gizi buruk (BB sangat kurang)"
    if z < -2:
        return "Gizi kurang"
    if z <= 1:
        return "BB normal"
    return "Risiko BB lebih"


def classify_permenkes_haz(z: Optional[float]) -> str:
    if z is None:
        return "Tidak diketahui"
    if z < -3:
        return "Sangat pendek (stunting berat)"
    if z < -2:
        return "Pendek (stunting)"
    if z <= 3:
        return "Normal"
    return "Tinggi"


def classify_permenkes_whz(z: Optional[float]) -> str:
    if z is None:
        return "Tidak diketahui"
    if z < -3:
        return "Gizi buruk (sangat kurus)"
    if z < -2:
        return "Gizi kurang (kurus)"
    if z <= 1:
        return "Gizi baik (normal)"
    if z <= 2:
        return "Risiko gizi lebih"
    if z <= 3:
        return "Gizi lebih"
    return "Obesitas"


def classify_hcz(z: Optional[float]) -> str:
    if z is None:
        return "Tidak diketahui"
    if z < -3:
        return "Lingkar kepala sangat kecil (mikrosefali berat)"
    if z < -2:
        return "Lingkar kepala di bawah normal (mikrosefali)"
    if z > 3:
        return "Lingkar kepala sangat besar (makrosefali berat)"
    if z > 2:
        return "Lingkar kepala di atas normal (makrosefali)"
    return "Normal"


def build_interpretation(
    name_child: str,
    sex_label: str,
    age_mo: Optional[float],
    w_kg: Optional[float],
    h_cm: Optional[float],
    hc_cm: Optional[float],
    z: Dict[str, Optional[float]],
) -> str:
    title = f"## Hasil Analisis Gizi {'untuk ' + name_child if name_child else ''}\n"
    if age_mo is None:
        return title + "❌ Usia tidak valid. Pastikan tanggal lahir & tanggal ukur benar."

    sex_text = sex_label or "Tidak diketahui"

    lines = [
        f"- **Jenis kelamin:** {sex_text}",
        f"- **Usia:** {age_mo:.1f} bulan",
        f"- **Berat badan:** {w_kg:.1f} kg" if w_kg is not None else "- **Berat badan:** (tidak diisi)",
        f"- **Tinggi/panjang:** {h_cm:.1f} cm" if h_cm is not None else "- **Tinggi/panjang:** (tidak diisi)",
        f"- **Lingkar kepala:** {hc_cm:.1f} cm" if hc_cm is not None else "- **Lingkar kepala:** (tidak diisi)",
        "",
        "### Ringkasan Z-score (WHO) & Klasifikasi Permenkes",
    ]

    def row(label, key, permenkes_fn):
        zv = z.get(key)
        if zv is None:
            return f"- **{label}:** Z = —  |  klasifikasi: (data tidak cukup)"
        per = z_to_percentile(zv)
        per_txt = f"{per} persentil" if per is not None else "—"
        perm = permenkes_fn(zv)
        return f"- **{label}:** Z = {zv:.2f}  (≈ {per_txt})  →  **{perm}**"

    lines.append(row("Berat menurut umur (WAZ)", "waz", classify_permenkes_waz))
    lines.append(row("Tinggi/panjang menurut umur (HAZ)", "haz", classify_permenkes_haz))
    lines.append(row("Berat menurut panjang/tinggi (WHZ)", "whz", classify_permenkes_whz))

    hcz = z.get("hcz")
    if hcz is not None:
        lines.append(
            f"- **Lingkar kepala menurut umur (HCZ):** Z = {hcz:.2f} → {classify_hcz(hcz)}"
        )

    lines.append("")
    lines.append(
        "💡 **Catatan:** Interpretasi ini mengikuti standar WHO & Permenkes RI No. 2 Tahun 2020. "
        "Gunakan sebagai alat bantu edukasi; keputusan klinis tetap oleh tenaga kesehatan."
    )
    return title + "\n".join(lines)

# -------------------------------------------------
# WHO growth curve helpers
# -------------------------------------------------
BOUNDS = {
    "wfa": (1.0, 30.0),       # berat (kg)
    "hfa": (45.0, 125.0),     # panjang/tinggi (cm)
    "hcfa": (30.0, 55.0),     # lingkar kepala (cm)
    "wfl_w": (1.0, 30.0),     # berat untuk BB/TB
    "wfl_l": (45.0, 110.0),   # panjang/tinggi untuk BB/TB
}

AGE_GRID = np.arange(0.0, 60.0 + 1e-9, 0.25)  # 0–60 bulan, step 0.25


def _safe_z(calc_func, *args) -> Optional[float]:
    if calc is None:
        return None
    try:
        z = calc_func(*args)
        if z is None:
            return None
        z_float = float(z)
        if math.isnan(z_float) or math.isinf(z_float):
            return None
        return z_float
    except Exception:
        return None


def brentq_simple(f, a: float, b: float, xtol: float = 1e-3, maxiter: int = 50) -> float:
    fa = f(a)
    fb = f(b)
    if fa is None or fb is None:
        return (a + b) / 2.0
    if fa == 0:
        return a
    if fb == 0:
        return b
    if fa * fb > 0:
        return (a + b) / 2.0

    for _ in range(maxiter):
        m = 0.5 * (a + b)
        fm = f(m)
        if fm is None:
            return m
        if abs(fm) < 1e-5 or (b - a) / 2.0 < xtol:
            return m
        if fa * fm < 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return 0.5 * (a + b)


def invert_z_with_scan(z_of_m, target_z: float, lo: float, hi: float, samples: int = 80) -> float:
    xs = np.linspace(lo, hi, samples)
    last_x = None
    last_f = None
    best_x = None
    best_abs = float("inf")

    for x in xs:
        z = z_of_m(x)
        if z is None:
            continue
        f = z - target_z
        af = abs(f)
        if af < best_abs:
            best_x = x
            best_abs = af
        if last_f is not None and f * last_f < 0:
            try:
                root = brentq_simple(lambda t: (z_of_m(t) or 0.0) - target_z, last_x, x)
                return float(root)
            except Exception:
                pass
        last_x, last_f = x, f

    if best_x is not None:
        return float(best_x)
    return float((lo + hi) / 2.0)


def generate_wfa_curve(sex: str, target_z: float) -> Tuple[np.ndarray, np.ndarray]:
    ages = AGE_GRID
    lo, hi = BOUNDS["wfa"]

    def z_func(weight, age_mo):
        return _safe_z(calc.wfa, weight, age_mo, sex)

    weights = []
    for age in ages:
        val = invert_z_with_scan(lambda w: z_func(w, age), target_z, lo, hi)
        weights.append(val)
    return ages.copy(), np.array(weights)


def generate_hfa_curve(sex: str, target_z: float) -> Tuple[np.ndarray, np.ndarray]:
    ages = AGE_GRID
    lo, hi = BOUNDS["hfa"]

    def z_func(height, age_mo):
        return _safe_z(calc.lhfa, height, age_mo, sex)

    heights = []
    for age in ages:
        val = invert_z_with_scan(lambda h: z_func(h, age), target_z, lo, hi)
        heights.append(val)
    return ages.copy(), np.array(heights)


def generate_hcfa_curve(sex: str, target_z: float) -> Tuple[np.ndarray, np.ndarray]:
    ages = AGE_GRID
    lo, hi = BOUNDS["hcfa"]

    def z_func(hc, age_mo):
        return _safe_z(calc.hcfa, hc, age_mo, sex)

    vals = []
    for age in ages:
        val = invert_z_with_scan(lambda h: z_func(h, age), target_z, lo, hi)
        vals.append(val)
    return ages.copy(), np.array(vals)


def generate_wfl_curve(sex: str, age_months: float, target_z: float) -> Tuple[np.ndarray, np.ndarray]:
    lengths = np.arange(BOUNDS["wfl_l"][0], BOUNDS["wfl_l"][1] + 0.5, 0.5)
    lo_w, hi_w = BOUNDS["wfl_w"]

    def z_func(weight, length):
        return _safe_z(calc.wfl, weight, age_months, sex, length)

    weights = []
    for L in lengths:
        val = invert_z_with_scan(lambda w: z_func(w, L), target_z, lo_w, hi_w)
        weights.append(val)
    return lengths, np.array(weights)


@lru_cache(maxsize=64)
def generate_wfa_curve_cached(sex: str, z: float):
    return generate_wfa_curve(sex, z)


@lru_cache(maxsize=64)
def generate_hfa_curve_cached(sex: str, z: float):
    return generate_hfa_curve(sex, z)


@lru_cache(maxsize=64)
def generate_hcfa_curve_cached(sex: str, z: float):
    return generate_hcfa_curve(sex, z)


@lru_cache(maxsize=128)
def generate_wfl_curve_cached(sex: str, age_key: float, z: float):
    return generate_wfl_curve(sex, age_key, z)

# -------------------------------------------------
# Checklist bulanan & KPSP
# -------------------------------------------------
IMMUNIZATION_SCHEDULE = {
    0: ["HB 0", "BCG", "Polio 0"],
    1: ["HB 1", "Polio 1", "DPT-HB-Hib 1"],
    2: ["Polio 2", "DPT-HB-Hib 2"],
    3: ["Polio 3", "DPT-HB-Hib 3"],
    4: ["Polio 4", "DPT-HB-Hib 4"],
    9: ["Campak/MR 1"],
    12: ["Campak Booster"],
    18: ["DPT-HB-Hib Booster", "Polio Booster"],
    24: ["Campak Rubella (MR) 2"],
}

KPSP_QUESTIONS = {
    3: [
        "Mengangkat kepala 45° saat tengkurap?",
        "Tersenyum saat diajak bicara?",
        "Mengoceh (suara vokal)?",
        "Menatap dan mengikuti wajah ibu?",
        "Meraih benda/mainan?",
    ],
    6: [
        "Duduk dengan bantuan (bersandar)?",
        "Memindahkan mainan dari tangan ke tangan?",
        "Mengeluarkan suara 'a-u-o'?",
        "Tertawa keras saat bermain?",
        "Mengenal orang asing (malu/marah)?",
    ],
    9: [
        "Duduk sendiri tanpa bantuan?",
        "Merangkak maju?",
        "Mengucap 'mama/papa' (belum tentu tepat)?",
        "Meraih benda kecil dengan dua jari?",
        "Menirukan gerakan tepuk tangan?",
    ],
    12: [
        "Berdiri sendiri minimal beberapa detik?",
        "Berjalan berpegangan furnitur?",
        "Mengucap 2–3 kata bermakna?",
        "Minum dari cangkir sendiri (sedikit tumpah)?",
        "Menunjuk benda yang diinginkan?",
    ],
    18: [
        "Berjalan sendiri dengan stabil?",
        "Makan sendiri dengan sendok (masih berantakan)?",
        "Mengucap ≥10 kata?",
        "Menumpuk 2–4 kubus?",
        "Menunjuk 3 bagian tubuh?",
    ],
    24: [
        "Berlari beberapa langkah?",
        "Melompat dengan kedua kaki?",
        "Menyusun kalimat 2–3 kata?",
        "Meniru garis vertikal saat menggambar?",
        "Mengikuti perintah 2 langkah?",
    ],
}


def nearest_kpsp_month(age_mo: float) -> int:
    keys = sorted(KPSP_QUESTIONS.keys())
    return min(keys, key=lambda k: abs(k - age_mo))


def build_checklist(age_mo: float) -> str:
    m = int(round(age_mo))
    m = max(0, min(60, m))
    title = f"## Checklist Bulanan & KPSP (Usia ~{m} bulan)\n"

    # Imunisasi bulan ini (tepat atau ±1 bulan)
    imm = [
        (bulan, v)
        for bulan, v in IMMUNIZATION_SCHEDULE.items()
        if abs(bulan - m) <= 1
    ]
    if imm:
        lines = ["### 💉 Imunisasi yang perlu dicek bulan ini:"]
        for bulan, vaks in imm:
            lines.append(f"- Usia {bulan} bulan: " + ", ".join(vaks))
    else:
        lines = ["### 💉 Imunisasi:", "- Tidak ada jadwal khusus bulan ini, cek buku KIA."]

    # KPSP
    ref = nearest_kpsp_month(m)
    lines.append("")
    lines.append(f"### 🧠 Skrining perkembangan (KPSP) sekitar usia {ref} bulan:")
    for q in KPSP_QUESTIONS[ref]:
        lines.append(f"- [ ] {q}")

    lines.append("")
    lines.append(
        "👉 Jika banyak jawaban **TIDAK**, konsultasikan dengan tenaga kesehatan "
        "untuk skrining perkembangan lanjutan."
    )

    return title + "\n".join(lines)

# -------------------------------------------------
# Plotting: Z-score bar + growth curves
# -------------------------------------------------
def make_zscore_bar_chart(z: Dict[str, Optional[float]]) -> plt.Figure:
    labels = ["WAZ", "HAZ", "WHZ", "BAZ", "HCZ"]
    keys = ["waz", "haz", "whz", "baz", "hcz"]
    values = [z.get(k) if z.get(k) is not None else 0 for k in keys]

    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    ax.bar(labels, values)
    ax.axhline(0, color="black", linewidth=1)
    ax.axhline(-2, color="red", linestyle="--", linewidth=1)
    ax.axhline(2, color="red", linestyle="--", linewidth=1)
    ax.set_ylabel("Z-score")
    ax.set_title("Ringkasan Z-score WHO")
    ax.set_ylim(-4, 4)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig


def _sex_code(sex_label: str) -> str:
    return "M" if sex_label.lower().startswith("l") else "F"


def plot_wfa_curve(payload: Dict[str, Any]) -> Optional[plt.Figure]:
    if calc is None:
        return None
    age_mo = payload.get("age_mo")
    w = payload.get("w")
    sex_label = payload.get("sex_label") or ""
    if age_mo is None or w is None:
        return None

    sex = _sex_code(sex_label)
    sd_levels = [-3, -2, -1, 0, 1, 2, 3]

    curves = {}
    for z in sd_levels:
        ages, weights = generate_wfa_curve_cached(sex, float(z))
        curves[z] = (ages, weights)

    fig, ax = plt.subplots(figsize=(5.5, 3.5))

    # Zona normal -2 s/d +2
    ages = curves[0][0]
    ax.fill_between(ages, curves[-2][1], curves[2][1], color="#E8F5E9", alpha=0.7, label="Normal (-2 s/d +2 SD)")

    for z in sd_levels:
        ages, weights = curves[z]
        if z == 0:
            style, width = "-", 2.2
        elif abs(z) == 1:
            style, width = "--", 1.3
        else:
            style, width = ":", 1.0
        ax.plot(ages, weights, linestyle=style, linewidth=width, label=f"{z:+d} SD")

    waz = payload.get("z", {}).get("waz")
    color = "tab:green"
    if waz is not None:
        if abs(waz) > 3:
            color = "tab:red"
        elif abs(waz) > 2:
            color = "orange"
    ax.scatter([age_mo], [w], s=40, color=color, zorder=5, label="Data anak")

    ax.set_xlim(0, 60)
    ax.set_xlabel("Usia (bulan)")
    ax.set_ylabel("Berat badan (kg)")
    ax.set_title("Grafik BB menurut Umur (BB/U) - WHO")
    ax.grid(True, linestyle="--", alpha=0.4)

    y_vals = np.concatenate([curves[z][1] for z in (-3, -2, 0, 2, 3)])
    ax.set_ylim(max(0, y_vals.min() - 1), y_vals.max() + 2)

    ax.legend(fontsize=7, ncol=2, loc="upper left")
    fig.tight_layout()
    return fig


def plot_hfa_curve(payload: Dict[str, Any]) -> Optional[plt.Figure]:
    if calc is None:
        return None
    age_mo = payload.get("age_mo")
    h = payload.get("h")
    sex_label = payload.get("sex_label") or ""
    if age_mo is None or h is None:
        return None

    sex = _sex_code(sex_label)
    sd_levels = [-3, -2, -1, 0, 1, 2, 3]

    curves = {}
    for z in sd_levels:
        ages, heights = generate_hfa_curve_cached(sex, float(z))
        curves[z] = (ages, heights)

    fig, ax = plt.subplots(figsize=(5.5, 3.5))

    ages = curves[0][0]
    ax.fill_between(ages, curves[-2][1], curves[2][1], color="#E3F2FD", alpha=0.6, label="Normal (-2 s/d +2 SD)")

    for z in sd_levels:
        ages, heights = curves[z]
        if z == 0:
            style, width = "-", 2.2
        elif abs(z) == 1:
            style, width = "--", 1.3
        else:
            style, width = ":", 1.0
        ax.plot(ages, heights, linestyle=style, linewidth=width, label=f"{z:+d} SD")

    haz = payload.get("z", {}).get("haz")
    color = "tab:green"
    if haz is not None:
        if abs(haz) > 3:
            color = "tab:red"
        elif abs(haz) > 2:
            color = "orange"
    ax.scatter([age_mo], [h], s=40, color=color, zorder=5, label="Data anak")

    ax.set_xlim(0, 60)
    ax.set_xlabel("Usia (bulan)")
    ax.set_ylabel("Panjang/Tinggi (cm)")
    ax.set_title("Grafik TB menurut Umur (TB/U) - WHO")
    ax.grid(True, linestyle="--", alpha=0.4)

    y_vals = np.concatenate([curves[z][1] for z in (-3, -2, 0, 2, 3)])
    ax.set_ylim(max(45, y_vals.min() - 1), y_vals.max() + 2)

    ax.legend(fontsize=7, ncol=2, loc="upper left")
    fig.tight_layout()
    return fig


def plot_hcfa_curve(payload: Dict[str, Any]) -> Optional[plt.Figure]:
    if calc is None:
        return None
    age_mo = payload.get("age_mo")
    hc = payload.get("hc")
    sex_label = payload.get("sex_label") or ""
    if age_mo is None or hc is None:
        return None

    sex = _sex_code(sex_label)
    sd_levels = [-3, -2, -1, 0, 1, 2, 3]

    curves = {}
    for z in sd_levels:
        ages, vals = generate_hcfa_curve_cached(sex, float(z))
        curves[z] = (ages, vals)

    fig, ax = plt.subplots(figsize=(5.5, 3.5))

    ages = curves[0][0]
    ax.fill_between(ages, curves[-2][1], curves[2][1], color="#FFF9C4", alpha=0.6, label="Normal (-2 s/d +2 SD)")

    for z in sd_levels:
        ages, vals = curves[z]
        if z == 0:
            style, width = "-", 2.2
        elif abs(z) == 1:
            style, width = "--", 1.3
        else:
            style, width = ":", 1.0
        ax.plot(ages, vals, linestyle=style, linewidth=width, label=f"{z:+d} SD")

    hcz = payload.get("z", {}).get("hcz")
    color = "tab:green"
    if hcz is not None:
        if abs(hcz) > 3:
            color = "tab:red"
        elif abs(hcz) > 2:
            color = "orange"
    ax.scatter([age_mo], [hc], s=40, color=color, zorder=5, label="Data anak")

    ax.set_xlim(0, 60)
    ax.set_xlabel("Usia (bulan)")
    ax.set_ylabel("Lingkar kepala (cm)")
    ax.set_title("Grafik LK menurut Umur (LK/U) - WHO")
    ax.grid(True, linestyle="--", alpha=0.4)

    y_vals = np.concatenate([curves[z][1] for z in (-3, -2, 0, 2, 3)])
    ax.set_ylim(max(30, y_vals.min() - 1), y_vals.max() + 2)

    ax.legend(fontsize=7, ncol=2, loc="upper left")
    fig.tight_layout()
    return fig


def plot_wfl_curve(payload: Dict[str, Any]) -> Optional[plt.Figure]:
    if calc is None:
        return None
    age_mo = payload.get("age_mo")
    w = payload.get("w")
    h = payload.get("h")
    sex_label = payload.get("sex_label") or ""
    if age_mo is None or w is None or h is None:
        return None

    sex = _sex_code(sex_label)
    sd_levels = [-3, -2, -1, 0, 1, 2, 3]

    age_key = round(age_mo * 2) / 2.0  # dibulatkan 0.5 bulan untuk caching
    curves = {}
    for z in sd_levels:
        lengths, weights = generate_wfl_curve_cached(sex, age_key, float(z))
        curves[z] = (lengths, weights)

    fig, ax = plt.subplots(figsize=(5.5, 3.5))

    lengths = curves[0][0]
    ax.fill_between(lengths, curves[-2][1], curves[2][1], color="#E8F5E9", alpha=0.6, label="Normal (-2 s/d +2 SD)")

    for z in sd_levels:
        lengths, weights = curves[z]
        if z == 0:
            style, width = "-", 2.2
        elif abs(z) == 1:
            style, width = "--", 1.3
        else:
            style, width = ":", 1.0
        ax.plot(lengths, weights, linestyle=style, linewidth=width, label=f"{z:+d} SD")

    whz = payload.get("z", {}).get("whz")
    color = "tab:green"
    if whz is not None:
        if abs(whz) > 3:
            color = "tab:red"
        elif abs(whz) > 2:
            color = "orange"
    ax.scatter([h], [w], s=40, color=color, zorder=5, label="Data anak")

    ax.set_xlabel("Panjang/Tinggi (cm)")
    ax.set_ylabel("Berat badan (kg)")
    ax.set_title("Grafik BB menurut TB (BB/TB) - WHO")
    ax.grid(True, linestyle="--", alpha=0.4)

    y_vals = np.concatenate([curves[z][1] for z in (-3, -2, 0, 2, 3)])
    ax.set_ylim(max(0, y_vals.min() - 1), y_vals.max() + 2)
    ax.set_xlim(BOUNDS["wfl_l"][0], BOUNDS["wfl_l"][1])

    ax.legend(fontsize=7, ncol=2, loc="upper left")
    fig.tight_layout()
    return fig

# -------------------------------------------------
# PDF generator
# -------------------------------------------------
def generate_pdf_report(payload: Dict[str, Any]) -> str:
    """
    Buat laporan PDF sederhana dari payload analisis.
    Mengembalikan path file PDF di folder outputs/.
    """
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    name = (payload.get("name_child") or "anak").strip().replace(" ", "_")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gizisikecil_report_{name}_{ts}.pdf"
    path = os.path.join(OUTPUTS_DIR, filename)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    margin = 40

    z = payload.get("z", {})
    age_mo = payload.get("age_mo")
    sex_label = payload.get("sex_label") or "Tidak diketahui"
    w_kg = payload.get("w")
    h_cm = payload.get("h")
    hc_cm = payload.get("hc")

    text = c.beginText()
    text.setTextOrigin(margin, height - margin - 20)
    text.setFont("Helvetica-Bold", 14)
    text.textLine("Laporan Status Gizi Anak (GiziSiKecil)")
    text.setFont("Helvetica", 9)
    text.textLine(f"Tanggal cetak: {datetime.now().strftime('%d %B %Y, %H:%M WIB')}")
    text.textLine("")

    # Identitas singkat
    text.textLine("Identitas:")
    text.textLine(f"- Nama anak      : {payload.get('name_child') or '-'}")
    text.textLine(f"- Jenis kelamin  : {sex_label}")
    if age_mo is not None:
        text.textLine(f"- Usia           : {age_mo:.1f} bulan")
    else:
        text.textLine("- Usia           : (tidak valid)")
    text.textLine(
        f"- Berat badan    : {w_kg:.1f} kg" if w_kg is not None else "- Berat badan    : (tidak diisi)"
    )
    text.textLine(
        f"- Tinggi/Panjang : {h_cm:.1f} cm" if h_cm is not None else "- Tinggi/Panjang : (tidak diisi)"
    )
    text.textLine(
        f"- Lingkar kepala : {hc_cm:.1f} cm" if hc_cm is not None else "- Lingkar kepala : (tidak diisi)"
    )
    text.textLine("")

    # Z-score
    text.textLine("Z-score WHO & klasifikasi Permenkes:")

    def z_line(label: str, key: str, fn_perm):
        zv = z.get(key)
        if zv is None:
            return f"- {label}: Z = — | (data tidak cukup)"
        per = z_to_percentile(zv)
        per_txt = f"{per} persentil" if per is not None else "—"
        klas = fn_perm(zv)
        return f"- {label}: Z = {zv:.2f} (~ {per_txt}) → {klas}"

    text.textLine(z_line("Berat menurut umur (WAZ)", "waz", classify_permenkes_waz))
    text.textLine(z_line("Tinggi/Panjang menurut umur (HAZ)", "haz", classify_permenkes_haz))
    text.textLine(z_line("Berat menurut panjang/tinggi (WHZ)", "whz", classify_permenkes_whz))

    hcz = z.get("hcz")
    if hcz is not None:
        text.textLine(
            f"- Lingkar kepala (HCZ): Z = {hcz:.2f} → {classify_hcz(hcz)}"
        )

    text.textLine("")
    text.textLine("Catatan penting:")
    text.textLine(
        "- Laporan ini bersifat skrining edukatif, bukan pengganti diagnosis klinis."
    )
    text.textLine(
        "- Untuk penilaian menyeluruh, konsultasikan hasil ini dengan tenaga kesehatan."
    )
    text.textLine("- Data diolah berdasarkan WHO Child Growth Standards & Permenkes No. 2/2020.")
    text.textLine("")

    c.drawText(text)
    c.showPage()
    c.save()
    return path

# -------------------------------------------------
# EduParenting helpers
# -------------------------------------------------
def get_random_quote() -> str:
    if not MOM_QUOTES:
        return "Ibu/Ayah, kamu sudah melakukan yang terbaik hari ini. Terima kasih sudah berjuang untuk Si Kecil. 💖"
    return random.choice(MOM_QUOTES)


def get_recommended_videos(age_mo: Optional[float]):
    if age_mo is None:
        keys = ["imunisasi"]
    else:
        a = age_mo
        keys = []
        if a < 5:
            keys.append("imunisasi")
        if 5 <= a <= 8:
            keys.extend(["mpasi_6bln", "motorik_6bln"])
        if 8 < a <= 11:
            keys.extend(["mpasi_9bln", "motorik_6bln"])
        if a >= 11:
            keys.extend(["bahasa_12bln", "imunisasi"])

    seen = set()
    videos = []
    for k in keys:
        if k in seen:
            continue
        v = YOUTUBE_VIDEOS.get(k)
        if v:
            videos.append(v)
            seen.add(k)

    if not videos:
        videos = [YOUTUBE_VIDEOS["imunisasi"]]

    return videos


def edu_callback(
    sex_label,
    age_mode,
    dob_str,
    dom_str,
    age_months_manual,
):
    if age_mode == "Tanggal":
        dob = parse_date(dob_str) if dob_str else None
        dom = parse_date(dom_str) if dom_str else date.today()
        age_mo = age_months_from_dates(dob, dom) if (dob and dom) else None
    else:
        age_mo = as_float(age_months_manual)

    quote = "### 💌 Pesan untuk Ibu/Ayah\n\n"
    quote += f"> {get_random_quote()}\n\n"

    if age_mo is None:
        quote += "_Isi tanggal lahir atau usia anak terlebih dahulu agar rekomendasi lebih spesifik._\n\n"
    else:
        quote += f"_Rekomendasi ini disesuaikan untuk usia sekitar **{age_mo:.1f} bulan**._\n\n"

    videos = get_recommended_videos(age_mo)
    md = "### 🎥 Rekomendasi tontonan edukatif\n\n"
    md += "Video-video berikut membantu orang tua memahami gizi, stimulasi, dan imunisasi sesuai usia anak.\n\n"

    for i, v in enumerate(videos, start=1):
        title = v["title"]
        url = v["url"]
        thumb = v["thumbnail"]
        md += f"{i}. **{title}**  \n"
        md += f"[Tonton di YouTube]({url})  \n"
        md += f"![thumbnail]({thumb})  \n\n"

    md += "_Catatan: Link mengarah ke YouTube, pastikan kuota & koneksi aman digunakan._"

    return quote, md

# -------------------------------------------------
# Analisis utama & callbacks
# -------------------------------------------------
def compute_analysis(
    name_child,
    sex_label,
    age_mode,
    dob_str,
    dom_str,
    age_months_manual,
    w_kg,
    h_cm,
    hc_cm,
):
    w = as_float(w_kg)
    h = as_float(h_cm)
    hc = as_float(hc_cm)

    if age_mode == "Tanggal":
        dob = parse_date(dob_str) if dob_str else None
        dom = parse_date(dom_str) if dom_str else date.today()
        age_mo = age_months_from_dates(dob, dom) if (dob and dom) else None
    else:
        age_mo = as_float(age_months_manual)

    if age_mo is not None and age_mo < 0:
        age_mo = None

    z = compute_zscores(sex_label, age_mo, w, h, hc)
    payload = {
        "name_child": name_child,
        "sex_label": sex_label,
        "age_mo": age_mo,
        "w": w,
        "h": h,
        "hc": hc,
        "z": z,
    }
    md = build_interpretation(name_child or "", sex_label, age_mo, w, h, hc, z)
    return payload, md


def generate_all_plots(payload: Dict[str, Any]):
    z = payload.get("z", {})
    any_valid = any(v is not None for v in z.values())
    summary_fig = make_zscore_bar_chart(z) if any_valid else None

    def safe_plot(fn):
        try:
            return fn(payload)
        except Exception:
            return None

    wfa_fig = safe_plot(plot_wfa_curve)
    hfa_fig = safe_plot(plot_hfa_curve)
    hcfa_fig = safe_plot(plot_hcfa_curve)
    wfl_fig = safe_plot(plot_wfl_curve)

    return summary_fig, wfa_fig, hfa_fig, hcfa_fig, wfl_fig


def analyze_callback(
    name_child,
    sex_label,
    age_mode,
    dob_str,
    dom_str,
    age_months_manual,
    w_kg,
    h_cm,
    hc_cm,
):
    try:
        payload, md = compute_analysis(
            name_child,
            sex_label,
            age_mode,
            dob_str,
            dom_str,
            age_months_manual,
            w_kg,
            h_cm,
            hc_cm,
        )
        summary_fig, wfa_fig, hfa_fig, hcfa_fig, wfl_fig = generate_all_plots(payload)
        return md, summary_fig, wfa_fig, hfa_fig, hcfa_fig, wfl_fig
    except Exception as e:
        msg = f"❌ Terjadi error saat analisis: {e}"
        return msg, None, None, None, None, None


def pdf_callback(
    name_child,
    sex_label,
    age_mode,
    dob_str,
    dom_str,
    age_months_manual,
    w_kg,
    h_cm,
    hc_cm,
):
    try:
        payload, _ = compute_analysis(
            name_child,
            sex_label,
            age_mode,
            dob_str,
            dom_str,
            age_months_manual,
            w_kg,
            h_cm,
            hc_cm,
        )
        path = generate_pdf_report(payload)
        return path
    except Exception as e:
        dummy_path = os.path.join(OUTPUTS_DIR, "ERROR.txt")
        with open(dummy_path, "w", encoding="utf-8") as f:
            f.write(f"Gagal membuat PDF: {e}")
        return dummy_path


def checklist_callback(age_months):
    try:
        age = as_float(age_months)
        if age is None:
            return "❌ Masukkan usia yang valid."
        return build_checklist(age)
    except Exception as e:
        return f"❌ Terjadi error saat membuat checklist: {e}"


def toggle_age_inputs(mode):
    if mode == "Tanggal":
        return gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
    else:
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

# -------------------------------------------------
# Build Gradio UI
# -------------------------------------------------
def build_demo() -> gr.Blocks:
    with gr.Blocks(
        title=APP_TITLE,
        theme=gr.themes.Soft(primary_hue="pink", secondary_hue="teal", neutral_hue="slate"),
    ) as demo:
        gr.Markdown(
            f"# 🏥 GiziSiKecil\n"
            f"Monitor pertumbuhan anak berbasis **WHO Child Growth Standards**\n\n"
            f"_Versi lengkap: Z-score, kurva WHO, PDF, checklist, EduParenting (v{APP_VERSION})_"
        )

        # ===================== TAB 1: KALKULATOR GIZI =====================
        with gr.Tab("📊 Kalkulator Gizi"):
            with gr.Row():
                with gr.Column(scale=1):
                    name_child = gr.Textbox(label="Nama anak (opsional)")
                    sex = gr.Radio(
                        ["Laki-laki", "Perempuan"],
                        value="Laki-laki",
                        label="Jenis kelamin",
                    )
                    age_mode = gr.Radio(
                        ["Tanggal", "Usia (bulan)"],
                        value="Tanggal",
                        label="Mode input usia",
                    )
                    dob = gr.Textbox(
                        label="Tanggal lahir (DD/MM/YYYY)",
                        placeholder="12/05/2023",
                    )
                    dom = gr.Textbox(
                        label="Tanggal ukur (DD/MM/YYYY)",
                        value=date.today().strftime("%d/%m/%Y"),
                    )
                    age_months_manual = gr.Number(
                        label="Usia (bulan)",
                        visible=False,
                        precision=1,
                    )

                    w_kg = gr.Number(label="Berat badan (kg)")
                    h_cm = gr.Number(label="Tinggi/panjang (cm)")
                    hc_cm = gr.Number(label="Lingkar kepala (cm)", value=None)

                    btn_analyze = gr.Button("🔍 Analisis sekarang", variant="primary")
                    btn_pdf = gr.Button("📄 Buat laporan PDF", variant="secondary")

                with gr.Column(scale=2):
                    result_md = gr.Markdown("Hasil analisis akan muncul di sini.")
                    summary_plot = gr.Plot(label="Ringkasan Z-score WHO")
                    with gr.Row():
                        wfa_plot = gr.Plot(label="BB menurut Umur (BB/U)")
                        hfa_plot = gr.Plot(label="TB menurut Umur (TB/U)")
                    with gr.Row():
                        hcfa_plot = gr.Plot(label="LK menurut Umur (LK/U)")
                        wfl_plot = gr.Plot(label="BB menurut TB (BB/TB)")
                    pdf_file = gr.File(label="Laporan PDF", interactive=False)

            age_mode.change(
                toggle_age_inputs,
                inputs=age_mode,
                outputs=[dob, dom, age_months_manual],
            )

            btn_analyze.click(
                analyze_callback,
                inputs=[
                    name_child,
                    sex,
                    age_mode,
                    dob,
                    dom,
                    age_months_manual,
                    w_kg,
                    h_cm,
                    hc_cm,
                ],
                outputs=[result_md, summary_plot, wfa_plot, hfa_plot, hcfa_plot, wfl_plot],
            )

            btn_pdf.click(
                pdf_callback,
                inputs=[
                    name_child,
                    sex,
                    age_mode,
                    dob,
                    dom,
                    age_months_manual,
                    w_kg,
                    h_cm,
                    hc_cm,
                ],
                outputs=[pdf_file],
            )

        # ===================== TAB 2: CHECKLIST =====================
        with gr.Tab("📅 Checklist bulanan & KPSP"):
            gr.Markdown(
                "Checklist ini membantu orang tua mengingat imunisasi dan memantau perkembangan "
                "anak berdasarkan usia."
            )
            age_for_check = gr.Slider(0, 60, value=6, step=1, label="Usia anak (bulan)")
            checklist_md = gr.Markdown()
            age_for_check.change(checklist_callback, inputs=age_for_check, outputs=checklist_md)

        # ===================== TAB 3: EDUPARENTING =====================
        with gr.Tab("🎥 EduParenting & Motivasi"):
            gr.Markdown(
                "Tab ini berisi **motivasi untuk orang tua** dan rekomendasi video edukatif "
                "tentang MPASI, stimulasi motorik, bahasa, dan imunisasi, disesuaikan dengan usia anak."
            )

            with gr.Row():
                with gr.Column(scale=1):
                    sex2 = gr.Radio(
                        ["Laki-laki", "Perempuan"],
                        value="Laki-laki",
                        label="Jenis kelamin anak",
                    )
                    age_mode2 = gr.Radio(
                        ["Tanggal", "Usia (bulan)"],
                        value="Tanggal",
                        label="Mode input usia",
                    )
                    dob2 = gr.Textbox(
                        label="Tanggal lahir (DD/MM/YYYY)",
                        placeholder="12/05/2023",
                    )
                    dom2 = gr.Textbox(
                        label="Tanggal cek (DD/MM/YYYY)",
                        value=date.today().strftime("%d/%m/%Y"),
                    )
                    age_months_manual2 = gr.Number(
                        label="Usia (bulan)",
                        visible=False,
                        precision=1,
                    )

                    btn_edu = gr.Button("✨ Tampilkan rekomendasi", variant="primary")

                with gr.Column(scale=2):
                    quote_md = gr.Markdown("Pesan motivasi untuk orang tua akan muncul di sini.")
                    video_md = gr.Markdown("Rekomendasi video akan muncul di sini.")

            age_mode2.change(
                toggle_age_inputs,
                inputs=age_mode2,
                outputs=[dob2, dom2, age_months_manual2],
            )

            btn_edu.click(
                edu_callback,
                inputs=[sex2, age_mode2, dob2, dom2, age_months_manual2],
                outputs=[quote_md, video_md],
            )

        gr.Markdown(
            "Made with ❤️ oleh mahasiswa FKIK UNJA. "
            "Untuk edukasi, bukan pengganti konsultasi langsung dengan tenaga kesehatan."
        )

    return demo

# -------------------------------------------------
# FastAPI + mounting Gradio
# -------------------------------------------------
app_fastapi = FastAPI(
    title="GiziSiKecil API",
    description="WHO Child Growth Standards + Permenkes + checklist & EduParenting",
    version=APP_VERSION,
)

app_fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(STATIC_DIR):
    app_fastapi.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if os.path.exists(OUTPUTS_DIR):
    app_fastapi.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")


@app_fastapi.get("/health", response_model=dict)
async def health_check():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "calculator": bool(calc),
        "time": datetime.now().isoformat(),
    }


@app_fastapi.get("/premium", response_class=HTMLResponse)
async def premium_page():
    html = f"""
    <html><head><title>GiziSiKecil Premium</title></head>
    <body style="font-family: sans-serif; padding: 2rem;">
      <h1>GiziSiKecil Premium</h1>
      <p>Halaman ini placeholder untuk materi premium (PDF lengkap, template laporan, dsb.).</p>
      <p>Silakan hubungi admin (+62 {os.getenv('CONTACT_WA', '---')}) jika ingin mengembangkan versi premium.</p>
    </body></html>
    """
    return HTMLResponse(content=html)


demo = build_demo()
app = gr.mount_gradio_app(app_fastapi, demo, path="/")
