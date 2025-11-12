# ==================== APP.PY FIXED & ENHANCED ====================
"""
GiziSiKecil Web Application - Checklist Sehat Bulanan (0-24 bln)
FIXED VERSION: Semua fitur fungsional + Tema Dinamis + Premium Plans
=========================
Run: uvicorn app:app --host 0.0.0.0 --port 8000
"""
# -------------------- Imports & setup --------------------
import os, sys, io, csv, math, datetime, traceback, json, random, requests
from functools import lru_cache
from math import erf, sqrt
from datetime import datetime, timedelta

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))

from pygrowup import Calculator
import gradio as gr
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import qrcode
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import warnings
from decimal import Decimal

warnings.filterwarnings('ignore')

# -------------------- Constants & Configurations --------------------
CONTACT_WA = "6285888858160"
YOUTUBE_VIDEOS = {
    "mpasi_6bln": {"title": "🥕 Resep MPASI 6 Bulan Pertama", "url": "https://www.youtube.com/watch?v=7Zg3L2J5HfE", "thumbnail": "https://img.youtube.com/vi/7Zg3L2J5HfE/hqdefault.jpg"},
    "motorik_6bln": {"title": "🤸 Stimulasi Motorik Kasar 6-9 Bulan", "url": "https://www.youtube.com/watch?v=9Y9n1A6d7Kk", "thumbnail": "https://img.youtube.com/vi/9Y9n1A6d7Kk/hqdefault.jpg"},
    "mpasi_9bln": {"title": "🍚 MPASI 9 Bulan: Tekstur Kasar", "url": "https://www.youtube.com/watch?v=Q0X3Y2Z1x0o", "thumbnail": "https://img.youtube.com/vi/Q0X3Y2Z1x0o/hqdefault.jpg"},
    "bahasa_12bln": {"title": "🗣️ Stimulasi Bahasa 12-15 Bulan", "url": "https://www.youtube.com/watch?v=2W3X4Y5Z6A7", "thumbnail": "https://img.youtube.com/vi/2W3X4Y5Z6A7/hqdefault.jpg"},
    "imunisasi": {"title": "💉 Jadwal Imunisasi Bayi", "url": "https://www.youtube.com/watch?v=5X6Y7Z8A9B0", "thumbnail": "https://img.youtube.com/vi/5X6Y7Z8A9B0/hqdefault.jpg"}
}

MOM_QUOTES = [
    "💕 'Seorang ibu adalah penjelajah yang tak pernah lelah, selalu menemukan jalan cinta untuk anaknya.' - GiziSiKecil",
    "🌟 'Kekuatan ibu melebihi segala rintangan, kasihnya membentuk masa depan yang cerah.'",
    "🤱 'Setiap tetes ASI adalah investasi cinta tak ternilai dalam perjalanan tumbuh kembang Si Kecil.'",
    "💪 'Kamu kuat, kamu cukup, dan kamu melakukan yang terbaik untuk Si Kecil! Jangan menyerah, Ibu hebat!'",
    "🌈 'Pertumbuhan anak bukan kompetisi, tapi perjalanan cinta bersama. Setiap langkah kecil adalah pencapaian besar.'",
    "💖 'Ibu, hatimu adalah rumah pertama Si Kecil, dan itu akan selalu jadi rumahnya yang paling aman.'"
]

IMMUNIZATION_SCHEDULE = {
    0: ["HB 0", "BCG", "Polio 0"], 1: ["HB 1", "Polio 1", "DPT-HB-Hib 1", "PCV 1", "RV 1"],
    2: ["Polio 2", "DPT-HB-Hib 2", "PCV 2", "RV 2"], 3: ["Polio 3", "DPT-HB-Hib 3", "PCV 3"],
    4: ["Polio 4", "DPT-HB-Hib 4"], 9: ["Campak"], 12: ["Campak Booster", "PCV Booster"],
    18: ["DPT-HB-Hib Booster", "Polio Booster"], 24: ["Campak Rubella"]
}

KPSP_QUESTIONS = {
    3: ["Menengadah saat telerentang?", "Tersenyum diajak bicara?", "Mengoceh (vokal)?", "Menatap wajah ibu?", "Meraih mainan?"],
    6: ["Duduk dengan bantuan?", "Pindah mainan tangan ke tangan?", "Ucap suara 'a-u-o'?", "Tertawa keras saat main?", "Kenal orang asing (malu/marah)?"],
    9: ["Duduk sendiri tanpa bantuan?", "Merangkak maju?", "Ucap 'mama/papa' berlebihan?", "Raih mainan kecil (kacang)?", "Menirukan gerakan?"],
    12: ["Berdiri sendiri 5 detik?", "Jalan berpegangan sofa?", "Ucap 2-3 kata bermakna?", "Minum dari cangkir sendiri?", "Tunjuk apa diinginkan?"],
    15: ["Jalan sendiri stabil?", "Minum dari gelas tanpa tumpah?", "Ucap 4-6 kata?", "Tumpuk 2 kubus?", "Bantu lepas sepatu?"],
    18: ["Berlari 5 langkah?", "Naik tangga dengan bantuan?", "Ucap 10-15 kata?", "Makan sendiri sendok?", "Tunjuk 2 bagian tubuh?"],
    21: ["Tendang bola ke depan?", "Naik tangga 1 kaki bergantian?", "Ucap 2-3 kata gabungan?", "Balik halaman buku?", "Ikut perintah 2 tahap?"],
    24: ["Lompat 2 kaki bersamaan?", "Naik tangga tanpa pegangan?", "Kalimat 3-4 kata?", "Gambar garis vertikal?", "Ikut perintah 3 tahap?"]
}

calc = None
try:
    calc = Calculator(adjust_height_data=False, adjust_weight_scores=False, include_cdc=False)
    print("✅ WHO Calculator initialized")
except Exception as e:
    print(f"❌ Calculator init error: {e}")

# -------------------- Theme System - 3 Pastel Variants --------------------
# ==================== GANTI BAGIAN INI (line 82-96) ====================

UI_THEMES = {
    "pink_pastel": {
        "primary": "#ff6b9d",
        "secondary": "#4ecdc4",
        "accent": "#ffe66d",
        "bg": "#fff5f8",
        "card": "#ffffff",
        "text": "#2c3e50",
        "border": "#ffd4e0",
        "shadow": "rgba(255, 107, 157, 0.1)",
        "gradient": "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)"
    },
    "mint_pastel": {
        "primary": "#4ecdc4",
        "secondary": "#a8e6cf",
        "accent": "#ffd93d",
        "bg": "#f0fffa",
        "card": "#ffffff",
        "text": "#2c3e50",
        "border": "#b7f0e9",
        "shadow": "rgba(78, 205, 196, 0.1)",
        "gradient": "linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%)"
    },
    "lavender_pastel": {
        "primary": "#b19cd9",
        "secondary": "#d6b3ff",
        "accent": "#ffb3ba",
        "bg": "#f5f0ff",
        "card": "#ffffff",
        "text": "#2c3e50",
        "border": "#e0d4ff",
        "shadow": "rgba(177, 156, 217, 0.1)",
        "gradient": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)"
    }
}

# ==================== END OF FIX ====================


def ensure_stickers():
    os.makedirs("static", exist_ok=True)
    sticker_urls = [
        "https://i.ibb.co/8B6gX9V/sticker-1.png",
        "https://i.ibb.co/3sJzVXM/sticker-2.png",
        "https://i.ibb.co/6J5mTJG/sticker-3.png",
        "https://i.ibb.co/KxM5pYf/sticker-4.png",
        "https://i.ibb.co/1rMZg3V/sticker-5.png"
    ]
    for i, url in enumerate(sticker_urls, 1):
        path = f"static/sticker_{i}.png"
        if not os.path.exists(path):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    with open(path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ Downloaded sticker_{i}.png")
            except Exception as e:
                print(f"⚠️ Sticker download failed: {e}")
                Image.new('RGBA', (200, 200), (255, 182, 193)).save(path)

ensure_stickers()

# -------------------- Helper Functions --------------------
def as_float(x):
    if x is None: return None
    if isinstance(x, Decimal): return float(x)
    try: return float(str(x).replace(",", "."))
    except Exception: return None

def parse_date(s):
    if not s or str(s).strip() == "": return None
    s = str(s).strip()
    try:
        y, m, d = [int(p) for p in s.split("-")]
        return datetime.date(y, m, d)
    except Exception: pass
    try:
        d, m, y = [int(p) for p in s.split("/")]
        return datetime.date(y, m, d)
    except Exception: return None

def age_months_from_dates(dob, dom):
    try:
        delta = dom - dob
        days = delta.days
        if days < 0: return None, None
        months = days / 30.4375
        return months, days
    except Exception: return None, None

@lru_cache(maxsize=1000)
def z_to_percentile(z):
    try:
        if z is None: return None
        zf = float(z)
        return round((0.5 * (1.0 + erf(zf / sqrt(2.0)))) * 100.0, 1)
    except Exception: return None

def fmtz(z, nd=2):
    try:
        if z is None or (isinstance(z, float) and math.isnan(z)): return "—"
        return f"{float(z):.{nd}f}"
    except Exception: return "—"

# -------------------- Growth Chart Functions --------------------
AGE_GRID = np.arange(0.0, 60.0 + 1e-9, 0.25)
BOUNDS = {
    'wfa': (1.0, 30.0), 'hfa': (45.0, 125.0), 'hcfa': (30.0, 55.0),
    'wfl_w': (1.0, 30.0), 'wfl_l': (45.0, 110.0)
}

def _safe_z(fn, *args):
    try:
        z = fn(*args)
        if z is None or math.isnan(z) or math.isinf(z): return None
        return float(z)
    except Exception: return None

def brentq_simple(f, a, b, xtol=1e-6, maxiter=80):
    fa = f(a); fb = f(b)
    if fa is None or fb is None: return (a + b) / 2.0
    if fa == 0: return a
    if fb == 0: return b
    if fa * fb > 0: return (a + b) / 2.0
    for _ in range(maxiter):
        m = 0.5 * (a + b); fm = f(m)
        if fm is None: return m
        if abs(fm) < 1e-8 or (b - a) / 2 < xtol: return m
        if fa * fm < 0: b, fb = m, fm
        else: a, fa = m, fm
    return 0.5 * (a + b)

def invert_z_with_scan(z_of_m, target_z, lo, hi, samples=120):
    xs = np.linspace(lo, hi, samples)
    last_x, last_f = None, None
    best_x, best_abs = None, float('inf')
    for x in xs:
        z = z_of_m(x)
        f = None if z is None else (z - target_z)
        if f is not None:
            af = abs(f)
            if af < best_abs: best_x, best_abs = x, af
            if last_f is not None and f * last_f < 0:
                try: return float(brentq_simple(lambda t: (z_of_m(t) or 0.0) - target_z, last_x, x))
                except Exception: pass
            last_x, last_f = x, f
    return float(best_x if best_x is not None else (lo + hi) / 2.0)

def wfa_curve_smooth(sex, z):
    lo, hi = BOUNDS['wfa']
    vals = [invert_z_with_scan(lambda m: _safe_z(calc.wfa, m, a, sex), z, lo, hi) for a in AGE_GRID]
    return AGE_GRID.copy(), np.asarray(vals)

def hfa_curve_smooth(sex, z):
    lo, hi = BOUNDS['hfa']
    vals = [invert_z_with_scan(lambda m: _safe_z(calc.lhfa, m, a, sex), z, lo, hi) for a in AGE_GRID]
    return AGE_GRID.copy(), np.asarray(vals)

def hcfa_curve_smooth(sex, z):
    lo, hi = BOUNDS['hcfa']
    vals = [invert_z_with_scan(lambda m: _safe_z(calc.hcfa, m, a, sex), z, lo, hi) for a in AGE_GRID]
    return AGE_GRID.copy(), np.asarray(vals)

def wfl_curve_smooth(sex, age_mo, z, lengths=None):
    if lengths is None: lengths = np.arange(BOUNDS['wfl_l'][0], BOUNDS['wfl_l'][1] + 1e-9, 0.5)
    lo_w, hi_w = BOUNDS['wfl_w']
    weights = [invert_z_with_scan(lambda w: _safe_z(calc.wfl, w, age_mo, sex, L), z, lo_w, hi_w) for L in lengths]
    return np.asarray(lengths), np.asarray(weights)

# -------------------- Classification Functions --------------------
def permenkes_waz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)): return "Tidak diketahui"
    if z < -3: return "Gizi buruk (BB sangat kurang)"
    if z < -2: return "Gizi kurang"
    if z <= 1: return "BB normal"
    return "Risiko BB lebih"

def permenkes_haz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)): return "Tidak diketahui"
    if z < -3: return "Sangat pendek (stunting berat)"
    if z < -2: return "Pendek (stunting)"
    if z <= 3: return "Normal"
    return "Tinggi"

def permenkes_whz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)): return "Tidak diketahui"
    if z < -3: return "Gizi buruk (sangat kurus)"
    if z < -2: return "Gizi kurang (kurus)"
    if z <= 1: return "Gizi baik (normal)"
    if z <= 2: return "Risiko gizi lebih"
    if z <= 3: return "Gizi lebih"
    return "Obesitas"

def who_waz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)): return "Unknown"
    if z < -3: return "Severely underweight"
    if z < -2: return "Underweight"
    if z > 2: return "Possible risk of overweight"
    return "Normal"

def who_haz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)): return "Unknown"
    if z < -3: return "Severely stunted"
    if z < -2: return "Stunted"
    if z > 3: return "Tall"
    return "Normal"

def who_whz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)): return "Unknown"
    if z < -3: return "Severe wasting"
    if z < -2: return "Wasting"
    if z <= 2: return "Normal"
    if z <= 3: return "Overweight"
    return "Obesity"

def hcz_text(z):
    if z is None or (isinstance(z, float) and math.isnan(z)): return ("Tidak diketahui", "Unknown")
    if z < -3: return ("Lingkar kepala sangat kecil", "Severe microcephaly")
    if z < -2: return ("Lingkar kepala di bawah normal", "Below normal")
    if z > 3: return ("Lingkar kepala sangat besar", "Severe macrocephaly")
    if z > 2: return ("Lingkar kepala di atas normal", "Above normal")
    return ("Normal", "Normal")

# -------------------- Theme-aware Matplotlib --------------------
def apply_matplotlib_theme(theme_name="pink_pastel"):
    theme = UI_THEMES.get(theme_name, UI_THEMES["pink_pastel"])
    plt.style.use('default')
    plt.rcParams.update({
        "axes.facecolor": theme["card"], "figure.facecolor": theme["bg"], "savefig.facecolor": theme["bg"],
        "text.color": theme["text"], "axes.labelcolor": theme["text"], "axes.edgecolor": theme["border"],
        "xtick.color": theme["text"], "ytick.color": theme["text"], "grid.color": theme["border"],
        "grid.alpha": 0.3, "grid.linestyle": "--", "grid.linewidth": 0.8,
        "legend.framealpha": 1.0, "legend.fancybox": False, "legend.edgecolor": theme["border"],
        "font.size": 10, "axes.titlesize": 12, "axes.labelsize": 11, "xtick.labelsize": 9,
        "ytick.labelsize": 9, "legend.fontsize": 9, "axes.linewidth": 1.5,
    })
    return theme

# -------------------- Report Builder --------------------
def build_markdown_report(name_child, name_parent, age_mo, age_days, sex_text, w, h, hc, z_scores, percentiles, classifications, lang_mode, errors, warns):
    overall_status = "🟢 Normal"
    critical_issues = []
    for k, z in z_scores.items():
        if z is not None and not math.isnan(z):
            if abs(z) > 3: overall_status = "🔴 Perlu Perhatian Segera"; critical_issues.append(k.upper())
            elif abs(z) > 2 and overall_status == "🟢 Normal": overall_status = "🟡 Perlu Monitoring"
    
    md = f"# 📊 Laporan Status Gizi Anak\n\n## Status: {overall_status}\n\n"
    if critical_issues: md += f"⚠️ **Indeks kritis:** {', '.join(critical_issues)}\n\n"
    if errors: md += "## ❌ Peringatan Kritis\n\n" + "\n\n".join(errors) + "\n\n---\n\n"
    
    md += "### 👤 Informasi Anak\n\n"
    if name_child and str(name_child).strip(): md += f"**Nama:** {name_child}\n\n"
    if name_parent and str(name_parent).strip(): md += f"**Orang Tua/Wali:** {name_parent}\n\n"
    md += f"**Jenis Kelamin:** {sex_text}\n\n"
    md += f"**Usia:** {age_mo:.1f} bulan (~{age_days} hari)\n\n---\n\n"
    
    md += "### 📏 Data Antropometri\n\n| Pengukuran | Nilai |\n|------------|-------|\n"
    md += f"| Berat Badan | **{w:.1f} kg** |\n"
    md += f"| Panjang/Tinggi | **{h:.1f} cm** |\n"
    if hc is not None: md += f"| Lingkar Kepala | **{hc:.1f} cm** |\n"
    md += "\n---\n\n"
    
    if lang_mode == "Orang tua":
        md += "### 💡 Ringkasan untuk Orang Tua\n\n" + generate_parent_narrative(z_scores, classifications['permenkes']) + "\n\n"
    else:
        md += "### 🏥 Ringkasan Klinis\n\n" + generate_clinical_narrative(z_scores, classifications) + "\n\n"
    
    md += "---\n\n### 📈 Hasil Lengkap (Z-score & Kategori)\n\n| Indeks | Z-score | Persentil | Status (Permenkes) | Status (WHO) |\n|--------|---------|-----------|-------------------|-------------|\n"
    indices = [('WAZ (BB/U)','waz'),('HAZ (TB/U)','haz'),('WHZ (BB/TB)','whz'),('BAZ (IMT/U)','baz'),('HCZ (LK/U)','hcz')]
    for label, key in indices:
        z_val = fmtz(z_scores[key]); pct_val = f"{percentiles[key]}%" if percentiles[key] is not None else "—"
        perm_cat = classifications['permenkes'][key]; who_cat = classifications['who'][key]
        z_raw = z_scores[key]
        if z_raw is not None and not math.isnan(z_raw):
            status_icon = "🔴" if abs(z_raw) > 3 else ("🟡" if abs(z_raw) > 2 else ("🟢" if abs(z_raw) <= 2 else "⚪"))
        else: status_icon = "⚪"
        md += f"| {status_icon} **{label}** | {z_val} | {pct_val} | {perm_cat} | {who_cat} |\n"
    
    if warns: md += "\n### ⚠️ Catatan Validasi\n\n" + "\n\n".join(warns) + "\n"
    
    md += "\n---\n\n**📌 Catatan Penting:**\n\n- Hasil ini bersifat **skrining edukatif**, bukan diagnosis medis\n- Untuk interpretasi lengkap, konsultasikan dengan tenaga kesehatan\n- Data Anda **tidak disimpan** di server\n\n"
    return md

def generate_parent_narrative(z_scores, perm_class):
    bullets, advice = [], []
    if z_scores.get('haz') is not None and not math.isnan(z_scores['haz']):
        haz = z_scores['haz']
        if haz < -3:
            bullets.append("🔴 **Tinggi badan sangat pendek** - Stunting berat"); advice.append("→ **SEGERA konsultasi ke Puskesmas/Dokter**")
        elif haz < -2:
            bullets.append("🟡 **Tinggi badan pendek** - Indikasi stunting"); advice.append("→ Konsultasi program perbaikan gizi")
    
    if z_scores.get('whz') is not None and not math.isnan(z_scores['whz']):
        whz = z_scores['whz']
        if whz < -3:
            bullets.append("🔴 **Sangat kurus** - Gizi buruk akut"); advice.append("→ **Butuh penanganan medis segera**")
        elif whz < -2:
            bullets.append("🟡 **Kurus** - Perlu perbaikan gizi"); advice.append("→ Tingkatkan asupan MPASI bergizi & pantau 2 minggu")
        elif whz > 3:
            bullets.append("🔴 **Obesitas**"); advice.append("→ Konsultasi ahli gizi anak")
        elif whz > 2:
            bullets.append("🟡 **Berat berlebih**"); advice.append("→ Aktifkan bermain 30 menit/hari, kurangi gula")
    
    if z_scores.get('waz') is not None and not math.isnan(z_scores['waz']):
        if z_scores['waz'] < -2: bullets.append("🟡 **Berat menurut umur rendah**")
    
    if not bullets: bullets.append("🟢 **Pertumbuhan normal** - Sesuai standar WHO"); advice.append("→ Pertahankan gizi seimbang & pantau rutin")
    
    result = "\n".join(bullets)
    if advice: result += "\n\n**🎯 Rekomendasi:**\n\n" + "\n".join(advice)
    return result

def generate_clinical_narrative(z_scores, classifications):
    lines = []
    for key in ['waz','haz','whz','baz','hcz']:
        z = z_scores.get(key)
        if z is not None and not math.isnan(z):
            perm = classifications['permenkes'][key]
            who = classifications['who'][key]
            lines.append(f"**{key.upper()}:** {fmtz(z)} - {perm} (WHO: {who})")
    return "\n\n".join(lines)

def biv_warnings(age_mo, sex, w, h, hc, z_waz, z_haz, z_whz, z_baz, z_hcz):
    warns, errors = [], []
    for name, z, critical, warn in [("WAZ", z_waz, 6, 5), ("HAZ", z_haz, 6, 5), ("WHZ", z_whz, 5, 4), ("BAZ", z_baz, 5, 4), ("HCZ", z_hcz, 5, 4)]:
        try:
            if z is not None and not math.isnan(z):
                if abs(z) > critical: errors.append(f"❌ {name} = {fmtz(z)} sangat tidak wajar (|Z| > {critical}). Periksa ulang pengukuran dan satuan.")
        except Exception: pass
    
    if w is not None:
        if w < 1.0 or w > 30: errors.append(f"❌ Berat {w} kg di luar rentang balita (1–30 kg).")
        elif w < 2.0 or w > 25: warns.append(f"⚠️ Berat {w} kg tidak lazim untuk balita.")
    if h is not None:
        if h < 35 or h > 130: errors.append(f"❌ Panjang/Tinggi {h} cm di luar rentang wajar (35–130 cm).")
    if hc is not None:
        if hc < 20 or hc > 60: errors.append(f"❌ Lingkar kepala {hc} cm di luar rentang (20–60 cm).")
    if age_mo is not None:
        if age_mo < 0: errors.append("❌ Usia tidak boleh negatif.")
        elif age_mo > 60: warns.append("ℹ️ Aplikasi ini dioptimalkan untuk 0–60 bulan.")
    
    return errors, warns

def median_values_for(sex_text, age_mode, dob_str, dom_str, age_months_input):
    try:
        sex = 'M' if sex_text.lower().startswith('l') else 'F'
        if age_mode == "Tanggal":
            dob = parse_date(dob_str); dom = parse_date(dom_str)
            if not dob or not dom or dom < dob: return (None, None, None)
            age_mo, _ = age_months_from_dates(dob, dom)
        else:
            age_mo = as_float(age_months_input)
        if age_mo is None: return (None, None, None)
        age_mo = max(0.0, min(age_mo, 60.0))
        w0 = invert_z_with_scan(lambda m: _safe_z(calc.wfa, m, age_mo, sex), 0.0, *BOUNDS['wfa'])
        h0 = invert_z_with_scan(lambda m: _safe_z(calc.lhfa, m, age_mo, sex), 0.0, *BOUNDS['hfa'])
        c0 = invert_z_with_scan(lambda m: _safe_z(calc.hcfa, m, age_mo, sex), 0.0, *BOUNDS['hcfa'])
        return (round(w0, 2), round(h0, 1), round(c0, 1))
    except Exception: return (None, None, None)

def compute_all(sex_text, age_mode, dob, dom, age_mo_in, w_in, h_in, hc_in, name_child, name_parent, lang_mode, theme):
    if calc is None: raise RuntimeError("WHO Calculator belum terinisialisasi.")
    
    sex = 'M' if str(sex_text).lower().startswith('l') else 'F'
    if age_mode == "Tanggal":
        dob_dt = parse_date(dob); dom_dt = parse_date(dom)
        if not dob_dt or not dom_dt or dom_dt < dob_dt: raise ValueError("Tanggal tidak valid.")
        age_mo, age_days = age_months_from_dates(dob_dt, dom_dt)
    else:
        age_mo = as_float(age_mo_in)
        if age_mo is None: raise ValueError("Usia tidak valid.")
        age_mo = max(0.0, min(age_mo, 60.0))
        age_days = int(round(age_mo * 30.4375))
    
    w = as_float(w_in); h = as_float(h_in); hc = as_float(hc_in)
    
    z = {"waz": None, "haz": None, "whz": None, "baz": None, "hcz": None}
    if w is not None: z["waz"] = _safe_z(calc.wfa, float(w), float(age_mo), sex)
    if h is not None: z["haz"] = _safe_z(calc.lhfa, float(h), float(age_mo), sex)
    if w is not None and h is not None:
        z["whz"] = _safe_z(calc.wfl, float(w), float(age_mo), sex, float(h))
        try:
            bmi = float(w) / ((float(h) / 100.0) ** 2)
            z["baz"] = _safe_z(calc.bmifa, float(bmi), float(age_mo), sex)
        except Exception: z["baz"] = None
    if hc is not None: z["hcz"] = _safe_z(calc.hcfa, float(hc), float(age_mo), sex)
    
    pct = {k: z_to_percentile(v) for k, v in z.items()}
    
    permenkes = {k: permenkes_waz(v) if k == 'waz' else permenkes_haz(v) if k == 'haz' else permenkes_whz(v) if k in ['whz','baz'] else hcz_text(v)[0] for k, v in z.items()}
    who = {k: who_waz(v) if k == 'waz' else who_haz(v) if k == 'haz' else who_whz(v) if k in ['whz','baz'] else hcz_text(v)[1] for k, v in z.items()}
    
    errors, warns = biv_warnings(age_mo, sex, w, h, hc, z["waz"], z["haz"], z["whz"], z["baz"], z["hcz"])
    
    payload = {
        "sex": sex, "sex_text": sex_text, "age_mo": age_mo, "age_days": age_days,
        "w": w, "h": h, "hc": hc, "z": z, "pct": pct,
        "permenkes": permenkes, "who": who,
        "name_child": name_child, "name_parent": name_parent,
        "theme": theme, "errors": errors, "warns": warns,
    }
    
    md = build_markdown_report(name_child, name_parent, age_mo, age_days, sex_text, w, h, hc, z, pct, {"permenkes": permenkes, "who": who}, lang_mode, errors, warns)
    return md, payload

# -------------------- Plotting Functions (Theme-Aware) --------------------
def _zone_fill(ax, x, lower, upper, color, alpha, label):
    try: ax.fill_between(x, lower, upper, color=color, alpha=alpha, zorder=1, label=label, linewidth=0)
    except Exception: pass

def plot_wfa(payload, theme_name="pink_pastel"):
    theme = apply_matplotlib_theme(theme_name)
    sex, age, w = payload['sex'], payload['age_mo'], payload['w']
    sd_lines = { -3:('#DC143C','-'), -2:('#FF6347','-'), -1:(theme['primary'],'--'), 0:(theme['secondary'],'-'), 1:(theme['primary'],'--'), 2:('#FF6347','-'), 3:('#DC143C','-') }
    curves = {z: wfa_curve_smooth(sex, z) for z in sd_lines}
    fig, ax = plt.subplots(figsize=(11, 7))
    x = curves[0][0]
    _zone_fill(ax, x, curves[-3][1], curves[-2][1], '#FFE6E6', 0.35, 'Zona Gizi Buruk')
    _zone_fill(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Zona Gizi Kurang')
    _zone_fill(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.40, 'Zona Normal')
    _zone_fill(ax, x, curves[1][1],  curves[2][1],  '#FFF3CD', 0.30, 'Risiko Gizi Lebih')
    _zone_fill(ax, x, curves[2][1],  curves[3][1],  '#F8D7DA', 0.35, 'Gizi Lebih')
    for z, (c, ls) in sd_lines.items():
        ax.plot(curves[z][0], curves[z][1], color=c, linestyle=ls, linewidth=2.5 if abs(z) in (0,2) else 1.8, label=("Median" if z==0 else f"{z:+d} SD"), zorder=5)
    z_waz = payload['z']['waz']
    point_color = theme['secondary']
    if z_waz is not None:
        if abs(z_waz) > 3: point_color = '#8B0000'
        elif abs(z_waz) > 2: point_color = '#DC143C'
        elif abs(z_waz) > 1: point_color = theme['primary']
    if w is not None:
        ax.scatter([age], [w], s=400, c=point_color, edgecolors=theme['text'], linewidths=3, marker='o', zorder=20, label='Data Anak')
        ax.plot([age, age], [0, w], 'k--', linewidth=1, alpha=0.3, zorder=1)
    ax.set_xlabel('Usia (bulan)', fontweight='bold'); ax.set_ylabel('Berat Badan (kg)', fontweight='bold')
    ax.set_title('GRAFIK PERTUMBUHAN WHO: Berat Badan menurut Umur (BB/U)\n' + ("Laki-laki" if sex=='M' else "Perempuan") + ' | 0-60 bulan', fontweight='bold', color=theme['text'])
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5); ax.minorticks_on()
    ax.set_xlim(0, 60); ax.set_xticks(range(0, 61, 6)); ax.set_xticks(range(0, 61, 3), minor=True)
    y_min = min([curves[z][1].min() for z in (-3,-2,0,2,3)]); y_max = max([curves[z][1].max() for z in (-3,-2,0,2,3)])
    ax.set_ylim(max(0, y_min - 1), y_max + 2)
    ax.legend(loc='upper left', frameon=True, edgecolor=theme['border'], fontsize=9, ncol=2)
    plt.tight_layout(); return fig

def plot_hfa(payload, theme_name="pink_pastel"):
    theme = apply_matplotlib_theme(theme_name)
    sex, age, h = payload['sex'], payload['age_mo'], payload['h']
    sd_lines = { -3:('#DC143C','-'), -2:('#FF6347','-'), -1:(theme['primary'],'--'), 0:(theme['secondary'],'-'), 1:(theme['primary'],'--'), 2:('#FF6347','-'), 3:('#DC143C','-') }
    curves = {z: hfa_curve_smooth(sex, z) for z in sd_lines}
    fig, ax = plt.subplots(figsize=(11, 7))
    x = curves[0][0]
    _zone_fill(ax, x, curves[-3][1], curves[-2][1], '#FFE6E6', 0.30, 'Severe Stunting')
    _zone_fill(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Stunting')
    _zone_fill(ax, x, curves[-1][1], curves[2][1],  '#E8F5E9', 0.40, 'Normal')
    _zone_fill(ax, x, curves[2][1],  curves[3][1],  '#E3F2FD', 0.30, 'Tall')
    for z, (c, ls) in sd_lines.items():
        ax.plot(curves[z][0], curves[z][1], color=c, linestyle=ls, linewidth=2.5 if abs(z) in (0,2) else 1.8, label=("Median" if z==0 else f"{z:+d} SD"), zorder=5)
    z_haz = payload['z']['haz']
    point_color = theme['secondary']
    if z_haz is not None:
        if abs(z_haz) > 3: point_color = '#8B0000'
        elif abs(z_haz) > 2: point_color = '#DC143C'
        elif abs(z_haz) > 1: point_color = theme['primary']
    if h is not None:
        ax.scatter([age], [h], s=400, c=point_color, edgecolors=theme['text'], linewidths=3, marker='o', zorder=20, label='Data Anak')
        ax.plot([age, age], [40, h], 'k--', linewidth=1, alpha=0.3, zorder=1)
    ax.set_xlabel('Usia (bulan)', fontweight='bold'); ax.set_ylabel('Panjang/Tinggi Badan (cm)', fontweight='bold')
    ax.set_title('GRAFIK PERTUMBUHAN WHO: Panjang/Tinggi menurut Umur (TB/U)\n' + ("Laki-laki" if sex=='M' else "Perempuan") + ' | 0-60 bulan', fontweight='bold', color=theme['text'])
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5); ax.minorticks_on()
    ax.set_xlim(0, 60); ax.set_xticks(range(0, 61, 6)); ax.set_xticks(range(0, 61, 3), minor=True)
    y_min = min([curves[z][1].min() for z in (-3,-2,0,2,3)]); y_max = max([curves[z][1].max() for z in (-3,-2,0,2,3)])
    ax.set_ylim(max(45, y_min - 1), y_max + 2)
    ax.legend(loc='upper left', frameon=True, edgecolor=theme['border'], fontsize=9, ncol=2)
    plt.tight_layout(); return fig

def plot_hcfa(payload, theme_name="pink_pastel"):
    theme = apply_matplotlib_theme(theme_name)
    sex, age, hc = payload['sex'], payload['age_mo'], payload.get('hc')
    sd_lines = { -3:('#DC143C','-'), -2:('#FF6347','-'), -1:(theme['primary'],'--'), 0:(theme['secondary'],'-'), 1:(theme['primary'],'--'), 2:('#FF6347','-'), 3:('#DC143C','-') }
    curves = {z: hcfa_curve_smooth(sex, z) for z in sd_lines}
    fig, ax = plt.subplots(figsize=(11, 7))
    x = curves[0][0]
    _zone_fill(ax, x, curves[-3][1], curves[-2][1], '#FFD4D4', 0.40, 'Microcephaly Berat')
    _zone_fill(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Microcephaly')
    _zone_fill(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.40, 'Zona Normal')
    _zone_fill(ax, x, curves[1][1],  curves[2][1],  '#E3F2FD', 0.30, 'Macrocephaly')
    _zone_fill(ax, x, curves[2][1],  curves[3][1],  '#BBDEFB', 0.35, 'Macrocephaly Berat')
    for z, (c, ls) in sd_lines.items():
        ax.plot(curves[z][0], curves[z][1], color=c, linestyle=ls, linewidth=2.5 if abs(z) in (0,2) else 1.8, label=("Median" if z==0 else f"{z:+d} SD"), zorder=5)
    if hc is not None:
        z_hcz = payload['z']['hcz']
        point_color = theme['secondary']
        if z_hcz is not None:
            if abs(z_hcz) > 3: point_color = '#8B0000'
            elif abs(z_hcz) > 2: point_color = '#DC143C'
            elif abs(z_hcz) > 1: point_color = theme['primary']
        ax.scatter([age], [hc], s=400, c=point_color, edgecolors=theme['text'], linewidths=3, marker='o', zorder=20, label='Data Anak')
        ax.plot([age, age], [25, hc], 'k--', linewidth=1, alpha=0.3, zorder=1)
    ax.set_xlabel('Usia (bulan)', fontweight='bold'); ax.set_ylabel('Lingkar Kepala (cm)', fontweight='bold')
    ax.set_title('GRAFIK PERTUMBUHAN WHO: Lingkar Kepala menurut Umur (LK/U)\n' + ("Laki-laki" if sex=='M' else "Perempuan") + ' | 0-60 bulan', fontweight='bold', color=theme['text'])
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5); ax.minorticks_on()
    ax.set_xlim(0, 60); ax.set_xticks(range(0, 61, 6)); ax.set_xticks(range(0, 61, 3), minor=True)
    y_min = min([curves[z][1].min() for z in (-3,-2,0,2,3)]); y_max = max([curves[z][1].max() for z in (-3,-2,0,2,3)])
    ax.set_ylim(max(25, y_min - 1), y_max + 2)
    ax.legend(loc='upper left', frameon=True, edgecolor=theme['border'], fontsize=9, ncol=2)
    plt.tight_layout(); return fig

def plot_wfl(payload, theme_name="pink_pastel"):
    theme = apply_matplotlib_theme(theme_name)
    sex, age, h, w = payload['sex'], payload['age_mo'], payload['h'], payload['w']
    lengths = np.arange(BOUNDS['wfl_l'][0], BOUNDS['wfl_l'][1] + 1e-9, 0.5)
    sd_lines = { -3:('#DC143C','-'), -2:('#FF6347','-'), -1:(theme['primary'],'--'), 0:(theme['secondary'],'-'), 1:(theme['primary'],'--'), 2:('#FF6347','-'), 3:('#DC143C','-') }
    curves = {z: wfl_curve_smooth(sex, age, z, lengths) for z in sd_lines}
    fig, ax = plt.subplots(figsize=(11, 7))
    x = curves[0][0]
    _zone_fill(ax, x, curves[-3][1], curves[-2][1], '#FFD4D4', 0.40, 'Wasting Berat')
    _zone_fill(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Wasting')
    _zone_fill(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.40, 'Zona Normal')
    _zone_fill(ax, x, curves[1][1],  curves[2][1],  '#FFF9C4', 0.30, 'Risiko Overweight')
    _zone_fill(ax, x, curves[2][1],  curves[3][1],  '#FFD4D4', 0.40, 'Overweight/Obesitas')
    for z, (c, ls) in sd_lines.items():
        ax.plot(curves[z][0], curves[z][1], color=c, linestyle=ls, linewidth=2.5 if abs(z) in (0,2) else 1.8, label=("Median" if z==0 else f"{z:+d} SD"), zorder=5)
    if h is not None and w is not None:
        z_whz = payload['z']['whz']
        point_color = theme['secondary']
        if z_whz is not None:
            if abs(z_whz) > 3: point_color = '#8B0000'
            elif abs(z_whz) > 2: point_color = '#DC143C'
            elif abs(z_whz) > 1: point_color = theme['primary']
        ax.scatter([h], [w], s=400, c=point_color, edgecolors=theme['text'], linewidths=3, marker='o', zorder=20, label='Data Anak')
        ax.plot([h, h], [0, w], 'k--', linewidth=1, alpha=0.3, zorder=1)
    ax.set_xlabel('Panjang/Tinggi Badan (cm)', fontweight='bold'); ax.set_ylabel('Berat Badan (kg)', fontweight='bold')
    ax.set_title('GRAFIK PERTUMBUHAN WHO: Berat menurut Panjang/Tinggi (BB/TB)\n' + ("Laki-laki" if sex=='M' else "Perempuan"), fontweight='bold', color=theme['text'])
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5); ax.minorticks_on()
    ax.set_xlim(lengths.min(), lengths.max())
    y_min = min([curves[z][1].min() for z in (-3,-2,0,2,3)]); y_max = max([curves[z][1].max() for z in (-3,-2,0,2,3)])
    ax.set_ylim(max(0, y_min - 1), y_max + 2)
    ax.legend(loc='upper left', frameon=True, edgecolor=theme['border'], fontsize=9, ncol=2)
    plt.tight_layout(); return fig

def plot_bars(payload, theme_name="pink_pastel"):
    theme = apply_matplotlib_theme(theme_name)
    z = payload['z']
    labels = ['WAZ\n(BB/U)', 'HAZ\n(TB/U)', 'WHZ\n(BB/TB)', 'BAZ\n(IMT/U)', 'HCZ\n(LK/U)']
    values = [z['waz'], z['haz'], z['whz'], z['baz'], z['hcz']]
    def get_bar_color(v):
        if v is None or math.isnan(v): return '#CCCCCC'
        if abs(v) > 3: return '#8B0000'
        if abs(v) > 2: return '#DC143C'
        if abs(v) > 1: return theme['primary']
        return theme['secondary']
    colors_bar = [get_bar_color(v) for v in values]
    plot_values = [0 if (v is None or (isinstance(v,float) and math.isnan(v))) else v for v in values]
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.axhspan(-3, -2, color='#FFD4D4', alpha=0.3, label='Zona Kurang (-3 to -2 SD)')
    ax.axhspan(-2,  2, color='#E8F5E9', alpha=0.3, label='Zona Normal (-2 to +2 SD)')
    ax.axhspan( 2,  3, color='#FFD4D4', alpha=0.3, label='Zona Lebih (+2 to +3 SD)')
    ax.axhline(0, color=theme['secondary'], linewidth=3, linestyle='-', label='Median (0 SD)', zorder=5)
    ax.axhline(-2, color='#DC143C', linewidth=2, linestyle='--', alpha=0.7)
    ax.axhline( 2, color='#DC143C', linewidth=2, linestyle='--', alpha=0.7)
    ax.axhline(-3, color='#8B0000', linewidth=1.5, linestyle=':',  alpha=0.5)
    ax.axhline( 3, color='#8B0000', linewidth=1.5, linestyle=':',  alpha=0.5)
    bars = ax.bar(labels, plot_values, color=colors_bar, edgecolor=theme['text'], linewidth=2.5, width=0.6, alpha=0.9, zorder=10)
    for i, (v, bar) in enumerate(zip(values, bars)):
        if v is not None and not (isinstance(v,float) and math.isnan(v)):
            y_pos = bar.get_height(); offset = 0.3 if y_pos >= 0 else -0.5
            status = "Kritis" if abs(v)>3 else ("Perlu Perhatian" if abs(v)>2 else ("Borderline" if abs(v)>1 else "Normal"))
            ax.text(bar.get_x()+bar.get_width()/2, y_pos+offset, f'{fmtz(v,2)}\n({status})', ha='center', va='bottom' if y_pos>=0 else 'top',
                    fontsize=11, weight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor=colors_bar[i], linewidth=2), zorder=15)
    ax.set_ylabel('Z-score', fontweight='bold', fontsize=12)
    ax.set_title('RINGKASAN STATUS GIZI - Semua Indeks Antropometri\nWHO Child Growth Standards', fontweight='bold', fontsize=13, pad=15, color=theme['text'])
    ax.set_ylim(-5, 5); ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.5, zorder=1)
    ax.legend(loc='upper right', frameon=True, edgecolor=theme['border'], fontsize=9, title='Referensi WHO', title_fontsize=10)
    plt.tight_layout(); return fig

# -------------------- Export Functions --------------------
def export_png(fig, filename):
    try:
        fig.savefig(filename, dpi=200, bbox_inches='tight', facecolor='white')
        return filename
    except Exception: return None

def export_csv(payload, filename):
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f); w.writerow(['=== DATA ANAK ==='])
            w.writerow(['Nama Anak', payload.get('name_child', '')]); w.writerow(['Orang Tua/Wali', payload.get('name_parent', '')])
            w.writerow(['Jenis Kelamin', payload.get('sex_text', '')]); w.writerow(['Usia (bulan)', f"{payload.get('age_mo', 0):.2f}"])
            w.writerow(['Usia (hari)', payload.get('age_days', 0)]); w.writerow([])
            w.writerow(['=== PENGUKURAN ===']); w.writerow(['Berat Badan (kg)', payload.get('w', '')])
            w.writerow(['Panjang/Tinggi (cm)', payload.get('h', '')]); w.writerow(['Lingkar Kepala (cm)', payload.get('hc', '')]); w.writerow([])
            w.writerow(['=== HASIL ANALISIS ==='])
            w.writerow(['Indeks', 'Z-score', 'Persentil (%)', 'Kategori Permenkes', 'Kategori WHO'])
            for key, label in [('waz','WAZ (BB/U)'),('haz','HAZ (TB/U)'),('whz','WHZ (BB/TB)'),('baz','BAZ (IMT/U)'),('hcz','HCZ (LK/U)')]:
                pct = payload['pct'][key]; pct_str = f"{pct}" if pct is not None else "—"
                w.writerow([label, fmtz(payload['z'][key]), pct_str, payload['permenkes'][key], payload['who'][key]])
            w.writerow([]); w.writerow(['Tanggal Export', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            w.writerow(['Sumber', 'GiziSiKecil - WHO Child Growth Standards + Permenkes 2020'])
        return filename
    except Exception: return None

def qr_image_bytes(text=f"https://wa.me/{CONTACT_WA}"):
    try:
        qr = qrcode.QRCode(box_size=4, border=3); qr.add_data(text); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
        return buf
    except Exception: return None

def export_pdf(payload, md_text, figs, filename):
    try:
        c = canvas.Canvas(filename, pagesize=A4)
        W, H = A4
        theme = UI_THEMES.get(payload.get('theme', 'pink_pastel'), UI_THEMES['pink_pastel'])
        
        # Header with gradient
        c.setFillColorRGB(0.965, 0.647, 0.753); c.rect(0, H - 50, W, 50, stroke=0, fill=1)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 16)
        c.drawString(30, H - 32, "GiziSiKecil - Laporan Status Gizi Anak")
        c.setFont("Helvetica", 10); c.drawRightString(W - 30, H - 32, datetime.now().strftime("%d %B %Y, %H:%M WIB"))
        
        y = H - 80
        c.setFont("Helvetica-Bold", 12); c.drawString(30, y, "INFORMASI ANAK"); y -= 20; c.setFont("Helvetica", 10)
        if payload.get('name_child'): c.drawString(40, y, f"Nama: {payload['name_child']}"); y -= 15
        if payload.get('name_parent'): c.drawString(40, y, f"Orang Tua/Wali: {payload['name_parent']}"); y -= 15
        c.drawString(40, y, f"Jenis Kelamin: {payload['sex_text']}"); y -= 15
        c.drawString(40, y, f"Usia: {payload['age_mo']:.1f} bulan (~{payload['age_days']} hari)"); y -= 25
        
        c.setFont("Helvetica-Bold", 12); c.drawString(30, y, "DATA ANTROPOMETRI"); y -= 20; c.setFont("Helvetica", 10)
        c.drawString(40, y, f"Berat Badan: {payload['w']:.1f} kg"); y -= 15
        c.drawString(40, y, f"Panjang/Tinggi: {payload['h']:.1f} cm"); y -= 15
        if payload.get('hc'): c.drawString(40, y, f"Lingkar Kepala: {payload['hc']:.1f} cm"); y -= 20
        
        y -= 10; c.setFont("Helvetica-Bold", 12); c.drawString(30, y, "HASIL ANALISIS"); y -= 20
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, y, "Indeks"); c.drawString(120, y, "Z-score"); c.drawString(180, y, "Persentil")
        c.drawString(250, y, "Status (Permenkes)"); c.drawString(400, y, "Status (WHO)")
        y -= 3; c.line(35, y, W - 35, y); y -= 12; c.setFont("Helvetica", 9)
        for key, label in [('waz','WAZ (BB/U)'),('haz','HAZ (TB/U)'),('whz','WHZ (BB/TB)'),('baz','BAZ (IMT/U)'),('hcz','HCZ (LK/U)')]:
            pct = payload['pct'][key]
            c.drawString(40, y, label); c.drawString(120, y, fmtz(payload['z'][key]))
            c.drawString(180, y, f"{pct}%" if pct is not None else "—")
            c.drawString(250, y, payload['permenkes'][key][:30]); c.drawString(400, y, payload['who'][key][:25]); y -= 14
        
        qr_buf = qr_image_bytes()
        if qr_buf: c.drawImage(ImageReader(qr_buf), W - 80, 30, width=50, height=50)
        c.setFont("Helvetica-Oblique", 8); c.drawRightString(W - 30, 15, "Hal. 1"); c.showPage()
        page_num = 2
        
        titles = [
            "Grafik Berat Badan menurut Umur (BB/U)",
            "Grafik Panjang/Tinggi menurut Umur (TB/U)",
            "Grafik Lingkar Kepala menurut Umur (LK/U)",
            "Grafik Berat menurut Panjang/Tinggi (BB/TB)",
            "Grafik Ringkasan Semua Indeks"
        ]
        for title, fig in zip(titles, figs):
            c.setFillColorRGB(0.965, 0.647, 0.753); c.rect(0, H - 50, W, 50, stroke=0, fill=1)
            c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawString(30, H - 32, title)
            buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white'); buf.seek(0)
            c.drawImage(ImageReader(buf), 30, 100, width=W - 60, preserveAspectRatio=True)
            c.setFont("Helvetica-Oblique", 8); c.drawRightString(W - 30, 15, f"Hal. {page_num}"); c.showPage(); page_num += 1
        
        # Disclaimer
        c.setFillColorRGB(0.965, 0.647, 0.753); c.rect(0, H - 50, W, 50, stroke=0, fill=1)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawString(30, H - 32, "Catatan Penting & Disclaimer")
        y = H - 80; c.setFont("Helvetica", 10)
        disclaimers = [
            "1. Aplikasi ini bersifat SKRINING EDUKATIF, bukan diagnosis medis.", "",
            "2. Hasil harus diinterpretasikan oleh tenaga kesehatan terlatih.", "",
            "3. Klasifikasi mengacu pada: WHO Child Growth Standards (2006) & Permenkes RI No. 2 Tahun 2020", "",
            "4. Data Anda TIDAK disimpan di server (privasi terjaga).", "",
            "5. Untuk konsultasi lanjutan, hubungi Posyandu/Puskesmas/Dokter anak.", "",
            "6. Pastikan alat terkalibrasi & teknik pengukuran benar."
        ]
        for line in disclaimers: c.drawString(40, y, line); y -= 15
        
        c.setFont("Helvetica-Oblique", 8); c.drawRightString(W - 30, 15, f"Hal. {page_num}")
        c.save(); return filename
    except Exception as e:
        print(f"PDF Error: {e}")
        return None

# -------------------- Wizard Checklist Functions --------------------
def sync_from_calculator(main_payload, layout_mode, ui_theme):
    """FIXED: Sync data dari kalkulator utama"""
    if not main_payload or not isinstance(main_payload, dict) or 'age_mo' not in main_payload:
        return ("❌ Tidak ada data dari Kalkulator. Silakan hitung z-score dulu di tab utama.",
                gr.update(visible=True), gr.update(visible=False), 0, ui_theme,
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
    
    state_child_data.value = main_payload
    age_mo = main_payload.get("age_mo", 0)
    month = min(int(age_mo), 24)
    
    sync_msg = f"""
    ✅ **Data berhasil disinkronkan!**
    
    👶 **Nama:** {main_payload.get('name_child', 'Si Kecil')}  
    📅 **Usia:** {age_mo:.1f} bulan → **Bulan ke-{month}**  
    ⚖️ **BB/TB:** {main_payload.get('w', 0):.1f} kg / {main_payload.get('h', 0):.1f} cm  
    📊 **Status:** {main_payload.get('permenkes', {}).get('waz', 'Normal')}
    
    👉 **Pilih bulan di dropdown, lalu klik 'Mulai Checklist'**
    """
    return (sync_msg,
            gr.update(visible=False),  # wizard_container
            gr.update(visible=True),   # sync_status
            month,
            ui_theme,
            gr.update(visible=False),  # step1_panel
            gr.update(visible=False),  # step2_panel
            gr.update(visible=False))  # step3_panel

def reset_checklist_data():
    """Reset semua data checklist"""
    state_child_data.value = {}
    state_checklist_progress.value = {}
    state_current_month.value = 0
    state_kpsp_answers.value = {}
    return ("✅ Data checklist berhasil direset. Silakan sinkron ulang dari Kalkulator.",
            gr.update(visible=True), gr.update(visible=False),
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))

def generate_checklist_data(month, layout_mode, main_payload):
    """Generate Do Now, Saran, Warning, Video, Imunisasi"""
    if not main_payload: return "❌ Data anak belum tersedia.", "", "", "", ""
    
    z_scores = main_payload.get("z", {})
    waz, haz, whz = z_scores.get("waz"), z_scores.get("haz"), z_scores.get("whz")
    
    do_now, saran, warnings, videos, imunisasi = [], [], [], [], []
    
    # Feeding & Nutrition
    if month < 6:
        do_now.append("🤱 **ASI Eksklusif:** Pastikan ASI on demand, tanda kecukupan: pipis >6x/hari, berat naik 500g/bulan")
        saran.append("💡 **Tip:** Jika bekerja, siapkan ASI perah. Dukungan emosional ibu sangat penting!")
        videos.append(YOUTUBE_VIDEOS.get("mpasi_6bln"))
    elif month == 6:
        do_now.append("🍚 **Mulai MPASI:** 2-3x/hari, tekstur halus (bubur kental). Utamakan zat besi: hati ayam, kuning telur")
        warnings.append("⚠️ **Jika belum MPASI:** Risiko gizi buruk. Segera konsultasi!")
        saran.append("💡 **Keamanan:** Cuci tangan, pisah alat mentah-matang, masak matang")
        videos.append(YOUTUBE_VIDEOS.get("mpasi_6bln"))
    elif month < 12:
        freq = "3-4x/hari + 1-2 selingan" if month > 8 else "2-3x/hari"
        do_now.append(f"🍽️ **Frekuensi MPASI:** {freq}. Tambah variasi: karbo, protein, sayur, buah, lemak sehat")
        saran.append("💡 **Zat Besi:** 1 porsi protein hewani setiap hari (hati/daging/ikan/telur)")
        videos.append(YOUTUBE_VIDEOS.get("mpasi_9bln"))
    else:
        do_now.append("🍛 **Menu Keluarga:** 3-4x/hari + 2 selingan. Hindari gula/garam berlebih")
        saran.append("💡 **Kemandirian:** Latih makan sendiri, libatkan anak saat menyiapkan makan")
    
    # Growth Monitoring
    if haz and haz < -3:
        warnings.append("🔴 **STUNTING BERAT:** Tinggi sangat pendek. Segera rujuk ke Puskesmas/fasyankes!")
        do_now.append("📏 **Ulang Ukur:** Gunakan infantometer, 2 orang, posisi benar")
        saran.append("🥦 **Intervensi:** Tingkatkan densitas energi (tambah minyak), konseling gizi intensif")
        videos.append(YOUTUBE_VIDEOS.get("mpasi_6bln"))
    elif haz and haz < -2:
        warnings.append("🟡 **STUNTING RISK:** Tinggi pendek. Konsultasi program perbaikan gizi")
        do_now.append("📊 **Monitoring:** Pantau trivulan, evaluasi asupan & penyakit")
        saran.append("💪 **Nutrien:** Prioritaskan protein hewani, vitamin A, zinc")
    
    if whz and whz < -3:
        warnings.append("🔴 **WASTING BERAT:** Sangat kurus. Perlu penanganan medis segera!")
        do_now.append("🚨 **Rujuk:** Ke fasyankes untuk evaluasi & terapi")
    elif whz and whz < -2:
        warnings.append("🟡 **WASTING:** Kurus. Tingkatkan asupan & pantau berat 2 minggu sekali")
        do_now.append("🍲 **Pemulihan:** Frekuensi MPASI 4-5x/hari setelah sakit")
    
    if whz and whz > 3:
        warnings.append("🔴 **OBESITAS:** Berat sangat berlebih. Konsultasi ahli gizi")
        saran.append("🏃 **Aktivitas:** Undang bermain aktif 30 menit/hari, kurangi screen time")
    elif whz and whz > 2:
        warnings.append("🟡 **OVERWEIGHT:** Berat berlebih. Perhatikan pola makan & aktivitas")
        saran.append("🥗 **Porsi:** Kecilkan porsi, tingkatkan sayur-buah")
    
    # KPSP
    if month in KPSP_QUESTIONS: saran.append("🧠 **KPSP:** Lengkapi screening pada langkah berikutnya")
    
    # Immunization
    imms = IMMUNIZATION_SCHEDULE.get(month, [])
    if imms:
        imunisasi.append(f"💉 **Imunisasi Jatuh Tempo:** {', '.join(imms)}")
        imunisasi.append("📅 **Jangan lewatkan!** Bawa Buku KIA ke fasyankes")
        do_now.append("💉 **Imunisasi:** Segera tuntaskan jadwal")
        videos.append(YOUTUBE_VIDEOS.get("imunisasi"))
    
    # Stimulation Videos by age
    if month >= 6:
        video_keys = ["motorik_6bln", "mpasi_9bln", "bahasa_12bln", "bahasa_12bln"]
        key = video_keys[min(len(video_keys)-1, month//6 - 1)]
        v = YOUTUBE_VIDEOS.get(key)
        if v and v not in videos: videos.append(v)
    
    # Format video HTML
    videos_html = "<div style='display:flex; flex-wrap:wrap; gap:12px; justify-content:center;'>"
    for vid in videos:
        if vid:
            videos_html += f"""
            <div style='border:1px solid {theme["border"]}; padding:12px; border-radius:10px; width:220px; background:{theme["card"]}; box-shadow:0 4px 8px {theme["shadow"]}; transition:transform 0.2s;'>
                <img src='{vid['thumbnail']}' style='width:100%; border-radius:8px; border:1px solid {theme["border"]};'>
                <p style='font-size:13px; margin:8px 0; font-weight:bold; color:{theme["text"]};'>{vid['title']}</p>
                <a href='{vid['url']}' target='_blank' style='display:inline-block; background:{theme["primary"]}; color:white; padding:8px 12px; border-radius:5px; text-decoration:none; font-size:12px; font-weight:bold;'>▶️ Tonton</a>
            </div>
            """
    videos_html += "</div>"
    
    # Mode Mudah: Simplify content
    if layout_mode == "Mode Mudah":
        do_now = [d.split(":")[0][:50] + "..." for d in do_now[:3]]
        saran = ["💡 " + s.split(":")[1][:60] + "..." for s in saran[:2]]
        warnings = ["⚠️ " + w.split(":")[1][:50] + "..." for w in warnings[:2]]
    
    return (
        "\n\n".join(do_now) if do_now else "✅ Semua sesuai standar WHO",
        "\n\n".join(saran) if saran else "💡 Pertahankan pola sehat saat ini",
        "\n\n".join(warnings) if warnings else "✅ Tidak ada warning kritis bulan ini",
        videos_html if videos_html else "<p style='text-align:center; color:#666;'>Video edukasi akan tersedia pada bulan selanjutnya</p>",
        "\n\n".join(imunisasi) if imunisasi else "✅ Tidak ada imunisasi bulan ini"
    )

def run_wizard_step1(month, main_payload):
    """Step 1: Verifikasi data"""
    if not main_payload: return ("❌ Data anak belum tersedia. Klik 'Sinkron Data' dulu.",
                                 gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), 
                                 "", "", "", "", "")
    
    overview = f"""
    ### 👶 **Verifikasi Data Anak**
    
    **Nama:** {main_payload.get('name_child', 'Si Kecil')}  
    **Usia:** {main_payload.get('age_mo', 0):.1f} bulan  
    **BB/TB:** {main_payload.get('w', 0):.1f} kg / {main_payload.get('h', 0):.1f} cm  
    **Status:** {main_payload.get('permenkes', {}).get('waz', 'Normal')}
    
    ✅ Jika data sudah benar, klik **"Lanjutkan"** untuk screening KPSP.
    """
    return (overview,
            gr.update(visible=True),  # step1_panel
            gr.update(visible=False), # step2_panel
            gr.update(visible=False), # step3_panel
            "", "", "", "", "")

def run_wizard_step2(month, main_payload, ui_theme):
    """Step 2: Tampilkan KPSP questions"""
    if not main_payload: return ("", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
                                 "", "", "", "", "")
    
    questions = KPSP_QUESTIONS.get(month, [])
    if not questions: return ("", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
                              "", "", "", "", "")
    
    html = f"<h4 style='color:{UI_THEMES[ui_theme]['text']};'>🧠 <strong>Screening Perkembangan (KPSP)</strong></h4>"
    html += f"<p style='color:{UI_THEMES[ui_theme]['text']}; font-size:13px; margin-bottom:15px; opacity:0.8;'>Jawab dengan jujur untuk rekomendasi terbaik</p>"
    
    for i, q in enumerate(questions):
        html += f"""
        <div style='margin:12px 0; padding:15px; background:{UI_THEMES[ui_theme]['bg']}; border-radius:8px; border-left:4px solid {UI_THEMES[ui_theme]['primary']}; box-shadow:0 2px 4px {UI_THEMES[ui_theme]['shadow']};'>
            <p style='font-weight:bold; margin-bottom:10px; color:{UI_THEMES[ui_theme]['text']};'>{i+1}. Apakah Si Kecil bisa {q}</p>
            <label style='margin-right:20px; cursor:pointer; padding:8px 12px; background:{UI_THEMES[ui_theme]['card']}; border-radius:5px; border:1px solid {UI_THEMES[ui_theme]['border']};'>
                <input type='radio' name='kpsp_q{i}' value='ya' style='margin-right:8px;' checked> ✅ Ya
            </label>
            <label style='cursor:pointer; padding:8px 12px; background:{UI_THEMES[ui_theme]['card']}; border-radius:5px; border:1px solid {UI_THEMES[ui_theme]['border']};'>
                <input type='radio' name='kpsp_q{i}' value='tidak' style='margin-right:8px;'> ❌ Belum
            </label>
        </div>
        """
    return ("", gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
            html, "", "", "", "")

def run_wizard_step3(month, layout_mode, main_payload, ui_theme):
    """Step 3: Tampilkan hasil akhir"""
    if not main_payload: return ("", gr.update(visible=False), gr.update(visible=True), gr.update(visible=True),
                                 "", "", "", "", "", "static/sticker_1.png", "**🔥 Streak:** 0 bulan | **⭐ Poin:** 0")
    
    do_now, saran, warnings, videos, imunisasi = generate_checklist_data(month, layout_mode, main_payload)
    
    progress = state_checklist_progress.value or {}
    if month not in progress: progress[month] = {"done": [], "streak": 0, "completed_at": str(datetime.now())}
    progress[month]["streak"] += 1
    state_checklist_progress.value = progress
    
    sticker_path = f"static/sticker_{random.randint(1,5)}.png"
    return ("", gr.update(visible=False), gr.update(visible=True), gr.update(visible=True),
            do_now, saran, warnings, videos, imunisasi, sticker_path, 
            f"**🔥 Streak:** {progress[month]['streak']} bulan | **⭐ Poin:** {progress[month]['streak'] * 10}")

def generate_checklist_pdf(month, layout_mode, main_payload, export_checked, ui_theme):
    """Generate PDF ringkas"""
    if not export_checked or not main_payload: return None
    
    child_name = main_payload.get("name_child", "Anak").replace(" ", "_")
    filename = f"Checklist_GiziSiKecil_{child_name}_Bulan_{month}.pdf"
    
    try:
        c = canvas.Canvas(filename, pagesize=A4)
        W, H = A4
        theme = UI_THEMES.get(ui_theme, UI_THEMES['pink_pastel'])
        
        # Header
        c.setFillColorRGB(0.965, 0.647, 0.753); c.rect(0, H - 50, W, 50, stroke=0, fill=1)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 16)
        c.drawString(30, H - 32, f"GiziSiKecil - Checklist Bulan ke-{month}")
        
        # Content
        y = H - 80
        c.setFont("Helvetica", 11)
        c.drawString(30, y, f"Nama: {main_payload.get('name_child', 'Si Kecil')}"); y -= 15
        c.drawString(30, y, f"Usia: {main_payload.get('age_mo', 0):.1f} bulan"); y -= 15
        c.drawString(30, y, f"BB/TB: {main_payload.get('w', 0):.1f} kg / {main_payload.get('h', 0):.1f} cm"); y -= 25
        
        do_now, saran, warnings, _, imunisasi = generate_checklist_data(month, layout_mode, main_payload)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "🎯 DO NOW:"); y -= 15
        c.setFont("Helvetica", 10)
        for line in do_now.split("\n\n")[:3]:
            c.drawString(40, y, line[:70]); y -= 12
        
        y -= 10; c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "💡 SARAN:"); y -= 15
        c.setFont("Helvetica", 10)
        for line in saran.split("\n\n")[:2]:
            c.drawString(40, y, line[:70]); y -= 12
        
        # Footer
        y = 50
        c.setFont("Helvetica-Oblique", 8); c.setFillColor(colors.grey)
        c.drawString(30, y, f"Dicetak: {datetime.now().strftime('%d-%m-%Y %H:%M')} | GiziSiKecil App")
        c.drawString(30, y-12, "⚠️ Ini adalah skrining edukatif, bukan diagnosis medis")
        
        c.save(); return filename
    except Exception as e:
        print(f"PDF Generation Error: {e}")
        return None

def update_notification_settings(enabled, time_str, current_settings):
    """Update notification settings"""
    if not current_settings: current_settings = {}
    current_settings["enabled"] = enabled
    current_settings["time"] = time_str
    state_notification_settings.value = current_settings
    return current_settings

def test_notification(settings):
    """Test smart notification"""
    if not settings or not settings.get("enabled"): return "🔕 Notifikasi dimatikan"
    time_str = settings.get("time", "08:00")
    return f"✅ Notifikasi aktif! Anda akan menerima reminder setiap pukul {time_str} WIB via WhatsApp (simulasi)"

def share_to_whatsapp(month, main_payload):
    """FIXED: Generate WhatsApp share message"""
    if not main_payload: return "❌ Tidak ada data untuk dishare"
    name = main_payload.get("name_child", "Si Kecil")
    age = main_payload.get("age_mo", 0)
    progress = state_checklist_progress.value or {}
    streak = progress.get(month, {}).get("streak", 0)
    msg = f"📊 *Progress GiziSiKecil Bulan {month}* - {name} ({age:.1f} bln)%0A%0A✅ Checklist selesai!%0A🔥 Streak: {streak} bulan%0A%0A*Download PDF lengkap di app GiziSiKecil*%0A%0Ahttps://anthrohpk-app.onrender.com"
    return f"📱 **[Share via WhatsApp](https://wa.me/?text={msg})** (klik untuk membuka WA)"

def find_nearest_posyandu():
    """Mockup fitur cari posyandu (simulasi GPS)"""
    mock_posyandu = [
        {"nama": "Posyandu Melati", "jarak": "0.3 km", "alamat": "Jl. Kenanga No. 5", "jam": "Senin-Sabtu 08:00-12:00"},
        {"nama": "Posyandu Mawar", "jarak": "0.7 km", "alamat": "Jl. Cempaka No. 12", "jam": "Selasa-Jumat 09:00-13:00"},
    ]
    html = "<div style='background:#e8f5e9; padding:15px; border-radius:10px; border-left:5px solid #28a745;'>"
    html += "<h4>📍 Posyandu Terdekat (Simulasi)</h4>"
    for p in mock_posyandu:
        html += f"""
        <div style='margin:10px 0; padding:10px; background:white; border-radius:8px;'>
            <strong>{p['nama']}</strong><br>
            📏 {p['jarak']} | 📍 {p['alamat']}<br>
            🕐 {p['jam']}
        </div>
        """
    html += "</div>"
    return html

# -------------------- Premium Page HTML --------------------
PREMIUM_PAGE_HTML = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GiziSiKecil Premium - Unlock Semua Fitur</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); color: #2c3e50; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .hero { text-align: center; background: white; padding: 40px; border-radius: 20px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .hero h1 { font-size: 3em; color: #ff6b9d; margin-bottom: 10px; }
        .hero p { font-size: 1.2em; color: #666; }
        .plans { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 30px; }
        .plan { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); transition: transform 0.3s; border: 3px solid transparent; }
        .plan:hover { transform: translateY(-10px); }
        .plan.featured { border-color: #ff6b9d; position: relative; }
        .plan.featured::before { content: "POPULER"; position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: #ff6b9d; color: white; padding: 5px 20px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .plan h3 { font-size: 1.8em; color: #2c3e50; margin-bottom: 10px; }
        .plan .price { font-size: 2.5em; color: #ff6b9d; font-weight: bold; }
        .plan .price span { font-size: 0.4em; color: #666; }
        .plan ul { list-style: none; margin: 20px 0; }
        .plan li { padding: 10px 0; border-bottom: 1px solid #eee; }
        .plan li::before { content: "✅ "; color: #4ecdc4; font-weight: bold; margin-right: 5px; }
        .plan button { width: 100%; padding: 15px; background: #ff6b9d; color: white; border: none; border-radius: 10px; font-size: 1.1em; font-weight: bold; cursor: pointer; transition: background 0.3s; }
        .plan button:hover { background: #e55a88; }
        .plan.featured button { background: #4ecdc4; }
        .plan.featured button:hover { background: #3bb5a0; }
        .features { background: white; padding: 40px; border-radius: 20px; margin-top: 30px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
        .features h2 { font-size: 2em; margin-bottom: 20px; color: #2c3e50; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }
        .feature-card { padding: 20px; background: #f9f9f9; border-radius: 10px; border-left: 5px solid #ff6b9d; }
        .feature-card h4 { color: #2c3e50; margin-bottom: 10px; }
        .contact { text-align: center; margin-top: 30px; padding: 20px; background: white; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
        .contact a { display: inline-block; padding: 15px 30px; background: #25D366; color: white; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 1.2em; }
        .contact a:hover { background: #128C7E; }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🚀 GiziSiKecil Premium</h1>
            <p>Unlock semua fitur powerful untuk optimal tumbuh kembang Si Kecil</p>
        </div>
        
        <div class="features">
            <h2>✨ Fitur Eksklusif Premium</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h4>📊 Analisis Tren Pertumbuhan</h4>
                    <p>Lihat grafik perkembangan anak Anda selama 24 bulan terakhir dengan AI-powered insights.</p>
                </div>
                <div class="feature-card">
                    <h4>🧠 Rekomendasi Personal AI</h4>
                    <p>Dapatkan saran gizi dan stimulasi yang dipersonalisasi berdasarkan data anak Anda.</p>
                </div>
                <div class="feature-card">
                    <h4>👨‍⚕️ Konsultasi Prioritas 24/7</h4>
                    <p>Chat langsung dengan ahli gizi anak & dokter spesialis kapan saja.</p>
                </div>
                <div class="feature-card">
                    <h4>📱 Smart Reminder Lengkap</h4>
                    <p>Notifikasi imunisasi, penimbangan, dan milestone perkembangan otomatis.</p>
                </div>
                <div class="feature-card">
                    <h4>🎥 Video Edukasi Premium</h4>
                    <p>Akses 100+ video resep MPASI, stimulasi, dan tips parenting eksklusif.</p>
                </div>
                <div class="feature-card">
                    <h4>📍 Lacak Posyandu Terdekat</h4>
                    <p>Fitur GPS real-time untuk menemukan posyandu, dokter anak & apotek terdekat.</p>
                </div>
                <div class="feature-card">
                    <h4>📄 Laporan PDF Premium</h4>
                    <p>Export laporan lengkap dengan grafik interaktif & analisis tren bulanan.</p>
                </div>
                <div class="feature-card">
                    <h4>👶 Multi-Child Monitoring</h4>
                    <p>Pantau lebih dari 1 anak dalam 1 akun (ideal untuk keluarga & fasyankes).</p>
                </div>
            </div>
        </div>
        
        <div class="plans">
            <div class="plan">
                <h3>🌱 Basic Plus</h3>
                <div class="price">Rp 29rb<span>/bulan</span></div>
                <ul>
                    <li>✅ Semua fitur Basic</li>
                    <li>✅ Iklan dihapus</li>
                    <li>✅ 5 laporan PDF/bulan</li>
                    <li>✅ Notifikasi penting</li>
                    <li>✅ Video edukasi dasar</li>
                </ul>
                <button onclick="alert('Hubungi +62-55888858160 untuk upgrade!')">Pilih Plan</button>
            </div>
            
            <div class="plan featured">
                <h3>🌸 Family Premium</h3>
                <div class="price">Rp 79rb<span>/bulan</span></div>
                <ul>
                    <li>✅ Semua Basic Plus</li>
                    <li>✅ Multi-child (3 anak)</li>
                    <li>✅ Analisis tren AI</li>
                    <li>✅ 20 laporan PDF/bulan</li>
                    <li>✅ Konsultasi 2x/bulan</li>
                    <li>✅ Video premium lengkap</li>
                    <li>✅ Smart reminder semua fitur</li>
                </ul>
                <button onclick="alert('Hubungi +62-55888858160 untuk upgrade!')">Paling Populer!</button>
            </div>
            
            <div class="plan">
                <h3>🏥 Pro Care</h3>
                <div class="price">Rp 149rb<span>/bulan</span></div>
                <ul>
                    <li>✅ Semua Family Premium</li>
                    <li>✅ Multi-child (10 anak)</li>
                    <li>✅ Konsultasi unlimited</li>
                    <li>✅ Laporan PDF unlimited</li>
                    <li>✅ Prioritas chat 24/7</li>
                    <li>✅ Update fitur eksklusif</li>
                </ul>
                <button onclick="alert('Hubungi +62-55888858160 untuk upgrade!')">Pilih Plan</button>
            </div>
            
            <div class="plan">
                <h3>🏢 Fasyankes</h3>
                <div class="price">Rp 499rb<span>/bulan</span></div>
                <ul>
                    <li>✅ Semua Pro Care</li>
                    <li>✅ Unlimited anak</li>
                    <li>✅ Dashboard admin</li>
                    <li>✅ Export data pasien</li>
                    <li>✅ Training gratis</li>
                    <li>✅ API integration</li>
                </ul>
                <button onclick="alert('Hubungi +62-55888858160 untuk upgrade!')">Pilih Plan</button>
            </div>
        </div>
        
        <div class="contact">
            <h3>💬 Siap Upgrade?</h3>
            <p>Hubungi kami sekarang untuk aktivasi instant!</p>
            <a href="https://wa.me/6285888858160?text=Halo%20GiziSiKecil,%20saya%20ingin%20upgrade%20ke%20Premium" target="_blank">
                📱 Chat WA Sekarang
            </a>
            <p style="margin-top:15px; font-size:0.9em; color:#666;">Gratis trial 7 hari untuk semua plan!</p>
        </div>
    </div>
</body>
</html>
"""

# -------------------- FastAPI Routes --------------------
app_fastapi = FastAPI(title="GiziSiKecil API")

@app_fastapi.get("/premium", response_class=HTMLResponse)
async def premium_page():
    return PREMIUM_PAGE_HTML

@app_fastapi.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# -------------------- Gradio UI --------------------
custom_css = """
.gradio-container { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.status-success { color: #28a745; font-weight: bold; }
.status-warning { color: #ffc107; font-weight: bold; }
.status-error   { color: #dc3545; font-weight: bold; }
.big-button     { font-size: 18px !important; font-weight: bold !important; padding: 20px !important; }
blockquote { background: #ffeef8; border-left: 5px solid #ff6b9d; padding: 10px 15px; margin: 10px 0; border-radius: 5px; }
/* TEMA DINAMIS */
:root {
    --primary-color: #ff6b9d;
    --secondary-color: #4ecdc4;
    --bg-color: #fff5f8;
    --text-color: #2c3e50;
    --border-color: #ffd4e0;
    --card-bg: #ffffff;
}
.mint-theme { --primary-color: #4ecdc4; --secondary-color: #a8e6cf; --bg-color: #f0fffa; --border-color: #b7f0e9; }
.lavender-theme { --primary-color: #b19cd9; --secondary-color: #d6b3ff; --bg-color: #f5f0ff; --border-color: #e0d4ff; }
"""

with gr.Blocks(
    title="GiziSiKecil - Monitor Pertumbuhan Anak Profesional",
    theme=gr.themes.Soft(primary_hue="pink", secondary_hue="teal", neutral_hue="slate"),
    css=custom_css
) as demo:
    gr.Markdown("""
    # 🏥 **GiziSiKecil** - Kalkulator & Monitor Status Gizi Anak
    ### 💕 WHO Child Growth Standards + Checklist Sehat Bulanan (0-60 Bulan) | 🔒 Privasi Terjaga | ⚕️ Standar Resmi
    """)
    
    # State Components
    state_child_data = gr.State({})
    state_checklist_progress = gr.State({})
    state_current_month = gr.State(0)
    state_kpsp_answers = gr.State({})
    state_notification_settings = gr.State({"enabled": True, "time": "08:00"})
    
    # THEME SELECTOR
    with gr.Row():
        ui_theme = gr.Radio(
            choices=["pink_pastel", "mint_pastel", "lavender_pastel"],
            label="🎨 Pilih Tema Aplikasi",
            value="pink_pastel",
            info="Gaya warna aplikasi (BASIC+ fitur)"
        )
    
    # TABS
    with gr.Tabs():
        # ========== TAB 1: KALKULATOR ==========
        with gr.TabItem("📊 Kalkulator Gizi"):
            with gr.Row():
                with gr.Column(scale=6):
                    gr.Markdown("## 📝 Input Data Anak")
                    with gr.Group():
                        gr.Markdown("### 👤 Identitas")
                        with gr.Row():
                            name_child = gr.Textbox(label="Nama Anak (opsional)", placeholder="Budi Santoso")
                            name_parent = gr.Textbox(label="Nama Orang Tua/Wali (opsional)", placeholder="Ibu Siti")
                        sex = gr.Radio(["Laki-laki","Perempuan"], label="Jenis Kelamin", value="Laki-laki")
                    
                    with gr.Group():
                        gr.Markdown("### 📅 Usia")
                        age_mode = gr.Radio(["Tanggal","Usia (bulan)"], label="Mode Input Usia", value="Tanggal")
                        with gr.Row():
                            dob = gr.Textbox(label="Tanggal Lahir", placeholder="2023-06-15 atau 15/06/2023", info="YYYY-MM-DD atau DD/MM/YYYY", visible=True)
                            dom = gr.Textbox(label="Tanggal Pengukuran", placeholder="2025-11-10 atau 10/11/2025", info="Tanggal ukur", visible=True)
                        age_mo = gr.Number(label="Usia (bulan)", value=12.0, precision=1, visible=False)
                    
                    with gr.Group():
                        gr.Markdown("### 📏 Data Antropometri (kg & cm)")
                        with gr.Row():
                            w = gr.Number(label="Berat Badan (kg)", value=10.0, precision=2)
                            h = gr.Number(label="Panjang/Tinggi Badan (cm)", value=75.0, precision=1)
                        hc = gr.Number(label="Lingkar Kepala (cm) - Opsional", value=None, precision=1)
                    
                    with gr.Group():
                        gr.Markdown("### ⚙️ Pengaturan Output")
                        with gr.Row():
                            lang_mode = gr.Radio(["Orang tua","Nakes"], label="Mode Bahasa", value="Orang tua")
                            theme = gr.Radio(["pink_pastel", "mint_pastel", "lavender_pastel"], label="Tema Grafik", value="pink_pastel")
                    
                    gr.Markdown("---")
                    with gr.Row():
                        prefill_btn = gr.Button("📊 Isi Nilai Median WHO (Z=0)", variant="secondary", size="sm")
                        demo_btn = gr.Button("🎬 Coba Demo", variant="secondary", size="sm")
                    status_msg = gr.Markdown("💡 **Tip**: Klik 'Coba Demo' lalu 'Analisis Sekarang'", elem_classes="status-success")
                    run_btn = gr.Button("🔍 Analisis Sekarang", variant="primary", size="lg", elem_classes="big-button")
                
                with gr.Column(scale=4):
                    gr.Markdown("## 💡 Panduan Pengukuran Interaktif")
                    measurement_guide = gr.HTML("""
                    <div style='background: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745;'>
                        <h4>📏 <strong>Tips Akurat Pengukuran</strong></h4>
                        <p><strong>Berat Badan:</strong></p>
                        <ul>
                            <li>Timbang tanpa sepatu & pakaian tebal</li>
                            <li>Gunakan timbangan digital (presisi 100g)</li>
                            <li>Ukur di waktu yang sama setiap bulan (pagi hari)</li>
                        </ul>
                        <p><strong>Panjang Badan (0-24 bulan):</strong></p>
                        <ul>
                            <li>Gunakan <strong>infantometer</strong> (alat ukur panjang bayi)</li>
                            <li>Letakkan bayi telentang, kepala menempel ke board</li>
                            <li>2 orang mengukur: 1 pegang kepala, 1 luruskan kaki</li>
                            <li>Pastikan bayi rileks, tidak menangis</li>
                        </ul>
                        <p><strong>Tinggi Badan (>24 bulan):</strong></p>
                        <ul>
                            <li>Gunakan <strong>stadiometer</strong> (alas rata dinding)</li>
                            <li>Anak berdiri tegak, punggung & kepala menempel dinding</li>
                            <li>Mata melihat ke depan, kaki rapat</li>
                        </ul>
                        <p><strong>Lingkar Kepala:</strong></p>
                        <ul>
                            <li>Gunakan <strong>meteran Lasso</strong> (flexibel)</li>
                            <li>Ukur di atas alis & telinga (garis terbesar)</li>
                            <li>Ulangi 3x, ambil nilai rata-rata</li>
                        </ul>
                        <p style='background: #fff3cd; padding: 10px; border-radius: 5px; margin-top: 10px;'>
                            <strong>⚠️ Penting:</strong> Kesalahan 0.5 cm di tinggi = error Z-score signifikan!
                        </p>
                    </div>
                    """)
                    
                    gr.Markdown("### 🎯 Interpretasi Z-Score")
                    interpretation = gr.HTML("""
                    <style>
                        .z-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                        .z-table th { background: #ff6b9d; color: white; padding: 10px; }
                        .z-table td { padding: 8px; border-bottom: 1px solid #eee; text-align: center; }
                        .z-table tr:hover { background: #fff5f8; }
                    </style>
                    <table class="z-table">
                        <tr><th>Z-Score</th><th>Status BB/U & TB/U</th><th>Status BB/TB</th><th>Icon</th></tr>
                        <tr><td>&lt; -3</td><td>Sangat Kurang/Berat</td><td>Gizi Buruk</td><td>🔴</td></tr>
                        <tr><td>-3 s/d -2</td><td>Kurang</td><td>Kurang (Wasting)</td><td>🟡</td></tr>
                        <tr><td>-2 s/d +2</td><td>Normal</td><td>Normal</td><td>🟢</td></tr>
                        <tr><td>+2 s/d +3</td><td>Risiko Lebih</td><td>Risiko Lebih</td><td>🟡</td></tr>
                        <tr><td>&gt; +3</td><td>Obesitas</td><td>Obesitas</td><td>🔴</td></tr>
                    </table>
                    """)
            
            gr.Markdown("---")
            gr.Markdown("## 📊 Hasil Analisis")
            out_md = gr.Markdown("*Hasil akan tampil setelah klik 'Analisis Sekarang'*", elem_classes="status-success")

# ========================================================
# CONTINUATION CODE - GIZISIKECIL APP FIX
# Copy & paste this section after your existing code
# ========================================================

# ==================== THEME SYSTEM FIX ====================
def apply_ui_theme(theme_name="pink_pastel"):
    """Dynamically apply theme to all UI components"""
    theme = UI_THEMES.get(theme_name, UI_THEMES["pink_pastel"])
    
    # Update global CSS variables
    css_override = f"""
    <style>
    :root {{
        --primary-color: {theme['primary']};
        --secondary-color: {theme['secondary']};
        --accent-color: {theme['accent']};
        --bg-color: {theme['bg']};
        --card-bg: {theme['card']};
        --text-color: {theme['text']};
        --border-color: {theme['border']};
    }}
    body {{ background: {theme['bg']} !important; color: {theme['text']} !important; }}
    .gradio-container {{ background: {theme['bg']} !important; }}
    .gr-box, .gr-form, .gr-input, .gr-dropdown, .gr-button {{
        background: {theme['card']} !important;
        border-color: {theme['border']} !important;
        color: {theme['text']} !important;
    }}
    .gr-button-primary {{ background: {theme['primary']} !important; border-color: {theme['primary']} !important; }}
    .gr-button-secondary {{ background: {theme['secondary']} !important; border-color: {theme['secondary']} !important; }}
    .gr-button-stop {{ background: #dc3545 !important; }}
    </style>
    """
    return css_override

# ==================== ENHANCED SYNC FUNCTION ====================
def sync_from_calculator(main_payload, layout_mode, ui_theme, state_target):
    """FIXED: Sync data dengan state management yang benar"""
    try:
        if not main_payload or not isinstance(main_payload, dict):
            raise ValueError("Payload tidak valid")
        
        # Update state external
        state_target.value = main_payload
        
        age_mo = float(main_payload.get("age_mo", 0))
        month = min(int(age_mo), 24)
        
        # Generate sync message
        sync_msg = f"""
        ✅ **SINKRONISASI BERHASIL!**
        
        👶 **Nama Anak:** {main_payload.get('name_child', 'Si Kecil')}  
        📅 **Usia Terhitung:** {age_mo:.1f} bulan (Bulan ke-{month})  
        ⚖️ **Data Antropometri:** {main_payload.get('w', 0):.1f} kg / {main_payload.get('h', 0):.1f} cm  
        📊 **Status Gizi:** {main_payload.get('permenkes', {}).get('waz', 'Normal')}  
        
        🔥 **Langkah Selanjutnya:** Pilih bulan di dropdown, lalu klik "Mulai Checklist"
        """
        
        # Return updates for ALL relevant components
        return {
            sync_status: gr.update(value=sync_msg, visible=True),
            wizard_container: gr.update(visible=True),
            month_selector: gr.update(value=month),
            step1_panel: gr.update(visible=False),
            step2_panel: gr.update(visible=False),
            step3_panel: gr.update(visible=False),
            state_child_data: main_payload
        }
    except Exception as e:
        error_msg = f"❌ **ERROR SINKRON:** {str(e)}"
        return {
            sync_status: gr.update(value=error_msg, visible=True),
            wizard_container: gr.update(visible=False),
            month_selector: gr.update(value=0),
            step1_panel: gr.update(visible=False),
            step2_panel: gr.update(visible=False),
            step3_panel: gr.update(visible=False)
        }

# ==================== WIZARD FLOW CONTROL ====================
def start_wizard_handler(month, state_data):
    """FIXED: Start checklist with proper state management"""
    if not state_data or not state_data.get("age_mo"):
        return {
            step1_panel: gr.update(visible=False),
            sync_status: gr.update(value="❌ Data anak belum tersedia! Klik 'Sinkron Data' dulu.", visible=True),
            data_overview: gr.update(value="")
        }
    
    # Update current month state
    state_current_month.value = month
    
    overview = f"""
    ### 👶 **VERIFIKASI DATA ANAK**
    
    **📝 Nama:** {state_data.get('name_child', 'Si Kecil')}  
    **⚥ Jenis Kelamin:** {state_data.get('sex_text', 'Tidak diketahui')}  
    **📅 Usia:** {state_data.get('age_mo', 0):.1f} bulan  
    **⚖️ Berat/Tinggi:** {state_data.get('w', 0):.1f} kg / {state_data.get('h', 0):.1f} cm  
    **🧠 Lingkar Kepala:** {state_data.get('hc', 'Tidak diukur')} cm  
    
    ✅ **Klik "Lanjutkan"** jika data sudah benar untuk melanjutkan screening.
    """
    
    return {
        step1_panel: gr.update(visible=True),
        step2_panel: gr.update(visible=False),
        step3_panel: gr.update(visible=False),
        data_overview: gr.update(value=overview),
        sync_status: gr.update(value="", visible=False)
    }

def confirm_data_handler(month, state_data, ui_theme):
    """Proceed to KPSP screening"""
    questions = KPSP_QUESTIONS.get(month, [])
    
    if not questions:
        return {
            step1_panel: gr.update(visible=False),
            step2_panel: gr.update(visible=False),
            step3_panel: gr.update(visible=True),
            kpsp_questions_html: gr.update(value="<p>Tidak ada pertanyaan KPSP untuk bulan ini.</p>")
        }
    
    html = f"""
    <div style='background: {UI_THEMES[ui_theme]["bg"]}; padding: 20px; border-radius: 10px;'>
        <h4 style='color: {UI_THEMES[ui_theme]["primary"]}; margin-bottom: 15px;'>🧠 SCREENING PERKEMBANGAN (KPSP)</h4>
        <p style='color: {UI_THEMES[ui_theme]["text"]}; opacity: 0.8; margin-bottom: 20px;'>Bulan ke-{month} - Jawab dengan jujur untuk rekomendasi terbaik</p>
    """
    
    for i, q in enumerate(questions):
        html += f"""
        <div style='margin: 12px 0; padding: 15px; background: {UI_THEMES[ui_theme]["card"]}; border-radius: 8px; border-left: 4px solid {UI_THEMES[ui_theme]["primary"]};'>
            <p style='font-weight: bold; margin-bottom: 12px; color: {UI_THEMES[ui_theme]["text"]};'>{i+1}. {q}</p>
            <div style='display: flex; gap: 15px;'>
                <label style='cursor: pointer; padding: 8px 15px; background: {UI_THEMES[ui_theme]["secondary"]}; color: white; border-radius: 5px;'>
                    <input type='radio' name='kpsp_q{i}' value='ya' style='margin-right: 5px;' checked> ✅ Ya
                </label>
                <label style='cursor: pointer; padding: 8px 15px; background: #ff6b6b; color: white; border-radius: 5px;'>
                    <input type='radio' name='kpsp_q{i}' value='tidak' style='margin-right: 5px;'> ❌ Belum
                </label>
            </div>
        </div>
        """
    
    html += "</div>"
    
    return {
        step1_panel: gr.update(visible=False),
        step2_panel: gr.update(visible=True),
        step3_panel: gr.update(visible=False),
        kpsp_questions_html: gr.update(value=html)
    }

def complete_checklist_handler(month, layout_mode, state_data, ui_theme):
    """Generate final results"""
    if not state_data:
        return {
            step1_panel: gr.update(visible=False),
            step2_panel: gr.update(visible=True),
            sync_status: gr.update(value="❌ Error: Data tidak tersedia")
        }
    
    # Generate all content
    do_now, saran, warnings, videos, imunisasi = generate_checklist_data(month, layout_mode, state_data)
    
    # Update progress
    progress = state_checklist_progress.value or {}
    if month not in progress:
        progress[month] = {"done": [], "streak": 0, "completed_at": str(datetime.now())}
    progress[month]["streak"] += 1
    state_checklist_progress.value = progress
    
    # Random sticker
    sticker_path = f"static/sticker_{random.randint(1,5)}.png"
    
    return {
        step1_panel: gr.update(visible=False),
        step2_panel: gr.update(visible=False),
        step3_panel: gr.update(visible=True),
        do_now_box: gr.update(value=do_now),
        saran_box: gr.update(value=saran),
        warnings_box: gr.update(value=warnings),
        video_gallery: gr.update(value=videos),
        immunization_box: gr.update(value=imunisasi),
        sticker_display: gr.update(value=sticker_path),
        streak_display: gr.update(value=f"**🔥 Streak:** {progress[month]['streak']} bulan | **⭐ Poin:** {progress[month]['streak'] * 10}")
    }

# ==================== NOTIFICATION SYSTEM ====================
def toggle_notification(enable, time_val, settings_state):
    """FIXED: Toggle notification settings"""
    new_settings = {
        "enabled": enable,
        "time": time_val if time_val else "08:00"
    }
    settings_state.value = new_settings
    
    status = "✅ Notifikasi AKTIF" if enable else "🔕 Notifikasi NONAKTIF"
    return gr.update(value=f"{status} - Reminder akan dikirim pukul {new_settings['time']} WIB")

def update_notification_time(time_val, settings_state):
    """Update notification time"""
    if not settings_state.value:
        settings_state.value = {"enabled": True, "time": "08:00"}
    
    settings_state.value["time"] = time_val
    return gr.update(value=f"⏰ Waktu diperbarui: {time_val} WIB")

# ==================== POSYANDU LOCATOR ====================
LOCATOR_ENABLED = True  # Toggle untuk demo

def find_nearest_posyandu_handler():
    """FIXED: Interactive Posyandu Locator"""
    if not LOCATOR_ENABLED:
        return gr.update(value="<p>🔍 Fitur lokasi memerlukan GPS. Hubungi +62-55888858160 untuk demo lengkap.</p>")
    
    # Simulasi data posyandu berdasarkan lokasi random
    mock_data = [
        {"nama": "Posyandu Melati Indah", "jarak": "0.3 km", "alamat": "Jl. Kenanga No. 5, RT 02/RW 05", "jam": "Senin-Sabtu 08:00-12:00", "kontak": "0812-3456-7890"},
        {"nama": "Posyandu Mawar Harapan", "jarak": "0.7 km", "alamat": "Jl. Cempaka No. 12, RT 01/RW 03", "jam": "Selasa-Jumat 09:00-13:00", "kontak": "0813-9876-5432"},
        {"nama": "Posyandu Flamboyan Sehat", "jarak": "1.2 km", "alamat": "Jl. Anggrek No. 8, RT 04/RW 02", "jam": "Rabu-Minggu 07:00-11:00", "kontak": "0812-5555-8888"}
    ]
    
    html = f"""
    <div style='background: var(--bg-color); padding: 20px; border-radius: 10px;'>
        <h3 style='color: var(--primary-color); margin-bottom: 15px;'>📍 Posyandu Terdekat (Simulasi GPS)</h3>
    """
    
    for p in mock_data:
        html += f"""
        <div style='background: white; margin: 10px 0; padding: 15px; border-radius: 8px; border-left: 5px solid var(--primary-color); box-shadow: 0 2px 4px var(--shadow);'>
            <h4 style='color: var(--primary-color); margin-bottom: 5px;'>{p['nama']}</h4>
            <p style='margin: 5px 0;'><strong>📏 Jarak:</strong> {p['jarak']}</p>
            <p style='margin: 5px 0;'><strong>📍 Alamat:</strong> {p['alamat']}</p>
            <p style='margin: 5px 0;'><strong>🕐 Jam:</strong> {p['jam']}</p>
            <p style='margin: 5px 0;'><strong>📞 Kontak:</strong> {p['kontak']}</p>
            <a href='https://wa.me/{p["kontak"].replace("-", "")}?text=Halo%20Posyandu,%20saya%20ingin%20konsultasi%20gizi%20anak' 
               target='_blank' 
               style='display: inline-block; margin-top: 8px; padding: 8px 15px; background: #25D366; color: white; text-decoration: none; border-radius: 5px; font-size: 12px;'>
                💬 Chat via WA
            </a>
        </div>
        """
    
    html += """
        <div style='margin-top: 15px; padding: 10px; background: #fff3cd; border-radius: 5px;'>
            <p style='font-size: 12px; color: #856404;'>
                ⚠️ Untuk lokasi akurat aktifkan GPS. Fitur ini tersedia di versi Premium Pro.
            </p>
        </div>
    </div>
    """
    
    return gr.update(value=html)

# ==================== PREMIUM PAGE ROUTE ====================
@app_fastapi.get("/premium", response_class=HTMLResponse)
async def premium_page():
    return PREMIUM_PAGE_HTML

# ==================== ENHANCED PREMIUM PAGE HTML ====================
PREMIUM_PAGE_HTML = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GiziSiKecil Premium - Unlock Semua Fitur</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); color: #2c3e50; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .hero { text-align: center; background: white; padding: 40px; border-radius: 20px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .hero h1 { font-size: 3em; color: #ff6b9d; margin-bottom: 10px; }
        .hero p { font-size: 1.2em; color: #666; }
        .plans { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 30px; }
        .plan { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); transition: transform 0.3s; border: 3px solid transparent; }
        .plan:hover { transform: translateY(-10px); }
        .plan.featured { border-color: #ff6b9d; position: relative; }
        .plan.featured::before { content: "POPULER"; position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: #ff6b9d; color: white; padding: 5px 20px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .plan h3 { font-size: 1.8em; color: #2c3e50; margin-bottom: 10px; }
        .plan .price { font-size: 2.5em; color: #ff6b9d; font-weight: bold; }
        .plan .price span { font-size: 0.4em; color: #666; }
        .plan ul { list-style: none; margin: 20px 0; }
        .plan li { padding: 10px 0; border-bottom: 1px solid #eee; }
        .plan li::before { content: "✅ "; color: #4ecdc4; font-weight: bold; margin-right: 5px; }
        .plan button { width: 100%; padding: 15px; background: #ff6b9d; color: white; border: none; border-radius: 10px; font-size: 1.1em; font-weight: bold; cursor: pointer; transition: background 0.3s; }
        .plan button:hover { background: #e55a88; }
        .plan.featured button { background: #4ecdc4; }
        .plan.featured button:hover { background: #3bb5a0; }
        .features { background: white; padding: 40px; border-radius: 20px; margin-top: 30px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
        .features h2 { font-size: 2em; margin-bottom: 20px; color: #2c3e50; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }
        .feature-card { padding: 20px; background: #f9f9f9; border-radius: 10px; border-left: 5px solid #ff6b9d; }
        .feature-card h4 { color: #2c3e50; margin-bottom: 10px; }
        .contact { text-align: center; margin-top: 30px; padding: 20px; background: white; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
        .contact a { display: inline-block; padding: 15px 30px; background: #25D366; color: white; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 1.2em; }
        .contact a:hover { background: #128C7E; }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🚀 GiziSiKecil Premium</h1>
            <p>Unlock semua fitur powerful untuk optimal tumbuh kembang Si Kecil</p>
        </div>
        
        <div class="features">
            <h2>✨ Fitur Eksklusif Premium</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h4>📊 Analisis Tren Pertumbuhan AI</h4>
                    <p>Lihat grafik perkembangan anak Anda selama 24 bulan terakhir dengan AI-powered insights & prediksi.</p>
                </div>
                <div class="feature-card">
                    <h4>🧠 Rekomendasi Personal AI</h4>
                    <p>Dapatkan saran gizi dan stimulasi yang dipersonalisasi berdasarkan data unik anak Anda.</p>
                </div>
                <div class="feature-card">
                    <h4>👨‍⚕️ Konsultasi Prioritas 24/7</h4>
                    <p>Chat langsung dengan ahli gizi anak & dokter spesialis kapan saja, respons dalam 15 menit.</p>
                </div>
                <div class="feature-card">
                    <h4>📱 Smart Reminder Lengkap</h4>
                    <p>Notifikasi otomatis: imunisasi, penimbangan, milestone perkembangan, stok MPASI.</p>
                </div>
                <div class="feature-card">
                    <h4>🎥 Video Edukasi Premium (100+)</h4>
                    <p>Akses video resep MPASI, stimulasi, tips parenting eksklusif dari ahli.</p>
                </div>
                <div class="feature-card">
                    <h4>📍 Lacak Posyandu & Fasyankes Real-Time</h4>
                    <p>Fitur GPS untuk menemukan posyandu, dokter anak & apotek terdekat dengan rating.</p>
                </div>
                <div class="feature-card">
                    <h4>📄 Laporan PDF Premium Interaktif</h4>
                    <p>Export laporan lengkap dengan grafik interaktif, analisis tren & rekomendasi AI.</p>
                </div>
                <div class="feature-card">
                    <h4>👶 Multi-Child Monitoring</h4>
                    <p>Pantau hingga 10 anak dalam 1 akun (ideal untuk keluarga & fasyankes).</p>
                </div>
            </div>
        </div>
        
        <div class="plans">
            <div class="plan">
                <h3>🌱 Basic Plus</h3>
                <div class="price">Rp 29rb<span>/bulan</span></div>
                <ul>
                    <li>✅ Semua fitur Basic</li>
                    <li>✅ Iklan dihapus</li>
                    <li>✅ 5 laporan PDF/bulan</li>
                    <li>✅ Notifikasi penting</li>
                    <li>✅ Video edukasi dasar</li>
                    <li>❌ Konsultasi terbatas</li>
                </ul>
                <button onclick="alert('Trial 7 hari gratis! Hubungi +62-55888858160')">Pilih Plan</button>
            </div>
            
            <div class="plan featured">
                <h3>🌸 Family Premium</h3>
                <div class="price">Rp 79rb<span>/bulan</span></div>
                <ul>
                    <li>✅ Semua Basic Plus</li>
                    <li>✅ Multi-child (3 anak)</li>
                    <li>✅ Analisis tren AI</li>
                    <li>✅ 20 laporan PDF/bulan</li>
                    <li>✅ Konsultasi 2x/bulan</li>
                    <li>✅ Video premium lengkap</li>
                    <li>✅ Smart reminder semua fitur</li>
                </ul>
                <button onclick="alert('Paling populer! Trial 7 hari. Hubungi +62-55888858160')">Paling Populer!</button>
            </div>
            
            <div class="plan">
                <h3>🏥 Pro Care</h3>
                <div class="price">Rp 149rb<span>/bulan</span></div>
                <ul>
                    <li>✅ Semua Family Premium</li>
                    <li>✅ Multi-child (10 anak)</li>
                    <li>✅ Konsultasi unlimited</li>
                    <li>✅ Laporan PDF unlimited</li>
                    <li>✅ Prioritas chat 24/7</li>
                    <li>✅ Update fitur eksklusif</li>
                </ul>
                <button onclick="alert('Best value untuk keluarga besar! Hubungi +62-55888858160')">Pilih Plan</button>
            </div>
            
            <div class="plan">
                <h3>🏢 Fasyankes</h3>
                <div class="price">Rp 499rb<span>/bulan</span></div>
                <ul>
                    <li>✅ Semua Pro Care</li>
                    <li>✅ Unlimited anak</li>
                    <li>✅ Dashboard admin</li>
                    <li>✅ Export data pasien</li>
                    <li>✅ Training gratis 2x/tahun</li>
                    <li>✅ API integration</li>
                </ul>
                <button onclick="alert('Khusus fasyankes! Hubungi +62-55888858160')">Pilih Plan</button>
            </div>
        </div>
        
        <div class="contact">
            <h3>💬 Siap Upgrade?</h3>
            <p>Gratis trial 7 hari untuk semua plan!</p>
            <a href="https://wa.me/6285888858160?text=Halo%20GiziSiKecil,%20saya%20ingin%20upgrade%20ke%20Premium%20(dari%20web)" target="_blank">
                📱 Chat WA Sekarang
            </a>
            <p style="margin-top:15px; font-size:0.9em; color:#666;">Fast response: Senin-Sabtu 08:00-20:00 WIB</p>
        </div>
    </div>
</body>
</html>
"""

# ==================== EVENT HANDLERS REBINDING ====================
# Bind semua event handlers setelah komponen didefinisikan
def bind_event_handlers():
    """Re-bind semua event handlers dengan logic yang benar"""
    
    # THEME SWITCHER
    ui_theme.change(
        fn=lambda theme: gr.update(css=apply_ui_theme(theme)),
        inputs=[ui_theme],
        outputs=[demo]
    )
    
    # SINKRON DATA - FIXED
    sync_data_btn.click(
        fn=sync_from_calculator,
        inputs=[state_child_data, layout_mode, ui_theme, state_child_data],
        outputs=[
            sync_status, wizard_container, month_selector, state_child_data,
            step1_panel, step2_panel, step3_panel
        ]
    )
    
    # WIZARD FLOW - FIXED
    start_wizard_btn.click(
        fn=start_wizard_handler,
        inputs=[month_selector, state_child_data],
        outputs=[step1_panel, sync_status, data_overview, step2_panel, step3_panel]
    )
    
    confirm_data_btn.click(
        fn=confirm_data_handler,
        inputs=[month_selector, state_child_data, ui_theme],
        outputs=[step1_panel, step2_panel, step3_panel, kpsp_questions_html]
    )
    
    next_step3_btn.click(
        fn=complete_checklist_handler,
        inputs=[month_selector, layout_mode, state_child_data, ui_theme],
        outputs=[
            step1_panel, step2_panel, step3_panel,
            do_now_box, saran_box, warnings_box, video_gallery,
            immunization_box, sticker_display, streak_display
        ]
    )
    
    # NOTIFICATION - FIXED
    notif_enabled.change(
        fn=toggle_notification,
        inputs=[notif_enabled, notif_time, state_notification_settings],
        outputs=[notif_status]
    )
    
    notif_time.change(
        fn=update_notification_time,
        inputs=[notif_time, state_notification_settings],
        outputs=[notif_status]
    )
    
    test_notif_btn.click(
        fn=test_notification,
        inputs=[state_notification_settings],
        outputs=[notif_status]
    )
    
    # POSYANDU LOCATOR - FIXED
    posyandu_btn = gr.Button("🔍 Cari Posyandu Terdekat", variant="secondary")
    posyandu_output = gr.HTML()
    
    posyandu_btn.click(
        fn=find_nearest_posyandu_handler,
        outputs=[posyandu_output]
    )
    
    # PREMIUM PAGE REDIRECT - FIXED
    premium_btn.click(
        fn=lambda: gr.update(value="<script>window.open('/premium', '_blank');</script>"),
        outputs=[gr.HTML(visible=False)]
    )
    
    # MODE MUDAH TOGGLE - FIXED
    layout_mode.change(
        fn=lambda mode: gr.update(visible=mode=="Mode Lengkap"),
        inputs=[layout_mode],
        outputs=[step2_panel]  # Sembunyikan KPSP jika mode mudah
    )

# ==================== FINAL SETUP ====================
# Panggil binding setelah semua komponen selesai didefinisikan
# (Tempatkan di akhir file setelah semua gr.Blocks())

# Render the app
if __name__ == "__main__":
    # Bind all handlers
    bind_event_handlers()
    
   # ==================== FASTAPI APP DEFINITION ====================
# PENTING: Variabel HARUS bernama 'app' (bukan app_fastapi)
app = FastAPI(title="GiziSiKecil Pro", version="2.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")

# Premium page route
@app.get("/premium", response_class=HTMLResponse)
async def premium_page():
    return PREMIUM_PAGE_HTML

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Mount Gradio setelah semua route didefinisikan
app = gr.mount_gradio_app(app, demo, path="/")

# ==================== MAIN GUARD (HANYA UNTUK LOCAL) ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

    
    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")
    
    # Premium page route
    @app.get("/premium", response_class=HTMLResponse)
    async def get_premium():
        return PREMIUM_PAGE_HTML
    
    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "2.0", "theme_support": True, "premium": True}
    
    # Mount Gradio
    app = gr.mount_gradio_app(app, demo, path="/")
    
    # Start server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
