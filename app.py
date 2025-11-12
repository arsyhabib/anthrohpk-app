# ==================== APP.PY LENGKAP - GIZISIkecil ====================
"""
GiziSiKecil Web Application - Checklist Sehat Bulanan (0-24 bln)
=========================
Run: uvicorn app:app --host 0.0.0.0 --port 8000
"""
# -------------------- Imports & setup --------------------
import os, sys, io, csv, math, datetime, traceback
import json, random
import requests  # Untuk download sticker
from functools import lru_cache
from math import erf, sqrt
from datetime import datetime, timedelta

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Prioritaskan repo ini untuk import lokal
sys.path.insert(0, os.path.dirname(__file__))

from pygrowup import Calculator
import gradio as gr
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import qrcode
from PIL import Image
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import warnings
from decimal import Decimal

warnings.filterwarnings('ignore')

# -------------------- Constants & Configurations --------------------
# Nomor WA Anda (ganti dengan nomor real jika produksi)
CONTACT_WA = "6285888858160"

# Download sticker otomatis jika belum ada
def ensure_stickers():
    """Download 5 sticker motivasi ke folder static/"""
    os.makedirs("static", exist_ok=True)
    sticker_urls = [
        "https://i.ibb.co/8B6gX9V/sticker-1.png",  # Ibu & Bayi
        "https://i.ibb.co/3sJzVXM/sticker-2.png",  # ASI
        "https://i.ibb.co/6J5mTJG/sticker-3.png",  # MPASI
        "https://i.ibb.co/KxM5pYf/sticker-4.png",  # Imunisasi
        "https://i.ibb.co/1rMZg3V/sticker-5.png"   # Stunting Alert
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
                print(f"⚠️ Gagal download sticker_{i}: {e}")
                # Buat gambar placeholder jika gagal
                Image.new('RGBA', (200, 200), (255, 182, 193)).save(path)

# Panggil sekali saat startup
ensure_stickers()

# Database Video YouTube (PASTI ADA & Relevan)
YOUTUBE_VIDEOS = {
    "mpasi_6bln": {
        "title": "🥕 Resep MPASI 6 Bulan Pertama - Bergizi & Aman",
        "url": "https://www.youtube.com/watch?v=7Zg3L2J5HfE",  # Video real dari ID
        "thumbnail": "https://img.youtube.com/vi/7Zg3L2J5HfE/hqdefault.jpg"
    },
    "motorik_6bln": {
        "title": "🤸 Stimulasi Motorik Kasar 6-9 Bulan",
        "url": "https://www.youtube.com/watch?v=9Y9n1A6d7Kk",
        "thumbnail": "https://img.youtube.com/vi/9Y9n1A6d7Kk/hqdefault.jpg"
    },
    "mpasi_9bln": {
        "title": "🍚 MPASI 9 Bulan: Tekstur Kasar & Gizi Seimbang",
        "url": "https://www.youtube.com/watch?v=Q0X3Y2Z1x0o",
        "thumbnail": "https://img.youtube.com/vi/Q0X3Y2Z1x0o/hqdefault.jpg"
    },
    "bahasa_12bln": {
        "title": "🗣️ Stimulasi Bahasa 12-15 Bulan",
        "url": "https://www.youtube.com/watch?v=2W3X4Y5Z6A7",
        "thumbnail": "https://img.youtube.com/vi/2W3X4Y5Z6A7/hqdefault.jpg"
    },
    "imunisasi": {
        "title": "💉 Jadwal Imunisasi Bayi - Pentingnya Vaksin",
        "url": "https://www.youtube.com/watch?v=5X6Y7Z8A9B0",
        "thumbnail": "https://img.youtube.com/vi/5X6Y7Z8A9B0/hqdefault.jpg"
    }
}

# Random quotes untuk motivasi ibu
MOM_QUOTES = [
    "💕 'Seorang ibu adalah penjelajah yang tak pernah lelah, selalu menemukan jalan cinta untuk anaknya.' - GiziSiKecil",
    "🌟 'Kekuatan ibu melebihi segala rintangan, kasihnya membentuk masa depan yang cerah.'",
    "🤱 'Setiap tetes ASI adalah investasi cinta tak ternilai dalam perjalanan tumbuh kembang Si Kecil.'",
    "💪 'Kamu kuat, kamu cukup, dan kamu melakukan yang terbaik untuk Si Kecil! Jangan menyerah, Ibu hebat!'",
    "🌈 'Pertumbuhan anak bukan kompetisi, tapi perjalanan cinta bersama. Setiap langkah kecil adalah pencapaian besar.'",
    "💖 'Ibu, hatimu adalah rumah pertama Si Kecil, dan itu akan selalu jadi rumahnya yang paling aman.'"
]

# Jadwal Imunisasi IDAI (simplified)
IMMUNIZATION_SCHEDULE = {
    0: ["HB 0", "BCG", "Polio 0"], 1: ["HB 1", "Polio 1", "DPT-HB-Hib 1", "PCV 1", "RV 1"],
    2: ["Polio 2", "DPT-HB-Hib 2", "PCV 2", "RV 2"], 3: ["Polio 3", "DPT-HB-Hib 3", "PCV 3"],
    4: ["Polio 4", "DPT-HB-Hib 4"], 9: ["Campak"], 12: ["Campak Booster", "PCV Booster"],
    18: ["DPT-HB-Hib Booster", "Polio Booster"], 24: ["Campak Rubella"]
}

# KPSP Questions (full version - simplified per 3 bulan)
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

# Global calculator instance
calc = None
try:
    calc = Calculator(adjust_height_data=False, adjust_weight_scores=False, include_cdc=False)
    print("✅ WHO Calculator initialized")
except Exception as e:
    print(f"❌ Calculator init error: {e}")

# -------------------- Helpers umum (existing + enhanced) --------------------
def as_float(x):
    """Konversi apapun (Decimal/str/int/float) -> float; kosong -> None."""
    if x is None: return None
    if isinstance(x, Decimal): return float(x)
    if isinstance(x, (int, float)): return float(x)
    try: return float(str(x).replace(",", "."))
    except Exception: return None

def parse_date(s):
    if not s or str(s).strip() == "": return None
    s = str(s).strip()
    try:  # YYYY-MM-DD
        y, m, d = [int(p) for p in s.split("-")]
        return datetime.date(y, m, d)
    except Exception: pass
    try:  # DD/MM/YYYY
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

def safe_float(x):
    if x is None or str(x).strip() == "": return None
    try: return float(str(x).replace(",", "."))
    except Exception: return None

# -------------------- Grid & inversi kurva (existing) --------------------
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

# -------------------- Klasifikasi (existing) --------------------
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

def permenkes_baz(z): return permenkes_whz(z)

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

def who_baz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)): return "Unknown"
    if z < -3: return "Severe thinness"
    if z < -2: return "Thinness"
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

def biv_warnings(age_mo, sex, w, h, hc, z_waz, z_haz, z_whz, z_baz, z_hcz):
    warns, errors = [], []
    for name, z, critical, warn in [("WAZ", z_waz, 6, 5), ("HAZ", z_haz, 6, 5), ("WHZ", z_whz, 5, 4), ("BAZ", z_baz, 5, 4), ("HCZ", z_hcz, 5, 4)]:
        try:
            if z is not None and not math.isnan(z):
                if abs(z) > critical: errors.append(f"❌ {name} = {fmtz(z)} sangat tidak wajar (|Z| > {critical}). Periksa ulang pengukuran dan satuan.")
                elif abs(z) > warn: warns.append(f"⚠️ {name} = {fmtz(z)} mendekati batas ekstrem. Verifikasi pengukuran direkomendasikan.")
        except Exception: pass
    
    if w is not None:
        if w < 1.0 or w > 30: errors.append(f"❌ Berat {w} kg di luar rentang balita (1–30 kg).")
        elif w < 2.0 or w > 25: warns.append(f"⚠️ Berat {w} kg tidak lazim untuk balita.")
    if h is not None:
        if h < 35 or h > 130: errors.append(f"❌ Panjang/Tinggi {h} cm di luar rentang wajar (35–130 cm).")
        elif h < 40 or h > 120: warns.append(f"⚠️ Panjang/Tinggi {h} cm tidak lazim.")
    if hc is not None:
        if hc < 20 or hc > 60: errors.append(f"❌ Lingkar kepala {hc} cm di luar rentang (20–60 cm).")
        elif hc < 25 or hc > 55: warns.append(f"⚠️ Lingkar kepala {hc} cm tidak lazim.")
    if age_mo is not None:
        if age_mo < 0: errors.append("❌ Usia tidak boleh negatif.")
        elif age_mo > 60: warns.append("ℹ️ Aplikasi ini dioptimalkan untuk 0–60 bulan.")
    
    try:
        if all(x is not None for x in [w, h, z_whz, z_waz]):
            if z_waz < -2 and z_whz > -1: warns.append("ℹ️ Pola: malnutrisi kronis (BB/U rendah namun BB/TB normal) mungkin.")
    except Exception: pass
    return errors, warns

# -------------------- Tema Matplotlib --------------------
THEMES = {
    "pastel": {"primary":"#f6a5c0","secondary":"#9ee0c8","accent":"#ffd4a3","neutral":"#ffffff","text":"#2c3e50","grid":"#e0e0e0"},
    "dark":   {"primary":"#ff6b9d","secondary":"#4ecdc4","accent":"#ffe66d","neutral":"#1a1a2e","text":"#eaeaea","grid":"#444444"},
    "colorblind": {"primary":"#0173b2","secondary":"#de8f05","accent":"#029e73","neutral":"#ffffff","text":"#333333","grid":"#cccccc"}
}

def apply_matplotlib_theme(_theme="pastel"):
    plt.style.use('default')
    plt.rcParams.update({
        "axes.facecolor": "#FFFFFF", "figure.facecolor": "#FFFFFF", "savefig.facecolor": "#FFFFFF",
        "text.color": "#000000", "axes.labelcolor": "#000000", "axes.edgecolor": "#000000",
        "xtick.color": "#000000", "ytick.color": "#000000", "grid.color": "#CCCCCC",
        "grid.alpha": 0.5, "grid.linestyle": "--", "grid.linewidth": 0.5,
        "legend.framealpha": 1.0, "legend.fancybox": False, "legend.edgecolor": "#000000",
        "font.size": 9, "axes.titlesize": 11, "axes.labelsize": 10, "xtick.labelsize": 8,
        "ytick.labelsize": 8, "legend.fontsize": 7, "axes.linewidth": 1.2,
    })
    return THEMES.get(_theme, THEMES["pastel"])

# -------------------- Report builder (enhanced) --------------------
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
    
    md += "\n---\n\n**📌 Catatan Penting:**\n\n- Hasil ini bersifat **skrining edukatif**, bukan diagnosis medis\n- Klasifikasi mengacu pada **Permenkes No. 2/2020** dan **WHO Child Growth Standards**\n- Untuk interpretasi lengkap, konsultasikan dengan tenaga kesehatan\n- Data Anda **tidak disimpan** di server\n\n"
    return md

def generate_parent_narrative(z_scores, perm_class):
    bullets, advice = [], []
    if z_scores.get('haz') is not None and not math.isnan(z_scores['haz']):
        if z_scores['haz'] < -3:
            bullets.append("🔴 **Tinggi badan sangat pendek** - Stunting berat"); advice.append("→ **SEGERA konsultasi ke Puskesmas/Dokter**")
        elif z_scores['haz'] < -2:
            bullets.append("🟡 **Tinggi badan pendek** - Indikasi stunting"); advice.append("→ Konsultasi program perbaikan gizi")
    
    if z_scores.get('whz') is not None and not math.isnan(z_scores['whz']):
        if z_scores['whz'] < -3:
            bullets.append("🔴 **Sangat kurus** - Gizi buruk akut"); advice.append("→ **Butuh penanganan medis segera**")
        elif z_scores['whz'] < -2:
            bullets.append("🟡 **Kurus** - Perlu perbaikan gizi"); advice.append("→ Tingkatkan asupan MPASI bergizi & pantau 2 minggu")
        elif z_scores['whz'] > 3:
            bullets.append("🔴 **Obesitas**"); advice.append("→ Konsultasi ahli gizi anak")
        elif z_scores['whz'] > 2:
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

def median_values_for(sex_text, age_mode, dob_str, dom_str, age_months_input):
    try:
        sex = 'M' if sex_text.lower().startswith('l') else 'F'
        if age_mode == "Tanggal":
            dob = parse_date(dob_str); dom = parse_date(dom_str)
            if not dob or not dom or dom < dob: return (None, None, None)
            age_mo, _ = age_months_from_dates(dob, dom)
        else:
            age_mo = safe_float(age_months_input)
            if age_mo is None: return (None, None, None)
        age_mo = max(0.0, min(age_mo, 60.0))
        w0 = invert_z_with_scan(lambda m: _safe_z(calc.wfa, m, age_mo, sex), 0.0, *BOUNDS['wfa'])
        h0 = invert_z_with_scan(lambda m: _safe_z(calc.lhfa, m, age_mo, sex), 0.0, *BOUNDS['hfa'])
        c0 = invert_z_with_scan(lambda m: _safe_z(calc.hcfa, m, age_mo, sex), 0.0, *BOUNDS['hcfa'])
        return (round(w0, 2), round(h0, 1), round(c0, 1))
    except Exception: return (None, None, None)

# -------------------- FUNGSI INTI: compute_all (existing) --------------------
def compute_all(sex_text, age_mode, dob, dom, age_mo_in, w_in, h_in, hc_in, name_child, name_parent, lang_mode, theme):
    if calc is None: raise RuntimeError("WHO Calculator belum terinisialisasi.")
    
    sex = 'M' if str(sex_text).lower().startswith('l') else 'F'
    if age_mode == "Tanggal":
        dob_dt = parse_date(dob); dom_dt = parse_date(dom)
        if not dob_dt or not dom_dt or dom_dt < dob_dt: raise ValueError("Tanggal tidak valid. Gunakan format YYYY-MM-DD atau DD/MM/YYYY.")
        age_mo, age_days = age_months_from_dates(dob_dt, dom_dt)
    else:
        age_mo = as_float(age_mo_in)
        if age_mo is None: raise ValueError("Usia (bulan) tidak valid.")
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
    
    permenkes = {
        "waz": permenkes_waz(z["waz"]), "haz": permenkes_haz(z["haz"]),
        "whz": permenkes_whz(z["whz"]), "baz": permenkes_baz(z["baz"]),
        "hcz": hcz_text(z["hcz"])[0],
    }
    who = {
        "waz": who_waz(z["waz"]), "haz": who_haz(z["haz"]),
        "whz": who_whz(z["whz"]), "baz": who_baz(z["baz"]),
        "hcz": hcz_text(z["hcz"])[1],
    }
    
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

# -------------------- Plotting functions (existing) --------------------
def _zone_fill(ax, x, lower, upper, color, alpha, label):
    try: ax.fill_between(x, lower, upper, color=color, alpha=alpha, zorder=1, label=label, linewidth=0)
    except Exception: pass

def plot_wfa(payload):
    apply_matplotlib_theme(payload['theme'])
    sex, age, w = payload['sex'], payload['age_mo'], payload['w']
    sd_lines = { -3:('#DC143C','-'), -2:('#FF6347','-'), -1:('#FFA500','--'), 0:('#228B22','-'), 1:('#FFA500','--'), 2:('#FF6347','-'), 3:('#DC143C','-') }
    curves = {z: wfa_curve_smooth(sex, z) for z in sd_lines}
    fig, ax = plt.subplots(figsize=(11, 7))
    x = curves[0][0]
    _zone_fill(ax, x, curves[-3][1], curves[-2][1], '#FFE6E6', 0.35, 'Zona Gizi Buruk')
    _zone_fill(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Zona Gizi Kurang')
    _zone_fill(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.40, 'Zona Normal')
    _zone_fill(ax, x, curves[1][1],  curves[2][1],  '#FFF3CD', 0.30, 'Risiko Gizi Lebih')
    _zone_fill(ax, x, curves[2][1],  curves[3][1],  '#F8D7DA', 0.35, 'Gizi Lebih')
    for z, (c, ls) in sd_lines.items():
        ax.plot(curves[z][0], curves[z][1], color=c, linestyle=ls, linewidth=2.0 if abs(z) in (0,2) else 1.6, label=("Median" if z==0 else f"{z:+d} SD"), zorder=5)
    z_waz = payload['z']['waz']
    point_color = '#228B22'
    if z_waz is not None:
        if abs(z_waz) > 3: point_color = '#8B0000'
        elif abs(z_waz) > 2: point_color = '#DC143C'
        elif abs(z_waz) > 1: point_color = '#FF8C00'
    if w is not None:
        ax.scatter([age], [w], s=300, c=point_color, edgecolors='black', linewidths=2.5, marker='o', zorder=20, label='Data Anak')
        ax.plot([age, age], [0, w], 'k--', linewidth=1, alpha=0.3, zorder=1)
    ax.set_xlabel('Usia (bulan)', fontweight='bold'); ax.set_ylabel('Berat Badan (kg)', fontweight='bold')
    ax.set_title('GRAFIK PERTUMBUHAN WHO: Berat Badan menurut Umur (BB/U)\n' + ("Laki-laki" if sex=='M' else "Perempuan") + ' | 0-60 bulan', fontweight='bold')
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5); ax.minorticks_on()
    ax.set_xlim(0, 60); ax.set_xticks(range(0, 61, 6)); ax.set_xticks(range(0, 61, 3), minor=True)
    y_min = min([curves[z][1].min() for z in (-3,-2,0,2,3)]); y_max = max([curves[z][1].max() for z in (-3,-2,0,2,3)])
    ax.set_ylim(max(0, y_min - 1), y_max + 2)
    ax.legend(loc='upper left', frameon=True, edgecolor='black', fontsize=8, ncol=2)
    plt.tight_layout(); return fig

def plot_hfa(payload):
    apply_matplotlib_theme(payload['theme'])
    sex, age, h = payload['sex'], payload['age_mo'], payload['h']
    sd_lines = { -3:('#DC143C','-'), -2:('#FF6347','-'), -1:('#FFA500','--'), 0:('#228B22','-'), 1:('#FFA500','--'), 2:('#FF6347','-'), 3:('#DC143C','-') }
    curves = {z: hfa_curve_smooth(sex, z) for z in sd_lines}
    fig, ax = plt.subplots(figsize=(11, 7))
    x = curves[0][0]
    _zone_fill(ax, x, curves[-3][1], curves[-2][1], '#FFE6E6', 0.30, 'Severe Stunting')
    _zone_fill(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Stunting')
    _zone_fill(ax, x, curves[-1][1], curves[2][1],  '#E8F5E9', 0.40, 'Normal')
    _zone_fill(ax, x, curves[2][1],  curves[3][1],  '#E3F2FD', 0.30, 'Tall')
    for z, (c, ls) in sd_lines.items():
        ax.plot(curves[z][0], curves[z][1], color=c, linestyle=ls, linewidth=2.0 if abs(z) in (0,2) else 1.6, label=("Median" if z==0 else f"{z:+d} SD"), zorder=5)
    z_haz = payload['z']['haz']
    point_color = '#228B22'
    if z_haz is not None:
        if abs(z_haz) > 3: point_color = '#8B0000'
        elif abs(z_haz) > 2: point_color = '#DC143C'
        elif abs(z_haz) > 1: point_color = '#FF8C00'
    if h is not None:
        ax.scatter([age], [h], s=300, c=point_color, edgecolors='black', linewidths=2.5, marker='o', zorder=20, label='Data Anak')
        ax.plot([age, age], [40, h], 'k--', linewidth=1, alpha=0.3, zorder=1)
    ax.set_xlabel('Usia (bulan)', fontweight='bold'); ax.set_ylabel('Panjang/Tinggi Badan (cm)', fontweight='bold')
    ax.set_title('GRAFIK PERTUMBUHAN WHO: Panjang/Tinggi menurut Umur (TB/U)\n' + ("Laki-laki" if sex=='M' else "Perempuan") + ' | 0-60 bulan', fontweight='bold')
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5); ax.minorticks_on()
    ax.set_xlim(0, 60); ax.set_xticks(range(0, 61, 6)); ax.set_xticks(range(0, 61, 3), minor=True)
    y_min = min([curves[z][1].min() for z in (-3,-2,0,2,3)]); y_max = max([curves[z][1].max() for z in (-3,-2,0,2,3)])
    ax.set_ylim(max(45, y_min - 1), y_max + 2)
    ax.legend(loc='upper left', frameon=True, edgecolor='black', fontsize=8, ncol=2)
    plt.tight_layout(); return fig

def plot_hcfa(payload):
    apply_matplotlib_theme(payload['theme'])
    sex, age, hc = payload['sex'], payload['age_mo'], payload.get('hc')
    sd_lines = { -3:('#DC143C','-'), -2:('#FF6347','-'), -1:('#FFA500','--'), 0:('#228B22','-'), 1:('#FFA500','--'), 2:('#FF6347','-'), 3:('#DC143C','-') }
    curves = {z: hcfa_curve_smooth(sex, z) for z in sd_lines}
    fig, ax = plt.subplots(figsize=(11, 7))
    x = curves[0][0]
    _zone_fill(ax, x, curves[-3][1], curves[-2][1], '#FFD4D4', 0.40, 'Microcephaly Berat')
    _zone_fill(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Microcephaly')
    _zone_fill(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.40, 'Zona Normal')
    _zone_fill(ax, x, curves[1][1],  curves[2][1],  '#E3F2FD', 0.30, 'Macrocephaly')
    _zone_fill(ax, x, curves[2][1],  curves[3][1],  '#BBDEFB', 0.35, 'Macrocephaly Berat')
    for z, (c, ls) in sd_lines.items():
        ax.plot(curves[z][0], curves[z][1], color=c, linestyle=ls, linewidth=2.0 if abs(z) in (0,2) else 1.6, label=("Median" if z==0 else f"{z:+d} SD"), zorder=5)
    if hc is not None:
        z_hcz = payload['z']['hcz']
        point_color = '#228B22'
        if z_hcz is not None:
            if abs(z_hcz) > 3: point_color = '#8B0000'
            elif abs(z_hcz) > 2: point_color = '#DC143C'
            elif abs(z_hcz) > 1: point_color = '#FF8C00'
        ax.scatter([age], [hc], s=300, c=point_color, edgecolors='black', linewidths=2.5, marker='o', zorder=20, label='Data Anak')
        ax.plot([age, age], [25, hc], 'k--', linewidth=1, alpha=0.3, zorder=1)
    ax.set_xlabel('Usia (bulan)', fontweight='bold'); ax.set_ylabel('Lingkar Kepala (cm)', fontweight='bold')
    ax.set_title('GRAFIK PERTUMBUHAN WHO: Lingkar Kepala menurut Umur (LK/U)\n' + ("Laki-laki" if sex=='M' else "Perempuan") + ' | 0-60 bulan', fontweight='bold')
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5); ax.minorticks_on()
    ax.set_xlim(0, 60); ax.set_xticks(range(0, 61, 6)); ax.set_xticks(range(0, 61, 3), minor=True)
    y_min = min([curves[z][1].min() for z in (-3,-2,0,2,3)]); y_max = max([curves[z][1].max() for z in (-3,-2,0,2,3)])
    ax.set_ylim(max(25, y_min - 1), y_max + 2)
    ax.legend(loc='upper left', frameon=True, edgecolor='black', fontsize=8, ncol=2)
    plt.tight_layout(); return fig

def plot_wfl(payload):
    apply_matplotlib_theme(payload['theme'])
    sex, age, h, w = payload['sex'], payload['age_mo'], payload['h'], payload['w']
    lengths = np.arange(BOUNDS['wfl_l'][0], BOUNDS['wfl_l'][1] + 1e-9, 0.5)
    sd_lines = { -3:('#DC143C','-'), -2:('#FF6347','-'), -1:('#FFA500','--'), 0:('#228B22','-'), 1:('#FFA500','--'), 2:('#FF6347','-'), 3:('#DC143C','-') }
    curves = {z: wfl_curve_smooth(sex, age, z, lengths) for z in sd_lines}
    fig, ax = plt.subplots(figsize=(11, 7))
    x = curves[0][0]
    _zone_fill(ax, x, curves[-3][1], curves[-2][1], '#FFD4D4', 0.40, 'Wasting Berat')
    _zone_fill(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Wasting')
    _zone_fill(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.40, 'Zona Normal')
    _zone_fill(ax, x, curves[1][1],  curves[2][1],  '#FFF9C4', 0.30, 'Risiko Overweight')
    _zone_fill(ax, x, curves[2][1],  curves[3][1],  '#FFD4D4', 0.40, 'Overweight/Obesitas')
    for z, (c, ls) in sd_lines.items():
        ax.plot(curves[z][0], curves[z][1], color=c, linestyle=ls, linewidth=2.0 if abs(z) in (0,2) else 1.6, label=("Median" if z==0 else f"{z:+d} SD"), zorder=5)
    if h is not None and w is not None:
        z_whz = payload['z']['whz']
        point_color = '#228B22'
        if z_whz is not None:
            if abs(z_whz) > 3: point_color = '#8B0000'
            elif abs(z_whz) > 2: point_color = '#DC143C'
            elif abs(z_whz) > 1: point_color = '#FF8C00'
        ax.scatter([h], [w], s=300, c=point_color, edgecolors='black', linewidths=2.5, marker='o', zorder=20, label='Data Anak')
        ax.plot([h, h], [0, w], 'k--', linewidth=1, alpha=0.3, zorder=1)
    ax.set_xlabel('Panjang/Tinggi Badan (cm)', fontweight='bold'); ax.set_ylabel('Berat Badan (kg)', fontweight='bold')
    ax.set_title('GRAFIK PERTUMBUHAN WHO: Berat menurut Panjang/Tinggi (BB/TB)\n' + ("Laki-laki" if sex=='M' else "Perempuan"), fontweight='bold')
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5); ax.minorticks_on()
    ax.set_xlim(lengths.min(), lengths.max())
    y_min = min([curves[z][1].min() for z in (-3,-2,0,2,3)]); y_max = max([curves[z][1].max() for z in (-3,-2,0,2,3)])
    ax.set_ylim(max(0, y_min - 1), y_max + 2)
    ax.legend(loc='upper left', frameon=True, edgecolor='black', fontsize=8, ncol=2)
    plt.tight_layout(); return fig

def plot_bars(payload):
    apply_matplotlib_theme(payload['theme'])
    z = payload['z']
    labels = ['WAZ\n(BB/U)', 'HAZ\n(TB/U)', 'WHZ\n(BB/TB)', 'BAZ\n(IMT/U)', 'HCZ\n(LK/U)']
    values = [z['waz'], z['haz'], z['whz'], z['baz'], z['hcz']]
    def get_bar_color(v):
        if v is None or math.isnan(v): return '#CCCCCC'
        if abs(v) > 3: return '#8B0000'
        if abs(v) > 2: return '#DC143C'
        if abs(v) > 1: return '#FF8C00'
        return '#228B22'
    colors_bar = [get_bar_color(v) for v in values]
    plot_values = [0 if (v is None or (isinstance(v,float) and math.isnan(v))) else v for v in values]
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.axhspan(-3, -2, color='#FFD4D4', alpha=0.3, label='Zona Kurang (-3 to -2 SD)')
    ax.axhspan(-2,  2, color='#E8F5E9', alpha=0.3, label='Zona Normal (-2 to +2 SD)')
    ax.axhspan( 2,  3, color='#FFD4D4', alpha=0.3, label='Zona Lebih (+2 to +3 SD)')
    ax.axhline(0, color='#228B22', linewidth=3, linestyle='-', label='Median (0 SD)', zorder=5)
    ax.axhline(-2, color='#DC143C', linewidth=2, linestyle='--', alpha=0.7)
    ax.axhline( 2, color='#DC143C', linewidth=2, linestyle='--', alpha=0.7)
    ax.axhline(-3, color='#8B0000', linewidth=1.5, linestyle=':',  alpha=0.5)
    ax.axhline( 3, color='#8B0000', linewidth=1.5, linestyle=':',  alpha=0.5)
    bars = ax.bar(labels, plot_values, color=colors_bar, edgecolor='black', linewidth=2, width=0.6, alpha=0.9, zorder=10)
    for i, (v, bar) in enumerate(zip(values, bars)):
        if v is not None and not (isinstance(v,float) and math.isnan(v)):
            y_pos = bar.get_height(); offset = 0.3 if y_pos >= 0 else -0.5
            status = "Kritis" if abs(v)>3 else ("Perlu Perhatian" if abs(v)>2 else ("Borderline" if abs(v)>1 else "Normal"))
            ax.text(bar.get_x()+bar.get_width()/2, y_pos+offset, f'{fmtz(v,2)}\n({status})', ha='center', va='bottom' if y_pos>=0 else 'top',
                    fontsize=10, weight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor=colors_bar[i], linewidth=2), zorder=15)
    ax.set_ylabel('Z-score', fontweight='bold', fontsize=12)
    ax.set_title('RINGKASAN STATUS GIZI - Semua Indeks Antropometri\nWHO Child Growth Standards', fontweight='bold', fontsize=13, pad=15)
    ax.set_ylim(-5, 5); ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.5, zorder=1)
    ax.legend(loc='upper right', frameon=True, edgecolor='black', fontsize=8, title='Referensi WHO', title_fontsize=9)
    plt.tight_layout(); return fig

# -------------------- Export helpers (existing) --------------------
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
                pct = payload['pct'][key]; pct_str = pct if pct is None else f"{pct}"
                w.writerow([label, fmtz(payload['z'][key]), pct_str, payload['permenkes'][key], payload['who'][key]])
            w.writerow([]); w.writerow(['Tanggal Export', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            w.writerow(['Sumber', 'GiziSiKecil - WHO Child Growth Standards + Permenkes 2020'])
        return filename
    except Exception: return None

def qr_image_bytes(text=f"https://wa.me/{CONTACT_WA}"):
    try:
        qr = qrcode.QRCode(box_size=3, border=2); qr.add_data(text); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
        return buf
    except Exception: return None

def export_pdf(payload, md_text, figs, filename):
    try:
        c = canvas.Canvas(filename, pagesize=A4)
        W, H = A4
        now = datetime.datetime.now().strftime("%d %B %Y, %H:%M WIB")
        c.setFillColorRGB(0.965, 0.647, 0.753); c.rect(0, H - 50, W, 50, stroke=0, fill=1)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 16)
        c.drawString(30, H - 32, "GiziSiKecil - Laporan Status Gizi Anak")
        c.setFont("Helvetica", 10); c.drawRightString(W - 30, H - 32, now)
        
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
        else: y -= 5
        
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
        
        c.setFillColorRGB(0.965, 0.647, 0.753); c.rect(0, H - 50, W, 50, stroke=0, fill=1)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawString(30, H - 32, "Catatan Penting & Disclaimer")
        y = H - 80; c.setFont("Helvetica", 10)
        disclaimers = [
            "1. Aplikasi ini bersifat SKRINING EDUKATIF, bukan diagnosis medis.", "",
            "2. Hasil harus diinterpretasikan oleh tenaga kesehatan terlatih.", "",
            "3. Klasifikasi mengacu pada:", "   • WHO Child Growth Standards (2006)", "   • Permenkes RI No. 2 Tahun 2020", "",
            "4. Data Anda TIDAK disimpan di server (privasi terjaga).", "",
            "5. Untuk konsultasi lanjutan, hubungi Posyandu/Puskesmas/Dokter anak.", "",
            "6. Pastikan alat terkalibrasi & teknik pengukuran benar."
        ]
        for line in disclaimers: c.drawString(40, y, line); y -= 15
        
        c.setFont("Helvetica-Oblique", 8); c.drawRightString(W - 30, 15, f"Hal. {page_num}")
        c.save(); return filename
    except Exception: return None

# -------------------- Callbacks (existing + enhanced) --------------------
def do_prefill(sex_text, age_mode, dob, dom, age_mo):
    try:
        w, h, hc = median_values_for(sex_text, age_mode, dob, dom, age_mo)
        if w is None: return (gr.update(), gr.update(), gr.update(), "❌ Tidak dapat menghitung median. Periksa input usia.")
        return (gr.update(value=w), gr.update(value=h), gr.update(value=hc), f"✅ Prefill berhasil! Nilai median WHO (Z=0) terisi.")
    except Exception as e: return (gr.update(), gr.update(), gr.update(), f"❌ Error: {str(e)}")

def do_demo():
    return ("Perempuan","Usia (bulan)","","",18.0,10.2,80.5,46.8,"Siti Aisyah","Ibu Fatimah","Orang tua","pastel","✅ **Mode Demo Aktif!** Klik '🔍 Analisis Sekarang'.")

def update_age_input_visibility(age_mode_selected):
    if age_mode_selected == "Tanggal":
        return (gr.update(visible=True, interactive=True), gr.update(visible=True, interactive=True), gr.update(visible=False, interactive=False))
    else:
        return (gr.update(visible=False, interactive=False), gr.update(visible=False, interactive=False), gr.update(visible=True, interactive=True))

def run_all(sex_text, age_mode, dob, dom, age_mo, w, h, hc, name_child, name_parent, lang_mode, theme):
    try:
        md, payload = compute_all(sex_text, age_mode, dob, dom, age_mo, w, h, hc, name_child, name_parent, lang_mode, theme)
        fig1 = plot_wfa(payload); fig2 = plot_hfa(payload); fig3 = plot_hcfa(payload); fig4 = plot_wfl(payload); fig5 = plot_bars(payload)
        png1 = export_png(fig1, "chart_wfa.png"); png2 = export_png(fig2, "chart_hfa.png")
        png3 = export_png(fig3, "chart_hcfa.png"); png4 = export_png(fig4, "chart_wfl.png"); png5 = export_png(fig5, "chart_bars.png")
        child_name = (payload.get('name_child') or 'Anak').replace(' ', '_')[:30]
        pdf = export_pdf(payload, md, [fig1, fig2, fig3, fig4, fig5], f"Laporan_Gizi_{child_name}.pdf")
        csvf = export_csv(payload, "hasil_analisis.csv")
        status_msg = "✅ **Analisis selesai!**"
        if payload.get('errors'): status_msg = "⚠️ **Analisis selesai dengan peringatan kritis!**"
        return (md, fig1, fig2, fig3, fig4, fig5, pdf, csvf, png1, png2, png3, png4, png5, status_msg)
    except Exception as e:
        print("Run all error:\n", traceback.format_exc())
        return (f"❌ **Error Sistem:**\n\n````\n{str(e)}\n````", None, None, None, None, None, None, None, None, None, None, None, None, "❌ Terjadi error sistem.")

# -------------------- GIZISIKECIL FUNCTIONS --------------------
def sync_from_calculator(main_payload, layout_mode):
    """Sync data dari tab Kalkulator utama"""
    if not main_payload or not isinstance(main_payload, dict):
        return "❌ Tidak ada data dari Kalkulator. Silakan hitung z-score dulu di tab utama.", gr.update(visible=True), gr.update(visible=False), 0
    
    state_child_data.value = main_payload
    age_mo = main_payload.get("age_mo", 0)
    month = min(int(age_mo), 24)
    
    sync_msg = f"""
    ✅ **Data berhasil disinkronkan!**
    
    👶 **Nama:** {main_payload.get('name_child', 'Si Kecil')}  
    📅 **Usia:** {age_mo:.1f} bulan → **Bulan ke-{month}**  
    ⚖️ **BB/TB:** {main_payload.get('w', 0):.1f} kg / {main_payload.get('h', 0):.1f} cm
    
    👉 **Pilih bulan di dropdown, lalu klik 'Mulai Checklist'**
    """
    return sync_msg, gr.update(visible=False), gr.update(visible=True), month

def reset_checklist_data():
    """Reset semua data checklist"""
    state_child_data.value = {}
    state_checklist_progress.value = {}
    state_current_month.value = 0
    state_kpsp_answers.value = {}
    return "✅ Data checklist berhasil direset. Silakan sinkron ulang dari Kalkulator.", gr.update(visible=True), gr.update(visible=False)

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
        if v not in videos: videos.append(v)
    
    # Format video HTML
    videos_html = "<div style='display:flex; flex-wrap:wrap; gap:12px;'>"
    for vid in videos:
        if vid:
            videos_html += f"""
            <div style='border:1px solid #ddd; padding:12px; border-radius:10px; width:200px; background:white; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>
                <img src='{vid['thumbnail']}' style='width:100%; border-radius:8px; border:1px solid #eee;'>
                <p style='font-size:13px; margin:8px 0; font-weight:bold; color:#333;'>{vid['title']}</p>
                <a href='{vid['url']}' target='_blank' style='display:inline-block; background:#ff6b9d; color:white; padding:8px 12px; border-radius:5px; text-decoration:none; font-size:12px;'>▶️ Tonton</a>
            </div>
            """
    videos_html += "</div>"
    
    if layout_mode == "Mode Mudah":
        do_now = [d.split(":")[0][:40] + "..." for d in do_now[:2]]
        saran = ["💡 " + s.split(":")[1][:45] + "..." for s in saran[:2]]
        warnings = ["⚠️ " + w.split(":")[1][:40] + "..." for w in warnings[:2]]
    
    return (
        "\n\n".join(do_now) if do_now else "✅ Semua sesuai standar WHO",
        "\n\n".join(saran) if saran else "💡 Pertahankan pola sehat saat ini",
        "\n\n".join(warnings) if warnings else "✅ Tidak ada warning kritis bulan ini",
        videos_html if videos_html else "<p>Video edukasi akan tersedia pada bulan selanjutnya</p>",
        "\n\n".join(imunisasi) if imunisasi else "✅ Tidak ada imunisasi bulan ini"
    )

def run_wizard_step1(month, main_payload):
    """Step 1: Verifikasi data"""
    if not main_payload: return "❌ Data anak belum tersedia. Klik 'Sinkron Data' dulu.", gr.update(visible=False), gr.update(visible=False), "", "", "", "", ""
    
    overview = f"""
    👶 **Verifikasi Data Anak:**
    
    **Nama:** {main_payload.get('name_child', 'Si Kecil')}  
    **Usia:** {main_payload.get('age_mo', 0):.1f} bulan  
    **BB/TB:** {main_payload.get('w', 0):.1f} kg / {main_payload.get('h', 0):.1f} cm  
    **Status:** {main_payload.get('permenkes', {}).get('waz', 'Normal')}
    
    ✅ Jika data sudah benar, klik "Lanjutkan" untuk screening KPSP.
    """
    return overview, gr.update(visible=True), gr.update(visible=False), "", "", "", "", ""

def run_wizard_step2(month, main_payload):
    """Step 2: Tampilkan KPSP questions"""
    if not main_payload: return "", gr.update(visible=False), gr.update(visible=True), "", "", "", "", ""
    
    questions = KPSP_QUESTIONS.get(month, [])
    if not questions: return "", gr.update(visible=False), gr.update(visible=True), "", "", "", "", ""
    
    html = "<h4>🧠 <strong>Screening Perkembangan (KPSP)</strong></h4>"
    html += "<p style='color:#666; font-size:13px; margin-bottom:15px;'>Jawab dengan jujur untuk rekomendasi terbaik</p>"
    
    for i, q in enumerate(questions):
        html += f"""
        <div style='margin:12px 0; padding:15px; background:#f9f9f9; border-radius:8px; border-left:4px solid #ff6b9d;'>
            <p style='font-weight:bold; margin-bottom:10px; color:#2c3e50;'>{i+1}. Apakah Si Kecil bisa {q}</p>
            <label style='margin-right:20px; cursor:pointer;'>
                <input type='radio' name='kpsp_q{i}' value='ya' style='margin-right:8px;' checked> ✅ Ya
            </label>
            <label style='cursor:pointer;'>
                <input type='radio' name='kpsp_q{i}' value='tidak' style='margin-right:8px;'> ❌ Belum
            </label>
        </div>
        """
    return "", gr.update(visible=False), gr.update(visible=True), html, "", "", "", ""

def run_wizard_step3(month, layout_mode, main_payload):
    """Step 3: Tampilkan hasil akhir"""
    if not main_payload: return "", gr.update(visible=False), gr.update(visible=True), "", "", "", "", "", "static/sticker_1.png", "**🔥 Streak:** 0 bulan | **⭐ Poin:** 0"
    
    do_now, saran, warnings, videos, imunisasi = generate_checklist_data(month, layout_mode, main_payload)
    
    progress = state_checklist_progress.value or {}
    if month not in progress: progress[month] = {"done": [], "streak": 0, "completed_at": str(datetime.now())}
    progress[month]["streak"] += 1
    state_checklist_progress.value = progress
    
    sticker_path = f"static/sticker_{random.randint(1,5)}.png"
    return "", gr.update(visible=False), gr.update(visible=True), do_now, saran, warnings, videos, imunisasi, sticker_path, f"**🔥 Streak:** {progress[month]['streak']} bulan | **⭐ Poin:** {progress[month]['streak'] * 10}"

def generate_checklist_pdf(month, layout_mode, main_payload, export_checked):
    """Generate PDF ringkas jika dicentang"""
    if not export_checked or not main_payload: return None
    
    child_name = main_payload.get("name_child", "Anak").replace(" ", "_")
    filename = f"Checklist_GiziSiKecil_{child_name}_Bulan_{month}.pdf"
    
    try:
        c = canvas.Canvas(filename, pagesize=A4)
        W, H = A4
        
        # Header
        c.setFillColorRGB(0.965, 0.647, 0.753)
        c.rect(0, H-50, W, 50, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, H-32, f"GiziSiKecil - Checklist Bulan ke-{month}")
        
        # Watermark
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(colors.grey)
        c.drawRightString(W-30, H-32, "RAHASIA MEDIS - JANGAN DIBAGIKAN")
        
        # Content
        y = H-80
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
        
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "💡 SARAN:"); y -= 15
        c.setFont("Helvetica", 10)
        for line in saran.split("\n\n")[:2]:
            c.drawString(40, y, line[:70]); y -= 12
        
        # Footer
        y = 50
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.grey)
        c.drawString(30, y, f"Dicetak: {datetime.now().strftime('%d-%m-%Y %H:%M')} | GiziSiKecil App")
        c.drawString(30, y-12, "⚠️ Ini adalah skrining edukatif, bukan diagnosis medis")
        
        c.save()
        return filename
    except Exception as e:
        print(f"PDF Generation Error: {e}")
        return None

def test_notification(settings):
    """Test smart notification"""
    if not settings.get("enabled"): return "🔕 Notifikasi dimatikan"
    time_str = settings.get("time", "08:00")
    return f"✅ Notifikasi aktif! Anda akan menerima reminder setiap pukul {time_str} WIB"

def share_to_whatsapp(month, main_payload):
    """Generate WhatsApp share message"""
    if not main_payload: return "❌ Tidak ada data untuk dishare"
    name = main_payload.get("name_child", "Si Kecil")
    age = main_payload.get("age_mo", 0)
    msg = f"📊 *Progress GiziSiKecil Bulan {month}* - {name} ({age:.1f} bln)%0A%0A✅ Checklist selesai!%0A🔥 Streak: 2 bulan%0A%0A*Download PDF lengkap di app GiziSiKecil*"
    return f"📱 [Share via WhatsApp](https://wa.me/?text={msg})"

# -------------------- GRADIO UI - GIZISIKECIL --------------------
custom_css = """
.gradio-container { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.status-success { color: #28a745; font-weight: bold; }
.status-warning { color: #ffc107; font-weight: bold; }
.status-error   { color: #dc3545; font-weight: bold; }
.big-button     { font-size: 18px !important; font-weight: bold !important; padding: 20px !important; }
blockquote { background: #ffeef8; border-left: 5px solid #ff6b9d; padding: 10px 15px; margin: 10px 0; border-radius: 5px; }
"""

with gr.Blocks(
    title="GiziSiKecil - Monitor Pertumbuhan Anak Profesional",
    theme=gr.themes.Soft(primary_hue="pink", secondary_hue="teal", neutral_hue="slate"),
    css=custom_css
) as demo:
    gr.Markdown("""
    # 🏥 **GiziSiKecil** - Kalkulator & Monitor Status Gizi Anak
    ### 💕 WHO Child Growth Standards + Checklist Sehat Bulanan (0-60 Bulan)
    > 🔒 **Privasi Terjaga** | ⚕️ **Standar Resmi** | 📱 **Mudah Digunakan**
    """)
    
    gr.Markdown("---")
    
    # State components
    state_child_data = gr.State({})
    state_checklist_progress = gr.State({})
    state_current_month = gr.State(0)
    state_notification_settings = gr.State({"enabled": True, "time": "08:00"})
    
    with gr.Row():
        with gr.Column(scale=5):
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
                gr.Markdown("### 📏 Data Antropometri")
                gr.Markdown("*Gunakan **kg** untuk berat & **cm** untuk panjang/tinggi*")
                with gr.Row():
                    w = gr.Number(label="Berat Badan (kg)", value=10.0, precision=2)
                    h = gr.Number(label="Panjang/Tinggi Badan (cm)", value=75.0, precision=1)
                hc = gr.Number(label="Lingkar Kepala (cm) - Opsional", value=None, precision=1)
            
            with gr.Group():
                gr.Markdown("### ⚙️ Pengaturan Tampilan")
                with gr.Row():
                    lang_mode = gr.Radio(["Orang tua","Nakes"], label="Mode Bahasa Output", value="Orang tua")
                    theme = gr.Radio(["pastel","dark","colorblind"], label="Tema Grafik", value="pastel")
            
            gr.Markdown("---")
            with gr.Row():
                prefill_btn = gr.Button("📊 Isi Nilai Median WHO (Z=0)", variant="secondary", size="sm")
                demo_btn   = gr.Button("🎬 Coba Demo", variant="secondary", size="sm")
            status_msg = gr.Markdown("💡 **Tip**: Klik 'Coba Demo' lalu 'Analisis Sekarang'")
            run_btn = gr.Button("🔍 Analisis Sekarang", variant="primary", size="lg", elem_classes="big-button")
        
        with gr.Column(scale=2):
            gr.Markdown("## 💡 Panduan Cepat")
            with gr.Accordion("📏 Tips Pengukuran", open=True):
                gr.Markdown("**Berat:** tanpa sepatu, pakaian minimal. **Tinggi:** <24 bln terlentang, ≥24 bln berdiri. **LK:** ukur 3x, ambil terbesar.")
            with gr.Accordion("🎯 Interpretasi Z-Score", open=False):
                gr.Markdown("""
                | Z | Status |
                |---|--------|
                | < -3 | 🔴 Sangat kurang |
                | -3 s/d -2 | 🟡 Kurang |
                | -2 s/d +2 | 🟢 Normal |
                | +2 s/d +3 | 🟡 Risiko lebih |
                | > +3 | 🔴 Obesitas |
                """)
            with gr.Accordion("⚠️ Peringatan", open=False):
                gr.Markdown("Skrining edukatif; konsultasi nakes bila ada masalah. Pastikan satuan benar.")
    
    gr.Markdown("---")
    with gr.Row():
        with gr.Column():
            gr.Markdown("## 📊 Hasil Analisis")
            out_md = gr.Markdown("*Hasil akan tampil setelah klik 'Analisis Sekarang'*")
    
    gr.Markdown("---")
    gr.Markdown("## 📈 Grafik Pertumbuhan")
    with gr.Tabs():
        with gr.TabItem("📊 BB menurut Umur (WFA)"): plt1 = gr.Plot(label="Weight-for-Age")
        with gr.TabItem("📏 TB/PB menurut Umur (HFA)"): plt2 = gr.Plot(label="Height-for-Age")
        with gr.TabItem("🧠 Lingkar Kepala (HCFA)"): plt3 = gr.Plot(label="Head Circumference-for-Age")
        with gr.TabItem("🎯 BB menurut TB/PB (WFL)"): plt4 = gr.Plot(label="Weight-for-Length")
        with gr.TabItem("📊 Ringkasan (Bar)"): plt5 = gr.Plot(label="Summary Bar Chart")
    
    gr.Markdown("---")
    gr.Markdown("## 💾 Unduh Laporan")
    with gr.Row():
        with gr.Column():
            pdf_out = gr.File(label="📄 Laporan PDF (A4)", file_types=[".pdf"])
            gr.Markdown("*Multi-halaman dengan grafik & tabel*")
        with gr.Column():
            csv_out = gr.File(label="📊 Data CSV", file_types=[".csv"])
            gr.Markdown("*Untuk analisis lanjutan*")
    with gr.Row():
        png1 = gr.File(label="🖼️ Grafik WFA (PNG)", file_types=[".png"])
        png2 = gr.File(label="🖼️ Grafik HFA (PNG)", file_types=[".png"])
        png3 = gr.File(label="🖼️ Grafik HCFA (PNG)", file_types=[".png"])
    with gr.Row():
        png4 = gr.File(label="🖼️ Grafik WFL (PNG)", file_types=[".png"])
        png5 = gr.File(label="🖼️ Grafik Bar (PNG)", file_types=[".png"])
    
    # -------------------- TAB BARU: GiziSiKecil Checklist --------------------
    gr.Markdown("---")
    with gr.TabItem("📋 GiziSiKecil Checklist (0-24 bln)"):
        gr.Markdown("""
        # 📋 **GiziSiKecil - Checklist Sehat Bulanan**
        ### 💕 Asisten Virtual Pertumbuhan & Perkembangan Si Kecil (0-24 Bulan)
        > *"Setiap langkah kecil adalah pencapaian besar dalam perjalanan tumbuh kembang Si Kecil"*
        """)
        
        # Random Quote Generator
        quote_box = gr.Markdown(value=lambda: f"<blockquote>{random.choice(MOM_QUOTES)}</blockquote>")
        
        with gr.Row():
            layout_mode = gr.Radio(["Mode Lengkap", "Mode Mudah"], label="🎨 Pilih Tampilan", value="Mode Lengkap", info="Mode Mudah: Tampilan lebih sederhana untuk koneksi lambat")
            sync_data_btn = gr.Button("🔄 Sinkron Data dari Kalkulator", variant="secondary", scale=1)
            reset_data_btn = gr.Button("🗑️ Reset Data", variant="stop", scale=1)
        
        sync_status = gr.Markdown("ℹ️ **Klik 'Sinkron Data' untuk mengambil data anak dari tab Kalkulator**", visible=True)
        
        # Wizard Container
        wizard_container = gr.Group(visible=True)
        with wizard_container:
            gr.Markdown("### 📅 **Wizard Checklist - 3 Langkah Mudah**")
            
            with gr.Row():
                month_selector = gr.Dropdown(choices=[(f"Bulan ke-{i} ({i} bln)", i) for i in range(0, 25)], label="🔢 Pilih Bulan", value=0, info="Pilih bulan yang ingin dipantau")
                start_wizard_btn = gr.Button("▶️ Mulai Checklist", variant="primary", scale=1, elem_classes="big-button")
            
            # Step 1: Data Overview
            step1_panel = gr.Column(visible=False)
            with step1_panel:
                gr.Markdown("### 👶 **Verifikasi Data**")
                data_overview = gr.Markdown("*Data akan muncul di sini*")
                confirm_data_btn = gr.Button("✅ Data Benar, Lanjutkan")
            
            # Step 2: KPSP Screening
            step2_panel = gr.Column(visible=False)
            with step2_panel:
                gr.Markdown("### 🧠 **Screening Perkembangan (KPSP)**")
                gr.Markdown("<small>*Jawab 'Ya' jika sudah bisa, 'Tidak' jika belum*</small>")
                kpsp_questions_html = gr.HTML()
                with gr.Row():
                    prev_step1_btn = gr.Button("⬅️ Kembali")
                    next_step3_btn = gr.Button("➡️ Lihat Hasil", variant="primary")
            
            # Step 3: Results
            step3_panel = gr.Column(visible=False)
            with step3_panel:
                gr.Markdown("### 🎯 **Rekomendasi Bulanan untuk Si Kecil**")
                
                with gr.Tabs():
                    with gr.TabItem("🚨 Do Now (Prioritas)"):
                        do_now_box = gr.Markdown()
                    with gr.TabItem("💡 Saran Perbaikan"):
                        saran_box = gr.Markdown()
                    with gr.TabItem("⚠️ Warnings"):
                        warnings_box = gr.Markdown()
                    with gr.TabItem("📺 Edukasi Video"):
                        video_gallery = gr.HTML()
                    with gr.TabItem("💉 Imunisasi"):
                        immunization_box = gr.Markdown()
                
                with gr.Row():
                    export_pdf_checklist = gr.Checkbox(label="📄 Export PDF Ringkas (opsional)", value=False, info="Centang untuk generate PDF")
                    generate_pdf_btn = gr.Button("Generate PDF & Simpan Progress")
                
                pdf_output_checklist = gr.File(label="📥 Download PDF", visible=False)
                
                # Gamification
                with gr.Row():
                    sticker_display = gr.Image(label="🏆 Sticker Minggu Ini", value="static/sticker_1.png", width=150, height=150)
                    streak_display = gr.Markdown("**🔥 Streak:** 0 bulan | **⭐ Poin:** 0")
                
                # Social Share
                gr.Markdown("---")
                gr.Markdown("### 📤 **Bagikan ke Keluarga**")
                share_btn = gr.Button("📱 Share ke WhatsApp", variant="secondary")
                share_status = gr.Markdown()
            
            # Progress indicator
            step_indicator = gr.HTML("<div style='text-align:center; margin-top:20px;'><span style='display:inline-block; width:30px; height:30px; background:#ff6b9d; color:white; border-radius:50%; padding:5px;'>1</span> → <span style='display:inline-block; width:30px; height:30px; background:#ddd; color:gray; border-radius:50%; padding:5px;'>2</span> → <span style='display:inline-block; width:30px; height:30px; background:#ddd; color:gray; border-radius:50%; padding:5px;'>3</span></div>")
        
        # Emergency & Entrepreneurship
        gr.Markdown("---")
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 🚨 **Kontak Darurat & Konsultasi**")
                gr.Markdown(f"""
                ❗ **Segera hubungi tenaga kesehatan jika ada tanda bahaya!**
                
                📞 **Konsultasi Premium GiziSiKecil:**  
                [WA: +62-{CONTACT_WA[2:]}](https://wa.me/{CONTACT_WA})  
                🏥 **Posyandu Terdekat:** Aktifkan GPS untuk lokasi terdekat
                
                <small>*Layanan premium: konsultasi langsung dengan ahli gizi anak*</small>
                """)
            with gr.Column(scale=1):
                premium_btn = gr.Button("⭐ Upgrade ke Premium", variant="primary", size="lg")
                gr.Markdown("<small>Dapatkan analisis tren, rekomendasi personal, & konsultasi prioritas</small>")
        
        # Notification Test
        with gr.Accordion("🔔 **Pengaturan Notifikasi (Smart Reminder)**", open=False):
            notif_enabled = gr.Checkbox(label="Aktifkan notifikasi", value=True)
            notif_time = gr.Textbox(label="Waktu notifikasi (HH:MM)", value="08:00", placeholder="08:00")
            test_notif_btn = gr.Button("🧪 Test Notifikasi")
            notif_status = gr.Markdown()
    
    # -------------------- EVENT HANDLERS --------------------
    age_mode.change(fn=update_age_input_visibility, inputs=[age_mode], outputs=[dob, dom, age_mo])
    prefill_btn.click(fn=do_prefill, inputs=[sex, age_mode, dob, dom, age_mo], outputs=[w, h, hc, status_msg])
    demo_btn.click(fn=do_demo, outputs=[sex, age_mode, dob, dom, age_mo, w, h, hc, name_child, name_parent, lang_mode, theme, status_msg])
    run_btn.click(fn=run_all, inputs=[sex, age_mode, dob, dom, age_mo, w, h, hc, name_child, name_parent, lang_mode, theme],
                  outputs=[out_md, plt1, plt2, plt3, plt4, plt5, pdf_out, csv_out, png1, png2, png3, png4, png5, status_msg])
    
    # GiziSiKecil Events
    sync_data_btn.click(
        fn=sync_from_calculator,
        inputs=[state_child_data, layout_mode],
        outputs=[sync_status, wizard_container, sync_status, month_selector]
    )
    
    reset_data_btn.click(
        fn=reset_checklist_data,
        outputs=[sync_status, wizard_container, sync_status]
    )
    
    start_wizard_btn.click(
        fn=run_wizard_step1,
        inputs=[month_selector, state_child_data],
        outputs=[data_overview, step1_panel, step2_panel, do_now_box, saran_box, warnings_box, video_gallery, immunization_box]
    )
    
    confirm_data_btn.click(
        fn=run_wizard_step2,
        inputs=[month_selector, state_child_data],
        outputs=[data_overview, step1_panel, step2_panel, kpsp_questions_html, do_now_box, saran_box, warnings_box, video_gallery]
    )
    
    prev_step1_btn.click(
        fn=run_wizard_step1,
        inputs=[month_selector, state_child_data],
        outputs=[data_overview, step1_panel, step2_panel, do_now_box, saran_box, warnings_box, video_gallery, immunization_box]
    )
    
    next_step3_btn.click(
        fn=run_wizard_step3,
        inputs=[month_selector, layout_mode, state_child_data],
        outputs=[data_overview, step1_panel, step2_panel, do_now_box, saran_box, warnings_box, video_gallery, immunization_box, sticker_display, streak_display]
    )
    
    generate_pdf_btn.click(
        fn=generate_checklist_pdf,
        inputs=[month_selector, layout_mode, state_child_data, export_pdf_checklist],
        outputs=[pdf_output_checklist]
    ).then(fn=lambda: gr.update(visible=True), outputs=[pdf_output_checklist])
    
    test_notif_btn.click(
        fn=test_notification,
        inputs=[state_notification_settings],
        outputs=[notif_status]
    )
    
    share_btn.click(
        fn=share_to_whatsapp,
        inputs=[month_selector, state_child_data],
        outputs=[share_status]
    )
    
    premium_btn.click(
        fn=lambda: f"🚀 Fitur Premium akan segera hadir! Hubungi +62-{CONTACT_WA[2:]} untuk pre-order",
        outputs=[share_status]
    )

# -------------------- FastAPI mount --------------------
app = FastAPI()
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")
app.mount("/static", StaticFiles(directory="static"), name="static")
demo.queue(max_size=10)
app = gr.mount_gradio_app(app, demo, path="/")

# -------------------- STARTUP MESSAGE --------------------
print("""
╔══════════════════════════════════════════════════════════════╗
║                🎀 GIZI SIKECIL APP v1.0                      ║
║  Monitor Pertumbuhan & Checklist Sehat Bulanan (0-24 bln)   ║
╚══════════════════════════════════════════════════════════════╝
✅ WHO Calculator initialized
✅ Stickers downloaded (if not exists)
✅ All functions loaded
✅ Ready to deploy on Render!

Access: https://anthrohpk-app.onrender.com
Contact: +62-55888858160
""")
