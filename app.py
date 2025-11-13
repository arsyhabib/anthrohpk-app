#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         PeduliGiziBalita v3.2 - PRODUCTION                   ║
║                  Aplikasi Pemantauan Pertumbuhan Anak Profesional            ║
║                                                                              ║
║  Author:   Habib Arsy                                                       ║
║  Version:  3.2.0 (NEW FEATURES UPDATE)                                      ║
║  Standards: WHO Child Growth Standards 2006 + Permenkes RI No. 2 Tahun 2020 ║
║  License:  Educational & Healthcare Use                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

NEW IN v3.2:
✅ Mode Mudah - Quick reference untuk range normal
✅ Perpustakaan Updated - Link valid & terverifikasi (50+ artikel)
✅ Kalkulator Target Kejar Tumbuh - Growth velocity monitoring profesional
✅ Bug Fix - HTML rendering di checklist wizard

PREVIOUS v3.1 FEATURES:
✅ YouTube video education links integrated (KPSP & MP-ASI)
✅ Dark mode optimization for better contrast  
✅ Reminder slider changed from minutes to hours
✅ 50 curated Indonesian articles (now replaced by v3.2 library)
✅ Article previews with expandable summaries

PREVIOUS v3.0 FEATURES:
✅ Optimized code structure with proper error handling
✅ Enhanced UI/UX with better flow and feedback
✅ Memory management for matplotlib figures
✅ Robust WHO calculator integration
✅ Professional PDF reports with QR codes
✅ Comprehensive checklist wizard with KPSP
✅ Deployment-optimized for Render.com

RUN: uvicorn app:app --host 0.0.0.0 --port $PORT
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: IMPORTS & ENVIRONMENT SETUP
# ═══════════════════════════════════════════════════════════════════════════════

import sys
import os

# Ensure local modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core Python
import io
import csv
import math
import json
import random
import traceback
import warnings
from datetime import datetime, date, timedelta
from functools import lru_cache
from typing import Dict, List, Tuple, Optional, Any, Union

# Suppress warnings for cleaner logs
warnings.filterwarnings('ignore')

# WHO Growth Calculator
try:
    from pygrowup import Calculator
    print("✅ WHO Growth Calculator (pygrowup) loaded successfully")
except ImportError as e:
    print(f"❌ CRITICAL: pygrowup module not found! Error: {e}")
    print("   Please ensure pygrowup package is in the same directory")
    sys.exit(1)

# Scientific Computing
import numpy as np
from scipy.special import erf
import pandas as pd

# Visualization
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
plt.ioff()  # Disable interactive mode
plt.rcParams.update({
    'figure.max_open_warning': 0,  # Prevent memory leak warnings
    'figure.dpi': 100,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
})

# Image Processing
from PIL import Image
import qrcode

# PDF Generation
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors as rl_colors
from reportlab.lib.units import cm

# Web Framework
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Gradio UI
import gradio as gr

# HTTP Requests
import requests

print("✅ All imports successful")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: GLOBAL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Application Metadata
APP_VERSION = "3.2.0" # MODIFIED from v3.1
APP_TITLE = "PeduliGiziBalita - Monitor Pertumbuhan Anak Profesional" # MODIFIED
APP_DESCRIPTION = "Aplikasi berbasis WHO Child Growth Standards untuk pemantauan antropometri anak 0-60 bulan" # MODIFIED
CONTACT_WA = "6285888858160"
BASE_URL = "https://anthrohpk-app.onrender.com" # Note: Base URL (domain) di-hardcode, ganti jika perlu

# Premium Packages Configuration
PREMIUM_PACKAGES = {
    "silver": {
        "name": "Silver",
        "price": 10000,
        "features": [
            "🚫 Bebas Iklan",
            "📊 Semua fitur dasar",
            "💾 Export unlimited"
        ],
        "color": "#C0C0C0"
    },
    "gold": {
        "name": "Gold",
        "price": 50000,
        "features": [
            "🚫 Bebas Iklan",
            "🔔 Notifikasi Browser Customizable",
            "💬 3x Konsultasi 30 menit via WhatsApp dengan Ahli Gizi",
            "📊 Semua fitur dasar",
            "💾 Export unlimited",
            "⭐ Priority support"
        ],
        "color": "#FFD700"
    }
}

# Notification Templates
NOTIFICATION_TEMPLATES = {
    "monthly_checkup": {
        "title": "🩺 Waktunya Pemeriksaan Bulanan!",
        "body": "Sudah 30 hari sejak pemeriksaan terakhir. Yuk cek pertumbuhan {child_name}!",
        "icon": "📊"
    },
    "immunization": {
        "title": "💉 Jadwal Imunisasi",
        "body": "Jangan lupa! {child_name} perlu imunisasi {vaccine_name} hari ini.",
        "icon": "💉"
    },
    "milestone": {
        "title": "🎯 Milestone Alert",
        "body": "{child_name} sekarang {age} bulan! Cek milestone perkembangan.",
        "icon": "🌟"
    },
    "nutrition": {
        "title": "🍽️ Reminder Nutrisi",
        "body": "Waktunya memberi makan {child_name}. Menu hari ini: {menu}",
        "icon": "🥗"
    },
    "custom": {
        "title": "🔔 Pengingat Custom",
        "body": "{message}",
        "icon": "⏰"
    }
}

# Directories Setup
STATIC_DIR = "static"
OUTPUTS_DIR = "outputs"
PYGROWUP_DIR = "pygrowup"

# Create necessary directories
for directory in [STATIC_DIR, OUTPUTS_DIR]:
    os.makedirs(directory, exist_ok=True)
    print(f"✅ Directory ensured: {directory}")

# WHO Calculator Configuration
CALC_CONFIG = {
    'adjust_height_data': False,
    'adjust_weight_scores': False,
    'include_cdc': False,
    'logger_name': 'who_calculator',
    'log_level': 'ERROR'
}

# Anthropometric Measurement Bounds (WHO Standards)
BOUNDS = {
    'wfa': (1.0, 30.0),      # Weight-for-Age (kg)
    'hfa': (45.0, 125.0),    # Height-for-Age (cm)
    'hcfa': (30.0, 55.0),    # Head Circumference-for-Age (cm)
    'wfl_w': (1.0, 30.0),    # Weight-for-Length: weight range
    'wfl_l': (45.0, 110.0)   # Weight-for-Length: length range
}

# Age grid for smooth curve generation (0-60 months, step 0.25)
AGE_GRID = np.arange(0.0, 60.25, 0.25)

# UI Themes (Pastel Professional)
UI_THEMES = {
    "pink_pastel": {
        "name": "Pink Pastel (Default)",
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
        "name": "Mint Pastel",
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
        "name": "Lavender Pastel",
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

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2B: YOUTUBE VIDEO LIBRARY & EDUCATIONAL CONTENT (from v3.1)
# ═══════════════════════════════════════════════════════════════════════════════

# YouTube Videos for KPSP Screening Guide
KPSP_YOUTUBE_VIDEOS = [
    {
        "title": "🎥 Panduan Skrining KPSP Mandiri untuk Orang Tua",
        "url": "https://www.youtube.com/watch?v=ooAYe5asbKY",
        "description": "Tutorial lengkap cara melakukan KPSP di rumah",
        "duration": "10:15"
    },
    {
        "title": "🎥 KPSP: Deteksi Dini Perkembangan Anak",
        "url": "https://www.youtube.com/watch?v=q3NkI8go1yQ",
        "description": "Penjelasan komprehensif tentang KPSP dari ahli",
        "duration": "12:30"
    },
    {
        "title": "🎥 Cara Melakukan KPSP untuk Balita",
        "url": "https://www.youtube.com/watch?v=3DoPpSIx3i0",
        "description": "Panduan praktis KPSP untuk usia 12 bulan",
        "duration": "8:45"
    }
]

# YouTube Videos for MP-ASI by Month (0-24 months)
MPASI_YOUTUBE_VIDEOS = {
    6: [
        {
            "title": "🥕 Resep MPASI 6 Bulan Pertama",
            "url": "https://www.youtube.com/results?search_query=mpasi+6+bulan+pertama+resep",
            "description": "Menu MPASI perdana: bubur saring, tekstur halus",
            "duration": "15:00"
        },
        {
            "title": "🍚 MPASI 6 Bulan: Panduan Lengkap",
            "url": "https://www.youtube.com/results?search_query=panduan+mpasi+6+bulan+WHO",
            "description": "Standar WHO untuk MPASI awal",
            "duration": "18:20"
        }
    ],
    7: [
        {
            "title": "🥗 Menu MPASI 7 Bulan Variatif",
            "url": "https://www.youtube.com/results?search_query=mpasi+7+bulan+menu",
            "description": "Variasi menu dan tekstur lebih kasar",
            "duration": "12:45"
        }
    ],
    8: [
        {
            "title": "🍖 MPASI 8 Bulan: Protein Tinggi",
            "url": "https://www.youtube.com/results?search_query=mpasi+8+bulan+protein+hewani",
            "description": "Fokus protein hewani untuk cegah stunting",
            "duration": "14:30"
        }
    ],
    9: [
        {
            "title": "🍚 MPASI 9 Bulan: Tekstur Kasar",
            "url": "https://www.youtube.com/results?search_query=mpasi+9+bulan+tekstur+kasar",
            "description": "Transisi ke makanan bertekstur kasar",
            "duration": "11:15"
        }
    ],
    10: [
        {
            "title": "🥘 MPASI 10 Bulan: Menu Keluarga",
            "url": "https://www.youtube.com/results?search_query=mpasi+10+bulan+menu+keluarga",
            "description": "Mengenalkan makanan keluarga",
            "duration": "13:00"
        }
    ],
    11: [
        {
            "title": "🍲 MPASI 11 Bulan: Finger Food",
            "url": "https://www.youtube.com/results?search_query=mpasi+11+bulan+finger+food",
            "description": "Makanan yang bisa digenggam sendiri",
            "duration": "10:30"
        }
    ],
    12: [
        {
            "title": "🍱 MPASI 12 Bulan: Makan Mandiri",
            "url": "https://www.youtube.com/results?search_query=mpasi+12+bulan+menu",
            "description": "Melatih anak makan sendiri",
            "duration": "16:00"
        }
    ],
    18: [
        {
            "title": "🍽️ Menu 18 Bulan: Makanan Keluarga",
            "url": "https://www.youtube.com/results?search_query=menu+makan+anak+18+bulan",
            "description": "Sudah bisa makan seperti orang dewasa",
            "duration": "12:00"
        }
    ],
    24: [
        {
            "title": "🥗 Menu 24 Bulan: Gizi Seimbang",
            "url": "https://www.youtube.com/results?search_query=menu+balita+2+tahun+gizi+seimbang",
            "description": "Menu lengkap dengan gizi seimbang",
            "duration": "14:45"
        }
    ]
}

# Educational Content (Original v3.0)
MOTIVATIONAL_QUOTES = [
    "💕 'Seorang ibu adalah penjelajah yang tak pernah lelah, selalu menemukan jalan cinta untuk anaknya.'",
    "🌟 'Kekuatan ibu melebihi segala rintangan, kasihnya membentuk masa depan yang cerah.'",
    "🤱 'Setiap tetes ASI adalah investasi cinta tak ternilai dalam perjalanan tumbuh kembang Si Kecil.'",
    "💪 'Kamu kuat, kamu cukup, dan kamu melakukan yang terbaik untuk Si Kecil! Jangan menyerah!'",
    "🌈 'Pertumbuhan anak bukan kompetisi, tapi perjalanan cinta. Setiap langkah kecil adalah pencapaian besar.'",
    "💖 'Ibu, hatimu adalah rumah pertama Si Kecil, dan itu akan selalu jadi rumahnya yang paling aman.'",
    "🎯 'Fokus pada kemajuan, bukan kesempurnaan. Setiap anak tumbuh dengan kecepatannya sendiri.'",
    "🌸 'Nutrisi terbaik bukan hanya soal makanan, tapi kasih sayang yang kamu berikan setiap hari.'"
]

# Indonesian Immunization Schedule (Permenkes)
IMMUNIZATION_SCHEDULE = {
    0: ["HB-0 (< 24 jam)", "BCG", "Polio 0 (OPV)"],
    1: ["HB-1", "Polio 1", "DPT-HB-Hib 1", "PCV 1", "Rotavirus 1"],
    2: ["Polio 2", "DPT-HB-Hib 2", "PCV 2", "Rotavirus 2"],
    3: ["Polio 3", "DPT-HB-Hib 3", "PCV 3", "Rotavirus 3"],
    4: ["Polio 4", "DPT-HB-Hib 4"],
    9: ["Campak/MR 1"],
    12: ["Campak Booster", "PCV Booster"],
    15: ["Influenza (opsional)"],
    18: ["DPT-HB-Hib Booster", "Polio Booster"],
    24: ["Campak Rubella (MR) 2", "Japanese Encephalitis (daerah endemis)"]
}

# KPSP (Kuesioner Pra Skrining Perkembangan) by Age
KPSP_QUESTIONS = {
    3: [
        "Apakah anak dapat mengangkat kepalanya 45° saat tengkurap?",
        "Apakah anak tersenyum saat diajak bicara atau tersenyum sendiri?",
        "Apakah anak mengeluarkan suara-suara (mengoceh)?",
        "Apakah anak dapat menatap dan mengikuti wajah ibu/pengasuh?",
        "Apakah anak berusaha meraih benda atau mainan yang ditunjukkan?"
    ],
    6: [
        "Apakah anak dapat duduk dengan bantuan (bersandar)?",
        "Apakah anak dapat memindahkan mainan dari tangan satu ke tangan lain?",
        "Apakah anak mengeluarkan suara vokal seperti 'a-u-o'?",
        "Apakah anak tertawa keras saat bermain atau diajak bercanda?",
        "Apakah anak mengenal orang asing (tampak malu atau marah)?"
    ],
    9: [
        "Apakah anak dapat duduk sendiri tanpa bantuan minimal 1 menit?",
        "Apakah anak dapat merangkak maju (bukan mundur)?",
        "Apakah anak mengucapkan 'mama' atau 'papa' (meski berlebihan)?",
        "Apakah anak dapat meraih benda kecil dengan jempol dan telunjuk?",
        "Apakah anak dapat menirukan gerakan tepuk tangan?"
    ],
    12: [
        "Apakah anak dapat berdiri sendiri minimal 5 detik tanpa berpegangan?",
        "Apakah anak dapat berjalan berpegangan pada furniture?",
        "Apakah anak dapat mengucapkan 2-3 kata yang bermakna?",
        "Apakah anak dapat minum dari cangkir sendiri?",
        "Apakah anak dapat menunjuk benda yang diinginkannya?"
    ],
    15: [
        "Apakah anak dapat berjalan sendiri dengan stabil minimal 5 langkah?",
        "Apakah anak dapat minum dari gelas tanpa tumpah?",
        "Apakah anak dapat mengucapkan 4-6 kata dengan jelas?",
        "Apakah anak dapat menumpuk 2 kubus dengan stabil?",
        "Apakah anak dapat membantu melepas sepatunya sendiri?"
    ],
    18: [
        "Apakah anak dapat berlari minimal 5 langkah berturut-turut?",
        "Apakah anak dapat naik tangga dengan bantuan pegangan?",
        "Apakah anak dapat mengucapkan 10-15 kata yang berbeda?",
        "Apakah anak dapat makan sendiri dengan sendok?",
        "Apakah anak dapat menunjuk minimal 2 bagian tubuhnya?"
    ],
    21: [
        "Apakah anak dapat menendang bola ke depan tanpa jatuh?",
        "Apakah anak dapat naik tangga dengan 1 kaki bergantian?",
        "Apakah anak dapat mengucapkan kalimat 2-3 kata?",
        "Apakah anak dapat membalik halaman buku satu per satu?",
        "Apakah anak dapat mengikuti perintah sederhana 2 tahap?"
    ],
    24: [
        "Apakah anak dapat melompat dengan 2 kaki bersamaan?",
        "Apakah anak dapat naik-turun tangga tanpa pegangan?",
        "Apakah anak dapat membuat kalimat 3-4 kata yang runtut?",
        "Apakah anak dapat menggambar garis vertikal setelah dicontohkan?",
        "Apakah anak dapat mengikuti perintah kompleks 3 tahap?"
    ]
}

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2C: PERPUSTAKAAN IBU BALITA (REPLACED by v3.2)
# ═══════════════════════════════════════════════════════════════════════════════

# Variabel PERPUSTAKAAN_IBU_BALITA (v3.1) yang lama DIHAPUS
# dan digantikan oleh `PERPUSTAKAAN_IBU_BALITA_UPDATED` dari v3.2
# Fungsi-fungsi helper untuk perpustakaan juga dipindahkan ke Section 10B

print(f"✅ Configuration loaded (v3.1 base):")
print(f"   - {len(KPSP_YOUTUBE_VIDEOS)} KPSP videos")
print(f"   - {sum(len(v) for v in MPASI_YOUTUBE_VIDEOS.values())} MP-ASI videos across {len(MPASI_YOUTUBE_VIDEOS)} age groups")
print(f"   - {len(IMMUNIZATION_SCHEDULE)} immunization schedules")
print(f"   - {len(KPSP_QUESTIONS)} KPSP question sets")
print(f"   - {len(UI_THEMES)} UI themes")
print("   - ℹ️ Old v3.1 Library removed, will be replaced by v3.2 Library")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: WHO CALCULATOR INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

# Initialize WHO Growth Calculator
calc = None

try:
    calc = Calculator(**CALC_CONFIG)
    print("✅ WHO Calculator initialized successfully")
    print(f"   - Height adjustment: {CALC_CONFIG['adjust_height_data']}")
    print(f"   - Weight scores adjustment: {CALC_CONFIG['adjust_weight_scores']}")
    print(f"   - CDC standards: {CALC_CONFIG['include_cdc']}")
except Exception as e:
    print(f"❌ CRITICAL: WHO Calculator initialization failed!")
    print(f"   Error: {e}")
    print(f"   Traceback: {traceback.format_exc()}")
    calc = None

if calc is None:
    print("⚠️  WARNING: Application will run with limited functionality")

print("=" * 80)
print(f"🚀 {APP_TITLE} v{APP_VERSION} - Configuration Complete")
print("=" * 80)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: UTILITY FUNCTIONS (from v3.0)
# ═══════════════════════════════════════════════════════════════════════════════

def as_float(x: Any) -> Optional[float]:
    """
    Safely convert any input to float
    
    Args:
        x: Input value (can be string, number, Decimal, etc)
        
    Returns:
        Float value or None if conversion fails
    """
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        # Handle comma as decimal separator (Indonesian format)
        clean_str = str(x).replace(",", ".").strip()
        return float(clean_str)
    except (ValueError, AttributeError):
        return None


def parse_date(date_str: str) -> Optional[date]:
    """
    Parse date string in multiple formats
    
    Supported formats:
        - YYYY-MM-DD (ISO 8601)
        - DD/MM/YYYY (Indonesian format)
    
    Args:
        date_str: Date string to parse
        
    Returns:
        datetime.date object or None if parsing fails
    """
    if not date_str or str(date_str).strip() == "":
        return None
    
    s = str(date_str).strip()
    
    # Try ISO format (YYYY-MM-DD)
    try:
        parts = s.split("-")
        if len(parts) == 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            return date(y, m, d)
    except (ValueError, IndexError):
        pass
    
    # Try Indonesian format (DD/MM/YYYY)
    try:
        parts = s.split("/")
        if len(parts) == 3:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            return date(y, m, d)
    except (ValueError, IndexError):
        pass
    
    return None


def calculate_age_from_dates(dob: date, dom: date) -> Tuple[Optional[float], Optional[int]]:
    """
    Calculate age in months and days from dates
    
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
        
        # Use average month length (365.25 days / 12 months)
        months = days / 30.4375
        
        return round(months, 2), days
    except Exception as e:
        print(f"Age calculation error: {e}")
        return None, None


@lru_cache(maxsize=2048)
def z_to_percentile(z_score: Optional[float]) -> Optional[float]:
    """
    Convert Z-score to percentile using standard normal CDF
    
    Args:
        z_score: Z-score value
        
    Returns:
        Percentile (0-100) or None if invalid
    """
    if z_score is None:
        return None
    
    try:
        z = float(z_score)
        if math.isnan(z) or math.isinf(z):
            return None
        
        # Standard normal cumulative distribution function
        # Φ(z) = 0.5 * (1 + erf(z/√2))
        percentile = 0.5 * (1.0 + erf(z / math.sqrt(2.0))) * 100.0
        
        return round(percentile, 1)
    except Exception:
        return None


def format_zscore(z: Optional[float], decimals: int = 2) -> str:
    """
    Format Z-score for display with proper sign
    
    Args:
        z: Z-score value
        decimals: Number of decimal places
        
    Returns:
        Formatted string like "+2.34" or "-1.23" or "—" for invalid
    """
    if z is None:
        return "—"
    
    try:
        z_float = float(z)
        if math.isnan(z_float) or math.isinf(z_float):
            return "—"
        
        # Add explicit + sign for positive values
        sign = "+" if z_float >= 0 else ""
        return f"{sign}{z_float:.{decimals}f}"
    except Exception:
        return "—"


def validate_anthropometry(age_mo: Optional[float], 
                          weight: Optional[float], 
                          height: Optional[float], 
                          head_circ: Optional[float]) -> Tuple[List[str], List[str]]:
    """
    Validate anthropometric measurements against WHO plausibility ranges
    
    Args:
        age_mo: Age in months
        weight: Weight in kg
        height: Height/length in cm
        head_circ: Head circumference in cm
        
    Returns:
        Tuple of (errors, warnings) - lists of validation messages
    """
    errors = []
    warnings = []
    
    # Age validation
    if age_mo is not None:
        if age_mo < 0:
            errors.append("❌ Usia tidak boleh negatif")
        elif age_mo > 60:
            warnings.append("ℹ️ Aplikasi dioptimalkan untuk usia 0-60 bulan (WHO standards)")
    
    # Weight validation (WHO plausibility ranges)
    if weight is not None:
        if weight < 1.0 or weight > 30.0:
            errors.append(f"❌ Berat badan {weight:.1f} kg di luar rentang plausibel (1-30 kg)")
        elif weight < 2.0:
            warnings.append(f"⚠️ Berat badan {weight:.1f} kg sangat rendah - verifikasi ulang pengukuran")
        elif weight > 25.0:
            warnings.append(f"⚠️ Berat badan {weight:.1f} kg tidak umum - verifikasi ulang pengukuran")
    
    # Height validation (WHO plausibility ranges)
    if height is not None:
        if height < 35 or height > 130:
            errors.append(f"❌ Panjang/tinggi {height:.1f} cm di luar rentang plausibel (35-130 cm)")
        elif height < 45:
            warnings.append(f"⚠️ Panjang/tinggi {height:.1f} cm sangat pendek - verifikasi pengukuran")
        elif height > 120:
            warnings.append(f"⚠️ Tinggi {height:.1f} cm tidak umum untuk balita - verifikasi pengukuran")
    
    # Head circumference validation (WHO standards)
    if head_circ is not None:
        if head_circ < 20 or head_circ > 60:
            errors.append(f"❌ Lingkar kepala {head_circ:.1f} cm di luar rentang plausibel (20-60 cm)")
        elif head_circ < 30:
            warnings.append(f"⚠️ Lingkar kepala {head_circ:.1f} cm sangat kecil - konsultasi dokter anak")
        elif head_circ > 55:
            warnings.append(f"⚠️ Lingkar kepala {head_circ:.1f} cm sangat besar - konsultasi dokter anak")
    
    return errors, warnings


def get_random_quote() -> str:
    """Get random motivational quote for parents"""
    return random.choice(MOTIVATIONAL_QUOTES)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: WHO Z-SCORE CALCULATIONS (from v3.0)
# ═══════════════════════════════════════════════════════════════════════════════

def _safe_z_calc(calc_func, *args) -> Optional[float]:
    """
    Safely call WHO calculator function with error handling
    
    Args:
        calc_func: Calculator method to call
        *args: Arguments to pass to the calculator
        
    Returns:
        Z-score float or None if calculation fails
    """
    if calc is None:
        return None
    
    try:
        z = calc_func(*args)
        
        if z is None:
            return None
        
        z_float = float(z)
        
        # Check for invalid values (NaN or Inf)
        if math.isnan(z_float) or math.isinf(z_float):
            return None
        
        return z_float
    except Exception as e:
        # Silent failure for robustness
        return None


def calculate_all_zscores(sex: str, 
                          age_months: float, 
                          weight: Optional[float], 
                          height: Optional[float], 
                          head_circ: Optional[float]) -> Dict[str, Optional[float]]:
    """
    Calculate all WHO z-scores for a child
    
    Args:
        sex: 'M' (male) or 'F' (female)
        age_months: Age in months
        weight: Weight in kg
        height: Height/length in cm
        head_circ: Head circumference in cm
        
    Returns:
        Dictionary with keys:
            - waz: Weight-for-Age Z-score
            - haz: Height-for-Age Z-score (or LAZ if < 24 months)
            - whz: Weight-for-Height Z-score (or WFL if < 24 months)
            - baz: BMI-for-Age Z-score
            - hcz: Head Circumference-for-Age Z-score
    """
    results = {
        'waz': None,
        'haz': None,
        'whz': None,
        'baz': None,
        'hcz': None
    }
    
    if calc is None:
        return results
    
    # Weight-for-Age (WAZ)
    if weight is not None:
        results['waz'] = _safe_z_calc(calc.wfa, weight, age_months, sex)
    
    # Height-for-Age (HAZ) / Length-for-Age (LAZ)
    if height is not None:
        results['haz'] = _safe_z_calc(calc.lhfa, height, age_months, sex)
    
    # Weight-for-Height (WHZ) / Weight-for-Length (WFL)
    if weight is not None and height is not None:
        results['whz'] = _safe_z_calc(calc.wfl, weight, age_months, sex, height)
    
    # BMI-for-Age (BAZ)
    if weight is not None and height is not None and height > 0:
        bmi = weight / ((height / 100) ** 2)
        results['baz'] = _safe_z_calc(calc.bmifa, bmi, age_months, sex)
    
    # Head Circumference-for-Age (HCZ)
    if head_circ is not None:
        results['hcz'] = _safe_z_calc(calc.hcfa, head_circ, age_months, sex)
    
    return results


def classify_permenkes_2020(z_scores: Dict[str, Optional[float]]) -> Dict[str, str]:
    """
    Classify nutritional status according to Permenkes RI No. 2 Tahun 2020
    
    Args:
        z_scores: Dictionary of z-scores from calculate_all_zscores()
        
    Returns:
        Dictionary with Permenkes classifications for each index
    """
    classifications = {}
    
    # Weight-for-Age (BB/U)
    waz = z_scores.get('waz')
    if waz is not None and not math.isnan(waz):
        if waz < -3:
            classifications['waz'] = "Berat Badan Sangat Kurang"
        elif waz < -2:
            classifications['waz'] = "Berat Badan Kurang"
        elif waz <= 2:
            classifications['waz'] = "Berat Badan Normal"
        else:
            classifications['waz'] = "Risiko Berat Badan Lebih"
    else:
        classifications['waz'] = "Data Tidak Tersedia"
    
    # Height-for-Age (TB/U)
    haz = z_scores.get('haz')
    if haz is not None and not math.isnan(haz):
        if haz < -3:
            classifications['haz'] = "Sangat Pendek (Severely Stunted)"
        elif haz < -2:
            classifications['haz'] = "Pendek (Stunted)"
        elif haz <= 3:
            classifications['haz'] = "Tinggi Badan Normal"
        else:
            classifications['haz'] = "Tinggi Badan Berlebih"
    else:
        classifications['haz'] = "Data Tidak Tersedia"
    
    # Weight-for-Height (BB/TB)
    whz = z_scores.get('whz')
    if whz is not None and not math.isnan(whz):
        if whz < -3:
            classifications['whz'] = "Gizi Buruk (Severely Wasted)"
        elif whz < -2:
            classifications['whz'] = "Gizi Kurang (Wasted)"
        elif whz <= 2:
            classifications['whz'] = "Gizi Baik (Normal)"
        elif whz <= 3:
            classifications['whz'] = "Berisiko Gizi Lebih (Possible Risk of Overweight)"
        else:
            classifications['whz'] = "Gizi Lebih (Overweight)"
    else:
        classifications['whz'] = "Data Tidak Tersedia"
    
    # BMI-for-Age (IMT/U)
    baz = z_scores.get('baz')
    if baz is not None and not math.isnan(baz):
        if baz < -3:
            classifications['baz'] = "Gizi Buruk (Severely Wasted)"
        elif baz < -2:
            classifications['baz'] = "Gizi Kurang (Wasted)"
        elif baz <= 1:
            classifications['baz'] = "Gizi Baik (Normal)"
        elif baz <= 2:
            classifications['baz'] = "Berisiko Gizi Lebih (Possible Risk of Overweight)"
        elif baz <= 3:
            classifications['baz'] = "Gizi Lebih (Overweight)"
        else:
            classifications['baz'] = "Obesitas (Obese)"
    else:
        classifications['baz'] = "Data Tidak Tersedia"
    
    # Head Circumference-for-Age (LK/U)
    hcz = z_scores.get('hcz')
    if hcz is not None and not math.isnan(hcz):
        if abs(hcz) <= 2:
            classifications['hcz'] = "Normal"
        elif hcz < -2:
            classifications['hcz'] = "Mikrosefali (perlu evaluasi)"
        else:
            classifications['hcz'] = "Makrosefali (perlu evaluasi)"
    else:
        classifications['hcz'] = "Data Tidak Tersedia"
    
    return classifications


def classify_who_standards(z_scores: Dict[str, Optional[float]]) -> Dict[str, str]:
    """
    Classify nutritional status according to WHO Child Growth Standards
    
    Args:
        z_scores: Dictionary of z-scores from calculate_all_zscores()
        
    Returns:
        Dictionary with WHO classifications for each index
    """
    classifications = {}
    
    # Weight-for-Age
    waz = z_scores.get('waz')
    if waz is not None and not math.isnan(waz):
        if waz < -3:
            classifications['waz'] = "Severely underweight"
        elif waz < -2:
            classifications['waz'] = "Underweight"
        elif waz <= 2:
            classifications['waz'] = "Normal weight"
        else:
            classifications['waz'] = "Overweight"
    else:
        classifications['waz'] = "N/A"
    
    # Height-for-Age
    haz = z_scores.get('haz')
    if haz is not None and not math.isnan(haz):
        if haz < -3:
            classifications['haz'] = "Severely stunted"
        elif haz < -2:
            classifications['haz'] = "Stunted"
        elif haz <= 3:
            classifications['haz'] = "Normal height"
        else:
            classifications['haz'] = "Tall"
    else:
        classifications['haz'] = "N/A"
    
    # Weight-for-Height
    whz = z_scores.get('whz')
    if whz is not None and not math.isnan(whz):
        if whz < -3:
            classifications['whz'] = "Severely wasted"
        elif whz < -2:
            classifications['whz'] = "Wasted"
        elif whz <= 2:
            classifications['whz'] = "Normal"
        elif whz <= 3:
            classifications['whz'] = "Risk of overweight"
        else:
            classifications['whz'] = "Overweight"
    else:
        classifications['whz'] = "N/A"
    
    # BMI-for-Age
    baz = z_scores.get('baz')
    if baz is not None and not math.isnan(baz):
        if baz < -3:
            classifications['baz'] = "Severely wasted"
        elif baz < -2:
            classifications['baz'] = "Wasted"
        elif baz <= 1:
            classifications['baz'] = "Normal"
        elif baz <= 2:
            classifications['baz'] = "Risk of overweight"
        elif baz <= 3:
            classifications['baz'] = "Overweight"
        else:
            classifications['baz'] = "Obese"
    else:
        classifications['baz'] = "N/A"
    
    # Head Circumference-for-Age
    hcz = z_scores.get('hcz')
    if hcz is not None and not math.isnan(hcz):
        if abs(hcz) <= 2:
            classifications['hcz'] = "Normal"
        elif hcz < -2:
            classifications['hcz'] = "Microcephaly"
        else:
            classifications['hcz'] = "Macrocephaly"
    else:
        classifications['hcz'] = "N/A"
    
    return classifications


def validate_zscores(z_scores: Dict[str, Optional[float]]) -> Tuple[List[str], List[str]]:
    """
    Validate z-scores for extreme values that need attention
    
    Args:
        z_scores: Dictionary of z-scores
        
    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []
    
    warn_threshold = 3
    critical_threshold = 5
    
    for key, z in z_scores.items():
        if z is None or math.isnan(z):
            continue
        
        name = {
            'waz': 'WAZ (BB/U)',
            'haz': 'HAZ (TB/U)',
            'whz': 'WHZ (BB/TB)',
            'baz': 'BAZ (IMT/U)',
            'hcz': 'HCZ (LK/U)'
        }.get(key, key)
        
        abs_z = abs(z)
        
        if abs_z > critical_threshold:
            errors.append(
                f"🚨 {name} = {format_zscore(z)} sangat ekstrem (|Z| > {critical_threshold}). "
                f"PENTING: Verifikasi ulang semua pengukuran dan konsultasi dokter anak."
            )
        elif abs_z > warn_threshold:
            warnings.append(
                f"⚠️ {name} = {format_zscore(z)} di luar rentang umum (|Z| > {warn_threshold}). "
                f"Verifikasi ulang pengukuran atau konsultasi tenaga kesehatan."
            )
    
    return errors, warnings


print("✅ Section 4-5 loaded: Utility functions & WHO z-score calculations")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: GROWTH CURVE GENERATION (from v3.0/v3.1)
# ═══════════════════════════════════════════════════════════════════════════════

def brentq_rootfind(f, a: float, b: float, xtol: float = 1e-6, maxiter: int = 100) -> float:
    """
    Brent's method for root finding (scipy-free implementation)
    
    Args:
        f: Function to find root of
        a, b: Bracket endpoints [a, b]
        xtol: Tolerance for convergence
        maxiter: Maximum iterations
        
    Returns:
        Root approximation
    """
    fa = f(a)
    fb = f(b)
    
    if fa is None or fb is None:
        return (a + b) / 2.0
    
    if abs(fa) < 1e-10:
        return a
    if abs(fb) < 1e-10:
        return b
    
    # Ensure bracket is valid
    if fa * fb > 0:
        return (a + b) / 2.0
    
    for iteration in range(maxiter):
        m = 0.5 * (a + b)
        fm = f(m)
        
        if fm is None:
            return m
        
        if abs(fm) < 1e-10 or (b - a) / 2 < xtol:
            return m
        
        if fa * fm < 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    
    return 0.5 * (a + b)


def invert_zscore_function(z_func, target_z: float, lo: float, hi: float, samples: int = 150) -> float:
    """
    Invert z-score function to find measurement value that produces target z-score
    
    Uses grid scan + Brent's method for robustness
    
    Args:
        z_func: Function that takes measurement and returns z-score
        target_z: Target z-score to achieve
        lo, hi: Search bounds for measurement
        samples: Number of grid points to scan
        
    Returns:
        Measurement value that gives target_z
    """
    xs = np.linspace(lo, hi, samples)
    last_x, last_f = None, None
    best_x, best_abs = None, float('inf')
    
    # Grid scan phase
    for x in xs:
        z = z_func(x)
        f = None if z is None else (z - target_z)
        
        if f is not None:
            af = abs(f)
            if af < best_abs:
                best_x, best_abs = x, af
            
            # Check for sign change (indicates root bracket)
            if last_f is not None and f * last_f < 0:
                try:
                    # Refine with Brent's method
                    root = brentq_rootfind(
                        lambda t: (z_func(t) or 0.0) - target_z,
                        last_x,
                        x,
                        xtol=1e-5
                    )
                    return float(root)
                except Exception:
                    pass
            
            last_x, last_f = x, f
    
    # Return best approximation if no bracket found
    return float(best_x if best_x is not None else (lo + hi) / 2.0)


@lru_cache(maxsize=128)
def generate_wfa_curve(sex: str, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Weight-for-Age WHO curve for given z-score
    
    Args:
        sex: 'M' or 'F'
        z_score: Z-score line to generate (-3 to +3 typically)
        
    Returns:
        Tuple of (age_array, weight_array)
    """
    lo, hi = BOUNDS['wfa']
    
    def z_func(weight, age):
        return _safe_z_calc(calc.wfa, weight, age, sex)
    
    weights = []
    for age in AGE_GRID:
        weight = invert_zscore_function(
            lambda w: z_func(w, age),
            z_score,
            lo,
            hi
        )
        weights.append(weight)
    
    return AGE_GRID.copy(), np.array(weights)


@lru_cache(maxsize=128)
def generate_hfa_curve(sex: str, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Height-for-Age WHO curve for given z-score
    
    Args:
        sex: 'M' or 'F'
        z_score: Z-score line to generate
        
    Returns:
        Tuple of (age_array, height_array)
    """
    lo, hi = BOUNDS['hfa']
    
    def z_func(height, age):
        return _safe_z_calc(calc.lhfa, height, age, sex)
    
    heights = []
    for age in AGE_GRID:
        height = invert_zscore_function(
            lambda h: z_func(h, age),
            z_score,
            lo,
            hi
        )
        heights.append(height)
    
    return AGE_GRID.copy(), np.array(heights)


@lru_cache(maxsize=128)
def generate_hcfa_curve(sex: str, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Head Circumference-for-Age WHO curve for given z-score
    
    Args:
        sex: 'M' or 'F'
        z_score: Z-score line to generate
        
    Returns:
        Tuple of (age_array, head_circ_array)
    """
    lo, hi = BOUNDS['hcfa']
    
    def z_func(hc, age):
        return _safe_z_calc(calc.hcfa, hc, age, sex)
    
    head_circs = []
    for age in AGE_GRID:
        hc = invert_zscore_function(
            lambda h: z_func(h, age),
            z_score,
            lo,
            hi
        )
        head_circs.append(hc)
    
    return AGE_GRID.copy(), np.array(head_circs)


@lru_cache(maxsize=128)
def generate_wfl_curve(sex: str, age_months: float, z_score: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate Weight-for-Length WHO curve for given z-score
    
    Args:
        sex: 'M' or 'F'
        age_months: Child's age (needed for WHO calculation)
        z_score: Z-score line to generate
        
    Returns:
        Tuple of (length_array, weight_array)
    """
    lengths = np.arange(BOUNDS['wfl_l'][0], BOUNDS['wfl_l'][1] + 0.5, 0.5)
    lo_w, hi_w = BOUNDS['wfl_w']
    
    def z_func(weight, length):
        return _safe_z_calc(calc.wfl, weight, age_months, sex, length)
    
    weights = []
    for length in lengths:
        weight = invert_zscore_function(
            lambda w: z_func(w, length),
            z_score,
            lo_w,
            hi_w
        )
        weights.append(weight)
    
    return lengths, np.array(weights)


print("✅ Section 6 loaded: Growth curve generation with caching")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: MATPLOTLIB PLOTTING FUNCTIONS (from v3.0/v3.1)
# ═══════════════════════════════════════════════════════════════════════════════

def apply_matplotlib_theme(theme_name: str = "pink_pastel") -> Dict[str, str]:
    """
    Apply custom theme to matplotlib
    
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
        "grid.alpha": 0.35,
        "grid.linestyle": "--",
        "grid.linewidth": 0.8,
        "legend.framealpha": 1.0,
        "legend.fancybox": True,
        "legend.edgecolor": theme["border"],
        "legend.shadow": True,
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.linewidth": 1.5,
    })
    
    return theme


def _fill_zone_between_curves(ax, x: np.ndarray, lower: np.ndarray, upper: np.ndarray, 
                              color: str, alpha: float, label: str):
    """Helper to fill colored zones between SD curves"""
    try:
        ax.fill_between(
            x, lower, upper,
            color=color,
            alpha=alpha,
            zorder=1,
            label=label,
            linewidth=0,
            edgecolor='none'
        )
    except Exception as e:
        print(f"Fill zone warning: {e}")


def plot_weight_for_age(payload: Dict, theme_name: str = "pink_pastel") -> Figure:
    """
    Plot Weight-for-Age growth chart with child's data point
    
    Args:
        payload: Data dict containing sex, age_mo, weight, z-scores, etc
        theme_name: Theme to apply
        
    Returns:
        Matplotlib Figure object
    """
    theme = apply_matplotlib_theme(theme_name)
    
    sex = payload['sex']
    age = payload['age_mo']
    weight = payload.get('w')
    
    # SD lines to plot
    sd_lines = {
        -3: ('#DC143C', '-', 2.0),  # Dark red, solid
        -2: ('#FF6347', '-', 2.5),  # Tomato, solid
        -1: (theme['primary'], '--', 1.5),  # Theme color, dashed
        0: (theme['secondary'], '-', 2.5),  # Median, solid, thick
        1: (theme['primary'], '--', 1.5),  # Theme color, dashed
        2: ('#FF6347', '-', 2.5),  # Tomato, solid
        3: ('#DC143C', '-', 2.0)   # Dark red, solid
    }
    
    # Generate curves
    curves = {z: generate_wfa_curve(sex, z) for z in sd_lines.keys()}
    
    fig, ax = plt.subplots(figsize=(12, 7.5))
    
    x = curves[0][0]
    
    # Fill nutritional status zones
    _fill_zone_between_curves(ax, x, curves[-3][1], curves[-2][1], '#FFE6E6', 0.4, 'Gizi Buruk')
    _fill_zone_between_curves(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.35, 'Gizi Kurang')
    _fill_zone_between_curves(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.45, 'Normal')
    _fill_zone_between_curves(ax, x, curves[1][1],  curves[2][1],  '#FFF3CD', 0.35, 'Risiko Lebih')
    _fill_zone_between_curves(ax, x, curves[2][1],  curves[3][1],  '#F8D7DA', 0.4, 'Gizi Lebih')
    
    # Plot SD lines
    for z, (color, linestyle, linewidth) in sd_lines.items():
        label = "Median (WHO)" if z == 0 else f"{z:+d} SD"
        ax.plot(
            curves[z][0], curves[z][1],
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            label=label,
            zorder=5,
            alpha=0.9
        )
    
    # Plot child's data point
    if weight is not None:
        z_waz = payload['z'].get('waz')
        
        # Color based on z-score severity
        if z_waz is not None:
            if abs(z_waz) > 3:
                point_color = '#8B0000'  # Dark red for extreme
                point_size = 500
            elif abs(z_waz) > 2:
                point_color = '#DC143C'  # Red for severe
                point_size = 450
            elif abs(z_waz) > 1:
                point_color = theme['primary']
                point_size = 400
            else:
                point_color = theme['secondary']
                point_size = 400
        else:
            point_color = theme['secondary']
            point_size = 400
        
        ax.scatter(
            [age], [weight],
            s=point_size,
            c=point_color,
            edgecolors='white',
            linewidths=3,
            label=f"Data Anak ({weight:.1f} kg)",
            zorder=10,
            marker='o',
            alpha=1.0
        )
        
        # Add annotation
        ax.annotate(
            f"{weight:.1f} kg\nZ: {format_zscore(z_waz)}",
            (age, weight),
            xytext=(10, 10),
            textcoords='offset points',
            fontsize=10,
            fontweight='bold',
            bbox=dict(
                boxstyle='round,pad=0.6',
                facecolor=point_color,
                edgecolor='white',
                linewidth=2,
                alpha=0.9
            ),
            color='white',
            zorder=11
        )
    
    # Styling
    ax.set_xlabel("Usia (bulan)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Berat Badan (kg)", fontsize=12, fontweight='bold')
    ax.set_title(
        f"Grafik Berat Badan menurut Umur (BB/U) - WHO Standards\n"
        f"{'Laki-laki' if sex == 'M' else 'Perempuan'} | Usia: {age:.1f} bulan",
        fontsize=14,
        fontweight='bold',
        pad=15
    )
    
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.legend(
        loc='upper left',
        framealpha=0.95,
        edgecolor=theme['border'],
        fancybox=True,
        shadow=True,
        fontsize=9
    )
    
    ax.set_xlim(-1, 62)
    ax.set_ylim(0, None)
    
    plt.tight_layout()
    
    return fig


def plot_height_for_age(payload: Dict, theme_name: str = "pink_pastel") -> Figure:
    """
    Plot Height-for-Age growth chart with child's data point
    
    Args:
        payload: Data dict containing sex, age_mo, height, z-scores, etc
        theme_name: Theme to apply
        
    Returns:
        Matplotlib Figure object
    """
    theme = apply_matplotlib_theme(theme_name)
    
    sex = payload['sex']
    age = payload['age_mo']
    height = payload.get('h')
    
    # SD lines
    sd_lines = {
        -3: ('#DC143C', '-', 2.0),
        -2: ('#FF6347', '-', 2.5),
        -1: (theme['primary'], '--', 1.5),
        0: (theme['secondary'], '-', 2.5),
        1: (theme['primary'], '--', 1.5),
        2: ('#FF6347', '-', 2.5),
        3: ('#DC143C', '-', 2.0)
    }
    
    curves = {z: generate_hfa_curve(sex, z) for z in sd_lines.keys()}
    
    fig, ax = plt.subplots(figsize=(12, 7.5))
    
    x = curves[0][0]
    
    # Fill zones
    _fill_zone_between_curves(ax, x, curves[-3][1], curves[-2][1], '#FFE6E6', 0.4, 'Sangat Pendek')
    _fill_zone_between_curves(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.35, 'Pendek')
    _fill_zone_between_curves(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.45, 'Normal')
    _fill_zone_between_curves(ax, x, curves[1][1],  curves[2][1],  '#FFF3CD', 0.35, 'Tinggi')
    
    # Plot SD lines
    for z, (color, linestyle, linewidth) in sd_lines.items():
        label = "Median (WHO)" if z == 0 else f"{z:+d} SD"
        ax.plot(
            curves[z][0], curves[z][1],
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            label=label,
            zorder=5,
            alpha=0.9
        )
    
    # Plot child's data
    if height is not None:
        z_haz = payload['z'].get('haz')
        
        if z_haz is not None:
            if abs(z_haz) > 3:
                point_color = '#8B0000'
                point_size = 500
            elif abs(z_haz) > 2:
                point_color = '#DC143C'
                point_size = 450
            elif abs(z_haz) > 1:
                point_color = theme['primary']
                point_size = 400
            else:
                point_color = theme['secondary']
                point_size = 400
        else:
            point_color = theme['secondary']
            point_size = 400
        
        ax.scatter(
            [age], [height],
            s=point_size,
            c=point_color,
            edgecolors='white',
            linewidths=3,
            label=f"Data Anak ({height:.1f} cm)",
            zorder=10,
            marker='o',
            alpha=1.0
        )
        
        ax.annotate(
            f"{height:.1f} cm\nZ: {format_zscore(z_haz)}",
            (age, height),
            xytext=(10, 10),
            textcoords='offset points',
            fontsize=10,
            fontweight='bold',
            bbox=dict(
                boxstyle='round,pad=0.6',
                facecolor=point_color,
                edgecolor='white',
                linewidth=2,
                alpha=0.9
            ),
            color='white',
            zorder=11
        )
    
    measurement_type = "Panjang Badan" if age < 24 else "Tinggi Badan"
    ax.set_xlabel("Usia (bulan)", fontsize=12, fontweight='bold')
    ax.set_ylabel(f"{measurement_type} (cm)", fontsize=12, fontweight='bold')
    ax.set_title(
        f"Grafik {measurement_type} menurut Umur (TB/U) - WHO Standards\n"
        f"{'Laki-laki' if sex == 'M' else 'Perempuan'} | Usia: {age:.1f} bulan",
        fontsize=14,
        fontweight='bold',
        pad=15
    )
    
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.legend(loc='upper left', framealpha=0.95, fancybox=True, shadow=True, fontsize=9)
    ax.set_xlim(-1, 62)
    ax.set_ylim(40, None)
    
    plt.tight_layout()
    
    return fig


def plot_head_circumference_for_age(payload: Dict, theme_name: str = "pink_pastel") -> Figure:
    """
    Plot Head Circumference-for-Age growth chart
    
    Args:
        payload: Data dict
        theme_name: Theme to apply
        
    Returns:
        Matplotlib Figure object
    """
    theme = apply_matplotlib_theme(theme_name)
    
    sex = payload['sex']
    age = payload['age_mo']
    head_circ = payload.get('hc')
    
    if head_circ is None:
        # Return empty figure with message
        fig, ax = plt.subplots(figsize=(12, 7.5))
        ax.text(
            0.5, 0.5,
            "Data lingkar kepala tidak tersedia",
            ha='center', va='center',
            transform=ax.transAxes,
            fontsize=14,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )
        ax.set_title("Grafik Lingkar Kepala menurut Umur (LK/U)")
        return fig
    
    sd_lines = {
        -3: ('#DC143C', '-', 2.0),
        -2: ('#FF6347', '-', 2.5),
        -1: (theme['primary'], '--', 1.5),
        0: (theme['secondary'], '-', 2.5),
        1: (theme['primary'], '--', 1.5),
        2: ('#FF6347', '-', 2.5),
        3: ('#DC143C', '-', 2.0)
    }
    
    curves = {z: generate_hcfa_curve(sex, z) for z in sd_lines.keys()}
    
    fig, ax = plt.subplots(figsize=(12, 7.5))
    
    x = curves[0][0]
    
    # Fill zones
    _fill_zone_between_curves(ax, x, curves[-3][1], curves[-2][1], '#FFE6E6', 0.4, 'Mikrosefali')
    _fill_zone_between_curves(ax, x, curves[-2][1], curves[2][1],  '#E8F5E9', 0.45, 'Normal')
    _fill_zone_between_curves(ax, x, curves[2][1],  curves[3][1],  '#FFE6E6', 0.4, 'Makrosefali')
    
    # Plot SD lines
    for z, (color, linestyle, linewidth) in sd_lines.items():
        label = "Median (WHO)" if z == 0 else f"{z:+d} SD"
        ax.plot(
            curves[z][0], curves[z][1],
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            label=label,
            zorder=5,
            alpha=0.9
        )
    
    # Plot child's data
    z_hcz = payload['z'].get('hcz')
    
    if z_hcz is not None:
        if abs(z_hcz) > 2:
            point_color = '#DC143C'
            point_size = 500
        elif abs(z_hcz) > 1:
            point_color = theme['primary']
            point_size = 450
        else:
            point_color = theme['secondary']
            point_size = 400
    else:
        point_color = theme['secondary']
        point_size = 400
    
    ax.scatter(
        [age], [head_circ],
        s=point_size,
        c=point_color,
        edgecolors='white',
        linewidths=3,
        label=f"Data Anak ({head_circ:.1f} cm)",
        zorder=10,
        marker='o',
        alpha=1.0
    )
    
    ax.annotate(
        f"{head_circ:.1f} cm\nZ: {format_zscore(z_hcz)}",
        (age, head_circ),
        xytext=(10, 10),
        textcoords='offset points',
        fontsize=10,
        fontweight='bold',
        bbox=dict(
            boxstyle='round,pad=0.6',
            facecolor=point_color,
            edgecolor='white',
            linewidth=2,
            alpha=0.9
        ),
        color='white',
        zorder=11
    )
    
    ax.set_xlabel("Usia (bulan)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Lingkar Kepala (cm)", fontsize=12, fontweight='bold')
    ax.set_title(
        f"Grafik Lingkar Kepala menurut Umur (LK/U) - WHO Standards\n"
        f"{'Laki-laki' if sex == 'M' else 'Perempuan'} | Usia: {age:.1f} bulan",
        fontsize=14,
        fontweight='bold',
        pad=15
    )
    
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.legend(loc='upper left', framealpha=0.95, fancybox=True, shadow=True, fontsize=9)
    ax.set_xlim(-1, 62)
    ax.set_ylim(28, None)
    
    plt.tight_layout()
    
    return fig


print("✅ Section 7 loaded: Matplotlib plotting functions (WFA, HFA, HCFA)")


def plot_weight_for_length(payload: Dict, theme_name: str = "pink_pastel") -> Figure:
    """
    Plot Weight-for-Length growth chart
    
    Args:
        payload: Data dict
        theme_name: Theme to apply
        
    Returns:
        Matplotlib Figure object
    """
    theme = apply_matplotlib_theme(theme_name)
    
    sex = payload['sex']
    age = payload['age_mo']
    weight = payload.get('w')
    height = payload.get('h')
    
    if weight is None or height is None:
        fig, ax = plt.subplots(figsize=(12, 7.5))
        ax.text(
            0.5, 0.5,
            "Data berat dan tinggi badan diperlukan untuk grafik BB/TB",
            ha='center', va='center',
            transform=ax.transAxes,
            fontsize=14,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )
        ax.set_title("Grafik Berat Badan menurut Tinggi Badan (BB/TB)")
        return fig
    
    sd_lines = {
        -3: ('#DC143C', '-', 2.0),
        -2: ('#FF6347', '-', 2.5),
        -1: (theme['primary'], '--', 1.5),
        0: (theme['secondary'], '-', 2.5),
        1: (theme['primary'], '--', 1.5),
        2: ('#FF6347', '-', 2.5),
        3: ('#DC143C', '-', 2.0)
    }
    
    curves = {z: generate_wfl_curve(sex, age, z) for z in sd_lines.keys()}
    
    fig, ax = plt.subplots(figsize=(12, 7.5))
    
    lengths = curves[0][0]
    
    # Fill zones
    _fill_zone_between_curves(ax, lengths, curves[-3][1], curves[-2][1], '#FFE6E6', 0.4, 'Gizi Buruk')
    _fill_zone_between_curves(ax, lengths, curves[-2][1], curves[-1][1], '#FFEBCC', 0.35, 'Gizi Kurang')
    _fill_zone_between_curves(ax, lengths, curves[-1][1], curves[1][1],  '#E8F5E9', 0.45, 'Normal')
    _fill_zone_between_curves(ax, lengths, curves[1][1],  curves[2][1],  '#FFF3CD', 0.35, 'Risiko Lebih')
    _fill_zone_between_curves(ax, lengths, curves[2][1],  curves[3][1],  '#F8D7DA', 0.4, 'Gizi Lebih')
    
    # Plot SD lines
    for z, (color, linestyle, linewidth) in sd_lines.items():
        label = "Median (WHO)" if z == 0 else f"{z:+d} SD"
        ax.plot(
            curves[z][0], curves[z][1],
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            label=label,
            zorder=5,
            alpha=0.9
        )
    
    # Plot child's data
    z_whz = payload['z'].get('whz')
    
    if z_whz is not None:
        if abs(z_whz) > 3:
            point_color = '#8B0000'
            point_size = 500
        elif abs(z_whz) > 2:
            point_color = '#DC143C'
            point_size = 450
        elif abs(z_whz) > 1:
            point_color = theme['primary']
            point_size = 400
        else:
            point_color = theme['secondary']
            point_size = 400
    else:
        point_color = theme['secondary']
        point_size = 400
    
    ax.scatter(
        [height], [weight],
        s=point_size,
        c=point_color,
        edgecolors='white',
        linewidths=3,
        label=f"Data Anak ({weight:.1f} kg)",
        zorder=10,
        marker='o',
        alpha=1.0
    )
    
    ax.annotate(
        f"{weight:.1f} kg / {height:.1f} cm\nZ: {format_zscore(z_whz)}",
        (height, weight),
        xytext=(10, 10),
        textcoords='offset points',
        fontsize=10,
        fontweight='bold',
        bbox=dict(
            boxstyle='round,pad=0.6',
            facecolor=point_color,
            edgecolor='white',
            linewidth=2,
            alpha=0.9
        ),
        color='white',
        zorder=11
    )
    
    measurement_type = "Panjang Badan" if age < 24 else "Tinggi Badan"
    ax.set_xlabel(f"{measurement_type} (cm)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Berat Badan (kg)", fontsize=12, fontweight='bold')
    ax.set_title(
        f"Grafik Berat Badan menurut {measurement_type} (BB/TB) - WHO Standards\n"
        f"{'Laki-laki' if sex == 'M' else 'Perempuan'} | Usia: {age:.1f} bulan",
        fontsize=14,
        fontweight='bold',
        pad=15
    )
    
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.legend(loc='upper left', framealpha=0.95, fancybox=True, shadow=True, fontsize=9)
    ax.set_xlim(BOUNDS['wfl_l'][0] - 2, BOUNDS['wfl_l'][1] + 2)
    ax.set_ylim(0, None)
    
    plt.tight_layout()
    
    return fig


def plot_zscore_summary_bars(payload: Dict, theme_name: str = "pink_pastel") -> Figure:
    """
    Plot bar chart summarizing all z-scores
    
    Args:
        payload: Data dict with z-scores
        theme_name: Theme to apply
        
    Returns:
        Matplotlib Figure object
    """
    theme = apply_matplotlib_theme(theme_name)
    
    z_scores = payload.get('z', {})
    
    # Prepare data
    indices = []
    values = []
    colors = []
    labels_text = []
    
    for key, label in [('waz', 'BB/U'), ('haz', 'TB/U'), ('whz', 'BB/TB'), 
                       ('baz', 'IMT/U'), ('hcz', 'LK/U')]:
        z = z_scores.get(key)
        if z is not None and not math.isnan(z):
            indices.append(label)
            values.append(z)
            labels_text.append(format_zscore(z))
            
            # Color based on severity
            if abs(z) > 3:
                colors.append('#8B0000')  # Dark red
            elif abs(z) > 2:
                colors.append('#DC143C')  # Red
            elif abs(z) > 1:
                colors.append('#FFA500')  # Orange
            else:
                colors.append('#28a745')  # Green
    
    if not indices:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(
            0.5, 0.5,
            "Tidak ada data z-score tersedia",
            ha='center', va='center',
            transform=ax.transAxes,
            fontsize=14
        )
        return fig
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    bars = ax.bar(indices, values, color=colors, edgecolor='white', linewidth=2, alpha=0.85)
    
    # Add value labels on bars
    for bar, val, txt in zip(bars, values, labels_text):
        height = bar.get_height()
        y_offset = 0.3 if height > 0 else -0.5
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + y_offset,
            txt,
            ha='center',
            va='bottom' if height > 0 else 'top',
            fontsize=12,
            fontweight='bold',
            color='black'
        )
    
    # Reference lines
    ax.axhline(y=-3, color='#DC143C', linestyle='--', linewidth=1.5, alpha=0.6, label='-3 SD')
    ax.axhline(y=-2, color='#FF6347', linestyle='--', linewidth=1.5, alpha=0.6, label='-2 SD')
    ax.axhline(y=0, color=theme['secondary'], linestyle='-', linewidth=2, alpha=0.7, label='Median')
    ax.axhline(y=2, color='#FF6347', linestyle='--', linewidth=1.5, alpha=0.6, label='+2 SD')
    ax.axhline(y=3, color='#DC143C', linestyle='--', linewidth=1.5, alpha=0.6, label='+3 SD')
    
    # Shaded zones
    ax.axhspan(-3, -2, facecolor='#FFE6E6', alpha=0.3, zorder=0)
    ax.axhspan(-2, 2, facecolor='#E8F5E9', alpha=0.3, zorder=0)
    ax.axhspan(2, 3, facecolor='#FFF3CD', alpha=0.3, zorder=0)
    
    ax.set_xlabel("Indeks Antropometri", fontsize=12, fontweight='bold')
    ax.set_ylabel("Z-Score", fontsize=12, fontweight='bold')
    ax.set_title(
        "Ringkasan Z-Score Semua Indeks WHO\n"
        f"Anak: {payload.get('name_child', 'N/A')} | "
        f"{'Laki-laki' if payload['sex'] == 'M' else 'Perempuan'} | "
        f"Usia: {payload['age_mo']:.1f} bulan",
        fontsize=14,
        fontweight='bold',
        pad=15
    )
    
    ax.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.7)
    ax.legend(loc='upper right', framealpha=0.95, fancybox=True, shadow=True, fontsize=9)
    ax.set_ylim(-4, 4)
    
    plt.tight_layout()
    
    return fig


def cleanup_matplotlib_figures(figures: List[Figure]):
    """
    Properly cleanup matplotlib figures to prevent memory leaks
    
    Args:
        figures: List of matplotlib Figure objects
    """
    for fig in figures:
        if fig is not None:
            plt.close(fig)


print("✅ Section 7B loaded: WFL plotting, bar chart & figure cleanup")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: EXPORT FUNCTIONS (PDF & CSV) (from v3.0/v3.1)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_qr_code(text: str = None) -> Optional[io.BytesIO]:
    """
    Generate QR code for WhatsApp contact or sharing
    
    Args:
        text: Text to encode in QR (defaults to WhatsApp contact)
        
    Returns:
        BytesIO buffer with PNG image or None
    """
    if text is None:
        text = f"https://wa.me/{CONTACT_WA}?text=Halo%20PeduliGiziBalita,%20saya%20tertarik%20dengan%20aplikasi%20ini"
    
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
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
        print(f"QR code generation error: {e}")
        return None


def export_to_csv(payload: Dict, filename: str) -> Optional[str]:
    """
    Export analysis results to CSV format
    
    Args:
        payload: Analysis data dictionary
        filename: Output filename
        
    Returns:
        Filepath if successful, None otherwise
    """
    try:
        filepath = os.path.join(OUTPUTS_DIR, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['═══════════════════════════════════════════════════════════'])
            writer.writerow(['PeduliGiziBalita - LAPORAN ANALISIS PERTUMBUHAN ANAK']) # MODIFIED
            writer.writerow(['Based on WHO Child Growth Standards 2006 & Permenkes RI 2020'])
            writer.writerow(['═══════════════════════════════════════════════════════════'])
            writer.writerow([])
            
            # Child information
            writer.writerow(['═══ INFORMASI ANAK ═══'])
            writer.writerow(['Nama Anak', payload.get('name_child', '-')])
            writer.writerow(['Nama Orang Tua/Wali', payload.get('name_parent', '-')])
            writer.writerow(['Jenis Kelamin', payload.get('sex_text', '-')])
            writer.writerow(['Usia (bulan)', f"{payload.get('age_mo', 0):.2f}"])
            writer.writerow(['Usia (hari)', payload.get('age_days', 0)])
            writer.writerow(['Tanggal Lahir', payload.get('dob', '-')])
            writer.writerow(['Tanggal Pengukuran', payload.get('dom', '-')])
            writer.writerow([])
            
            # Anthropometric measurements
            writer.writerow(['═══ PENGUKURAN ANTROPOMETRI ═══'])
            writer.writerow(['Berat Badan (kg)', f"{payload.get('w', 0):.2f}"])
            writer.writerow(['Panjang/Tinggi Badan (cm)', f"{payload.get('h', 0):.2f}"])
            hc = payload.get('hc')
            writer.writerow(['Lingkar Kepala (cm)', f"{hc:.2f}" if hc else '-'])
            
            # BMI calculation
            w = payload.get('w', 0)
            h = payload.get('h', 0)
            if w > 0 and h > 0:
                bmi = w / ((h / 100) ** 2)
                writer.writerow(['Indeks Massa Tubuh (BMI)', f"{bmi:.2f}"])
            writer.writerow([])
            
            # Analysis results
            writer.writerow(['═══ HASIL ANALISIS Z-SCORE ═══'])
            writer.writerow(['Indeks', 'Z-Score', 'Persentil (%)', 'Kategori (Permenkes)', 'Kategori (WHO)'])
            
            z_scores = payload.get('z', {})
            percentiles = payload.get('percentiles', {})
            permenkes = payload.get('permenkes', {})
            who = payload.get('who', {})
            
            for key, label in [('waz', 'WAZ (BB/U)'), ('haz', 'HAZ (TB/U)'), 
                               ('whz', 'WHZ (BB/TB)'), ('baz', 'BAZ (IMT/U)'), 
                               ('hcz', 'HCZ (LK/U)')]:
                z_val = format_zscore(z_scores.get(key))
                pct = percentiles.get(key)
                pct_str = f"{pct:.1f}" if pct is not None else "—"
                perm_cat = permenkes.get(key, "—")
                who_cat = who.get(key, "—")
                
                writer.writerow([label, z_val, pct_str, perm_cat, who_cat])
            
            writer.writerow([])
            
            # Metadata
            writer.writerow(['═══ METADATA ═══'])
            writer.writerow(['Tanggal Export', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['Versi Aplikasi', APP_VERSION])
            writer.writerow(['Sumber Data', 'WHO Child Growth Standards 2006'])
            writer.writerow(['Referensi', 'Permenkes RI No. 2 Tahun 2020'])
            writer.writerow(['URL Aplikasi', BASE_URL])
            writer.writerow(['Kontak', f'+{CONTACT_WA}'])
        
        print(f"✅ CSV exported: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ CSV export error: {e}")
        traceback.print_exc()
        return None


def export_to_pdf(payload: Dict, figures: List[Figure], filename: str) -> Optional[str]:
    """
    Export comprehensive PDF report with all charts and analysis
    
    Args:
        payload: Analysis data dictionary
        figures: List of matplotlib figures [WFA, HFA, HCFA, WFL, Bars]
        filename: Output filename
        
    Returns:
        Filepath if successful, None otherwise
    """
    try:
        filepath = os.path.join(OUTPUTS_DIR, filename)
        c = canvas.Canvas(filepath, pagesize=A4)
        W, H = A4
        
        theme = UI_THEMES.get(payload.get('theme', 'pink_pastel'), UI_THEMES['pink_pastel'])
        
        # ═════════ PAGE 1: SUMMARY & DATA ═════════
        
        # Header bar
        c.setFillColorRGB(0.965, 0.647, 0.753)  # Pink
        c.rect(0, H - 55, W, 55, stroke=0, fill=1)
        
        c.setFillColor(rl_colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(30, H - 30, "PeduliGiziBalita - Laporan Analisis Pertumbuhan Anak") # MODIFIED
        
        c.setFont("Helvetica", 10)
        c.drawRightString(W - 30, H - 30, datetime.now().strftime("%d %B %Y, %H:%M WIB"))
        
        # Child info section
        y = H - 85
        c.setFillColor(rl_colors.black)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(30, y, "INFORMASI ANAK")
        
        # Draw info box
        c.setStrokeColorRGB(0.9, 0.9, 0.9)
        c.setLineWidth(0.5)
        c.rect(25, y - 90, W - 50, 85, stroke=1, fill=0)
        
        y -= 20
        c.setFont("Helvetica", 11)
        
        if payload.get('name_child'):
            c.drawString(35, y, f"Nama: {payload['name_child']}")
            y -= 16
        
        if payload.get('name_parent'):
            c.drawString(35, y, f"Orang Tua/Wali: {payload['name_parent']}")
            y -= 16
        
        c.drawString(35, y, f"Jenis Kelamin: {payload['sex_text']}")
        y -= 16
        c.drawString(35, y, f"Usia: {payload['age_mo']:.1f} bulan (≈ {payload['age_days']} hari)")
        y -= 16
        
        if payload.get('dob'):
            c.drawString(35, y, f"Tanggal Lahir: {payload['dob']}")
            y -= 16
        
        if payload.get('dom'):
            c.drawString(35, y, f"Tanggal Pengukuran: {payload['dom']}")
        
        # Anthropometric data section
        y -= 40
        c.setFont("Helvetica-Bold", 13)
        c.drawString(30, y, "DATA ANTROPOMETRI")
        
        c.rect(25, y - 70, W - 50, 65, stroke=1, fill=0)
        
        y -= 20
        c.setFont("Helvetica", 11)
        c.drawString(35, y, f"Berat Badan: {payload['w']:.2f} kg")
        y -= 16
        c.drawString(35, y, f"Panjang/Tinggi: {payload['h']:.2f} cm")
        y -= 16
        
        if payload.get('hc'):
            c.drawString(35, y, f"Lingkar Kepala: {payload['hc']:.2f} cm")
            y -= 16
        
        # Calculate BMI
        w = payload['w']
        h = payload['h']
        if w > 0 and h > 0:
            bmi = w / ((h / 100) ** 2)
            c.drawString(35, y, f"Indeks Massa Tubuh (BMI): {bmi:.2f} kg/m²")
        
        # Results table
        y -= 35
        c.setFont("Helvetica-Bold", 13)
        c.drawString(30, y, "HASIL ANALISIS Z-SCORE")
        y -= 20
        
        # Table header
        c.setFont("Helvetica-Bold", 9)
        c.drawString(35, y, "Indeks")
        c.drawString(110, y, "Z-Score")
        c.drawString(165, y, "Persentil")
        c.drawString(230, y, "Status (Permenkes)")
        c.drawString(420, y, "Status (WHO)")
        
        y -= 3
        c.line(30, y, W - 30, y)
        y -= 14
        
        # Table rows
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
            pct_str = f"{pct:.1f}%" if pct is not None else "—"
            perm_cat = permenkes.get(key, "—")[:35]
            who_cat = who.get(key, "—")[:25]
            
            c.drawString(35, y, label)
            
            # Color-code z-score
            z = z_scores.get(key)
            if z is not None and not math.isnan(z):
                if abs(z) > 3:
                    c.setFillColorRGB(0.545, 0, 0)  # Dark red
                elif abs(z) > 2:
                    c.setFillColorRGB(0.863, 0.078, 0.235)  # Red
                elif abs(z) > 1:
                    c.setFillColorRGB(1, 0.647, 0)  # Orange
                else:
                    c.setFillColorRGB(0.157, 0.655, 0.271)  # Green
            
            c.drawString(110, y, z_val)
            c.setFillColor(rl_colors.black)
            
            c.drawString(165, y, pct_str)
            c.drawString(230, y, perm_cat)
            c.drawString(420, y, who_cat)
            y -= 14
        
        # QR Code
        qr_buf = generate_qr_code()
        if qr_buf:
            try:
                c.drawImage(ImageReader(qr_buf), W - 85, 40, width=55, height=55)
                c.setFont("Helvetica-Oblique", 7)
                c.drawRightString(W - 30, 30, "Scan untuk info lebih lanjut")
            except Exception as e:
                print(f"QR code insertion error: {e}")
        
        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(30, 20, f"WHO Child Growth Standards 2006 | Permenkes RI No. 2/2020")
        c.drawRightString(W - 30, 20, "Hal. 1")
        
        c.showPage()
        
        # ═════════ PAGES 2-6: CHARTS ═════════
        
        chart_titles = [
            "Grafik Berat Badan menurut Umur (BB/U)",
            "Grafik Panjang/Tinggi Badan menurut Umur (TB/U)",
            "Grafik Lingkar Kepala menurut Umur (LK/U)",
            "Grafik Berat menurut Panjang/Tinggi (BB/TB)",
            "Ringkasan Z-Score Semua Indeks"
        ]
        
        for page_num, (title, fig) in enumerate(zip(chart_titles, figures), start=2):
            if fig is None:
                continue
            
            # Header
            c.setFillColorRGB(0.965, 0.647, 0.753)
            c.rect(0, H - 45, W, 45, stroke=0, fill=1)
            c.setFillColor(rl_colors.white)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(30, H - 26, title)
            
            # Save figure to buffer
            buf = io.BytesIO()
            try:
                fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buf.seek(0)
                
                # Insert chart
                c.drawImage(ImageReader(buf), 30, 80, width=W - 60, height=H - 150)
                
            except Exception as e:
                print(f"Chart insertion error for {title}: {e}")
                c.setFont("Helvetica", 11)
                c.drawString(100, H / 2, f"Error rendering chart: {str(e)[:50]}")
            finally:
                buf.close()
            
            # Footer
            c.setFillColor(rl_colors.black)
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(30, 50, f"Anak: {payload.get('name_child', 'N/A')} | "
                                f"{'Laki-laki' if payload['sex'] == 'M' else 'Perempuan'} | "
                                f"Usia: {payload['age_mo']:.1f} bulan")
            c.drawRightString(W - 30, 50, f"Hal. {page_num}")
            
            c.showPage()
        
        # Save PDF
        c.save()
        
        print(f"✅ PDF exported: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ PDF export error: {e}")
        traceback.print_exc()
        return None


print("✅ Section 8 loaded: Export functions (PDF & CSV with QR codes)")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9: ANALYSIS HANDLER & INTERPRETATION (from v3.0/v3.1)
# ═══════════════════════════════════════════════════════════════════════════════

def create_interpretation_text(payload: Dict) -> str:
    """
    Create detailed interpretation text from analysis results
    
    Args:
        payload: Analysis data dictionary with z-scores and classifications
        
    Returns:
        Formatted markdown interpretation string
    """
    lines = []
    
    z_scores = payload.get('z', {})
    permenkes = payload.get('permenkes', {})
    who = payload.get('who', {})
    percentiles = payload.get('percentiles', {})
    
    # Header
    lines.append(f"## 📊 Interpretasi Hasil Analisis")
    lines.append(f"")
    lines.append(f"**Nama**: {payload.get('name_child', 'N/A')}")
    lines.append(f"**Jenis Kelamin**: {payload.get('sex_text', 'N/A')}")
    lines.append(f"**Usia**: {payload.get('age_mo', 0):.1f} bulan (~{payload.get('age_days', 0)} hari)")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    
    # WAZ (Weight-for-Age) Analysis
    waz = z_scores.get('waz')
    if waz is not None and not math.isnan(waz):
        pct = percentiles.get('waz')
        pct_text = f"persentil ke-{pct:.1f}" if pct else "N/A"
        
        lines.append(f"### 🔹 Berat Badan menurut Umur (BB/U)")
        lines.append(f"")
        lines.append(f"**Z-Score**: {format_zscore(waz)} ({pct_text})")
        lines.append(f"**Status (Permenkes)**: {permenkes.get('waz', 'N/A')}")
        lines.append(f"**Status (WHO)**: {who.get('waz', 'N/A')}")
        lines.append(f"")
        
        # Interpretation and recommendations
        if waz < -3:
            lines.append(f"⚠️ **PERHATIAN SERIUS**: Anak mengalami kekurangan berat badan sangat parah.")
            lines.append(f"")
            lines.append(f"**Rekomendasi**:")
            lines.append(f"- 🏥 Segera konsultasi ke dokter anak atau puskesmas")
            lines.append(f"- 💊 Mungkin memerlukan suplementasi gizi khusus")
            lines.append(f"- 📝 Evaluasi pola makan dan frekuensi pemberian makan")
            lines.append(f"- 🔍 Periksa kemungkinan penyakit penyerta (infeksi, malabsorpsi)")
        elif waz < -2:
            lines.append(f"⚠️ **PERHATIAN**: Anak mengalami kekurangan berat badan.")
            lines.append(f"")
            lines.append(f"**Rekomendasi**:")
            lines.append(f"- 🏥 Konsultasi ke tenaga kesehatan")
            lines.append(f"- 🍽️ Tingkatkan asupan kalori dan protein")
            lines.append(f"- 📊 Monitoring rutin setiap bulan")
            lines.append(f"- 🥗 Berikan makanan bergizi seimbang")
        elif waz <= 2:
            lines.append(f"✅ **BAIK**: Berat badan anak berada dalam rentang normal.")
            lines.append(f"")
            lines.append(f"**Rekomendasi**:")
            lines.append(f"- 👍 Pertahankan pola makan sehat dan seimbang")
            lines.append(f"- 📆 Lanjutkan pemantauan rutin tiap 3 bulan")
            lines.append(f"- 🎯 Pastikan ASI eksklusif hingga 6 bulan (jika bayi)")
        else:
            lines.append(f"⚠️ **PERHATIAN**: Risiko berat badan berlebih.")
            lines.append(f"")
            lines.append(f"**Rekomendasi**:")
            lines.append(f"- 🏥 Konsultasi ahli gizi untuk evaluasi pola makan")
            lines.append(f"- 🏃 Tingkatkan aktivitas fisik sesuai usia")
            lines.append(f"- 🍎 Batasi makanan tinggi gula dan lemak")
            lines.append(f"- 💧 Perbanyak konsumsi sayur dan buah")
        
        lines.append(f"")
    
    # HAZ (Height-for-Age) Analysis  
    haz = z_scores.get('haz')
    if haz is not None and not math.isnan(haz):
        pct = percentiles.get('haz')
        pct_text = f"persentil ke-{pct:.1f}" if pct else "N/A"
        
        lines.append(f"### 🔹 Tinggi/Panjang Badan menurut Umur (TB/U)")
        lines.append(f"")
        lines.append(f"**Z-Score**: {format_zscore(haz)} ({pct_text})")
        lines.append(f"**Status (Permenkes)**: {permenkes.get('haz', 'N/A')}")
        lines.append(f"**Status (WHO)**: {who.get('haz', 'N/A')}")
        lines.append(f"")
        
        if haz < -3:
            lines.append(f"⚠️ **STUNTING BERAT**: Anak mengalami gangguan pertumbuhan linear parah.")
            lines.append(f"")
            lines.append(f"**Rekomendasi**:")
            lines.append(f"- 🏥 **URGENT**: Konsultasi ke dokter spesialis anak")
            lines.append(f"- 🧬 Evaluasi hormon pertumbuhan dan penyakit kronis")
            lines.append(f"- 🍽️ Program gizi intensif dengan suplementasi")
            lines.append(f"- 📚 Stimulasi tumbuh kembang komprehensif")
            lines.append(f"- 💊 Pertimbangkan vitamin D dan kalsium")
        elif haz < -2:
            lines.append(f"⚠️ **STUNTING**: Anak mengalami gangguan pertumbuhan linear (pendek).")
            lines.append(f"")
            lines.append(f"**Rekomendasi**:")
            lines.append(f"- 🏥 Konsultasi ke puskesmas atau dokter anak")
            lines.append(f"- 🥛 Tingkatkan asupan protein, kalsium, zinc")
            lines.append(f"- 🌞 Paparan sinar matahari pagi untuk vitamin D")
            lines.append(f"- 📊 Monitoring ketat setiap bulan")
            lines.append(f"- 🔍 Cek riwayat penyakit infeksi berulang")
        elif haz <= 3:
            lines.append(f"✅ **BAIK**: Tinggi badan anak normal sesuai usia.")
            lines.append(f"")
            lines.append(f"**Rekomendasi**:")
            lines.append(f"- 👍 Pertahankan asupan gizi seimbang")
            lines.append(f"- 🏃 Aktivitas fisik teratur untuk mendukung pertumbuhan")
            lines.append(f"- 😴 Tidur cukup (10-12 jam untuk balita)")
        else:
            lines.append(f"ℹ️ **INFORMASI**: Tinggi badan di atas rata-rata (tinggi).")
            lines.append(f"")
            lines.append(f"**Catatan**: Umumnya normal, terutama jika orang tua juga tinggi.")
            lines.append(f"Jika sangat ekstrem, konsultasi dokter untuk evaluasi.")
        
        lines.append(f"")
    
    # WHZ (Weight-for-Height) Analysis
    whz = z_scores.get('whz')
    if whz is not None and not math.isnan(whz):
        pct = percentiles.get('whz')
        pct_text = f"persentil ke-{pct:.1f}" if pct else "N/A"
        
        lines.append(f"### 🔹 Berat Badan menurut Tinggi Badan (BB/TB)")
        lines.append(f"")
        lines.append(f"**Z-Score**: {format_zscore(whz)} ({pct_text})")
        lines.append(f"**Status (Permenkes)**: {permenkes.get('whz', 'N/A')}")
        lines.append(f"**Status (WHO)**: {who.get('whz', 'N/A')}")
        lines.append(f"")
        
        if whz < -3:
            lines.append(f"🚨 **GIZI BURUK (WASTING BERAT)**: Kondisi kritis!")
            lines.append(f"")
            lines.append(f"**TINDAKAN SEGERA**:")
            lines.append(f"- 🏥 Rujuk ke rumah sakit SEGERA")
            lines.append(f"- 💉 Mungkin perlu rawat inap dan terapi khusus")
            lines.append(f"- 🍼 Program Makanan Tambahan (PMT)")
            lines.append(f"- 💊 Evaluasi infeksi dan penyakit penyerta")
        elif whz < -2:
            lines.append(f"⚠️ **GIZI KURANG (WASTING)**: Perlu perhatian intensif.")
            lines.append(f"")
            lines.append(f"**Rekomendasi**:")
            lines.append(f"- 🏥 Konsultasi ke tenaga kesehatan segera")
            lines.append(f"- 🍽️ Tingkatkan frekuensi makan (5-6x/hari)")
            lines.append(f"- 🥛 Tambahkan makanan padat energi")
            lines.append(f"- 📊 Timbang setiap minggu")
        elif whz <= 2:
            lines.append(f"✅ **GIZI BAIK**: Status gizi akut anak normal.")
            lines.append(f"")
            lines.append(f"**Rekomendasi**:")
            lines.append(f"- 👍 Pertahankan pola makan seimbang")
            lines.append(f"- 🎯 Variasi menu untuk mencegah bosan")
        elif whz <= 3:
            lines.append(f"⚠️ **RISIKO GIZI LEBIH**: Waspadai obesitas.")
            lines.append(f"")
            lines.append(f"**Rekomendasi**:")
            lines.append(f"- 🏃 Tingkatkan aktivitas fisik")
            lines.append(f"- 🍎 Batasi camilan manis dan gorengan")
            lines.append(f"- 💧 Cukupi kebutuhan cairan (air putih)")
        else:
            lines.append(f"⚠️ **OBESITAS**: Kelebihan berat badan signifikan.")
            lines.append(f"")
            lines.append(f"**Rekomendasi**:")
            lines.append(f"- 🏥 Konsultasi ahli gizi anak")
            lines.append(f"- 📉 Program penurunan berat badan terkontrol")
            lines.append(f"- 🏃 Aktivitas fisik teratur minimal 60 menit/hari")
            lines.append(f"- 🍽️ Porsi makan terkontrol, hindari fast food")
        
        lines.append(f"")
    
    # HCZ (Head Circumference) Analysis
    hcz = z_scores.get('hcz')
    if hcz is not None and not math.isnan(hcz):
        pct = percentiles.get('hcz')
        pct_text = f"persentil ke-{pct:.1f}" if pct else "N/A"
        
        lines.append(f"### 🔹 Lingkar Kepala menurut Umur (LK/U)")
        lines.append(f"")
        lines.append(f"**Z-Score**: {format_zscore(hcz)} ({pct_text})")
        lines.append(f"**Status**: {permenkes.get('hcz', 'N/A')}")
        lines.append(f"")
        
        if abs(hcz) > 3:
            lines.append(f"🚨 **PERHATIAN KHUSUS**: Lingkar kepala sangat tidak normal.")
            lines.append(f"")
            lines.append(f"**TINDAKAN**:")
            lines.append(f"- 🏥 **SEGERA** konsultasi ke dokter spesialis anak")
            lines.append(f"- 🧠 Evaluasi neurologis lengkap")
            lines.append(f"- 📊 Pemeriksaan penunjang (USG kepala, CT scan jika perlu)")
            lines.append(f"- 👨‍⚕️ Kemungkinan rujukan ke ahli saraf anak")
        elif abs(hcz) > 2:
            lines.append(f"⚠️ **PERLU EVALUASI**: Lingkar kepala di luar normal.")
            lines.append(f"")
            lines.append(f"**Rekomendasi**:")
            lines.append(f"- 🏥 Konsultasi dokter anak untuk evaluasi")
            lines.append(f"- 📏 Monitoring ketat lingkar kepala tiap bulan")
            lines.append(f"- 🧬 Pertimbangkan faktor genetik (bandingkan dengan orang tua)")
        else:
            lines.append(f"✅ **NORMAL**: Lingkar kepala dalam batas normal.")
            lines.append(f"")
            lines.append(f"**Catatan**: Terus pantau perkembangan neurologis anak.")
        
        lines.append(f"")
    
    # Overall summary
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"### 💡 Catatan Penting")
    lines.append(f"")
    lines.append(f"1. **Hasil ini adalah skrining awal**, bukan diagnosis medis")
    lines.append(f"2. **Konsultasikan dengan tenaga kesehatan** untuk evaluasi lengkap")
    lines.append(f"3. **Pantau pertumbuhan secara rutin** minimal setiap 3 bulan")
    lines.append(f"4. **Perhatikan milestone perkembangan** sesuai usia")
    lines.append(f"5. **Gizi seimbang + stimulasi** = kunci tumbuh kembang optimal")
    lines.append(f"")
    lines.append(f"🔗 **Butuh konsultasi?** Hubungi: [WhatsApp +{CONTACT_WA}](https://wa.me/{CONTACT_WA})")
    
    return "\n".join(lines)


def run_comprehensive_analysis(
    name_child: str,
    name_parent: str,
    sex_choice: str,
    age_mode: str,
    dob_str: str,
    dom_str: str,
    age_months_manual: float,
    weight: float,
    height: float,
    head_circ: Optional[float],
    theme_name: str
) -> Tuple:
    """
    Main analysis function that orchestrates all calculations and outputs
    
    Args:
        name_child: Child's name
        name_parent: Parent/guardian name
        sex_choice: "Laki-laki" or "Perempuan"
        age_mode: "Tanggal" or "Usia (bulan)"
        dob_str: Date of birth string
        dom_str: Date of measurement string
        age_months_manual: Manual age input in months
        weight: Weight in kg
        height: Height/length in cm
        head_circ: Head circumference in cm (optional)
        theme_name: UI theme choice
        
    Returns:
        Tuple of (
            interpretation_text,
            wfa_plot, hfa_plot, hcfa_plot, wfl_plot, bars_plot,
            pdf_file, csv_file,
            state_payload
        )
    """
    try:
        # Initialize error collection
        all_errors = []
        all_warnings = []
        
        # Parse sex
        sex = 'M' if sex_choice == "Laki-laki" else 'F'
        sex_text = sex_choice
        
        # Calculate age
        age_mo = None
        age_days = None
        dob = None
        dom = None
        
        if age_mode == "Tanggal":
            dob = parse_date(dob_str)
            dom = parse_date(dom_str)
            
            if dob is None:
                all_errors.append("❌ Format tanggal lahir tidak valid. Gunakan format YYYY-MM-DD atau DD/MM/YYYY")
            if dom is None:
                all_errors.append("❌ Format tanggal pengukuran tidak valid. Gunakan format YYYY-MM-DD atau DD/MM/YYYY")
            
            if dob and dom:
                age_mo, age_days = calculate_age_from_dates(dob, dom)
                if age_mo is None:
                    all_errors.append("❌ Tanggal pengukuran harus setelah tanggal lahir")
        else:
            age_mo = as_float(age_months_manual)
            if age_mo is None or age_mo < 0:
                all_errors.append("❌ Usia harus berupa angka positif")
            else:
                age_days = int(age_mo * 30.4375)
        
        # Parse measurements
        w = as_float(weight)
        h = as_float(height)
        hc = as_float(head_circ) if head_circ else None
        
        if w is None:
            all_errors.append("❌ Berat badan harus diisi dengan angka valid")
        if h is None:
            all_errors.append("❌ Tinggi/panjang badan harus diisi dengan angka valid")
        
        # If critical errors, return early
        if all_errors:
            error_msg = "## ❌ Error dalam Input\n\n" + "\n".join(all_errors)
            return (
                error_msg,
                None, None, None, None, None,
                gr.update(visible=False), gr.update(visible=False),
                {}
            )
        
        # Validate anthropometry
        validation_errors, validation_warnings = validate_anthropometry(age_mo, w, h, hc)
        all_errors.extend(validation_errors)
        all_warnings.extend(validation_warnings)
        
        if validation_errors:
            error_msg = "## ❌ Error Validasi Pengukuran\n\n" + "\n".join(all_errors)
            if validation_warnings:
                error_msg += "\n\n### ⚠️ Peringatan\n\n" + "\n".join(validation_warnings)
            return (
                error_msg,
                None, None, None, None, None,
                gr.update(visible=False), gr.update(visible=False),
                {}
            )
        
        # Calculate all z-scores
        z_scores = calculate_all_zscores(sex, age_mo, w, h, hc)
        
        # Validate z-scores
        zscore_errors, zscore_warnings = validate_zscores(z_scores)
        all_warnings.extend(zscore_warnings)
        
        # Calculate percentiles
        percentiles = {
            key: z_to_percentile(z)
            for key, z in z_scores.items()
        }
        
        # Classifications
        permenkes_class = classify_permenkes_2020(z_scores)
        who_class = classify_who_standards(z_scores)
        
        # Build payload
        payload = {
            'name_child': name_child or "Si Kecil",
            'name_parent': name_parent or "",
            'sex': sex,
            'sex_text': sex_text,
            'age_mo': age_mo,
            'age_days': age_days,
            'dob': dob.isoformat() if dob else None,
            'dom': dom.isoformat() if dom else None,
            'w': w,
            'h': h,
            'hc': hc,
            'z': z_scores,
            'percentiles': percentiles,
            'permenkes': permenkes_class,
            'who': who_class,
            'theme': theme_name,
            'timestamp': datetime.now().isoformat()
        }
        
        # Generate interpretation
        interpretation = create_interpretation_text(payload)
        
        # Add warnings if any
        if all_warnings:
            warning_section = "\n\n### ⚠️ Peringatan\n\n" + "\n".join(all_warnings)
            interpretation = warning_section + "\n\n---\n\n" + interpretation
        
        # Generate plots
        try:
            fig_wfa = plot_weight_for_age(payload, theme_name)
            fig_hfa = plot_height_for_age(payload, theme_name)
            fig_hcfa = plot_head_circumference_for_age(payload, theme_name)
            fig_wfl = plot_weight_for_length(payload, theme_name)
            fig_bars = plot_zscore_summary_bars(payload, theme_name)
        except Exception as e:
            print(f"❌ Plotting error: {e}")
            traceback.print_exc()
            return (
                f"## ❌ Error saat membuat grafik\n\n{str(e)}",
                None, None, None, None, None,
                gr.update(visible=False), gr.update(visible=False),
                {}
            )
        
        # Generate export files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        child_safe_name = "".join(c for c in (name_child or "anak") if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
        
        pdf_filename = f"PeduliGiziBalita_{child_safe_name}_{timestamp}.pdf" # MODIFIED
        csv_filename = f"PeduliGiziBalita_{child_safe_name}_{timestamp}.csv" # MODIFIED
        
        figures_list = [fig_wfa, fig_hfa, fig_hcfa, fig_wfl, fig_bars]
        
        pdf_path = export_to_pdf(payload, figures_list, pdf_filename)
        csv_path = export_to_csv(payload, csv_filename)
        
        # Cleanup figures to prevent memory leaks
        cleanup_matplotlib_figures(figures_list)
        
        # Prepare file outputs
        pdf_output = gr.update(value=pdf_path, visible=True) if pdf_path else gr.update(visible=False)
        csv_output = gr.update(value=csv_path, visible=True) if csv_path else gr.update(visible=False)
        
        print(f"✅ Analysis completed for {name_child}")
        
        return (
            interpretation,
            fig_wfa, fig_hfa, fig_hcfa, fig_wfl, fig_bars,
            pdf_output, csv_output,
            payload
        )
        
    except Exception as e:
        print(f"❌ Critical error in analysis: {e}")
        traceback.print_exc()
        
        error_msg = f"""
## ❌ Error Sistem

Terjadi kesalahan saat memproses data:
{str(e)}
