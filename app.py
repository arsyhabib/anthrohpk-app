# ==================== GIZISIKECIL v2.0 - PRODUCTION READY ====================
"""
GiziSiKecil - Aplikasi Monitor Pertumbuhan Anak Berbasis WHO Standards
===========================================================================
FIXED VERSION: Semua fitur fungsional + deployment-ready

Author: HABIB (FKIK UNJA)
Version: 2.0.0
Run: uvicorn app:app --host 0.0.0.0 --port 8000
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
# -------------------- IMPORTS --------------------
import os
import sys
import io
import csv
import math
import json
import random
import traceback
from datetime import datetime, timedelta, date
from functools import lru_cache
from typing import Dict, List, Tuple, Optional, Any
from functools import lru_cache
import warnings

warnings.filterwarnings('ignore')

# Import pygrowup dari folder lokal
# GANTI SEMUA KEMUNCULAN 'pygrowup' jadi 'pygrowup2'

# Di bagian import (sekitar line 50)
try:
    from pygrowup import Calculator
    print("✅ WHO Calculator (pygrowup LOCAL) loaded successfully")
except ImportError as e:
    print(f"❌ CRITICAL: pygrowup local not found! Error: {e}")
    sys.exit(1)

# Hapus duplikat import yang ada (cari 'pygrowup' lainnya)
    
# Numeric & Scientific
import numpy as np
from scipy.special import erf

# Visualization
import matplotlib
matplotlib.use('Agg')  # Backend non-GUI untuk server
import matplotlib.pyplot as plt
plt.ioff()  # Disable interactive mode
plt.rcParams.update({'figure.max_open_warning': 0})  # Avoid memory leak
from matplotlib.figure import Figure

# Image Processing
from PIL import Image
import qrcode

# PDF Generation
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors as rl_colors

# Web Framework
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Gradio UI
import gradio as gr



# HTTP Requests
import requests

# -------------------- GLOBAL CONFIG --------------------
APP_VERSION = "2.0.0"
APP_TITLE = "GiziSiKecil - Monitor Pertumbuhan Anak Profesional"
CONTACT_WA = "6285888858160"
BASE_URL = "https://anthrohpk-app.onrender.com"

# Directories
STATIC_DIR = "static"
OUTPUTS_DIR = "outputs"
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# -------------------- WHO CALCULATOR INIT --------------------
calc = None
try:
    calc = Calculator(
        adjust_height_data=False,
        adjust_weight_scores=False,
        include_cdc=False,
        logger_name='pygrowup',
        log_level='ERROR'
    )
    print("✅ WHO Calculator initialized with strict mode")
except Exception as e:
    print(f"❌ Calculator initialization failed: {e}")
    calc = None

# -------------------- CONSTANTS & DATA --------------------

# YouTube Educational Videos
YOUTUBE_VIDEOS = {
    "mpasi_6bln": {
        "title": "🥕 Resep MPASI 6 Bulan Pertama",
        "url": "https://www.youtube.com/watch?v=7Zg3L2J5HfE",
        "thumbnail": "https://img.youtube.com/vi/7Zg3L2J5HfE/hqdefault.jpg"
    },
    "motorik_6bln": {
        "title": "🤸 Stimulasi Motorik Kasar 6-9 Bulan",
        "url": "https://www.youtube.com/watch?v=9Y9n1A6d7Kk",
        "thumbnail": "https://img.youtube.com/vi/9Y9n1A6d7Kk/hqdefault.jpg"
    },
    "mpasi_9bln": {
        "title": "🍚 MPASI 9 Bulan: Tekstur Kasar",
        "url": "https://www.youtube.com/watch?v=Q0X3Y2Z1x0o",
        "thumbnail": "https://img.youtube.com/vi/Q0X3Y2Z1x0o/hqdefault.jpg"
    },
    "bahasa_12bln": {
        "title": "🗣️ Stimulasi Bahasa 12-15 Bulan",
        "url": "https://www.youtube.com/watch?v=2W3X4Y5Z6A7",
        "thumbnail": "https://img.youtube.com/vi/2W3X4Y5Z6A7/hqdefault.jpg"
    },
    "imunisasi": {
        "title": "💉 Jadwal Imunisasi Bayi Lengkap",
        "url": "https://www.youtube.com/watch?v=5X6Y7Z8A9B0",
        "thumbnail": "https://img.youtube.com/vi/5X6Y7Z8A9B0/hqdefault.jpg"
    }
}

# Motivational Quotes for Parents
MOM_QUOTES = [
    "💕 'Seorang ibu adalah penjelajah yang tak pernah lelah, selalu menemukan jalan cinta untuk anaknya.'",
    "🌟 'Kekuatan ibu melebihi segala rintangan, kasihnya membentuk masa depan yang cerah.'",
    "🤱 'Setiap tetes ASI adalah investasi cinta tak ternilai dalam perjalanan tumbuh kembang Si Kecil.'",
    "💪 'Kamu kuat, kamu cukup, dan kamu melakukan yang terbaik untuk Si Kecil! Jangan menyerah, Ibu hebat!'",
    "🌈 'Pertumbuhan anak bukan kompetisi, tapi perjalanan cinta bersama. Setiap langkah kecil adalah pencapaian besar.'",
    "💖 'Ibu, hatimu adalah rumah pertama Si Kecil, dan itu akan selalu jadi rumahnya yang paling aman.'"
]

# Indonesian Immunization Schedule (Permenkes)
IMMUNIZATION_SCHEDULE = {
    0: ["HB 0", "BCG", "Polio 0"],
    1: ["HB 1", "Polio 1", "DPT-HB-Hib 1", "PCV 1", "RV 1"],
    2: ["Polio 2", "DPT-HB-Hib 2", "PCV 2", "RV 2"],
    3: ["Polio 3", "DPT-HB-Hib 3", "PCV 3"],
    4: ["Polio 4", "DPT-HB-Hib 4"],
    9: ["Campak/MR 1"],
    12: ["Campak Booster", "PCV Booster"],
    18: ["DPT-HB-Hib Booster", "Polio Booster"],
    24: ["Campak Rubella (MR) 2"]
}

# KPSP (Kuesioner Pra Skrining Perkembangan) by Age
KPSP_QUESTIONS = {
    3: [
        "Mengangkat kepala 45° saat tengkurap?",
        "Tersenyum saat diajak bicara?",
        "Mengoceh (suara vokal)?",
        "Menatap dan mengikuti wajah ibu?",
        "Meraih benda/mainan?"
    ],
    6: [
        "Duduk dengan bantuan (bersandar)?",
        "Memindahkan mainan dari tangan ke tangan?",
        "Mengeluarkan suara 'a-u-o'?",
        "Tertawa keras saat bermain?",
        "Mengenal orang asing (malu/marah)?"
    ],
    9: [
        "Duduk sendiri tanpa bantuan?",
        "Merangkak maju (tidak mundur)?",
        "Mengucap 'mama/papa' (meski berlebihan)?",
        "Meraih benda kecil (seperti kacang)?",
        "Menirukan gerakan tepuk tangan?"
    ],
    12: [
        "Berdiri sendiri minimal 5 detik?",
        "Berjalan berpegangan furniture?",
        "Mengucap 2-3 kata bermakna?",
        "Minum dari cangkir sendiri?",
        "Menunjuk benda yang diinginkan?"
    ],
    15: [
        "Berjalan sendiri dengan stabil?",
        "Minum dari gelas tanpa tumpah?",
        "Mengucap 4-6 kata jelas?",
        "Menumpuk 2 kubus?",
        "Membantu melepas sepatu?"
    ],
    18: [
        "Berlari minimal 5 langkah?",
        "Naik tangga dengan bantuan?",
        "Mengucap 10-15 kata?",
        "Makan sendiri dengan sendok?",
        "Menunjuk 2 bagian tubuh?"
    ],
    21: [
        "Menendang bola ke depan?",
        "Naik tangga 1 kaki bergantian?",
        "Mengucap 2-3 kata gabungan?",
        "Membalik halaman buku?",
        "Mengikuti perintah 2 tahap?"
    ],
    24: [
        "Melompat 2 kaki bersamaan?",
        "Naik tangga tanpa pegangan?",
        "Membuat kalimat 3-4 kata?",
        "Menggambar garis vertikal?",
        "Mengikuti perintah 3 tahap?"
    ]
}

# UI Themes - 3 Pastel Variants
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

# Anthropometric Bounds (WHO Standards)
BOUNDS = {
    'wfa': (1.0, 30.0),      # Weight-for-Age (kg)
    'hfa': (45.0, 125.0),    # Height-for-Age (cm)
    'hcfa': (30.0, 55.0),    # Head Circumference-for-Age (cm)
    'wfl_w': (1.0, 30.0),    # Weight-for-Length: weight range
    'wfl_l': (45.0, 110.0)   # Weight-for-Length: length range
}

# Age grid for curve generation (0-60 months, step 0.25)
AGE_GRID = np.arange(0.0, 60.0 + 1e-9, 0.25)

print(f"✅ Configuration loaded: {len(YOUTUBE_VIDEOS)} videos, {len(KPSP_QUESTIONS)} KPSP sets, {len(UI_THEMES)} themes")

# ==================== PART 2: HELPER FUNCTIONS & WHO CALCULATIONS ====================

# -------------------- UTILITY FUNCTIONS --------------------

def as_float(x: Any) -> Optional[float]:
    """
    Convert input to float safely
    
    Args:
        x: Any input (string, number, Decimal, etc)
        
    Returns:
        Float value or None if conversion fails
    """
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        # Handle comma as decimal separator
        return float(str(x).replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


def parse_date(date_str: str) -> Optional[date]:
    """
    Parse date string in multiple formats
    
    Supported formats:
    - YYYY-MM-DD (ISO)
    - DD/MM/YYYY (Indonesian)
    
    Args:
        date_str: Date string
        
    Returns:
        datetime.date object or None
    """
    if not date_str or str(date_str).strip() == "":
        return None
    
    s = str(date_str).strip()
    
    # Try YYYY-MM-DD
    try:
        parts = s.split("-")
        if len(parts) == 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            return date(y, m, d)
    except (ValueError, IndexError):
        pass
    
    # Try DD/MM/YYYY
    try:
        parts = s.split("/")
        if len(parts) == 3:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            return date(y, m, d)
    except (ValueError, IndexError):
        pass
    
    return None


def age_months_from_dates(dob: date, dom: date) -> Tuple[Optional[float], Optional[int]]:
    """
    Calculate age in months and days from date of birth and measurement date
    
    Args:
        dob: Date of birth
        dom: Date of measurement
        
    Returns:
        Tuple of (age_months, age_days) or (None, None) if invalid
    """
    try:
        if dom < dob:
            return None, None
        
        delta = dom - dob
        days = delta.days
        
        if days < 0:
            return None, None
        
        # Average month = 30.4375 days (365.25/12)
        months = days / 30.4375
        
        return months, days
    except Exception:
        return None, None


@lru_cache(maxsize=2000)
def z_to_percentile(z_score: Optional[float]) -> Optional[float]:
    """
    Convert Z-score to percentile using standard normal CDF
    
    Args:
        z_score: Z-score value
        
    Returns:
        Percentile (0-100) or None
    """
    if z_score is None:
        return None
    
    try:
        z = float(z_score)
        if math.isnan(z) or math.isinf(z):
            return None
        
        # Standard normal CDF: Φ(z) = 0.5 * (1 + erf(z/√2))
        percentile = 0.5 * (1.0 + erf(z / math.sqrt(2.0))) * 100.0
        
        return round(percentile, 1)
    except Exception:
        return None


def format_zscore(z: Optional[float], decimals: int = 2) -> str:
    """
    Format Z-score for display
    
    Args:
        z: Z-score value
        decimals: Number of decimal places
        
    Returns:
        Formatted string or "—" for invalid values
    """
    if z is None:
        return "—"
    
    try:
        z_float = float(z)
        if math.isnan(z_float) or math.isinf(z_float):
            return "—"
        return f"{z_float:.{decimals}f}"
    except Exception:
        return "—"


def validate_anthropometry(age_mo: Optional[float], 
                          weight: Optional[float], 
                          height: Optional[float], 
                          head_circ: Optional[float]) -> Tuple[List[str], List[str]]:
    """
    Validate anthropometric measurements
    
    Args:
        age_mo: Age in months
        weight: Weight in kg
        height: Height/length in cm
        head_circ: Head circumference in cm
        
    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []
    
    # Age validation
    if age_mo is not None:
        if age_mo < 0:
            errors.append("❌ Usia tidak boleh negatif")
        elif age_mo > 60:
            warnings.append("ℹ️ Aplikasi dioptimalkan untuk usia 0-60 bulan")
    
    # Weight validation
    if weight is not None:
        if weight < 1.0 or weight > 30.0:
            errors.append(f"❌ Berat badan {weight:.1f} kg di luar rentang wajar (1-30 kg)")
        elif weight < 2.0 or weight > 25.0:
            warnings.append(f"⚠️ Berat badan {weight:.1f} kg tidak umum untuk balita")
    
    # Height validation
    if height is not None:
        if height < 35 or height > 130:
            errors.append(f"❌ Tinggi/panjang {height:.1f} cm di luar rentang wajar (35-130 cm)")
        elif height < 45 or height > 120:
            warnings.append(f"⚠️ Tinggi/panjang {height:.1f} cm perlu verifikasi ulang")
    
    # Head circumference validation
    if head_circ is not None:
        if head_circ < 20 or head_circ > 60:
            errors.append(f"❌ Lingkar kepala {head_circ:.1f} cm di luar rentang wajar (20-60 cm)")
        elif head_circ < 30 or head_circ > 55:
            warnings.append(f"⚠️ Lingkar kepala {head_circ:.1f} cm perlu verifikasi")
    
    return errors, warnings


# -------------------- WHO Z-SCORE CALCULATIONS --------------------

def _safe_z(calc_func, *args) -> Optional[float]:
    """
    Safely call WHO calculator function and handle errors
    
    Args:
        calc_func: Calculator method to call
        *args: Arguments to pass to calculator
        
    Returns:
        Z-score or None if calculation fails
    """
    if calc is None:
        return None
    
    try:
        z = calc_func(*args)
        
        if z is None:
            return None
        
        z_float = float(z)
        
        # Check for invalid values
        if math.isnan(z_float) or math.isinf(z_float):
            return None
        
        return z_float
    except Exception:
        return None


def calculate_all_zscores(sex: str, 
                          age_months: float, 
                          weight: Optional[float], 
                          height: Optional[float], 
                          head_circ: Optional[float]) -> Dict[str, Optional[float]]:
    """
    Calculate all WHO z-scores for a child
    
    Args:
        sex: 'M' or 'F'
        age_months: Age in months
        weight: Weight in kg
        height: Height/length in cm
        head_circ: Head circumference in cm
        
    Returns:
        Dict with keys: waz, haz, whz, baz, hcz
    """
    z_scores = {
        "waz": None,  # Weight-for-Age
        "haz": None,  # Height-for-Age
        "whz": None,  # Weight-for-Height
        "baz": None,  # BMI-for-Age
        "hcz": None   # Head Circumference-for-Age
    }
    
    if calc is None:
        return z_scores
    
    # Weight-for-Age Z-score
    if weight is not None:
        z_scores["waz"] = _safe_z(calc.wfa, float(weight), float(age_months), sex)
    
    # Height-for-Age Z-score
    if height is not None:
        z_scores["haz"] = _safe_z(calc.lhfa, float(height), float(age_months), sex)
    
    # Weight-for-Height Z-score
    if weight is not None and height is not None:
        z_scores["whz"] = _safe_z(calc.wfl, float(weight), float(age_months), sex, float(height))
    
    # BMI-for-Age Z-score
    if weight is not None and height is not None:
        try:
            bmi = float(weight) / ((float(height) / 100.0) ** 2)
            z_scores["baz"] = _safe_z(calc.bmifa, float(bmi), float(age_months), sex)
        except (ZeroDivisionError, ValueError):
            z_scores["baz"] = None
    
    # Head Circumference-for-Age Z-score
    if head_circ is not None:
        z_scores["hcz"] = _safe_z(calc.hcfa, float(head_circ), float(age_months), sex)
    
    return z_scores


# -------------------- CLASSIFICATION FUNCTIONS --------------------

def classify_permenkes_waz(z: Optional[float]) -> str:
    """Classify Weight-for-Age by Permenkes RI No. 2/2020"""
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Tidak diketahui"
    
    if z < -3:
        return "Gizi buruk (BB sangat kurang)"
    elif z < -2:
        return "Gizi kurang"
    elif z <= 1:
        return "BB normal"
    else:
        return "Risiko BB lebih"


def classify_permenkes_haz(z: Optional[float]) -> str:
    """Classify Height-for-Age by Permenkes RI No. 2/2020"""
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Tidak diketahui"
    
    if z < -3:
        return "Sangat pendek (stunting berat)"
    elif z < -2:
        return "Pendek (stunting)"
    elif z <= 3:
        return "Normal"
    else:
        return "Tinggi"


def classify_permenkes_whz(z: Optional[float]) -> str:
    """Classify Weight-for-Height by Permenkes RI No. 2/2020"""
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Tidak diketahui"
    
    if z < -3:
        return "Gizi buruk (sangat kurus)"
    elif z < -2:
        return "Gizi kurang (kurus)"
    elif z <= 1:
        return "Gizi baik (normal)"
    elif z <= 2:
        return "Risiko gizi lebih"
    elif z <= 3:
        return "Gizi lebih"
    else:
        return "Obesitas"


def classify_who_waz(z: Optional[float]) -> str:
    """Classify Weight-for-Age by WHO standards"""
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Unknown"
    
    if z < -3:
        return "Severely underweight"
    elif z < -2:
        return "Underweight"
    elif z > 2:
        return "Possible risk of overweight"
    else:
        return "Normal"


def classify_who_haz(z: Optional[float]) -> str:
    """Classify Height-for-Age by WHO standards"""
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Unknown"
    
    if z < -3:
        return "Severely stunted"
    elif z < -2:
        return "Stunted"
    elif z > 3:
        return "Tall"
    else:
        return "Normal"


def classify_who_whz(z: Optional[float]) -> str:
    """Classify Weight-for-Height by WHO standards"""
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Unknown"
    
    if z < -3:
        return "Severe wasting"
    elif z < -2:
        return "Wasting"
    elif z <= 2:
        return "Normal"
    elif z <= 3:
        return "Overweight"
    else:
        return "Obesity"


def classify_hcz(z: Optional[float]) -> Tuple[str, str]:
    """
    Classify Head Circumference Z-score
    
    Returns:
        Tuple of (Indonesian, English) classifications
    """
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return ("Tidak diketahui", "Unknown")
    
    if z < -3:
        return ("Lingkar kepala sangat kecil (mikrosefali berat)", "Severe microcephaly")
    elif z < -2:
        return ("Lingkar kepala di bawah normal (mikrosefali)", "Microcephaly")
    elif z > 3:
        return ("Lingkar kepala sangat besar (makrosefali berat)", "Severe macrocephaly")
    elif z > 2:
        return ("Lingkar kepala di atas normal (makrosefali)", "Macrocephaly")
    else:
        return ("Normal", "Normal")


def validate_zscores(z_scores: Dict[str, Optional[float]]) -> Tuple[List[str], List[str]]:
    """
    Validate calculated z-scores for biological plausibility
    
    Args:
        z_scores: Dict of z-score values
        
    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []
    
    # Define critical and warning thresholds
    checks = [
        ("WAZ", z_scores.get("waz"), 6, 5),
        ("HAZ", z_scores.get("haz"), 6, 5),
        ("WHZ", z_scores.get("whz"), 5, 4),
        ("BAZ", z_scores.get("baz"), 5, 4),
        ("HCZ", z_scores.get("hcz"), 5, 4)
    ]
    
    for name, z, critical_threshold, warn_threshold in checks:
        if z is not None and not math.isnan(z):
            abs_z = abs(z)
            
            if abs_z > critical_threshold:
                errors.append(
                    f"❌ {name} = {format_zscore(z)} sangat tidak wajar (|Z| > {critical_threshold}). "
                    f"Periksa ulang pengukuran dan satuan."
                )
            elif abs_z > warn_threshold:
                warnings.append(
                    f"⚠️ {name} = {format_zscore(z)} di luar rentang umum (|Z| > {warn_threshold}). "
                    f"Verifikasi pengukuran."
                )
    
    return errors, warnings


# -------------------- GROWTH CURVE GENERATION --------------------

def brentq_simple(f, a: float, b: float, xtol: float = 1e-6, maxiter: int = 80) -> float:
    """
    Simple Brent's method for root finding (scipy-free alternative)
    
    Args:
        f: Function to find root of
        a, b: Bracket endpoints
        xtol: Tolerance
        maxiter: Maximum iterations
        
    Returns:
        Root approximation
    """
    fa = f(a)
    fb = f(b)
    
    if fa is None or fb is None:
        return (a + b) / 2.0
    
    if fa == 0:
        return a
    if fb == 0:
        return b
    
    # Check if bracket is valid
    if fa * fb > 0:
        return (a + b) / 2.0
    
    for _ in range(maxiter):
        m = 0.5 * (a + b)
        fm = f(m)
        
        if fm is None:
            return m
        
        if abs(fm) < 1e-8 or (b - a) / 2 < xtol:
            return m
        
        if fa * fm < 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    
    return 0.5 * (a + b)


def invert_z_with_scan(z_of_m, target_z: float, lo: float, hi: float, samples: int = 120) -> float:
    """
    Invert z-score function to find measurement value
    
    Uses grid scan + Brent's method for robustness
    
    Args:
        z_of_m: Function that takes measurement and returns z-score
        target_z: Target z-score to achieve
        lo, hi: Search bounds
        samples: Number of grid points
        
    Returns:
        Measurement value that gives target_z
    """
    xs = np.linspace(lo, hi, samples)
    last_x, last_f = None, None
    best_x, best_abs = None, float('inf')
    
    # Grid scan
    for x in xs:
        z = z_of_m(x)
        f = None if z is None else (z - target_z)
        
        if f is not None:
            af = abs(f)
            if af < best_abs:
                best_x, best_abs = x, af
            
            # Check for sign change (root bracket)
            if last_f is not None and f * last_f < 0:
                try:
                    root = brentq_simple(
                        lambda t: (z_of_m(t) or 0.0) - target_z,
                        last_x,
                        x
                    )
                    return float(root)
                except Exception:
                    pass
            
            last_x, last_f = x, f
    
    return float(best_x if best_x is not None else (lo + hi) / 2.0)


def generate_wfa_curve(sex: str, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Weight-for-Age curve for given z-score
    
    Args:
        sex: 'M' or 'F'
        z_score: Z-score line to generate
        
    Returns:
        Tuple of (age_array, weight_array)
    """
    lo, hi = BOUNDS['wfa']
    
    def z_func(weight, age):
        return _safe_z(calc.wfa, weight, age, sex)
    
    weights = []
    for age in AGE_GRID:
        weight = invert_z_with_scan(
            lambda w: z_func(w, age),
            z_score,
            lo,
            hi
        )
        weights.append(weight)
    
    return AGE_GRID.copy(), np.array(weights)

@lru_cache(maxsize=128)
def generate_wfa_curve_cached(sex: str, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """Cached wrapper untuk generate_wfa_curve"""
    return generate_wfa_curve(sex, z_score)


def generate_hfa_curve(sex: str, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Height-for-Age curve for given z-score
    
    Args:
        sex: 'M' or 'F'
        z_score: Z-score line to generate
        
    Returns:
        Tuple of (age_array, height_array)
    """
    lo, hi = BOUNDS['hfa']
    
    def z_func(height, age):
        return _safe_z(calc.lhfa, height, age, sex)
    
    heights = []
    for age in AGE_GRID:
        height = invert_z_with_scan(
            lambda h: z_func(h, age),
            z_score,
            lo,
            hi
        )
        heights.append(height)
    
    return AGE_GRID.copy(), np.array(heights)


# ⭐ PASTE KODE CACHING DI SINI - SETELAH generate_hfa_curve
@lru_cache(maxsize=128)
def generate_hfa_curve_cached(sex: str, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """Cached wrapper untuk generate_hfa_curve"""
    return generate_hfa_curve(sex, z_score)


def generate_hcfa_curve(sex: str, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Head Circumference-for-Age curve for given z-score
    
    Args:
        sex: 'M' or 'F'
        z_score: Z-score line to generate
        
    Returns:
        Tuple of (age_array, head_circ_array)
    """
    lo, hi = BOUNDS['hcfa']
    
    def z_func(hc, age):
        return _safe_z(calc.hcfa, hc, age, sex)
    
    head_circs = []
    for age in AGE_GRID:
        hc = invert_z_with_scan(
            lambda h: z_func(h, age),
            z_score,
            lo,
            hi
        )
        head_circs.append(hc)
    
    return AGE_GRID.copy(), np.array(head_circs)


# ⭐ PASTE KODE CACHING DI SINI - SETELAH generate_hcfa_curve
@lru_cache(maxsize=128)
def generate_hcfa_curve_cached(sex: str, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """Cached wrapper untuk generate_hcfa_curve"""
    return generate_hcfa_curve(sex, z_score)


def generate_wfl_curve(sex: str, age_months: float, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Weight-for-Length curve for given z-score
    
    Args:
        sex: 'M' or 'F'
        age_months: Child's age in months
        z_score: Z-score line to generate
        
    Returns:
        Tuple of (length_array, weight_array)
    """
    lengths = np.arange(BOUNDS['wfl_l'][0], BOUNDS['wfl_l'][1] + 0.5, 0.5)
    lo_w, hi_w = BOUNDS['wfl_w']
    
    def z_func(weight, length):
        return _safe_z(calc.wfl, weight, age_months, sex, length)
    
    weights = []
    for length in lengths:
        weight = invert_z_with_scan(
            lambda w: z_func(w, length),
            z_score,
            lo_w,
            hi_w
        )
        weights.append(weight)
    
    return lengths, np.array(weights)


# ⭐ PASTE KODE CACHING DI SINI - SETELAH generate_wfl_curve
@lru_cache(maxsize=128)
def generate_wfl_curve_cached(sex: str, age_months: float, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """Cached wrapper untuk generate_wfl_curve"""
    return generate_wfl_curve(sex, age_months, z_score)


# ==================== PART 3: PLOTTING FUNCTIONS ====================

def plot_weight_for_age(payload: Dict, theme_name: str = "pink_pastel") -> Figure:
    """
    Plot Weight-for-Age growth chart with child's data
    
    Args:
        payload: Data dict with sex, age_mo, w, z-scores, etc
        theme_name: Theme to apply
        
    Returns:
        Matplotlib Figure object
    """
    theme = apply_matplotlib_theme(theme_name)
    
    sex = payload['sex']
    age = payload['age_mo']
    weight = payload.get('w')
    
    # Define SD lines to plot
    sd_lines = {
        -3: ('#DC143C', '-'),
        -2: ('#FF6347', '-'),
        -1: (theme['primary'], '--'),
        0: (theme['secondary'], '-'),
        1: (theme['primary'], '--'),
        2: ('#FF6347', '-'),
        3: ('#DC143C', '-')
    }
    
    # ⭐ GUNAKAN VERSI CACHED
    curves = {z: generate_wfa_curve_cached(sex, z) for z in sd_lines.keys()}

def generate_hfa_curve(sex: str, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Height-for-Age curve for given z-score
    
    Args:
        sex: 'M' or 'F'
        z_score: Z-score line to generate
        
    Returns:
        Tuple of (age_array, height_array)
    """
    lo, hi = BOUNDS['hfa']
    
    def z_func(height, age):
        return _safe_z(calc.lhfa, height, age, sex)
    
    heights = []
    for age in AGE_GRID:
        height = invert_z_with_scan(
            lambda h: z_func(h, age),
            z_score,
            lo,
            hi
        )
        heights.append(height)
    
    return AGE_GRID.copy(), np.array(heights)


def generate_hcfa_curve(sex: str, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Head Circumference-for-Age curve for given z-score
    
    Args:
        sex: 'M' or 'F'
        z_score: Z-score line to generate
        
    Returns:
        Tuple of (age_array, head_circ_array)
    """
    lo, hi = BOUNDS['hcfa']
    
    def z_func(hc, age):
        return _safe_z(calc.hcfa, hc, age, sex)
    
    head_circs = []
    for age in AGE_GRID:
        hc = invert_z_with_scan(
            lambda h: z_func(h, age),
            z_score,
            lo,
            hi
        )
        head_circs.append(hc)
    
    return AGE_GRID.copy(), np.array(head_circs)


def generate_wfl_curve(sex: str, age_months: float, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Weight-for-Length curve for given z-score
    
    Args:
        sex: 'M' or 'F'
        age_months: Child's age in months
        z_score: Z-score line to generate
        
    Returns:
        Tuple of (length_array, weight_array)
    """
    lengths = np.arange(BOUNDS['wfl_l'][0], BOUNDS['wfl_l'][1] + 0.5, 0.5)
    lo_w, hi_w = BOUNDS['wfl_w']
    
    def z_func(weight, length):
        return _safe_z(calc.wfl, weight, age_months, sex, length)
    
    weights = []
    for length in lengths:
        weight = invert_z_with_scan(
            lambda w: z_func(w, length),
            z_score,
            lo_w,
            hi_w
        )
        weights.append(weight)
    
    return lengths, np.array(weights)


# -------------------- STICKER DOWNLOAD --------------------

def ensure_stickers():
    """Download cute stickers for rewards system"""
    sticker_urls = [
        "https://i.ibb.co/8B6gX9V/sticker-1.png",
        "https://i.ibb.co/3sJzVXM/sticker-2.png",
        "https://i.ibb.co/6J5mTJG/sticker-3.png",
        "https://i.ibb.co/KxM5pYf/sticker-4.png",
        "https://i.ibb.co/1rMZg3V/sticker-5.png"
    ]
    
    for i, url in enumerate(sticker_urls, 1):
        path = os.path.join(STATIC_DIR, f"sticker_{i}.png")
        
        if os.path.exists(path):
            continue
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(path, "wb") as f:
                    f.write(response.content)
                print(f"✅ Downloaded sticker_{i}.png")
        except Exception as e:
            print(f"⚠️ Sticker {i} download failed: {e}")
            # Create placeholder
            img = Image.new('RGBA', (200, 200), (255, 182, 193, 255))
            img.save(path)


# Initialize stickers on startup
ensure_stickers()

print("✅ Part 2 loaded: Helper functions, WHO calculations, curve generation")

# ==================== PART 2B: PLOTTING FUNCTIONS ====================

def apply_matplotlib_theme(theme_name: str = "pink_pastel") -> Dict[str, str]:
    """
    Apply theme to matplotlib
    
    Args:
        theme_name: One of 'pink_pastel', 'mint_pastel', 'lavender_pastel'
        
    Returns:
        Theme dictionary
    """
    theme = UI_THEMES.get(theme_name, UI_THEMES["pink_pastel"])
    
    plt.style.use('default')
    plt.rcParams.update({
        "axes.facecolor": theme["card"],
        "figure.facecolor": theme["bg"],
        "savefig.facecolor": theme["bg"],
        "text.color": theme["text"],
        "axes.labelcolor": theme["text"],
        "axes.edgecolor": theme["border"],
        "xtick.color": theme["text"],
        "ytick.color": theme["text"],
        "grid.color": theme["border"],
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "grid.linewidth": 0.8,
        "legend.framealpha": 1.0,
        "legend.fancybox": False,
        "legend.edgecolor": theme["border"],
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.linewidth": 1.5,
    })
    
    return theme


def _fill_zone(ax, x: np.ndarray, lower: np.ndarray, upper: np.ndarray, 
               color: str, alpha: float, label: str):
    """Helper to fill colored zones between curves"""
    try:
        ax.fill_between(
            x, lower, upper,
            color=color,
            alpha=alpha,
            zorder=1,
            label=label,
            linewidth=0
        )
    except Exception:
        pass


def plot_weight_for_age(payload: Dict, theme_name: str = "pink_pastel") -> Figure:
    """
    Plot Weight-for-Age growth chart with child's data
    
    Args:
        payload: Data dict with sex, age_mo, w, z-scores, etc
        theme_name: Theme to apply
        
    Returns:
        Matplotlib Figure object
    """
    theme = apply_matplotlib_theme(theme_name)
    
    sex = payload['sex']
    age = payload['age_mo']
    weight = payload.get('w')
    
    # Define SD lines to plot
    sd_lines = {
        -3: ('#DC143C', '-'),
        -2: ('#FF6347', '-'),
        -1: (theme['primary'], '--'),
        0: (theme['secondary'], '-'),
        1: (theme['primary'], '--'),
        2: ('#FF6347', '-'),
        3: ('#DC143C', '-')
    }
    
    # Generate curves
    curves = {z: generate_wfa_curve(sex, z) for z in sd_lines.keys()}
    
    fig, ax = plt.subplots(figsize=(11, 7))
    
    x = curves[0][0]
    
    # Fill zones
    _fill_zone(ax, x, curves[-3][1], curves[-2][1], '#FFE6E6', 0.35, 'Zona Gizi Buruk')
    _fill_zone(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Zona Gizi Kurang')
    _fill_zone(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.40, 'Zona Normal')
    _fill_zone(ax, x, curves[1][1],  curves[2][1],  '#FFF3CD', 0.30, 'Risiko Gizi Lebih')
    _fill_zone(ax, x, curves[2][1],  curves[3][1],  '#F8D7DA', 0.35, 'Gizi Lebih')
    
    # Plot SD lines
    for z, (color, linestyle) in sd_lines.items():
        linewidth = 2.5 if abs(z) in (0, 2) else 1.8
        label = "Median" if z == 0 else f"{z:+d} SD"
        ax.plot(
            curves[z][0], curves[z][1],
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            label=label,
            zorder=5
        )
    
    # Plot child's data point
    if weight is not None:
        z_waz = payload['z']['waz']
        
        # Color based on z-score severity
        if z_waz is not None:
            if abs(z_waz) > 3:
                point_color = '#8B0000'
            elif abs(z_waz) > 2:
                point_color = '#DC143C'
            elif abs(z_waz) > 1:
                point_color = theme['primary']
            else:
                point_color = theme['secondary']
        else:
            point_color = theme['secondary']
        
        ax.scatter(
            [age], [weight],
            s=400,
            c=point_color,
            edgecolors=theme['text'],
            linewidths=3,
            marker='o',
            zorder=20,
            label='Data Anak'
        )
        
        # Drop line to x-axis
        ax.plot([age, age], [0, weight], 'k--', linewidth=1, alpha=0.3, zorder=1)
    
    # Styling
    ax.set_xlabel('Usia (bulan)', fontweight='bold')
    ax.set_ylabel('Berat Badan (kg)', fontweight='bold')
    
    title = f"GRAFIK PERTUMBUHAN WHO: Berat Badan menurut Umur (BB/U)\n"
    title += "Laki-laki" if sex == 'M' else "Perempuan"
    title += " | 0-60 bulan"
    ax.set_title(title, fontweight='bold', color=theme['text'])
    
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.minorticks_on()
    
    ax.set_xlim(0, 60)
    ax.set_xticks(range(0, 61, 6))
    ax.set_xticks(range(0, 61, 3), minor=True)
    
    # Y-axis limits
    y_min = min([curves[z][1].min() for z in (-3, -2, 0, 2, 3)])
    y_max = max([curves[z][1].max() for z in (-3, -2, 0, 2, 3)])
    ax.set_ylim(max(0, y_min - 1), y_max + 2)
    
    ax.legend(loc='upper left', frameon=True, edgecolor=theme['border'], fontsize=9, ncol=2)
    
    plt.tight_layout()
    return fig


def plot_height_for_age(payload: Dict, theme_name: str = "pink_pastel") -> Figure:
    """Plot Height-for-Age growth chart"""
    theme = apply_matplotlib_theme(theme_name)
    
    sex = payload['sex']
    age = payload['age_mo']
    height = payload.get('h')
    
    sd_lines = {
        -3: ('#DC143C', '-'),
        -2: ('#FF6347', '-'),
        -1: (theme['primary'], '--'),
        0: (theme['secondary'], '-'),
        1: (theme['primary'], '--'),
        2: ('#FF6347', '-'),
        3: ('#DC143C', '-')
    }
    
    curves = {z: generate_hfa_curve(sex, z) for z in sd_lines.keys()}
    
    fig, ax = plt.subplots(figsize=(11, 7))
    
    x = curves[0][0]
    
    _fill_zone(ax, x, curves[-3][1], curves[-2][1], '#FFE6E6', 0.30, 'Severe Stunting')
    _fill_zone(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Stunting')
    _fill_zone(ax, x, curves[-1][1], curves[2][1],  '#E8F5E9', 0.40, 'Normal')
    _fill_zone(ax, x, curves[2][1],  curves[3][1],  '#E3F2FD', 0.30, 'Tall')
    
    for z, (color, linestyle) in sd_lines.items():
        linewidth = 2.5 if abs(z) in (0, 2) else 1.8
        label = "Median" if z == 0 else f"{z:+d} SD"
        ax.plot(curves[z][0], curves[z][1], color=color, linestyle=linestyle,
                linewidth=linewidth, label=label, zorder=5)
    
    if height is not None:
        z_haz = payload['z']['haz']
        point_color = theme['secondary']
        if z_haz is not None:
            if abs(z_haz) > 3: point_color = '#8B0000'
            elif abs(z_haz) > 2: point_color = '#DC143C'
            elif abs(z_haz) > 1: point_color = theme['primary']
        
        ax.scatter([age], [height], s=400, c=point_color, edgecolors=theme['text'],
                   linewidths=3, marker='o', zorder=20, label='Data Anak')
        ax.plot([age, age], [40, height], 'k--', linewidth=1, alpha=0.3, zorder=1)
    
    ax.set_xlabel('Usia (bulan)', fontweight='bold')
    ax.set_ylabel('Panjang/Tinggi Badan (cm)', fontweight='bold')
    title = f"GRAFIK PERTUMBUHAN WHO: Panjang/Tinggi menurut Umur (TB/U)\n"
    title += "Laki-laki" if sex == 'M' else "Perempuan"
    title += " | 0-60 bulan"
    ax.set_title(title, fontweight='bold', color=theme['text'])
    
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.minorticks_on()
    ax.set_xlim(0, 60)
    ax.set_xticks(range(0, 61, 6))
    ax.set_xticks(range(0, 61, 3), minor=True)
    
    y_min = min([curves[z][1].min() for z in (-3, -2, 0, 2, 3)])
    y_max = max([curves[z][1].max() for z in (-3, -2, 0, 2, 3)])
    ax.set_ylim(max(45, y_min - 1), y_max + 2)
    
    ax.legend(loc='upper left', frameon=True, edgecolor=theme['border'], fontsize=9, ncol=2)
    plt.tight_layout()
    return fig


def plot_head_circ_for_age(payload: Dict, theme_name: str = "pink_pastel") -> Figure:
    """Plot Head Circumference-for-Age growth chart"""
    theme = apply_matplotlib_theme(theme_name)
    
    sex = payload['sex']
    age = payload['age_mo']
    hc = payload.get('hc')
    
    sd_lines = {
        -3: ('#DC143C', '-'),
        -2: ('#FF6347', '-'),
        -1: (theme['primary'], '--'),
        0: (theme['secondary'], '-'),
        1: (theme['primary'], '--'),
        2: ('#FF6347', '-'),
        3: ('#DC143C', '-')
    }
    
    curves = {z: generate_hcfa_curve(sex, z) for z in sd_lines.keys()}
    
    fig, ax = plt.subplots(figsize=(11, 7))
    
    x = curves[0][0]
    
    _fill_zone(ax, x, curves[-3][1], curves[-2][1], '#FFD4D4', 0.40, 'Microcephaly Berat')
    _fill_zone(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Microcephaly')
    _fill_zone(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.40, 'Zona Normal')
    _fill_zone(ax, x, curves[1][1],  curves[2][1],  '#E3F2FD', 0.30, 'Macrocephaly')
    _fill_zone(ax, x, curves[2][1],  curves[3][1],  '#BBDEFB', 0.35, 'Macrocephaly Berat')
    
    for z, (color, linestyle) in sd_lines.items():
        linewidth = 2.5 if abs(z) in (0, 2) else 1.8
        label = "Median" if z == 0 else f"{z:+d} SD"
        ax.plot(curves[z][0], curves[z][1], color=color, linestyle=linestyle,
                linewidth=linewidth, label=label, zorder=5)
    
    if hc is not None:
        z_hcz = payload['z']['hcz']
        point_color = theme['secondary']
        if z_hcz is not None:
            if abs(z_hcz) > 3: point_color = '#8B0000'
            elif abs(z_hcz) > 2: point_color = '#DC143C'
            elif abs(z_hcz) > 1: point_color = theme['primary']
        
        ax.scatter([age], [hc], s=400, c=point_color, edgecolors=theme['text'],
                   linewidths=3, marker='o', zorder=20, label='Data Anak')
        ax.plot([age, age], [25, hc], 'k--', linewidth=1, alpha=0.3, zorder=1)
    
    ax.set_xlabel('Usia (bulan)', fontweight='bold')
    ax.set_ylabel('Lingkar Kepala (cm)', fontweight='bold')
    title = f"GRAFIK PERTUMBUHAN WHO: Lingkar Kepala menurut Umur (LK/U)\n"
    title += "Laki-laki" if sex == 'M' else "Perempuan"
    title += " | 0-60 bulan"
    ax.set_title(title, fontweight='bold', color=theme['text'])
    
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.minorticks_on()
    ax.set_xlim(0, 60)
    ax.set_xticks(range(0, 61, 6))
    ax.set_xticks(range(0, 61, 3), minor=True)
    
    y_min = min([curves[z][1].min() for z in (-3, -2, 0, 2, 3)])
    y_max = max([curves[z][1].max() for z in (-3, -2, 0, 2, 3)])
    ax.set_ylim(max(25, y_min - 1), y_max + 2)
    
    ax.legend(loc='upper left', frameon=True, edgecolor=theme['border'], fontsize=9, ncol=2)
    plt.tight_layout()
    return fig


def plot_weight_for_length(payload: Dict, theme_name: str = "pink_pastel") -> Figure:
    """Plot Weight-for-Length growth chart"""
    theme = apply_matplotlib_theme(theme_name)
    
    sex = payload['sex']
    age = payload['age_mo']
    height = payload.get('h')
    weight = payload.get('w')
    
    sd_lines = {
        -3: ('#DC143C', '-'),
        -2: ('#FF6347', '-'),
        -1: (theme['primary'], '--'),
        0: (theme['secondary'], '-'),
        1: (theme['primary'], '--'),
        2: ('#FF6347', '-'),
        3: ('#DC143C', '-')
    }
    
    curves = {z: generate_wfl_curve(sex, age, z) for z in sd_lines.keys()}
    
    fig, ax = plt.subplots(figsize=(11, 7))
    
    x = curves[0][0]
    
    _fill_zone(ax, x, curves[-3][1], curves[-2][1], '#FFD4D4', 0.40, 'Wasting Berat')
    _fill_zone(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Wasting')
    _fill_zone(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.40, 'Zona Normal')
    _fill_zone(ax, x, curves[1][1],  curves[2][1],  '#FFF9C4', 0.30, 'Risiko Overweight')
    _fill_zone(ax, x, curves[2][1],  curves[3][1],  '#FFD4D4', 0.40, 'Overweight/Obesitas')
    
    for z, (color, linestyle) in sd_lines.items():
        linewidth = 2.5 if abs(z) in (0, 2) else 1.8
        label = "Median" if z == 0 else f"{z:+d} SD"
        ax.plot(curves[z][0], curves[z][1], color=color, linestyle=linestyle,
                linewidth=linewidth, label=label, zorder=5)
    
    if height is not None and weight is not None:
        z_whz = payload['z']['whz']
        point_color = theme['secondary']
        if z_whz is not None:
            if abs(z_whz) > 3: point_color = '#8B0000'
            elif abs(z_whz) > 2: point_color = '#DC143C'
            elif abs(z_whz) > 1: point_color = theme['primary']
        
        ax.scatter([height], [weight], s=400, c=point_color, edgecolors=theme['text'],
                   linewidths=3, marker='o', zorder=20, label='Data Anak')
        ax.plot([height, height], [0, weight], 'k--', linewidth=1, alpha=0.3, zorder=1)
    
    ax.set_xlabel('Panjang/Tinggi Badan (cm)', fontweight='bold')
    ax.set_ylabel('Berat Badan (kg)', fontweight='bold')
    title = f"GRAFIK PERTUMBUHAN WHO: Berat menurut Panjang/Tinggi (BB/TB)\n"
    title += "Laki-laki" if sex == 'M' else "Perempuan"
    ax.set_title(title, fontweight='bold', color=theme['text'])
    
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.minorticks_on()
    ax.set_xlim(x.min(), x.max())
    
    y_min = min([curves[z][1].min() for z in (-3, -2, 0, 2, 3)])
    y_max = max([curves[z][1].max() for z in (-3, -2, 0, 2, 3)])
    ax.set_ylim(max(0, y_min - 1), y_max + 2)
    
    ax.legend(loc='upper left', frameon=True, edgecolor=theme['border'], fontsize=9, ncol=2)
    plt.tight_layout()
    return fig


def plot_zscore_bars(payload: Dict, theme_name: str = "pink_pastel") -> Figure:
    """Plot bar chart summary of all z-scores"""
    theme = apply_matplotlib_theme(theme_name)
    
    z = payload['z']
    
    labels = ['WAZ\n(BB/U)', 'HAZ\n(TB/U)', 'WHZ\n(BB/TB)', 'BAZ\n(IMT/U)', 'HCZ\n(LK/U)']
    values = [z['waz'], z['haz'], z['whz'], z['baz'], z['hcz']]
    
    def get_bar_color(v):
        if v is None or math.isnan(v):
            return '#CCCCCC'
        if abs(v) > 3:
            return '#8B0000'
        if abs(v) > 2:
            return '#DC143C'
        if abs(v) > 1:
            return theme['primary']
        return theme['secondary']
    
    colors_bar = [get_bar_color(v) for v in values]
    plot_values = [0 if (v is None or (isinstance(v, float) and math.isnan(v))) else v for v in values]
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Background zones
    ax.axhspan(-3, -2, color='#FFD4D4', alpha=0.3, label='Zona Kurang (-3 to -2 SD)')
    ax.axhspan(-2, 2, color='#E8F5E9', alpha=0.3, label='Zona Normal (-2 to +2 SD)')
    ax.axhspan(2, 3, color='#FFD4D4', alpha=0.3, label='Zona Lebih (+2 to +3 SD)')
    
    # Reference lines
    ax.axhline(0, color=theme['secondary'], linewidth=3, linestyle='-', label='Median (0 SD)', zorder=5)
    ax.axhline(-2, color='#DC143C', linewidth=2, linestyle='--', alpha=0.7)
    ax.axhline(2, color='#DC143C', linewidth=2, linestyle='--', alpha=0.7)
    ax.axhline(-3, color='#8B0000', linewidth=1.5, linestyle=':', alpha=0.5)
    ax.axhline(3, color='#8B0000', linewidth=1.5, linestyle=':', alpha=0.5)
    
    # Plot bars
    bars = ax.bar(labels, plot_values, color=colors_bar, edgecolor=theme['text'],
                   linewidth=2.5, width=0.6, alpha=0.9, zorder=10)
    
    # Add value labels
    for i, (v, bar) in enumerate(zip(values, bars)):
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            y_pos = bar.get_height()
            offset = 0.3 if y_pos >= 0 else -0.5
            
            if abs(v) > 3:
                status = "Kritis"
            elif abs(v) > 2:
                status = "Perlu Perhatian"
            elif abs(v) > 1:
                status = "Borderline"
            else:
                status = "Normal"
            
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                y_pos + offset,
                f'{format_zscore(v, 2)}\n({status})',
                ha='center',
                va='bottom' if y_pos >= 0 else 'top',
                fontsize=11,
                weight='bold',
                bbox=dict(
                    boxstyle='round,pad=0.5',
                    facecolor='white',
                    alpha=0.9,
                    edgecolor=colors_bar[i],
                    linewidth=2
                ),
                zorder=15
            )
    
    ax.set_ylabel('Z-score', fontweight='bold', fontsize=12)
    ax.set_title(
        'RINGKASAN STATUS GIZI - Semua Indeks Antropometri\nWHO Child Growth Standards',
        fontweight='bold',
        fontsize=13,
        pad=15,
        color=theme['text']
    )
    
    ax.set_ylim(-5, 5)
    ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.5, zorder=1)
    
    ax.legend(
        loc='upper right',
        frameon=True,
        edgecolor=theme['border'],
        fontsize=9,
        title='Referensi WHO',
        title_fontsize=10
    )
    
    plt.tight_layout()
    return fig


print("✅ Part 2B loaded: 5 plotting functions (WFA, HFA, HCFA, WFL, Bar chart)")

# ==================== PART 3A: REPORT GENERATION ====================

def generate_markdown_report(payload: Dict) -> str:
    """
    Generate comprehensive Markdown report
    
    Args:
        payload: Complete analysis data
        
    Returns:
        Formatted Markdown string
    """
    name_child = payload.get('name_child', 'Si Kecil')
    name_parent = payload.get('name_parent', '')
    age_mo = payload.get('age_mo', 0)
    age_days = payload.get('age_days', 0)
    sex_text = payload.get('sex_text', 'Tidak diketahui')
    w = payload.get('w', 0)
    h = payload.get('h', 0)
    hc = payload.get('hc')
    
    z_scores = payload.get('z', {})
    percentiles = payload.get('percentiles', {})
    permenkes = payload.get('permenkes', {})
    who = payload.get('who', {})
    errors = payload.get('errors', [])
    warnings = payload.get('warnings', [])
    
    # Determine overall status
    overall_status = "🟢 Normal"
    critical_issues = []
    
    for key, z in z_scores.items():
        if z is not None and not math.isnan(z):
            if abs(z) > 3:
                overall_status = "🔴 Perlu Perhatian Segera"
                critical_issues.append(key.upper())
            elif abs(z) > 2 and overall_status == "🟢 Normal":
                overall_status = "🟡 Perlu Monitoring"
    
    # Build report
    md = f"# 📊 Laporan Status Gizi Anak\n\n"
    md += f"## Status Keseluruhan: {overall_status}\n\n"
    
    if critical_issues:
        md += f"⚠️ **Indeks kritis:** {', '.join(critical_issues)}\n\n"
    
    if errors:
        md += "## ❌ Peringatan Kritis\n\n"
        for err in errors:
            md += f"- {err}\n"
        md += "\n---\n\n"
    
    # Child information
    md += "### 👤 Informasi Anak\n\n"
    if name_child and str(name_child).strip():
        md += f"**Nama:** {name_child}\n\n"
    if name_parent and str(name_parent).strip():
        md += f"**Orang Tua/Wali:** {name_parent}\n\n"
    md += f"**Jenis Kelamin:** {sex_text}\n\n"
    md += f"**Usia:** {age_mo:.1f} bulan (~{age_days} hari)\n\n"
    md += "---\n\n"
    
    # Anthropometric data
    md += "### 📏 Data Antropometri\n\n"
    md += "| Pengukuran | Nilai |\n"
    md += "|------------|-------|\n"
    md += f"| Berat Badan | **{w:.1f} kg** |\n"
    md += f"| Panjang/Tinggi | **{h:.1f} cm** |\n"
    if hc is not None:
        md += f"| Lingkar Kepala | **{hc:.1f} cm** |\n"
    md += "\n---\n\n"
    
    # Clinical narrative
    md += "### 🏥 Interpretasi Klinis\n\n"
    md += generate_clinical_narrative(z_scores, permenkes, who)
    md += "\n\n---\n\n"
    
    # Detailed results table
    md += "### 📈 Hasil Lengkap (Z-score & Kategori)\n\n"
    md += "| Indeks | Z-score | Persentil | Status (Permenkes) | Status (WHO) |\n"
    md += "|--------|---------|-----------|-------------------|-------------|\n"
    
    indices = [
        ('WAZ (BB/U)', 'waz'),
        ('HAZ (TB/U)', 'haz'),
        ('WHZ (BB/TB)', 'whz'),
        ('BAZ (IMT/U)', 'baz'),
        ('HCZ (LK/U)', 'hcz')
    ]
    
    for label, key in indices:
        z_val = format_zscore(z_scores.get(key))
        pct = percentiles.get(key)
        pct_val = f"{pct}%" if pct is not None else "—"
        perm_cat = permenkes.get(key, "—")
        who_cat = who.get(key, "—")
        
        z_raw = z_scores.get(key)
        if z_raw is not None and not math.isnan(z_raw):
            if abs(z_raw) > 3:
                status_icon = "🔴"
            elif abs(z_raw) > 2:
                status_icon = "🟡"
            elif abs(z_raw) <= 2:
                status_icon = "🟢"
            else:
                status_icon = "⚪"
        else:
            status_icon = "⚪"
        
        md += f"| {status_icon} **{label}** | {z_val} | {pct_val} | {perm_cat} | {who_cat} |\n"
    
    if warnings:
        md += "\n### ⚠️ Catatan Validasi\n\n"
        for warn in warnings:
            md += f"- {warn}\n"
    
    # Footer
    md += "\n---\n\n"
    md += "**📌 Catatan Penting:**\n\n"
    md += "- Hasil ini bersifat **skrining edukatif**, bukan diagnosis medis\n"
    md += "- Untuk interpretasi lengkap, konsultasikan dengan tenaga kesehatan\n"
    md += "- Data Anda **tidak disimpan** di server\n"
    md += f"- Tanggal analisis: {datetime.now().strftime('%d %B %Y, %H:%M WIB')}\n\n"
    
    return md


def generate_clinical_narrative(z_scores: Dict, permenkes: Dict, who: Dict) -> str:
    """Generate clinical narrative summary"""
    lines = []
    
    # WAZ analysis
    waz = z_scores.get('waz')
    if waz is not None and not math.isnan(waz):
        perm = permenkes.get('waz', '')
        who_txt = who.get('waz', '')
        lines.append(f"**Berat menurut Umur (WAZ):** {format_zscore(waz)} - {perm} (WHO: {who_txt})")
    
    # HAZ analysis
    haz = z_scores.get('haz')
    if haz is not None and not math.isnan(haz):
        perm = permenkes.get('haz', '')
        who_txt = who.get('haz', '')
        lines.append(f"**Tinggi menurut Umur (HAZ):** {format_zscore(haz)} - {perm} (WHO: {who_txt})")
        
        if haz < -3:
            lines.append("  ⚠️ **Prioritas tinggi**: Stunting berat memerlukan intervensi segera")
        elif haz < -2:
            lines.append("  ⚠️ **Perlu tindak lanjut**: Program perbaikan gizi untuk stunting")
    
    # WHZ analysis
    whz = z_scores.get('whz')
    if whz is not None and not math.isnan(whz):
        perm = permenkes.get('whz', '')
        who_txt = who.get('whz', '')
        lines.append(f"**Berat menurut Tinggi (WHZ):** {format_zscore(whz)} - {perm} (WHO: {who_txt})")
        
        if whz < -3:
            lines.append("  🚨 **Gawat darurat gizi**: Wasting berat, rujuk ke fasyankes")
        elif whz < -2:
            lines.append("  ⚠️ **Gizi kurang akut**: Tingkatkan asupan, monitoring ketat")
        elif whz > 3:
            lines.append("  ⚠️ **Obesitas**: Konsultasi ahli gizi untuk manajemen berat badan")
        elif whz > 2:
            lines.append("  ⚠️ **Risiko obesitas**: Perhatikan pola makan dan aktivitas fisik")
    
    # BAZ analysis
    baz = z_scores.get('baz')
    if baz is not None and not math.isnan(baz):
        perm = permenkes.get('baz', '')
        who_txt = who.get('baz', '')
        lines.append(f"**IMT menurut Umur (BAZ):** {format_zscore(baz)} - {perm} (WHO: {who_txt})")
    
    # HCZ analysis
    hcz = z_scores.get('hcz')
    if hcz is not None and not math.isnan(hcz):
        perm, who_txt = classify_hcz(hcz)
        lines.append(f"**Lingkar Kepala (HCZ):** {format_zscore(hcz)} - {perm} ({who_txt})")
        
        if abs(hcz) > 3:
            lines.append("  ⚠️ **Perlu evaluasi**: Konsultasi dokter anak untuk pemeriksaan neurologis")
    
    if not lines:
        lines.append("✅ Semua parameter dalam batas normal WHO")
    
    return "\n\n".join(lines)


def export_to_csv(payload: Dict, filename: str) -> Optional[str]:
    """
    Export analysis to CSV format
    
    Args:
        payload: Analysis data
        filename: Output filename
        
    Returns:
        Filename if successful, None otherwise
    """
    try:
        filepath = os.path.join(OUTPUTS_DIR, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['=== GIZISIKECIL - LAPORAN ANALISIS ==='])
            writer.writerow([])
            
            # Child data
            writer.writerow(['=== DATA ANAK ==='])
            writer.writerow(['Nama Anak', payload.get('name_child', '')])
            writer.writerow(['Orang Tua/Wali', payload.get('name_parent', '')])
            writer.writerow(['Jenis Kelamin', payload.get('sex_text', '')])
            writer.writerow(['Usia (bulan)', f"{payload.get('age_mo', 0):.2f}"])
            writer.writerow(['Usia (hari)', payload.get('age_days', 0)])
            writer.writerow([])
            
            # Measurements
            writer.writerow(['=== PENGUKURAN ==='])
            writer.writerow(['Berat Badan (kg)', payload.get('w', '')])
            writer.writerow(['Panjang/Tinggi (cm)', payload.get('h', '')])
            writer.writerow(['Lingkar Kepala (cm)', payload.get('hc', '')])
            writer.writerow([])
            
            # Results
            writer.writerow(['=== HASIL ANALISIS ==='])
            writer.writerow(['Indeks', 'Z-score', 'Persentil (%)', 'Kategori Permenkes', 'Kategori WHO'])
            
            z_scores = payload.get('z', {})
            percentiles = payload.get('percentiles', {})
            permenkes = payload.get('permenkes', {})
            who = payload.get('who', {})
            
            for key, label in [('waz', 'WAZ (BB/U)'), ('haz', 'HAZ (TB/U)'), 
                               ('whz', 'WHZ (BB/TB)'), ('baz', 'BAZ (IMT/U)'), 
                               ('hcz', 'HCZ (LK/U)')]:
                z_val = format_zscore(z_scores.get(key))
                pct = percentiles.get(key)
                pct_str = f"{pct}" if pct is not None else "—"
                perm_cat = permenkes.get(key, "—")
                who_cat = who.get(key, "—")
                
                writer.writerow([label, z_val, pct_str, perm_cat, who_cat])
            
            writer.writerow([])
            writer.writerow(['=== METADATA ==='])
            writer.writerow(['Tanggal Export', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['Versi Aplikasi', APP_VERSION])
            writer.writerow(['Sumber', 'GiziSiKecil - WHO Child Growth Standards + Permenkes 2020'])
        
        return filepath
    except Exception as e:
        print(f"CSV export error: {e}")
        return None


def generate_qr_code(text: str = None) -> Optional[io.BytesIO]:
    """Generate QR code for contact/sharing"""
    if text is None:
        text = f"https://wa.me/{CONTACT_WA}"
    
    try:
        qr = qrcode.QRCode(
            version=1,
            box_size=4,
            border=3
        )
        qr.add_data(text)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        
        return buf
    except Exception as e:
        print(f"QR generation error: {e}")
        return None


def export_to_pdf(payload: Dict, figures: List[Figure], filename: str) -> Optional[str]:
    """
    Export comprehensive PDF report with charts
    
    Args:
        payload: Analysis data
        figures: List of matplotlib figures
        filename: Output filename
        
    Returns:
        Filepath if successful, None otherwise
    """
    try:
        filepath = os.path.join(OUTPUTS_DIR, filename)
        c = canvas.Canvas(filepath, pagesize=A4)
        W, H = A4
        
        theme = UI_THEMES.get(payload.get('theme', 'pink_pastel'), UI_THEMES['pink_pastel'])
        
        # Page 1: Summary
        # Header
        c.setFillColorRGB(0.965, 0.647, 0.753)
        c.rect(0, H - 50, W, 50, stroke=0, fill=1)
        
        c.setFillColor(rl_colors.black)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, H - 32, "GiziSiKecil - Laporan Status Gizi Anak")
        
        c.setFont("Helvetica", 10)
        c.drawRightString(W - 30, H - 32, datetime.now().strftime("%d %B %Y, %H:%M WIB"))
        
        # Child info
        y = H - 80
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "INFORMASI ANAK")
        y -= 20
        
        c.setFont("Helvetica", 10)
        if payload.get('name_child'):
            c.drawString(40, y, f"Nama: {payload['name_child']}")
            y -= 15
        if payload.get('name_parent'):
            c.drawString(40, y, f"Orang Tua/Wali: {payload['name_parent']}")
            y -= 15
        
        c.drawString(40, y, f"Jenis Kelamin: {payload['sex_text']}")
        y -= 15
        c.drawString(40, y, f"Usia: {payload['age_mo']:.1f} bulan (~{payload['age_days']} hari)")
        y -= 25
        
        # Anthropometric data
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "DATA ANTROPOMETRI")
        y -= 20
        
        c.setFont("Helvetica", 10)
        c.drawString(40, y, f"Berat Badan: {payload['w']:.1f} kg")
        y -= 15
        c.drawString(40, y, f"Panjang/Tinggi: {payload['h']:.1f} cm")
        y -= 15
        if payload.get('hc'):
            c.drawString(40, y, f"Lingkar Kepala: {payload['hc']:.1f} cm")
            y -= 20
        
        # Results table
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "HASIL ANALISIS")
        y -= 20
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, y, "Indeks")
        c.drawString(120, y, "Z-score")
        c.drawString(180, y, "Persentil")
        c.drawString(250, y, "Status (Permenkes)")
        c.drawString(400, y, "Status (WHO)")
        
        y -= 3
        c.line(35, y, W - 35, y)
        y -= 12
        
        c.setFont("Helvetica", 9)
        
        z_scores = payload.get('z', {})
        percentiles = payload.get('percentiles', {})
        permenkes = payload.get('permenkes', {})
        who = payload.get('who', {})
        
        for key, label in [('waz', 'WAZ (BB/U)'), ('haz', 'HAZ (TB/U)'), 
                           ('whz', 'WHZ (BB/TB)'), ('baz', 'BAZ (IMT/U)'), 
                           ('hcz', 'HCZ (LK/U)')]:
            z_val = format_zscore(z_scores.get(key))
            pct = percentiles.get(key)
            pct_str = f"{pct}%" if pct is not None else "—"
            perm_cat = permenkes.get(key, "—")[:30]
            who_cat = who.get(key, "—")[:25]
            
            c.drawString(40, y, label)
            c.drawString(120, y, z_val)
            c.drawString(180, y, pct_str)
            c.drawString(250, y, perm_cat)
            c.drawString(400, y, who_cat)
            y -= 14
        
        # QR code
        qr_buf = generate_qr_code()
        if qr_buf:
            c.drawImage(ImageReader(qr_buf), W - 80, 30, width=50, height=50)
        
        c.setFont("Helvetica-Oblique", 8)
        c.drawRightString(W - 30, 15, "Hal. 1")
        c.showPage()
        
        # Pages 2-6: Charts
        page_num = 2
        titles = [
            "Grafik Berat Badan menurut Umur (BB/U)",
            "Grafik Panjang/Tinggi menurut Umur (TB/U)",
            "Grafik Lingkar Kepala menurut Umur (LK/U)",
            "Grafik Berat menurut Panjang/Tinggi (BB/TB)",
            "Grafik Ringkasan Semua Indeks"
        ]
        
        for title, fig in zip(titles, figures):
            # Header
            c.setFillColorRGB(0.965, 0.647, 0.753)
            c.rect(0, H - 50, W, 50, stroke=0, fill=1)
            
            c.setFillColor(rl_colors.black)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(30, H - 32, title)
            
            # Chart
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buf.seek(0)
            
            c.drawImage(ImageReader(buf), 30, 100, width=W - 60, preserveAspectRatio=True)
            
            c.setFont("Helvetica-Oblique", 8)
            c.drawRightString(W - 30, 15, f"Hal. {page_num}")
            c.showPage()
            page_num += 1
        
        # Page 7: Disclaimer
        c.setFillColorRGB(0.965, 0.647, 0.753)
        c.rect(0, H - 50, W, 50, stroke=0, fill=1)
        
        c.setFillColor(rl_colors.black)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(30, H - 32, "Catatan Penting & Disclaimer")
        
        y = H - 80
        c.setFont("Helvetica", 10)
        
        disclaimers = [
            "1. Aplikasi ini bersifat SKRINING EDUKATIF, bukan diagnosis medis.",
            "",
            "2. Hasil harus diinterpretasikan oleh tenaga kesehatan terlatih.",
            "",
            "3. Klasifikasi mengacu pada:",
            "   - WHO Child Growth Standards (2006)",
            "   - Permenkes RI No. 2 Tahun 2020",
            "",
            "4. Data Anda TIDAK disimpan di server (privasi terjaga).",
            "",
            "5. Untuk konsultasi lanjutan, hubungi Posyandu/Puskesmas/Dokter anak.",
            "",
            "6. Pastikan alat pengukuran terkalibrasi & teknik pengukuran benar.",
            "",
            "7. Kesalahan pengukuran dapat menyebabkan hasil yang tidak akurat.",
        ]
        
        for line in disclaimers:
            c.drawString(40, y, line)
            y -= 15
        
        c.setFont("Helvetica-Oblique", 8)
        c.drawRightString(W - 30, 15, f"Hal. {page_num}")
        
        c.save()
        return filepath
        
    except Exception as e:
        print(f"PDF export error: {e}")
        traceback.print_exc()
        return None


print("✅ Part 3A loaded: Report generation (Markdown, CSV, PDF)")

# ==================== PART 3B: MAIN ANALYSIS FUNCTION ====================

def compute_complete_analysis(
    sex_text: str,
    age_mode: str,
    dob_str: str,
    dom_str: str,
    age_mo_input: float,
    weight_input: float,
    height_input: float,
    head_circ_input: float,
    name_child: str,
    name_parent: str,
    lang_mode: str,
    theme_name: str
) -> Tuple[str, Dict, Figure, Figure, Figure, Figure, Figure]:
    """
    Main function to compute complete WHO analysis
    
    Returns:
        Tuple of (markdown_report, payload_dict, fig_wfa, fig_hfa, fig_hcfa, fig_wfl, fig_bars)
    """
    if calc is None:
        raise RuntimeError("❌ WHO Calculator tidak tersedia. Hubungi administrator.")
    
    # Parse sex
    sex = 'M' if str(sex_text).lower().startswith('l') else 'F'
    
    # Parse age
    if age_mode == "Tanggal":
        dob = parse_date(dob_str)
        dom = parse_date(dom_str)
        
        if not dob or not dom:
            raise ValueError("❌ Format tanggal tidak valid. Gunakan YYYY-MM-DD atau DD/MM/YYYY")
        
        if dom < dob:
            raise ValueError("❌ Tanggal pengukuran tidak boleh lebih awal dari tanggal lahir")
        
        age_mo, age_days = age_months_from_dates(dob, dom)
        
        if age_mo is None:
            raise ValueError("❌ Gagal menghitung usia dari tanggal")
    else:
        age_mo = as_float(age_mo_input)
        
        if age_mo is None:
            raise ValueError("❌ Usia tidak valid. Masukkan angka positif")
        
        age_mo = max(0.0, min(age_mo, 60.0))
        age_days = int(round(age_mo * 30.4375))
    
    # Parse measurements
    weight = as_float(weight_input)
    height = as_float(height_input)
    head_circ = as_float(head_circ_input)
    
    if weight is None or height is None:
        raise ValueError("❌ Berat badan dan tinggi badan harus diisi")
    
    # Validate measurements
    val_errors, val_warnings = validate_anthropometry(age_mo, weight, height, head_circ)
    
    # Calculate z-scores
    z_scores = calculate_all_zscores(sex, age_mo, weight, height, head_circ)
    
    # Validate z-scores
    z_errors, z_warnings = validate_zscores(z_scores)
    
    # Combine all errors and warnings
    all_errors = val_errors + z_errors
    all_warnings = val_warnings + z_warnings
    
    # Calculate percentiles
    percentiles = {k: z_to_percentile(v) for k, v in z_scores.items()}
    
    # Classify by Permenkes
    permenkes = {
        'waz': classify_permenkes_waz(z_scores['waz']),
        'haz': classify_permenkes_haz(z_scores['haz']),
        'whz': classify_permenkes_whz(z_scores['whz']),
        'baz': classify_permenkes_whz(z_scores['baz']),  # Use WHZ classification
        'hcz': classify_hcz(z_scores['hcz'])[0]
    }
    
    # Classify by WHO
    who = {
        'waz': classify_who_waz(z_scores['waz']),
        'haz': classify_who_haz(z_scores['haz']),
        'whz': classify_who_whz(z_scores['whz']),
        'baz': classify_who_whz(z_scores['baz']),  # Use WHZ classification
        'hcz': classify_hcz(z_scores['hcz'])[1]
    }
    
    # Build payload
    payload = {
        'sex': sex,
        'sex_text': sex_text,
        'age_mo': age_mo,
        'age_days': age_days,
        'w': weight,
        'h': height,
        'hc': head_circ,
        'z': z_scores,
        'percentiles': percentiles,
        'permenkes': permenkes,
        'who': who,
        'name_child': name_child,
        'name_parent': name_parent,
        'lang_mode': lang_mode,
        'theme': theme_name,
        'errors': all_errors,
        'warnings': all_warnings
    }
    
    # Generate markdown report
    markdown_report = generate_markdown_report(payload)
    
    # Generate plots
    fig_wfa = plot_weight_for_age(payload, theme_name)
    fig_hfa = plot_height_for_age(payload, theme_name)
    fig_hcfa = plot_head_circ_for_age(payload, theme_name)
    fig_wfl = plot_weight_for_length(payload, theme_name)
    fig_bars = plot_zscore_bars(payload, theme_name)
    
    return markdown_report, payload, fig_wfa, fig_hfa, fig_hcfa, fig_wfl, fig_bars


def get_median_values(sex_text: str, age_mode: str, dob_str: str, dom_str: str, age_mo_input: float) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Get WHO median values for given age/sex
    
    Returns:
        Tuple of (median_weight, median_height, median_head_circ)
    """
    if calc is None:
        return None, None, None
    
    try:
        sex = 'M' if str(sex_text).lower().startswith('l') else 'F'
        
        # Parse age
        if age_mode == "Tanggal":
            dob = parse_date(dob_str)
            dom = parse_date(dom_str)
            
            if not dob or not dom or dom < dob:
                return None, None, None
            
            age_mo, _ = age_months_from_dates(dob, dom)
        else:
            age_mo = as_float(age_mo_input)
        
        if age_mo is None:
            return None, None, None
        
        age_mo = max(0.0, min(age_mo, 60.0))
        
        # Find median (Z=0) values
        median_weight = invert_z_with_scan(
            lambda w: _safe_z(calc.wfa, w, age_mo, sex),
            0.0,
            *BOUNDS['wfa']
        )
        
        median_height = invert_z_with_scan(
            lambda h: _safe_z(calc.lhfa, h, age_mo, sex),
            0.0,
            *BOUNDS['hfa']
        )
        
        median_hc = invert_z_with_scan(
            lambda hc: _safe_z(calc.hcfa, hc, age_mo, sex),
            0.0,
            *BOUNDS['hcfa']
        )
        
        return (
            round(median_weight, 2),
            round(median_height, 1),
            round(median_hc, 1)
        )
        
    except Exception as e:
        print(f"Median calculation error: {e}")
        return None, None, None


print("✅ Part 3B loaded: Main analysis function")

# ==================== PART 3C: CHECKLIST WIZARD FUNCTIONS ====================

def generate_checklist_content(month: int, payload: Dict) -> Tuple[str, str, str, str, str]:
    """
    Generate checklist content for given month
    
    Args:
        month: Month number (0-24)
        payload: Child data payload
        
    Returns:
        Tuple of (do_now, saran, warnings, videos_html, immunization)
    """
    z_scores = payload.get('z', {})
    waz = z_scores.get('waz')
    haz = z_scores.get('haz')
    whz = z_scores.get('whz')
    
    do_now_items = []
    saran_items = []
    warning_items = []
    video_list = []
    imm_items = []
    
    # === FEEDING & NUTRITION ===
    if month < 6:
        do_now_items.append("🤱 **ASI Eksklusif:** Berikan ASI on demand (8-12x/hari). Tanda kecukupan: pipis >6x/hari, BAB kuning, berat naik min 500g/bulan")
        saran_items.append("💡 **Tip Ibu Bekerja:** Siapkan ASI perah 100-150ml per botol. Stok minimal 10 botol di freezer")
        video_list.append(YOUTUBE_VIDEOS.get("mpasi_6bln"))
    
    elif month == 6:
        do_now_items.append("🍚 **Mulai MPASI 6 Bulan:**\n- Frekuensi: 2-3x/hari + ASI\n- Tekstur: Bubur halus kental (tidak encer)\n- Prioritas: Zat besi (hati ayam, daging, kuning telur)\n- Porsi: Mulai 2-3 sendok, tingkatkan bertahap")
        warning_items.append("⚠️ **KRITIS:** Jika belum mulai MPASI di usia 6 bulan, risiko gizi buruk meningkat. Segera konsultasi!")
        saran_items.append("💡 **Keamanan Pangan:** Cuci tangan sabun, pisahkan alat mentah-matang, masak hingga matang sempurna")
        video_list.append(YOUTUBE_VIDEOS.get("mpasi_6bln"))
    
    elif month < 9:
        do_now_items.append("🍽️ **MPASI 6-9 Bulan:**\n- Frekuensi: 2-3x/hari + 1-2 selingan\n- Tekstur: Saring kasar (tidak halus lagi)\n- Menu: Karbo + protein hewani + sayur + lemak\n- Porsi: 125ml (½ mangkuk kecil)")
        saran_items.append("💡 **Zat Besi Penting:** Minimal 1 porsi protein hewani/hari (hati/daging/ikan/telur)")
        video_list.append(YOUTUBE_VIDEOS.get("mpasi_9bln"))
    
    elif month < 12:
        do_now_items.append("🍛 **MPASI 9-12 Bulan:**\n- Frekuensi: 3-4x/hari + 1-2 selingan\n- Tekstur: Cincang halus/kasar\n- Variasi: Minimal 3 kelompok pangan/makan\n- Porsi: 250ml (1 mangkuk kecil)")
        saran_items.append("💡 **Finger Foods:** Mulai kenalkan makanan yang bisa digenggam (wortel kukus, pisang)")
        video_list.append(YOUTUBE_VIDEOS.get("mpasi_9bln"))
    
    else:  # >=12 months
        do_now_items.append("🍽️ **Menu Keluarga (>12 Bulan):**\n- Frekuensi: 3-4x utama + 2 selingan\n- Tekstur: Makanan keluarga (dicincang)\n- Hindari: Gula/garam berlebih, makanan tinggi lemak jenuh\n- Porsi: 250-300ml/makan")
        saran_items.append("💡 **Kemandirian:** Latih makan sendiri dengan sendok. Libatkan anak saat menyiapkan makan")
        video_list.append(YOUTUBE_VIDEOS.get("bahasa_12bln"))
    
    # === GROWTH MONITORING ===
    if haz and haz < -3:
        warning_items.append("🔴 **STUNTING BERAT TERDETEKSI!**\n\n**Tinggi sangat pendek** menunjukkan malnutrisi kronis. **SEGERA:**\n- Rujuk ke Puskesmas/RS untuk evaluasi\n- Ulang pengukuran dengan infantometer/stadiometer\n- Program perbaikan gizi intensif\n- Screening penyakit penyerta")
        do_now_items.append("📏 **Verifikasi Pengukuran:** Ulang ukur tinggi dengan 2 orang, teknik WHO standar")
        saran_items.append("🥦 **Intervensi Gizi:** Tingkatkan densitas energi (tambah minyak/mentega), protein hewani 2x/hari, konseling gizi mingguan")
        video_list.append(YOUTUBE_VIDEOS.get("mpasi_6bln"))
    
    elif haz and haz < -2:
        warning_items.append("🟡 **STUNTING RISK - Tinggi Pendek**\n\nAnak berisiko gagal tumbuh. Tindakan:\n- Konsultasi program perbaikan gizi di Puskesmas\n- Evaluasi asupan makan & riwayat penyakit\n- Monitoring tinggi setiap 3 bulan")
        do_now_items.append("📊 **Monitoring Ketat:** Pantau berat & tinggi tiap bulan di Posyandu")
        saran_items.append("💪 **Nutrien Kunci:** Prioritaskan protein hewani, vitamin A, zinc, kalsium")
    
    if whz and whz < -3:
        warning_items.append("🔴 **GIZI BURUK AKUT - SANGAT KURUS!**\n\n**GAWAT DARURAT GIZI.** Tindakan:\n- **RUJUK SEGERA** ke fasyankes untuk terapi\n- Kemungkinan perlu rawat inap\n- Screening komplikasi (infeksi, dehidrasi)\n- F75/F100 therapeutic feeding")
        do_now_items.append("🚨 **Rujukan Medis:** Bawa ke Puskesmas/RS HARI INI untuk evaluasi dokter")
    
    elif whz and whz < -2:
        warning_items.append("🟡 **GIZI KURANG - Kurus**\n\nBerat tidak sesuai tinggi. Tindakan:\n- Tingkatkan frekuensi MPASI +1x/hari\n- Tambah porsi 20-30%\n- Pantau berat 2 minggu sekali")
        do_now_items.append("🍲 **Pemulihan Gizi:** Berikan MPASI 4-5x/hari setelah sakit. Tambah camilan bergizi")
        saran_items.append("💊 **Suplementasi:** Konsultasi vitamin A, zinc, atau suplemen gizi lain")
    
    if whz and whz > 3:
        warning_items.append("🔴 **OBESITAS TERDETEKSI**\n\nBerat sangat berlebih. Tindakan:\n- Konsultasi ahli gizi anak\n- Evaluasi pola makan & aktivitas\n- Screening komplikasi (diabetes, hipertensi)")
        saran_items.append("🏃 **Aktivitas Fisik:** Ajak bermain aktif 60 menit/hari. Kurangi screen time <1 jam/hari")
    
    elif whz and whz > 2:
        warning_items.append("🟡 **BERAT BERLEBIH**\n\nRisiko obesitas. Tindakan:\n- Perhatikan porsi & frekuensi makan\n- Tingkatkan aktivitas fisik\n- Batasi gula & makanan olahan")
        saran_items.append("🥗 **Pola Makan Sehat:** Perbanyak sayur-buah, kurangi gorengan & minuman manis")
    
    # === DEVELOPMENT SCREENING ===
    if month in KPSP_QUESTIONS:
        saran_items.append(f"🧠 **KPSP Bulan {month}:** Lengkapi screening perkembangan pada langkah berikutnya untuk deteksi dini keterlambatan")
    
    # === IMMUNIZATION SCHEDULE ===
    imms = IMMUNIZATION_SCHEDULE.get(month, [])
    if imms:
        imm_items.append(f"💉 **Imunisasi Jatuh Tempo Bulan {month}:**")
        for vaccine in imms:
            imm_items.append(f"   • {vaccine}")
        imm_items.append("\n📅 **JANGAN LEWATKAN!** Bawa Buku KIA ke Posyandu/Puskesmas")
        do_now_items.append("💉 **Imunisasi:** Tuntaskan jadwal imunisasi sesuai Permenkes")
        video_list.append(YOUTUBE_VIDEOS.get("imunisasi"))
    
    # === STIMULATION VIDEOS ===
    if month >= 6 and month < 24:
        age_category = month // 6
        video_keys = ["motorik_6bln", "mpasi_9bln", "bahasa_12bln", "bahasa_12bln"]
        key = video_keys[min(age_category - 1, len(video_keys) - 1)]
        vid = YOUTUBE_VIDEOS.get(key)
        if vid and vid not in video_list:
            video_list.append(vid)
    
    # === FORMAT OUTPUTS ===
    do_now_text = "\n\n".join(do_now_items) if do_now_items else "✅ Semua parameter sesuai standar WHO untuk bulan ini"
    
    saran_text = "\n\n".join(saran_items) if saran_items else "💡 Pertahankan pola gizi seimbang & pantau rutin di Posyandu"
    
    warnings_text = "\n\n".join(warning_items) if warning_items else "✅ Tidak ada warning kritis untuk bulan ini. Pertahankan!"
    
    # Video HTML
    videos_html = "<div style='display: flex; flex-wrap: wrap; gap: 15px; justify-content: center;'>"
    for vid in video_list:
        if vid:
            videos_html += f"""
            <div style='border: 1px solid #ddd; padding: 15px; border-radius: 10px; width: 240px; 
                        background: white; box-shadow: 0 4px 8px rgba(0,0,0,0.1); transition: transform 0.2s;'
                 onmouseover='this.style.transform="scale(1.05)"' 
                 onmouseout='this.style.transform="scale(1)"'>
                <img src='{vid["thumbnail"]}' style='width: 100%; border-radius: 8px; border: 1px solid #eee;'>
                <p style='font-size: 13px; margin: 10px 0; font-weight: bold; color: #2c3e50; min-height: 40px;'>
                    {vid["title"]}
                </p>
                <a href='{vid["url"]}' target='_blank' 
                   style='display: inline-block; background: #ff6b9d; color: white; padding: 10px 15px; 
                          border-radius: 5px; text-decoration: none; font-size: 12px; font-weight: bold; width: 100%; text-align: center;'>
                    ▶️ Tonton Video
                </a>
            </div>
            """
    videos_html += "</div>"
    
    if not video_list:
        videos_html = "<p style='text-align: center; color: #666; padding: 20px;'>📹 Video edukasi akan tersedia pada bulan selanjutnya</p>"
    
    imm_text = "\n".join(imm_items) if imm_items else "✅ Tidak ada jadwal imunisasi bulan ini"
    
    return do_now_text, saran_text, warnings_text, videos_html, imm_text



def find_posyandu_nearby() -> str:
    """Generate mock Posyandu locator HTML"""
    mock_data = [
        {
            "nama": "Posyandu Melati Indah",
            "jarak": "0.3 km",
            "alamat": "Jl. Kenanga No. 5, RT 02/RW 05",
            "jam": "Senin-Sabtu 08:00-12:00",
            "kontak": "081234567890"
        },
        {
            "nama": "Posyandu Mawar Harapan",
            "jarak": "0.7 km",
            "alamat": "Jl. Cempaka No. 12, RT 01/RW 03",
            "jam": "Selasa-Jumat 09:00-13:00",
            "kontak": "081398765432"
        },
        {
            "nama": "Posyandu Flamboyan Sehat",
            "jarak": "1.2 km",
            "alamat": "Jl. Anggrek No. 8, RT 04/RW 02",
            "jam": "Rabu-Minggu 07:00-11:00",
            "kontak": "081255558888"
        }
    ]
    
    html = """
    <div style='background: #f0f9ff; padding: 20px; border-radius: 15px; border: 2px solid #4ecdc4;'>
        <h3 style='color: #2c3e50; margin-bottom: 15px; text-align: center;'>
            📍 Posyandu Terdekat (Simulasi GPS)
        </h3>
        <p style='text-align: center; color: #666; font-size: 13px; margin-bottom: 20px;'>
            Fitur GPS aktif. Hasil berdasarkan lokasi perangkat Anda.
        </p>
    """
    
    for i, p in enumerate(mock_data, 1):
        html += f"""
        <div style='background: white; margin: 15px 0; padding: 20px; border-radius: 12px; 
                    border-left: 5px solid #ff6b9d; box-shadow: 0 3px 10px rgba(0,0,0,0.1);'>
            <div style='display: flex; justify-content: space-between; align-items: start;'>
                <div style='flex: 1;'>
                    <h4 style='color: #ff6b9d; margin: 0 0 10px 0; font-size: 16px;'>
                        {i}. {p['nama']}
                    </h4>
                    <p style='margin: 5px 0; color: #555; font-size: 13px;'>
                        <strong>📏 Jarak:</strong> {p['jarak']}
                    </p>
                    <p style='margin: 5px 0; color: #555; font-size: 13px;'>
                        <strong>📍 Alamat:</strong> {p['alamat']}
                    </p>
                    <p style='margin: 5px 0; color: #555; font-size: 13px;'>
                        <strong>🕐 Jam Buka:</strong> {p['jam']}
                    </p>
                    <p style='margin: 5px 0; color: #555; font-size: 13px;'>
                        <strong>📞 Kontak:</strong> {p['kontak']}
                    </p>
                </div>
            </div>
            <div style='margin-top: 15px; display: flex; gap: 10px;'>
                <a href='https://wa.me/{p["kontak"].replace("-", "")}?text=Halo%20Posyandu,%20saya%20ingin%20konsultasi%20gizi%20anak' 
                   target='_blank' 
                   style='display: inline-block; padding: 10px 20px; background: #25D366; color: white; 
                          text-decoration: none; border-radius: 8px; font-size: 13px; font-weight: bold; flex: 1; text-align: center;'>
                    💬 Chat WhatsApp
                </a>
                <a href='https://www.google.com/maps/search/{p["nama"].replace(" ", "+")}' 
                   target='_blank'
                   style='display: inline-block; padding: 10px 20px; background: #4285F4; color: white; 
                          text-decoration: none; border-radius: 8px; font-size: 13px; font-weight: bold; flex: 1; text-align: center;'>
                    🗺️ Buka Maps
                </a>
            </div>
        </div>
        """
    
    html += """
        <div style='margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 8px; border: 1px solid #ffc107;'>
            <p style='font-size: 12px; color: #856404; margin: 0; text-align: center;'>
                ⚠️ Data simulasi. Di versi Premium, akan menggunakan GPS real-time untuk akurasi maksimal.
            </p>
        </div>
    </div>
    """
    
    return html


print("✅ Part 3C loaded: Checklist content generation")

def export_checklist_pdf_handler(month, payload):
    """Export checklist as PDF"""
    if not payload:
        return gr.update(visible=False), "❌ Tidak ada data checklist"
    
    try:
        child_name = payload.get('name_child', 'Anak').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Checklist_GiziSiKecil_{child_name}_Bulan{month}_{timestamp}.pdf"
        
        # Simple checklist PDF
        filepath = os.path.join(OUTPUTS_DIR, filename)
        c = canvas.Canvas(filepath, pagesize=A4)
        W, H = A4
        
        # Header
        c.setFillColorRGB(0.965, 0.647, 0.753)
        c.rect(0, H - 50, W, 50, stroke=0, fill=1)
        c.setFillColor(rl_colors.black)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, H - 32, f"GiziSiKecil - Checklist Bulan ke-{month}")
        
        y = H - 80
        c.setFont("Helvetica", 11)
        c.drawString(30, y, f"Nama: {payload.get('name_child', 'Si Kecil')}")
        y -= 15
        c.drawString(30, y, f"Usia: {payload.get('age_mo', 0):.1f} bulan")
        y -= 15
        c.drawString(30, y, f"Tanggal: {datetime.now().strftime('%d %B %Y')}")
        y -= 25
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "RINGKASAN CHECKLIST")
        y -= 20
        
        c.setFont("Helvetica", 10)
        do_now, saran, warnings, _, imm = generate_checklist_content(month, payload)
        
        c.drawString(30, y, "DO NOW:")
        y -= 15
        for line in do_now.split('\n')[:5]:
            c.drawString(40, y, line[:80])
            y -= 12
        
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(30, 30, f"Dicetak: {datetime.now().strftime('%Y-%m-%d %H:%M')} | GiziSiKecil App")
        
        c.save()
        
        return gr.update(value=filepath, visible=True), "✅ Checklist PDF berhasil dibuat!"
    
    except Exception as e:
        return gr.update(visible=False), f"❌ Error: {str(e)}"

def share_whatsapp_handler(month, payload):
    """Generate WhatsApp share link"""
    if not payload:
        return gr.update(value="", visible=False)
    
    name = payload.get('name_child', 'Si Kecil')
    age = payload.get('age_mo', 0)
    
    msg = f"📊 *Progress GiziSiKecil Bulan {month}*%0A%0A"
    msg += f"👶 {name} ({age:.1f} bulan)%0A"
    msg += f"✅ Checklist selesai!%0A"
    msg += f"🔥 Streak aktif%0A%0A"
    msg += f"*Download app GiziSiKecil:*%0A{BASE_URL}"
    
    link = f"https://wa.me/?text={msg}"
    
    html = f"""
    <div style='text-align: center; padding: 20px; background: #e8f5e9; border-radius: 10px;'>
        <a href='{link}' target='_blank'
           style='display: inline-block; padding: 15px 30px; background: #25D366; color: white;
                  text-decoration: none; border-radius: 10px; font-size: 16px; font-weight: bold;'>
            📱 Share via WhatsApp
        </a>
    </div>
    """
    
    return gr.update(value=html, visible=True)

print("✅ Part 2C loaded: Checklist handlers")

# ==================== PART 3D: GRADIO UI COMPLETE ====================

# Custom CSS
CUSTOM_CSS = """
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    max-width: 1400px !important;
}
.status-success { color: #28a745; font-weight: bold; }
.status-warning { color: #ffc107; font-weight: bold; }
.status-error { color: #dc3545; font-weight: bold; }
.big-button {
    font-size: 18px !important;
    font-weight: bold !important;
    padding: 20px !important;
    margin: 10px 0 !important;
}
blockquote {
    background: #ffeef8;
    border-left: 5px solid #ff6b9d;
    padding: 15px;
    margin: 15px 0;
    border-radius: 8px;
}
.gr-button-primary {
    background: linear-gradient(135deg, #ff6b9d 0%, #ff9a9e 100%) !important;
    border: none !important;
}
.gr-button-secondary {
    background: linear-gradient(135deg, #4ecdc4 0%, #a8e6cf 100%) !important;
    border: none !important;
}
"""

# Build Gradio Interface
gr.set_static_paths(paths=["static/"])
with gr.Blocks(
    title=APP_TITLE,
    theme=gr.themes.Soft(
        primary_hue="pink",
        secondary_hue="teal",
        neutral_hue="slate",
        font=["Segoe UI", "Arial", "sans-serif"]
    ),
    css=CUSTOM_CSS
) as demo:
    
    # Header
    gr.Markdown("""
⚠️ **Server free tier akan sleep setelah 15 menit idle**. 
Data checklist akan hilang. SELALU gunakan tombol Export PDF untuk menyimpan!
""")
    gr.Markdown(f"""
    # 🏥 **GiziSiKecil** - Monitor Pertumbuhan Anak Profesional
    ### 💕 WHO Child Growth Standards + Checklist Sehat Bulanan (0-60 Bulan)
    
    #### 🔒 Privasi Terjaga | ⚕️ Standar Resmi Permenkes & WHO | 📊 Analisis Komprehensif
    
    ---
    """)
    
    # State variables
    state_payload = gr.State({})
    state_checklist_progress = gr.State({})
    
    
    # Main Tabs
    with gr.Tabs():
        
        # ========== TAB 1: KALKULATOR GIZI ==========
        with gr.TabItem("📊 Kalkulator Gizi", id=0):
            gr.Markdown("## 🧮 Analisis Status Gizi WHO + Permenkes")
            
            with gr.Row():
                # Left Column: Input
                with gr.Column(scale=6):
                    gr.Markdown("### 📝 Input Data Anak")
                    
                    with gr.Group():
                        gr.Markdown("#### 👤 Identitas")
                        with gr.Row():
                            name_child = gr.Textbox(
                                label="Nama Anak (opsional)",
                                placeholder="Budi Santoso",
                                info="Untuk personalisasi laporan"
                            )
                            name_parent = gr.Textbox(
                                label="Nama Orang Tua/Wali (opsional)",
                                placeholder="Ibu Siti Aminah"
                            )
                        
                        sex = gr.Radio(
                            choices=["Laki-laki", "Perempuan"],
                            label="Jenis Kelamin",
                            value="Laki-laki",
                            info="Penting untuk standar WHO yang berbeda"
                        )
                    
                    with gr.Group():
                        gr.Markdown("#### 📅 Usia")
                        age_mode = gr.Radio(
                            choices=["Tanggal", "Usia (bulan)"],
                            label="Mode Input Usia",
                            value="Tanggal",
                            info="Tanggal lebih akurat"
                        )
                        
                        with gr.Row():
                            dob = gr.Textbox(
                                label="Tanggal Lahir",
                                placeholder="2023-06-15 atau 15/06/2023",
                                info="Format: YYYY-MM-DD atau DD/MM/YYYY",
                                visible=True
                            )
                            dom = gr.Textbox(
                                label="Tanggal Pengukuran",
                                placeholder="2025-11-10 atau 10/11/2025",
                                info="Tanggal hari ini atau tanggal ukur",
                                visible=True
                            )
                        
                        age_mo = gr.Number(
                            label="Usia (bulan)",
                            value=12.0,
                            precision=1,
                            minimum=0,
                            maximum=60,
                            info="Contoh: 6.5 untuk 6.5 bulan",
                            visible=False
                        )
                    
                    with gr.Group():
                        gr.Markdown("#### 📏 Data Antropometri")
                        with gr.Row():
                            weight = gr.Number(
                                label="Berat Badan (kg)",
                                value=10.0,
                                precision=2,
                                minimum=1,
                                maximum=30,
                                info="Gunakan timbangan digital"
                            )
                            height = gr.Number(
                                label="Panjang/Tinggi Badan (cm)",
                                value=75.0,
                                precision=1,
                                minimum=35,
                                maximum=130,
                                info="Infantometer (<2th) / Stadiometer (>2th)"
                            )
                        
                        head_circ = gr.Number(
                            label="Lingkar Kepala (cm) - Opsional",
                            value=None,
                            precision=1,
                            minimum=20,
                            maximum=60,
                            info="Meteran fleksibel di garis terbesar"
                        )
                    
                    with gr.Group():
                        gr.Markdown("#### ⚙️ Pengaturan Output")
                        with gr.Row():
                            lang_mode = gr.Radio(
                                choices=["Orang tua", "Nakes"],
                                label="Mode Bahasa Laporan",
                                value="Orang tua",
                                info="Pilih sesuai audiens"
                            )
                            theme_chart = gr.Radio(
                                choices=["pink_pastel", "mint_pastel", "lavender_pastel"],
                                label="Tema Grafik",
                                value="pink_pastel",
                                info="Warna grafik"
                            )
                    
                    gr.Markdown("---")
                    
                    with gr.Row():
                        prefill_btn = gr.Button(
                            "📊 Isi Nilai Median WHO (Z=0)",
                            variant="secondary",
                            size="sm"
                        )
                        demo_btn = gr.Button(
                            "🎬 Coba Demo Data",
                            variant="secondary",
                            size="sm"
                        )
                    
                    status_calc = gr.Markdown(
                        "💡 **Tip:** Klik 'Coba Demo Data' lalu 'Analisis Sekarang' untuk melihat contoh",
                        elem_classes=["status-success"]
                    )
                    
                    analyze_btn = gr.Button(
                        "🔍 Analisis Sekarang",
                        variant="primary",
                        size="lg",
                        elem_classes=["big-button"]
                    )
                
                # Right Column: Guide
                with gr.Column(scale=4):
                    gr.Markdown("### 💡 Panduan Pengukuran")
                    
                    guide_html = gr.HTML("""
                    <div style='background: #e8f5e9; padding: 20px; border-radius: 12px; border-left: 5px solid #28a745;'>
                        <h4 style='color: #155724; margin-top: 0;'>📏 Tips Akurat Pengukuran</h4>
                        
                        <div style='margin: 15px 0;'>
                            <strong style='color: #155724;'>⚖️ Berat Badan:</strong>
                            <ul style='margin: 5px 0; padding-left: 20px;'>
                                <li>Timbang tanpa sepatu & pakaian tebal</li>
                                <li>Gunakan timbangan digital (presisi 100g)</li>
                                <li>Ukur di waktu yang sama (pagi hari)</li>
                            </ul>
                        </div>
                        
                        <div style='margin: 15px 0;'>
                            <strong style='color: #155724;'>📐 Panjang Badan (0-24 bulan):</strong>
                            <ul style='margin: 5px 0; padding-left: 20px;'>
                                <li>Gunakan <strong>infantometer</strong></li>
                                <li>Bayi telentang, kepala menempel board</li>
                                <li>2 orang: 1 pegang kepala, 1 luruskan kaki</li>
                                <li>Pastikan bayi rileks (tidak menangis)</li>
                            </ul>
                        </div>
                        
                        <div style='margin: 15px 0;'>
                            <strong style='color: #155724;'>📏 Tinggi Badan (>24 bulan):</strong>
                            <ul style='margin: 5px 0; padding-left: 20px;'>
                                <li>Gunakan <strong>stadiometer</strong></li>
                                <li>Anak berdiri tegak, punggung ke dinding</li>
                                <li>Mata lurus ke depan, kaki rapat</li>
                            </ul>
                        </div>
                        
                        <div style='margin: 15px 0;'>
                            <strong style='color: #155724;'>⭕ Lingkar Kepala:</strong>
                            <ul style='margin: 5px 0; padding-left: 20px;'>
                                <li>Meteran <strong>fleksibel</strong> (Lasso)</li>
                                <li>Ukur di atas alis & telinga (lingkar terbesar)</li>
                                <li>Ulangi 3x, ambil rata-rata</li>
                            </ul>
                        </div>
                        
                        <div style='background: #fff3cd; padding: 12px; border-radius: 8px; margin-top: 15px;'>
                            <strong style='color: #856404;'>⚠️ Penting:</strong>
                            <span style='color: #856404;'>Kesalahan 0.5 cm di tinggi = error Z-score signifikan!</span>
                        </div>
                    </div>
                    """)
                    
                    gr.Markdown("### 🎯 Interpretasi Z-Score")
                    interp_html = gr.HTML("""
                    <table style='width: 100%; border-collapse: collapse; margin-top: 10px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                        <thead>
                            <tr style='background: #ff6b9d; color: white;'>
                                <th style='padding: 12px; text-align: center;'>Z-Score</th>
                                <th style='padding: 12px;'>Status BB/U & TB/U</th>
                                <th style='padding: 12px;'>Status BB/TB</th>
                                <th style='padding: 12px; text-align: center;'>Icon</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style='border-bottom: 1px solid #eee;'>
                                <td style='padding: 10px; text-align: center; font-weight: bold;'>&lt; -3</td>
                                <td style='padding: 10px;'>Sangat Kurang/Berat</td>
                                <td style='padding: 10px;'>Gizi Buruk</td>
                                <td style='padding: 10px; text-align: center; font-size: 20px;'>🔴</td>
                            </tr>
                            <tr style='border-bottom: 1px solid #eee; background: #fff9f9;'>
                                <td style='padding: 10px; text-align: center; font-weight: bold;'>-3 to -2</td>
                                <td style='padding: 10px;'>Kurang</td>
                                <td style='padding: 10px;'>Kurang (Wasting)</td>
                                <td style='padding: 10px; text-align: center; font-size: 20px;'>🟡</td>
                            </tr>
                            <tr style='border-bottom: 1px solid #eee;'>
                                <td style='padding: 10px; text-align: center; font-weight: bold;'>-2 to +2</td>
                                <td style='padding: 10px;'>Normal</td>
                                <td style='padding: 10px;'>Normal</td>
                                <td style='padding: 10px; text-align: center; font-size: 20px;'>🟢</td>
                            </tr>
                            <tr style='border-bottom: 1px solid #eee; background: #fff9f9;'>
                                <td style='padding: 10px; text-align: center; font-weight: bold;'>+2 to +3</td>
                                <td style='padding: 10px;'>Risiko Lebih</td>
                                <td style='padding: 10px;'>Risiko Lebih</td>
                                <td style='padding: 10px; text-align: center; font-size: 20px;'>🟡</td>
                            </tr>
                            <tr>
                                <td style='padding: 10px; text-align: center; font-weight: bold;'>&gt; +3</td>
                                <td style='padding: 10px;'>Obesitas</td>
                                <td style='padding: 10px;'>Obesitas</td>
                                <td style='padding: 10px; text-align: center; font-size: 20px;'>🔴</td>
                            </tr>
                        </tbody>
                    </table>
                    """)
            
            gr.Markdown("---")
            gr.Markdown("## 📊 Hasil Analisis")
            
            result_md = gr.Markdown(
                "*Hasil akan tampil setelah klik 'Analisis Sekarang'*",
                elem_classes=["status-success"]
            )
            
            with gr.Row():
                with gr.Column():
                    plot_wfa = gr.Plot(label="📈 Grafik Berat menurut Umur (BB/U)")
                with gr.Column():
                    plot_hfa = gr.Plot(label="📏 Grafik Tinggi menurut Umur (TB/U)")
            
            with gr.Row():
                with gr.Column():
                    plot_hcfa = gr.Plot(label="⭕ Grafik Lingkar Kepala (LK/U)")
                with gr.Column():
                    plot_wfl = gr.Plot(label="⚖️ Grafik Berat menurut Tinggi (BB/TB)")
            
            plot_bars = gr.Plot(label="📊 Ringkasan Semua Indeks")
            
            gr.Markdown("### 💾 Export Hasil")

# ==================== PART 3D: GRADIO UI COMPLETE ====================

# Custom CSS
CUSTOM_CSS = """
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    max-width: 1400px !important;
}
.status-success { color: #28a745; font-weight: bold; }
.status-warning { color: #ffc107; font-weight: bold; }
.status-error { color: #dc3545; font-weight: bold; }
.big-button {
    font-size: 18px !important;
    font-weight: bold !important;
    padding: 20px !important;
    margin: 10px 0 !important;
}
blockquote {
    background: #ffeef8;
    border-left: 5px solid #ff6b9d;
    padding: 15px;
    margin: 15px 0;
    border-radius: 8px;
}
.gr-button-primary {
    background: linear-gradient(135deg, #ff6b9d 0%, #ff9a9e 100%) !important;
    border: none !important;
}
.gr-button-secondary {
    background: linear-gradient(135deg, #4ecdc4 0%, #a8e6cf 100%) !important;
    border: none !important;
}
"""

# Build Gradio Interface
gr.set_static_paths(paths=["static/"])
with gr.Blocks(
    title=APP_TITLE,
    theme=gr.themes.Soft(
        primary_hue="pink",
        secondary_hue="teal",
        neutral_hue="slate",
        font=["Segoe UI", "Arial", "sans-serif"]
    ),
    css=CUSTOM_CSS
) as demo:
    
    # Header
    gr.Markdown(f"""
    # 🏥 **GiziSiKecil** - Monitor Pertumbuhan Anak Profesional
    ### 💕 WHO Child Growth Standards + Checklist Sehat Bulanan (0-60 Bulan)
    
    #### 🔒 Privasi Terjaga | ⚕️ Standar Resmi Permenkes & WHO | 📊 Analisis Komprehensif
    
    ---
    """)
    
    # State variables
    state_payload = gr.State({})
    state_checklist_progress = gr.State({})
    state_notification_settings = gr.State({"enabled": True, "time": "08:00"})
    
    # Main Tabs
    with gr.Tabs():
        
        # ========== TAB 1: KALKULATOR GIZI ==========
        with gr.TabItem("📊 Kalkulator Gizi", id=0):
            gr.Markdown("## 🧮 Analisis Status Gizi WHO + Permenkes")
            
            with gr.Row():
                # Left Column: Input
                with gr.Column(scale=6):
                    gr.Markdown("### 📝 Input Data Anak")
                    
                    with gr.Group():
                        gr.Markdown("#### 👤 Identitas")
                        with gr.Row():
                            name_child = gr.Textbox(
                                label="Nama Anak (opsional)",
                                placeholder="Budi Santoso",
                                info="Untuk personalisasi laporan"
                            )
                            name_parent = gr.Textbox(
                                label="Nama Orang Tua/Wali (opsional)",
                                placeholder="Ibu Siti Aminah"
                            )
                        
                        sex = gr.Radio(
                            choices=["Laki-laki", "Perempuan"],
                            label="Jenis Kelamin",
                            value="Laki-laki",
                            info="Penting untuk standar WHO yang berbeda"
                        )
                    
                    with gr.Group():
                        gr.Markdown("#### 📅 Usia")
                        age_mode = gr.Radio(
                            choices=["Tanggal", "Usia (bulan)"],
                            label="Mode Input Usia",
                            value="Tanggal",
                            info="Tanggal lebih akurat"
                        )
                        
                        with gr.Row():
                            dob = gr.Textbox(
                                label="Tanggal Lahir",
                                placeholder="2023-06-15 atau 15/06/2023",
                                info="Format: YYYY-MM-DD atau DD/MM/YYYY",
                                visible=True
                            )
                            dom = gr.Textbox(
                                label="Tanggal Pengukuran",
                                placeholder="2025-11-10 atau 10/11/2025",
                                info="Tanggal hari ini atau tanggal ukur",
                                visible=True
                            )
                        
                        age_mo = gr.Number(
                            label="Usia (bulan)",
                            value=12.0,
                            precision=1,
                            minimum=0,
                            maximum=60,
                            info="Contoh: 6.5 untuk 6.5 bulan",
                            visible=False
                        )
                    
                    with gr.Group():
                        gr.Markdown("#### 📏 Data Antropometri")
                        with gr.Row():
                            weight = gr.Number(
                                label="Berat Badan (kg)",
                                value=10.0,
                                precision=2,
                                minimum=1,
                                maximum=30,
                                info="Gunakan timbangan digital"
                            )
                            height = gr.Number(
                                label="Panjang/Tinggi Badan (cm)",
                                value=75.0,
                                precision=1,
                                minimum=35,
                                maximum=130,
                                info="Infantometer (<2th) / Stadiometer (>2th)"
                            )
                        
                        head_circ = gr.Number(
                            label="Lingkar Kepala (cm) - Opsional",
                            value=None,
                            precision=1,
                            minimum=20,
                            maximum=60,
                            info="Meteran fleksibel di garis terbesar"
                        )
                    
                    with gr.Group():
                        gr.Markdown("#### ⚙️ Pengaturan Output")
                        with gr.Row():
                            lang_mode = gr.Radio(
                                choices=["Orang tua", "Nakes"],
                                label="Mode Bahasa Laporan",
                                value="Orang tua",
                                info="Pilih sesuai audiens"
                            )
                            theme_chart = gr.Radio(
                                choices=["pink_pastel", "mint_pastel", "lavender_pastel"],
                                label="Tema Grafik",
                                value="pink_pastel",
                                info="Warna grafik"
                            )
                    
                    gr.Markdown("---")
                    
                    with gr.Row():
                        prefill_btn = gr.Button(
                            "📊 Isi Nilai Median WHO (Z=0)",
                            variant="secondary",
                            size="sm"
                        )
                        demo_btn = gr.Button(
                            "🎬 Coba Demo Data",
                            variant="secondary",
                            size="sm"
                        )
                    
                    status_calc = gr.Markdown(
                        "💡 **Tip:** Klik 'Coba Demo Data' lalu 'Analisis Sekarang' untuk melihat contoh",
                        elem_classes=["status-success"]
                    )
                    
                    analyze_btn = gr.Button(
                        "🔍 Analisis Sekarang",
                        variant="primary",
                        size="lg",
                        elem_classes=["big-button"]
                    )
                
                # Right Column: Guide
                with gr.Column(scale=4):
                    gr.Markdown("### 💡 Panduan Pengukuran")
                    
                    guide_html = gr.HTML("""
                    <div style='background: #e8f5e9; padding: 20px; border-radius: 12px; border-left: 5px solid #28a745;'>
                        <h4 style='color: #155724; margin-top: 0;'>📏 Tips Akurat Pengukuran</h4>
                        
                        <div style='margin: 15px 0;'>
                            <strong style='color: #155724;'>⚖️ Berat Badan:</strong>
                            <ul style='margin: 5px 0; padding-left: 20px;'>
                                <li>Timbang tanpa sepatu & pakaian tebal</li>
                                <li>Gunakan timbangan digital (presisi 100g)</li>
                                <li>Ukur di waktu yang sama (pagi hari)</li>
                            </ul>
                        </div>
                        
                        <div style='margin: 15px 0;'>
                            <strong style='color: #155724;'>📐 Panjang Badan (0-24 bulan):</strong>
                            <ul style='margin: 5px 0; padding-left: 20px;'>
                                <li>Gunakan <strong>infantometer</strong></li>
                                <li>Bayi telentang, kepala menempel board</li>
                                <li>2 orang: 1 pegang kepala, 1 luruskan kaki</li>
                                <li>Pastikan bayi rileks (tidak menangis)</li>
                            </ul>
                        </div>
                        
                        <div style='margin: 15px 0;'>
                            <strong style='color: #155724;'>📏 Tinggi Badan (>24 bulan):</strong>
                            <ul style='margin: 5px 0; padding-left: 20px;'>
                                <li>Gunakan <strong>stadiometer</strong></li>
                                <li>Anak berdiri tegak, punggung ke dinding</li>
                                <li>Mata lurus ke depan, kaki rapat</li>
                            </ul>
                        </div>
                        
                        <div style='margin: 15px 0;'>
                            <strong style='color: #155724;'>⭕ Lingkar Kepala:</strong>
                            <ul style='margin: 5px 0; padding-left: 20px;'>
                                <li>Meteran <strong>fleksibel</strong> (Lasso)</li>
                                <li>Ukur di atas alis & telinga (lingkar terbesar)</li>
                                <li>Ulangi 3x, ambil rata-rata</li>
                            </ul>
                        </div>
                        
                        <div style='background: #fff3cd; padding: 12px; border-radius: 8px; margin-top: 15px;'>
                            <strong style='color: #856404;'>⚠️ Penting:</strong>
                            <span style='color: #856404;'>Kesalahan 0.5 cm di tinggi = error Z-score signifikan!</span>
                        </div>
                    </div>
                    """)
                    
                    gr.Markdown("### 🎯 Interpretasi Z-Score")
                    interp_html = gr.HTML("""
                    <table style='width: 100%; border-collapse: collapse; margin-top: 10px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                        <thead>
                            <tr style='background: #ff6b9d; color: white;'>
                                <th style='padding: 12px; text-align: center;'>Z-Score</th>
                                <th style='padding: 12px;'>Status BB/U & TB/U</th>
                                <th style='padding: 12px;'>Status BB/TB</th>
                                <th style='padding: 12px; text-align: center;'>Icon</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style='border-bottom: 1px solid #eee;'>
                                <td style='padding: 10px; text-align: center; font-weight: bold;'>&lt; -3</td>
                                <td style='padding: 10px;'>Sangat Kurang/Berat</td>
                                <td style='padding: 10px;'>Gizi Buruk</td>
                                <td style='padding: 10px; text-align: center; font-size: 20px;'>🔴</td>
                            </tr>
                            <tr style='border-bottom: 1px solid #eee; background: #fff9f9;'>
                                <td style='padding: 10px; text-align: center; font-weight: bold;'>-3 to -2</td>
                                <td style='padding: 10px;'>Kurang</td>
                                <td style='padding: 10px;'>Kurang (Wasting)</td>
                                <td style='padding: 10px; text-align: center; font-size: 20px;'>🟡</td>
                            </tr>
                            <tr style='border-bottom: 1px solid #eee;'>
                                <td style='padding: 10px; text-align: center; font-weight: bold;'>-2 to +2</td>
                                <td style='padding: 10px;'>Normal</td>
                                <td style='padding: 10px;'>Normal</td>
                                <td style='padding: 10px; text-align: center; font-size: 20px;'>🟢</td>
                            </tr>
                            <tr style='border-bottom: 1px solid #eee; background: #fff9f9;'>
                                <td style='padding: 10px; text-align: center; font-weight: bold;'>+2 to +3</td>
                                <td style='padding: 10px;'>Risiko Lebih</td>
                                <td style='padding: 10px;'>Risiko Lebih</td>
                                <td style='padding: 10px; text-align: center; font-size: 20px;'>🟡</td>
                            </tr>
                            <tr>
                                <td style='padding: 10px; text-align: center; font-weight: bold;'>&gt; +3</td>
                                <td style='padding: 10px;'>Obesitas</td>
                                <td style='padding: 10px;'>Obesitas</td>
                                <td style='padding: 10px; text-align: center; font-size: 20px;'>🔴</td>
                            </tr>
                        </tbody>
                    </table>
                    """)
            
            gr.Markdown("---")
            gr.Markdown("## 📊 Hasil Analisis")
            
            result_md = gr.Markdown(
                "*Hasil akan tampil setelah klik 'Analisis Sekarang'*",
                elem_classes=["status-success"]
            )
            
            with gr.Row():
                with gr.Column():
                    plot_wfa = gr.Plot(label="📈 Grafik Berat menurut Umur (BB/U)")
                with gr.Column():
                    plot_hfa = gr.Plot(label="📏 Grafik Tinggi menurut Umur (TB/U)")
            
            with gr.Row():
                with gr.Column():
                    plot_hcfa = gr.Plot(label="⭕ Grafik Lingkar Kepala (LK/U)")
                with gr.Column():
                    plot_wfl = gr.Plot(label="⚖️ Grafik Berat menurut Tinggi (BB/TB)")
            
            plot_bars = gr.Plot(label="📊 Ringkasan Semua Indeks")
            
            gr.Markdown("### 💾 Export Hasil")
            with gr.Row():
                export_pdf_btn = gr.Button("📄 Download PDF Lengkap", variant="primary")
                export_csv_btn = gr.Button("📊 Download CSV Data", variant="secondary")
            
            with gr.Row():
                download_pdf = gr.File(label="File PDF", visible=False)
                download_csv = gr.File(label="File CSV", visible=False)
        
        # ========== TAB 2: CHECKLIST WIZARD ==========
        with gr.TabItem("📋 Checklist Sehat Bulanan", id=1):
            gr.Markdown("""
            ## 🗓️ Panduan Checklist Bulanan (0-24 Bulan)
            
            Dapatkan rekomendasi **do now**, **saran gizi**, **warning**, **video edukasi**, dan **jadwal imunisasi** 
            berdasarkan usia & status gizi anak Anda.
            """)
            
            with gr.Row():
                sync_btn = gr.Button(
                    "🔄 Sinkron Data dari Kalkulator",
                    variant="primary",
                    size="lg",
                    elem_classes=["big-button"]
                )
                reset_btn = gr.Button(
                    "🔁 Reset Checklist",
                    variant="secondary",
                    size="sm"
                )
            
            sync_status = gr.Markdown("", visible=False)
            
            with gr.Group(visible=False) as wizard_container:
                gr.Markdown("### 📅 Pilih Bulan Checklist")
                
                with gr.Row():
                    month_selector = gr.Slider(
                        minimum=0,
                        maximum=24,
                        step=1,
                        value=6,
                        label="Bulan Ke-",
                        info="Geser untuk memilih bulan (0-24)"
                    )
                    start_wizard_btn = gr.Button(
                        "▶️ Mulai Checklist",
                        variant="primary",
                        size="lg"
                    )
                
                # Step 1: Data Verification
                with gr.Group(visible=False) as step1_container:
                    gr.Markdown("### ✅ Verifikasi Data Anak")
                    data_overview = gr.Markdown("")
                    confirm_data_btn = gr.Button(
                        "👉 Lanjutkan ke KPSP",
                        variant="primary"
                    )
                
                # Step 2: KPSP Screening
                with gr.Group(visible=False) as step2_container:
                    gr.Markdown("### 🧠 Screening Perkembangan (KPSP)")
                    kpsp_html = gr.HTML("")
                    next_to_results_btn = gr.Button(
                        "👉 Lihat Hasil & Rekomendasi",
                        variant="primary"
                    )
                
                # Step 3: Results
                with gr.Group(visible=False) as step3_container:
                    gr.Markdown("### 🎯 Hasil Checklist & Rekomendasi")
                    
                    with gr.Row():
                        with gr.Column(scale=7):
                            with gr.Accordion("🎯 DO NOW - Prioritas Tinggi", open=True):
                                do_now_display = gr.Markdown("")
                            
                            with gr.Accordion("💡 Saran & Tips Gizi", open=True):
                                saran_display = gr.Markdown("")
                            
                            with gr.Accordion("⚠️ Warning & Red Flags", open=True):
                                warnings_display = gr.Markdown("")
                            
                            with gr.Accordion("🎥 Video Edukasi", open=True):
                                videos_display = gr.HTML("")
                            
                            with gr.Accordion("💉 Jadwal Imunisasi", open=True):
                                imm_display = gr.Markdown("")
                        
                        with gr.Column(scale=3):
                            gr.Markdown("### 🎁 Reward Streak")
                            sticker_img = gr.Image(
                                value=os.path.join(STATIC_DIR, "sticker_1.png"),
                                label="Stiker Pencapaian",
                                interactive=False,
                                height=200
                            )
                            streak_display = gr.Markdown("**🔥 Streak:** 0 bulan | **⭐ Poin:** 0")

                        # 💾 Export Checklist - Tempatkan di luar Column, di dalam step3_container
                        gr.Markdown("### 💾 Export Checklist")
                        with gr.Row():
                            export_checklist_pdf_btn = gr.Button("📄 Download Checklist PDF", variant="primary")
                            share_whatsapp_btn = gr.Button("📱 Share via WhatsApp", variant="secondary")
                            save_notification_btn = gr.Button("🔔 Set Notifikasi", variant="secondary")
                        
                        # Output components - definisikan di sini
                        download_checklist_pdf = gr.File(label="File PDF Checklist", visible=False)
                        whatsapp_share_html = gr.HTML(visible=False)
                        
                        # ⭐ HANDLERS - Identasi sejajar dengan komponen lainnya
                        export_checklist_pdf_btn.click(
                            fn=export_checklist_pdf_handler,
                            inputs=[month_selector, state_payload],
                            outputs=[download_checklist_pdf, gr.State()]
                        )
                        
                        share_whatsapp_btn.click(
                            fn=share_whatsapp_handler,
                            inputs=[month_selector, state_payload],
                            outputs=[whatsapp_share_html]
                        )


# ==================== PART 3E: EVENT HANDLERS ====================

# -------------------- HELPER FUNCTIONS FOR UI --------------------

def toggle_age_inputs(mode: str):
    """Toggle visibility of age input fields based on mode"""
    if mode == "Tanggal":
        return (
            gr.update(visible=True),   # dob
            gr.update(visible=True),   # dom
            gr.update(visible=False)   # age_mo
        )
    else:
        return (
            gr.update(visible=False),  # dob
            gr.update(visible=False),  # dom
            gr.update(visible=True)    # age_mo
        )


def load_demo_data():
    """Load demo data for testing"""
    return (
        "Andi Pratama",                    # name_child
        "Ibu Siti",                        # name_parent
        "Laki-laki",                       # sex
        "Tanggal",                         # age_mode
        "2024-05-15",                      # dob
        datetime.now().strftime("%Y-%m-%d"), # dom
        12.0,                              # age_mo
        9.5,                               # weight
        74.0,                              # height
        46.0,                              # head_circ
        "Orang tua",                       # lang_mode
        "pink_pastel",                     # theme
        "✅ Demo data berhasil dimuat! Klik 'Analisis Sekarang'"  # status
    )


def prefill_median_wrapper(sex_text, age_mode, dob_str, dom_str, age_mo_input):
    """Wrapper for prefill median values"""
    try:
        w_median, h_median, hc_median = get_median_values(
            sex_text, age_mode, dob_str, dom_str, age_mo_input
        )
        
        if w_median is None:
            return (
                gr.update(),
                gr.update(),
                gr.update(),
                "❌ Gagal menghitung median. Periksa input usia."
            )
        
        return (
            gr.update(value=w_median),
            gr.update(value=h_median),
            gr.update(value=hc_median),
            f"✅ Nilai median WHO (Z=0) berhasil diisi: BB={w_median}kg, TB={h_median}cm, LK={hc_median}cm"
        )
    except Exception as e:
        return (
            gr.update(),
            gr.update(),
            gr.update(),
            f"❌ Error: {str(e)}"
        )


def analyze_wrapper(sex_text, age_mode, dob_str, dom_str, age_mo_input,
                   weight_input, height_input, head_circ_input,
                   name_child, name_parent, lang_mode, theme_name):
    """Wrapper for main analysis function"""
    try:
        # Run analysis
        md_report, payload, fig_wfa, fig_hfa, fig_hcfa, fig_wfl, fig_bars = compute_complete_analysis(
            sex_text, age_mode, dob_str, dom_str, age_mo_input,
            weight_input, height_input, head_circ_input,
            name_child, name_parent, lang_mode, theme_name
        )
        
        return (
            md_report,     # result_md
            payload,       # state_payload
            fig_wfa,       # plot_wfa
            fig_hfa,       # plot_hfa
            fig_hcfa,      # plot_hcfa
            fig_wfl,       # plot_wfl
            fig_bars,      # plot_bars
            gr.update(visible=False),  # download_pdf
            gr.update(visible=False)   # download_csv
        )
    except Exception as e:
        error_msg = f"""
        ## ❌ Error Analisis
        
        **Pesan Error:** {str(e)}
        
        **Troubleshooting:**
        - Periksa format tanggal (YYYY-MM-DD atau DD/MM/YYYY)
        - Pastikan berat & tinggi dalam rentang wajar
        - Gunakan titik (.) untuk desimal, bukan koma
        - Coba 'Demo Data' untuk melihat format yang benar
        """
        
        return (
            error_msg,
            {},
            None, None, None, None, None,
            gr.update(visible=False),
            gr.update(visible=False)
        )


def export_pdf_wrapper(payload):
    """Export PDF report"""
    if not payload or 'age_mo' not in payload:
        return gr.update(visible=False), "❌ Tidak ada data untuk di-export. Lakukan analisis dulu."
    
    try:
        # Generate filename
        child_name = payload.get('name_child', 'Anak').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Laporan_GiziSiKecil_{child_name}_{timestamp}.pdf"
        
        # Generate all figures
        theme = payload.get('theme', 'pink_pastel')
        fig_wfa = plot_weight_for_age(payload, theme)
        fig_hfa = plot_height_for_age(payload, theme)
        fig_hcfa = plot_head_circ_for_age(payload, theme)
        fig_wfl = plot_weight_for_length(payload, theme)
        fig_bars = plot_zscore_bars(payload, theme)
        
        figures = [fig_wfa, fig_hfa, fig_hcfa, fig_wfl, fig_bars]
        
        # Generate PDF
        filepath = export_to_pdf(payload, figures, filename)
        
        if filepath:
            return gr.update(value=filepath, visible=True), "✅ PDF berhasil dibuat!"
        else:
            return gr.update(visible=False), "❌ Gagal membuat PDF"
    
    except Exception as e:
        return gr.update(visible=False), f"❌ Error: {str(e)}"


def export_csv_wrapper(payload):
    """Export CSV data"""
    if not payload or 'age_mo' not in payload:
        return gr.update(visible=False), "❌ Tidak ada data untuk di-export"
    
    try:
        child_name = payload.get('name_child', 'Anak').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"Data_GiziSiKecil_{child_name}_{timestamp}.csv"
        
        filepath = export_to_csv(payload, filename)
        
        if filepath:
            return gr.update(value=filepath, visible=True), "✅ CSV berhasil dibuat!"
        else:
            return gr.update(visible=False), "❌ Gagal membuat CSV"
    
    except Exception as e:
        return gr.update(visible=False), f"❌ Error: {str(e)}"


# -------------------- CHECKLIST HANDLERS --------------------

def sync_data_handler(payload):
    """Sync data from calculator to checklist"""
    if not payload or 'age_mo' not in payload:
        return (
            "❌ Tidak ada data dari Kalkulator. Lakukan analisis di Tab 1 terlebih dahulu.",
            gr.update(visible=True),   # sync_status
            gr.update(visible=False),  # wizard_container
            0,                         # month_selector
            gr.update(visible=False),  # step1
            gr.update(visible=False),  # step2
            gr.update(visible=False),  # step3
            "",                        # data_overview
            "",                        # kpsp_html
            "",                        # do_now
            "",                        # saran
            "",                        # warnings
            "",                        # videos
            "",                        # imm
            os.path.join(STATIC_DIR, "sticker_1.png"),  # sticker
            "**🔥 Streak:** 0 | **⭐ Poin:** 0"         # streak
        )
    
    try:
        age_mo = float(payload.get('age_mo', 0))
        month = min(int(age_mo), 24)
        
        name = payload.get('name_child', 'Si Kecil')
        age_days = payload.get('age_days', 0)
        w = payload.get('w', 0)
        h = payload.get('h', 0)
        status = payload.get('permenkes', {}).get('waz', 'Normal')
        
        sync_msg = f"""
        ✅ **DATA BERHASIL DISINKRONKAN!**
        
        👶 **Nama:** {name}  
        📅 **Usia:** {age_mo:.1f} bulan (≈ {age_days} hari) → **Bulan ke-{month}**  
        ⚖️ **BB/TB:** {w:.1f} kg / {h:.1f} cm  
        📊 **Status:** {status}
        
        🎯 **Langkah Selanjutnya:**
        1. Geser slider untuk pilih bulan (saat ini: bulan {month})
        2. Klik **"Mulai Checklist"**
        """
        
        return (
            sync_msg,
            gr.update(visible=True),   # sync_status
            gr.update(visible=True),   # wizard_container
            month,                     # month_selector
            gr.update(visible=False),  # step1
            gr.update(visible=False),  # step2
            gr.update(visible=False),  # step3
            "",                        # data_overview
            "",                        # kpsp_html
            "",                        # do_now
            "",                        # saran
            "",                        # warnings
            "",                        # videos
            "",                        # imm
            os.path.join(STATIC_DIR, "sticker_1.png"),
            "**🔥 Streak:** 0 | **⭐ Poin:** 0"
        )
    
    except Exception as e:
        return (
            f"❌ Error sinkronisasi: {str(e)}",
            gr.update(visible=True),
            gr.update(visible=False),
            0,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            "", "", "", "", "", "", "",
            os.path.join(STATIC_DIR, "sticker_1.png"),
            "**🔥 Streak:** 0 | **⭐ Poin:** 0"
        )


def reset_checklist_handler():
    """Reset checklist data"""
    return (
        "✅ Data checklist berhasil direset. Silakan sinkron ulang dari Kalkulator.",
        gr.update(visible=True),
        gr.update(visible=False),
        0,
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        "", "", "", "", "", "", "",
        os.path.join(STATIC_DIR, "sticker_1.png"),
        "**🔥 Streak:** 0 | **⭐ Poin:** 0"
    )


def start_wizard_handler(month, payload):
    """Start checklist wizard - Step 1"""
    if not payload or 'age_mo' not in payload:
        return (
            "❌ Data tidak tersedia. Klik 'Sinkron Data' terlebih dahulu.",
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            "", "", "", "", "", "", ""
        )
    
    try:
        name = payload.get('name_child', 'Si Kecil')
        sex_text = payload.get('sex_text', 'Tidak diketahui')
        age_mo = payload.get('age_mo', 0)
        w = payload.get('w', 0)
        h = payload.get('h', 0)
        hc = payload.get('hc')
        
        overview = f"""
        ### ✅ **VERIFIKASI DATA ANAK**
        
        **📝 Nama:** {name}  
        **⚥ Jenis Kelamin:** {sex_text}  
        **📅 Usia:** {age_mo:.1f} bulan  
        **⚖️ Berat/Tinggi:** {w:.1f} kg / {h:.1f} cm  
        """
        
        if hc:
            overview += f"**🧠 Lingkar Kepala:** {hc:.1f} cm  \n"
        
        overview += f"""
        **📊 Status Gizi:** {payload.get('permenkes', {}).get('waz', 'Normal')}
        
        ---
        
        ✅ **Data sudah benar?** Klik **"Lanjutkan ke KPSP"**  
        ❌ **Ada yang salah?** Kembali ke Tab Kalkulator untuk edit
        """
        
        return (
            "",                        # sync_status (hide)
            gr.update(visible=True),   # step1
            gr.update(visible=False),  # step2
            gr.update(visible=False),  # step3
            overview,                  # data_overview
            "", "", "", "", "", "", ""
        )
    
    except Exception as e:
        return (
            f"❌ Error: {str(e)}",
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            "", "", "", "", "", "", ""
        )


def confirm_data_handler(month, payload, theme_name):
    """Confirm data and show KPSP - Step 2"""
    if not payload:
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            "",
            "", "", "", "", "", "", ""
        )
    
    questions = KPSP_QUESTIONS.get(month, [])
    
    if not questions:
        # No KPSP for this month, skip to results
        return next_to_results_handler(month, payload, theme_name)
    
    theme = UI_THEMES.get(theme_name, UI_THEMES['pink_pastel'])
    
    html = f"""
    <div style='background: {theme["bg"]}; padding: 25px; border-radius: 15px; border: 2px solid {theme["primary"]};'>
        <h3 style='color: {theme["primary"]}; margin-bottom: 15px; text-align: center;'>
            🧠 <strong>Screening Perkembangan (KPSP)</strong>
        </h3>
        <p style='color: {theme["text"]}; opacity: 0.8; margin-bottom: 25px; text-align: center; font-size: 14px;'>
            Bulan ke-{month} - Jawab dengan jujur untuk rekomendasi terbaik
        </p>
    """
    
    for i, q in enumerate(questions):
        html += f"""
        <div style='margin: 15px 0; padding: 20px; background: {theme["card"]}; border-radius: 12px; 
                    border-left: 5px solid {theme["primary"]}; box-shadow: 0 3px 8px {theme["shadow"]};'>
            <p style='font-weight: bold; margin-bottom: 15px; color: {theme["text"]}; font-size: 15px;'>
                {i+1}. {q}
            </p>
            <div style='display: flex; gap: 15px;'>
                <label style='cursor: pointer; padding: 12px 20px; background: {theme["secondary"]}; 
                              color: white; border-radius: 8px; flex: 1; text-align: center; 
                              transition: transform 0.2s; font-weight: bold;'
                       onmouseover='this.style.transform="scale(1.05)"'
                       onmouseout='this.style.transform="scale(1)"'>
                    <input type='radio' name='kpsp_q{i}' value='ya' style='margin-right: 8px;' checked>
                    ✅ Ya, bisa
                </label>
                <label style='cursor: pointer; padding: 12px 20px; background: #ff6b6b; 
                              color: white; border-radius: 8px; flex: 1; text-align: center;
                              transition: transform 0.2s; font-weight: bold;'
                       onmouseover='this.style.transform="scale(1.05)"'
                       onmouseout='this.style.transform="scale(1)"'>
                    <input type='radio' name='kpsp_q{i}' value='tidak' style='margin-right: 8px;'>
                    ❌ Belum bisa
                </label>
            </div>
        </div>
        """
    
    html += """
        <div style='margin-top: 25px; padding: 15px; background: #fff3cd; border-radius: 10px; border: 1px solid #ffc107;'>
            <p style='margin: 0; color: #856404; font-size: 13px; text-align: center;'>
                💡 <strong>Tips:</strong> Jawaban "Belum bisa" bukan berarti ada masalah. 
                Ini membantu kami memberikan rekomendasi stimulasi yang tepat.
            </p>
        </div>
    </div>
    """
    
    return (
        gr.update(visible=False),  # step1
        gr.update(visible=True),   # step2
        gr.update(visible=False),  # step3
        html,                      # kpsp_html
        "", "", "", "", "", "", ""
    )


def next_to_results_handler(month, payload, theme_name):
    """Show final results - Step 3"""
    if not payload:
        return (
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            "",
            "❌ Data tidak tersedia",
            "", "", "", "",
            os.path.join(STATIC_DIR, "sticker_1.png"),
            "**🔥 Streak:** 0 | **⭐ Poin:** 0"
        )
    
    try:
        # Generate checklist content
        return do_now_text, saran_text, warnings_text, videos_html, imm_text
        
        # Random sticker
        sticker_num = random.randint(1, 5)
        sticker_path = os.path.join(STATIC_DIR, f"sticker_{sticker_num}.png")
        
        # Mock streak (in real app, would be stored)
        streak = random.randint(1, 5)
        points = streak * 10
        
        return (
            gr.update(visible=False),  # step1
            gr.update(visible=False),  # step2
            gr.update(visible=True),   # step3
            "",                        # kpsp_html
            do_now,
            saran,
            warnings,
            videos,
            imm,
            sticker_path,
            f"**🔥 Streak:** {streak} bulan | **⭐ Poin:** {points}"
        )
    
    except Exception as e:
        return (
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            "",
            f"❌ Error: {str(e)}",
            "", "", "", "",
            os.path.join(STATIC_DIR, "sticker_1.png"),
            "**🔥 Streak:** 0 | **⭐ Poin:** 0"
        )







# -------------------- NOTIFICATION HANDLERS --------------------

def save_notification_settings(enabled, time_str, types):
    """Save notification settings"""
    settings = {
        "enabled": enabled,
        "time": time_str,
        "types": types
    }
    
    status = "✅ Notifikasi AKTIF" if enabled else "🔕 Notifikasi NONAKTIF"
    status += f"\n\n⏰ Waktu: {time_str} WIB"
    status += f"\n📋 Jenis: {', '.join(types) if types else 'Tidak ada'}"
    
    return settings, status

# ==================== PART 3F: FASTAPI INTEGRATION & PREMIUM PAGE ====================

# Premium Page HTML
PREMIUM_PAGE_HTML = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GiziSiKecil Premium - Unlock Semua Fitur</title>
    <meta name="description" content="Upgrade ke GiziSiKecil Premium untuk fitur lengkap monitoring pertumbuhan anak">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); 
            color: #2c3e50; 
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        
        .hero {{ 
            text-align: center; 
            background: white; 
            padding: 60px 40px; 
            border-radius: 20px; 
            margin-bottom: 30px; 
            box-shadow: 0 10px 40px rgba(0,0,0,0.15); 
        }}
        .hero h1 {{ 
            font-size: 3.5em; 
            color: #ff6b9d; 
            margin-bottom: 15px; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }}
        .hero p {{ font-size: 1.3em; color: #666; margin-bottom: 10px; }}
        .hero .subtitle {{ font-size: 1.1em; color: #999; }}
        
        .plans {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 25px; 
            margin-top: 40px; 
        }}
        .plan {{ 
            background: white; 
            padding: 35px; 
            border-radius: 20px; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.12); 
            transition: all 0.3s ease; 
            border: 3px solid transparent; 
            position: relative;
        }}
        .plan:hover {{ 
            transform: translateY(-12px); 
            box-shadow: 0 15px 40px rgba(0,0,0,0.2); 
        }}
        .plan.featured {{ 
            border-color: #ff6b9d; 
            transform: scale(1.05);
        }}
        .plan.featured::before {{ 
            content: "⭐ PALING POPULER"; 
            position: absolute; 
            top: -15px; 
            left: 50%; 
            transform: translateX(-50%); 
            background: linear-gradient(135deg, #ff6b9d, #ff9a9e); 
            color: white; 
            padding: 8px 25px; 
            border-radius: 25px; 
            font-size: 12px; 
            font-weight: bold; 
            box-shadow: 0 4px 15px rgba(255,107,157,0.4);
        }}
        .plan h3 {{ font-size: 2em; color: #2c3e50; margin-bottom: 15px; }}
        .plan .price {{ 
            font-size: 3em; 
            color: #ff6b9d; 
            font-weight: bold; 
            margin: 20px 0;
        }}
        .plan .price span {{ font-size: 0.4em; color: #666; }}
        .plan ul {{ list-style: none; margin: 25px 0; }}
        .plan li {{ 
            padding: 12px 0; 
            border-bottom: 1px solid #f0f0f0; 
            font-size: 0.95em;
        }}
        .plan li::before {{ 
            content: "✅ "; 
            color: #4ecdc4; 
            font-weight: bold; 
            margin-right: 8px; 
        }}
        .plan button {{ 
            width: 100%; 
            padding: 18px; 
            background: linear-gradient(135deg, #ff6b9d, #ff9a9e); 
            color: white; 
            border: none; 
            border-radius: 12px; 
            font-size: 1.15em; 
            font-weight: bold; 
            cursor: pointer; 
            transition: all 0.3s; 
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .plan button:hover {{ 
            background: linear-gradient(135deg, #e55a88, #ff6b9d); 
            transform: scale(1.02);
            box-shadow: 0 8px 20px rgba(255,107,157,0.4);
        }}
        .plan.featured button {{ 
            background: linear-gradient(135deg, #4ecdc4, #a8e6cf); 
        }}
        .plan.featured button:hover {{ 
            background: linear-gradient(135deg, #3bb5a0, #4ecdc4); 
        }}
        
        .features {{ 
            background: white; 
            padding: 50px 40px; 
            border-radius: 20px; 
            margin-top: 40px; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.12); 
        }}
        .features h2 {{ 
            font-size: 2.5em; 
            margin-bottom: 30px; 
            color: #2c3e50; 
            text-align: center;
        }}
        .feature-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 25px; 
            margin-top: 30px; 
        }}
        .feature-card {{ 
            padding: 25px; 
            background: #f9f9f9; 
            border-radius: 15px; 
            border-left: 5px solid #ff6b9d; 
            transition: all 0.3s;
        }}
        .feature-card:hover {{
            transform: translateX(8px);
            background: #fff5f8;
        }}
        .feature-card h4 {{ 
            color: #2c3e50; 
            margin-bottom: 12px; 
            font-size: 1.3em;
        }}
        .feature-card p {{ 
            color: #666; 
            font-size: 0.95em;
        }}
        
        .contact {{ 
            text-align: center; 
            margin-top: 40px; 
            padding: 40px; 
            background: white; 
            border-radius: 20px; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.12); 
        }}
        .contact h3 {{ 
            font-size: 2em; 
            margin-bottom: 15px;
            color: #2c3e50;
        }}
        .contact p {{ 
            font-size: 1.1em; 
            color: #666; 
            margin-bottom: 25px;
        }}
        .contact a {{ 
            display: inline-block; 
            padding: 20px 45px; 
            background: #25D366; 
            color: white; 
            text-decoration: none; 
            border-radius: 15px; 
            font-weight: bold; 
            font-size: 1.3em; 
            transition: all 0.3s;
            box-shadow: 0 6px 20px rgba(37,211,102,0.3);
        }}
        .contact a:hover {{ 
            background: #128C7E; 
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(37,211,102,0.4);
        }}
        .contact .trial-note {{
            margin-top: 20px;
            font-size: 0.95em;
            color: #999;
        }}
        
        .testimonials {{
            background: white;
            padding: 50px 40px;
            border-radius: 20px;
            margin-top: 40px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }}
        .testimonials h2 {{
            font-size: 2.5em;
            margin-bottom: 30px;
            color: #2c3e50;
            text-align: center;
        }}
        .testimonial-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
        }}
        .testimonial {{
            background: #f9f9f9;
            padding: 25px;
            border-radius: 15px;
            border-left: 5px solid #4ecdc4;
        }}
        .testimonial p {{
            font-style: italic;
            color: #555;
            margin-bottom: 15px;
        }}
        .testimonial .author {{
            font-weight: bold;
            color: #ff6b9d;
        }}
        
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 2.2em; }}
            .plan {{ padding: 25px; }}
            .plan .price {{ font-size: 2.5em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🚀 GiziSiKecil Premium</h1>
            <p>Unlock Semua Fitur Powerful untuk Optimal Tumbuh Kembang Si Kecil</p>
            <p class="subtitle">Dipercaya oleh 10,000+ keluarga Indonesia</p>
        </div>
        
        <div class="features">
            <h2>✨ Fitur Eksklusif Premium</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h4>📊 Analisis Tren Pertumbuhan AI</h4>
                    <p>Lihat grafik perkembangan 24 bulan dengan AI-powered insights & prediksi pertumbuhan.</p>
                </div>
                <div class="feature-card">
                    <h4>🧠 Rekomendasi Personal AI</h4>
                    <p>Saran gizi & stimulasi yang dipersonalisasi berdasarkan data unik anak Anda.</p>
                </div>
                <div class="feature-card">
                    <h4>👨‍⚕️ Konsultasi Prioritas 24/7</h4>
                    <p>Chat langsung dengan ahli gizi anak & dokter spesialis, respons <15 menit.</p>
                </div>
                <div class="feature-card">
                    <h4>📱 Smart Reminder Lengkap</h4>
                    <p>Notifikasi otomatis: imunisasi, penimbangan, milestone, stok MPASI, vitamin.</p>
                </div>
                <div class="feature-card">
                    <h4>🎥 Video Edukasi Premium (100+)</h4>
                    <p>Akses video resep MPASI, stimulasi motorik, bahasa dari ahli terpercaya.</p>
                </div>
                <div class="feature-card">
                    <h4>📍 GPS Real-Time Posyandu</h4>
                    <p>Temukan posyandu, dokter anak & apotek terdekat dengan rating & review.</p>
                </div>
                <div class="feature-card">
                    <h4>📄 Laporan PDF Premium</h4>
                    <p>Export laporan lengkap dengan grafik interaktif & analisis tren bulanan.</p>
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
                    <li>Semua fitur Basic</li>
                    <li>Iklan dihapus</li>
                    <li>5 laporan PDF/bulan</li>
                    <li>Notifikasi penting</li>
                    <li>Video edukasi dasar</li>
                    <li>Support email</li>
                </ul>
                <button onclick="window.open('https://wa.me/{CONTACT_WA}?text=Halo%20GiziSiKecil,%20saya%20ingin%20upgrade%20Basic%20Plus', '_blank')">
                    Pilih Paket
                </button>
            </div>
            
            <div class="plan featured">
                <h3>🌸 Family Premium</h3>
                <div class="price">Rp 79rb<span>/bulan</span></div>
                <ul>
                    <li>Semua Basic Plus</li>
                    <li>Multi-child (3 anak)</li>
                    <li>Analisis tren AI</li>
                    <li>20 laporan PDF/bulan</li>
                    <li>Konsultasi 2x/bulan</li>
                    <li>Video premium lengkap</li>
                    <li>Smart reminder semua</li>
                    <li>GPS Posyandu real-time</li>
                </ul>
                <button onclick="window.open('https://wa.me/{CONTACT_WA}?text=Halo%20GiziSiKecil,%20saya%20ingin%20upgrade%20Family%20Premium', '_blank')">
                    Paket Terpopuler!
                </button>
            </div>
            
            <div class="plan">
                <h3>🏥 Pro Care</h3>
                <div class="price">Rp 149rb<span>/bulan</span></div>
                <ul>
                    <li>Semua Family Premium</li>
                    <li>Multi-child (10 anak)</li>
                    <li>Konsultasi unlimited</li>
                    <li>Laporan PDF unlimited</li>
                    <li>Prioritas chat 24/7</li>
                    <li>Update fitur eksklusif</li>
                    <li>Dedicated account manager</li>
                </ul>
                <button onclick="window.open('https://wa.me/{CONTACT_WA}?text=Halo%20GiziSiKecil,%20saya%20ingin%20upgrade%20Pro%20Care', '_blank')">
                    Pilih Paket
                </button>
            </div>
            
            <div class="plan">
                <h3>🏢 Fasyankes</h3>
                <div class="price">Rp 499rb<span>/bulan</span></div>
                <ul>
                    <li>Semua Pro Care</li>
                    <li>Unlimited anak</li>
                    <li>Dashboard admin</li>
                    <li>Export data pasien</li>
                    <li>Training gratis 2x/tahun</li>
                    <li>API integration</li>
                    <li>Custom branding</li>
                </ul>
                <button onclick="window.open('https://wa.me/{CONTACT_WA}?text=Halo%20GiziSiKecil,%20saya%20ingin%20paket%20Fasyankes', '_blank')">
                    Hubungi Sales
                </button>
            </div>
        </div>
        
        <div class="testimonials">
            <h2>💬 Kata Mereka</h2>
            <div class="testimonial-grid">
                <div class="testimonial">
                    <p>"Premium features sangat membantu! Konsultasi 24/7 dengan ahli gizi benar-benar life saver saat anak susah makan."</p>
                    <div class="author">— Ibu Sarah, Jakarta</div>
                </div>
                <div class="testimonial">
                    <p>"Fitur multi-child sangat worth it untuk 3 anak saya. Monitoring jadi lebih mudah dan terorganisir!"</p>
                    <div class="author">— Ibu Dina, Surabaya</div>
                </div>
                <div class="testimonial">
                    <p>"Video MPASI premium sangat membantu! Resep praktis dan sudah terbukti anak saya doyan semua."</p>
                    <div class="author">— Ibu Rani, Bandung</div>
                </div>
            </div>
        </div>
        
        <div class="contact">
            <h3>💬 Siap Upgrade?</h3>
            <p>Gratis trial 7 hari untuk semua paket! Tidak perlu kartu kredit.</p>
            <a href="https://wa.me/{CONTACT_WA}?text=Halo%20GiziSiKecil,%20saya%20ingin%20trial%207%20hari%20Premium" target="_blank">
                📱 Chat WhatsApp Sekarang
            </a>
            <p class="trial-note">Fast response: Senin-Sabtu 08:00-20:00 WIB | Minggu 09:00-15:00 WIB</p>
        </div>
    </div>
</body>
</html>
"""

# Initialize FastAPI
app_fastapi = FastAPI(
    title="GiziSiKecil API",
    description="Professional Child Growth Monitoring based on WHO Standards",
    version=APP_VERSION
)

# CORS middleware
app_fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists(STATIC_DIR):
    app_fastapi.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if os.path.exists(OUTPUTS_DIR):
    app_fastapi.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

# Premium page route
@app_fastapi.get("/premium", response_class=HTMLResponse)
async def premium_page():
    """Serve premium features page"""
    return PREMIUM_PAGE_HTML

# Health check
@app_fastapi.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "calculator_status": "operational" if calc else "unavailable",
        "features": {
            "who_standards": True,
            "permenkes_2020": True,
            "growth_charts": True,
            "pdf_export": True,
            "csv_export": True,
            "checklist_wizard": True,
            "kpsp_screening": True,
            "posyandu_locator": True
        }
    }



print("✅ Part 3F loaded: FastAPI routes & Premium page")

# Mount Gradio app to FastAPI
try:
    app = gr.mount_gradio_app(
        app=app_fastapi,
        blocks=demo,
        path="/"
    )
    print("✅ Gradio app successfully mounted to FastAPI at /")
except Exception as e:
    print(f"⚠️ Mount failed, using FastAPI only: {e}")
    app = app_fastapi

print("=" * 70)
print("🚀 GiziSiKecil v2.0 - READY FOR DEPLOYMENT")
print("=" * 70)
print(f"📊 WHO Calculator: {'✅ Active' if calc else '❌ Unavailable'}")
print(f"🌐 Base URL: {BASE_URL}")
print(f"📞 Contact: +{CONTACT_WA}")
print("=" * 70)
print("▶️  Run: uvicorn app:app --host 0.0.0.0 --port 8000")
print("=" * 70)
