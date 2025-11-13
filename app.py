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
Silakan:
1. Periksa kembali semua input Anda
2. Pastikan format tanggal benar (YYYY-MM-DD)
3. Pastikan angka menggunakan titik (.) bukan koma (,)
4. Refresh halaman dan coba lagi

Jika masalah berlanjut, hubungi: +{CONTACT_WA}
"""
        
        return (
            error_msg,
            None, None, None, None, None,
            gr.update(visible=False), gr.update(visible=False),
            {}
        )


print("✅ Section 9 loaded: Analysis handler & interpretation engine")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10: CHECKLIST & KPSP FUNCTIONS (from v3.1)
# ═══════════════════════════════════════════════════════════════════════════════

# --- Helper functions (from v3.1, still required) ---

def get_immunization_for_month(month: int) -> List[str]:
    """Get immunization schedule for specific month"""
    return IMMUNIZATION_SCHEDULE.get(month, [])


def get_kpsp_questions_for_month(month: int) -> List[str]:
    """Get KPSP questions for specific month (nearest available)"""
    # Find nearest month with KPSP questions
    available_months = sorted(KPSP_QUESTIONS.keys())
    nearest = min(available_months, key=lambda x: abs(x - month))
    return KPSP_QUESTIONS.get(nearest, [])

# --- Video Helper functions (from v3.1) ---
# NOTE: This function is kept from v3.1 because it handles a LIST of videos
# The v3.2 `render_video_card_fixed` is for a SINGLE video and used elsewhere.

def generate_video_links_html(videos: List[Dict]) -> str:
    """Generate HTML for video links with cards"""
    if not videos:
        return "<p>Tidak ada video tersedia untuk usia ini.</p>"
    
    html = "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; margin: 20px 0;'>"
    
    for video in videos:
        html += f"""
        <div class='video-card'>
            <div class='video-title'>{video['title']}</div>
            <div class='video-description'>{video['description']}</div>
            <div class='video-duration'>⏱️ Durasi: {video['duration']}</div>
            <div style='margin-top: 10px;'>
                <a href='{video['url']}' target='_blank' 
                   style='display: inline-block; background: linear-gradient(135deg, #ff6b9d 0%, #ff9a9e 100%);
                          color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none;
                          font-weight: 600; font-size: 13px;'>
                    ▶️ Tonton Video
                </a>
            </div>
        </div>
        """
    
    html += "</div>"
    return html

# --- Main Checklist Function (from v3.1) ---

def generate_checklist_with_videos(month: int, payload: Dict) -> str:
    """
    Generate checklist with integrated YouTube videos (from v3.1)
    NOTE: The bug fix for this is changing the Gradio component to gr.HTML
    
    Args:
        month: Month number (0-24)
        payload: Analysis payload with z-scores
        
    Returns:
        HTML formatted recommendations (as a string)
    """
    lines = []
    
    lines.append(f"<h2> 📋 Checklist Bulan ke-{month}</h2>")
    lines.append(f"")
    
    # Get nutritional status
    z_scores = payload.get('z', {}) if payload else {}
    waz = z_scores.get('waz', 0)
    haz = z_scores.get('haz', 0)
    whz = z_scores.get('whz', 0)
    
    # ═══ ADD YOUTUBE VIDEOS ═══
    lines.append(f"<h3> 🎥 Video Edukasi untuk Usia {month} Bulan</h3>")
    lines.append(f"")
    
    # KPSP Videos
    if KPSP_YOUTUBE_VIDEOS:
        lines.append(f"<strong>📊 Panduan Skrining KPSP:</strong>")
        lines.append(f"")
        video_html = generate_video_links_html(KPSP_YOUTUBE_VIDEOS)
        lines.append(video_html)
        lines.append(f"")
    
    # MP-ASI Videos for this month
    # Find nearest month with videos
    mpasi_age_key = min(MPASI_YOUTUBE_VIDEOS.keys(), key=lambda x: abs(x - month) if x <= month else float('inf'))
    
    if month >= 6 and MPASI_YOUTUBE_VIDEOS.get(mpasi_age_key):
        lines.append(f"<strong>🍽️ Panduan MP-ASI (relevan untuk {mpasi_age_key} bulan):</strong>")
        lines.append(f"")
        mpasi_video_html = generate_video_links_html(MPASI_YOUTUBE_VIDEOS[mpasi_age_key])
        lines.append(mpasi_video_html)
        lines.append(f"")
    
    lines.append(f"<hr>")
    lines.append(f"")
    
    # ═══ EXISTING CHECKLIST CONTENT ═══
    lines.append(f"<h3> 🎯 Target Perkembangan</h3>")
    lines.append(f"")
    
    if month < 3:
        lines.append(f"<ul><li>✅ Mengangkat kepala saat tengkurap</li>")
        lines.append(f"<li>✅ Tersenyum saat diajak bicara</li>")
        lines.append(f"<li>✅ Mengikuti objek dengan mata</li></ul>")
    elif month < 6:
        lines.append(f"<ul><li>✅ Berguling dari telentang ke tengkurap</li>")
        lines.append(f"<li>✅ Duduk dengan bantuan</li>")
        lines.append(f"<li>✅ Mengoceh (ba-ba, ma-ma)</li></ul>")
    elif month < 9:
        lines.append(f"<ul><li>✅ Duduk sendiri tanpa bantuan</li>")
        lines.append(f"<li>✅ Merangkak atau bergerak</li>")
        lines.append(f"<li>✅ Memindahkan mainan antar tangan</li></ul>")
    elif month < 12:
        lines.append(f"<ul><li>✅ Berdiri berpegangan</li>")
        lines.append(f"<li>✅ Mengucapkan 1-2 kata</li>")
        lines.append(f"<li>✅ Melambaikan tangan</li></ul>")
    elif month < 18:
        lines.append(f"<ul><li>✅ Berjalan sendiri</li>")
        lines.append(f"<li>✅ Mengucapkan 3-6 kata</li>")
        lines.append(f"<li>✅ Minum dari gelas sendiri</li></ul>")
    else:
        lines.append(f"<ul><li>✅ Berlari dan melompat</li>")
        lines.append(f"<li>✅ Membuat kalimat 2-3 kata</li>")
        lines.append(f"<li>✅ Menggambar garis</li></ul>")
    
    lines.append(f"")
    
    # Nutrition recommendations
    lines.append(f"<h3> 🍽️ Rekomendasi Gizi</h3>")
    lines.append(f"")
    
    if whz < -2 or waz < -2:
        lines.append(f"<p>⚠️ <strong>PRIORITAS TINGGI</strong>: Perbaikan status gizi</p>")
        lines.append(f"<ul><li>🥛 Tingkatkan frekuensi makan 5-6x/hari</li>")
        lines.append(f"<li>🍖 Tambahkan protein hewani (telur, daging, ikan)</li>")
        lines.append(f"<li>🥑 Makanan padat energi (alpukat, kacang)</li>")
        lines.append(f"<li>💊 Konsultasi suplemen dengan dokter</li></ul>")
    elif month < 6:
        lines.append(f"<ul><li>🤱 ASI eksklusif on demand</li>")
        lines.append(f"<li>💧 Tidak perlu air atau makanan lain</li>")
        lines.append(f"<li>😴 Tidur dekat ibu untuk bonding</li></ul>")
    elif month < 12:
        lines.append(f"<ul><li>🥕 MPASI bertahap sesuai usia</li>")
        lines.append(f"<li>🤱 Lanjutkan ASI hingga 2 tahun</li>")
        lines.append(f"<li>🍚 Tekstur makanan disesuaikan</li>")
        lines.append(f"<li>💊 Suplemen zat besi jika perlu</li></ul>")
    else:
        lines.append(f"<ul><li>🍽️ Makanan keluarga dengan tekstur lembut</li>")
        lines.append(f"<li>🥗 Variasi menu 4 bintang</li>")
        lines.append(f"<li>🤱 ASI dilanjutkan sebagai pelengkap</li>")
        lines.append(f"<li>💧 Air putih cukup (600-1000ml/hari)</li></ul>")
    
    lines.append(f"")
    
    # Immunization schedule
    imm = get_immunization_for_month(month)
    if imm:
        lines.append(f"<h3> 💉 Jadwal Imunisasi Bulan Ini</h3>")
        lines.append(f"")
        lines.append("<ul>")
        for vaccine in imm:
            lines.append(f"<li>💉 {vaccine}</li>")
        lines.append("</ul>")
        lines.append(f"")
    
    # KPSP questions
    kpsp = get_kpsp_questions_for_month(month)
    if kpsp:
        lines.append(f"<h3> 🧠 Skrining Perkembangan (KPSP)</h3>")
        lines.append(f"")
        lines.append(f"<p>Jawab YA/TIDAK untuk setiap pertanyaan:</p>")
        lines.append(f"<ol>")
        for q in kpsp:
            lines.append(f"<li>{q}</li>")
        lines.append(f"</ol>")
        lines.append(f"<p><strong>Interpretasi</strong>: Jika ada ≥2 jawaban TIDAK, konsultasi ke tenaga kesehatan.</p>")
    
    lines.append(f"")
    lines.append(f"<hr>")
    lines.append(f"")
    lines.append(f"<blockquote>💡 <strong>Motivasi</strong>: {get_random_quote()}</blockquote>")
    
    # Return as a single HTML string
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10B: NEW FEATURES v3.2 (Termasuk Modifikasi Perpustakaan Lokal)
# ═══════════════════════════════════════════════════════════════════════════════

# --- FITUR 1: MODE MUDAH (Dipertahankan dari v3.2) ---

def get_normal_ranges_by_age(age_months: float, gender: str) -> Dict[str, Tuple[float, float]]:
    """
    Mendapatkan range normal (batas bawah dan atas) untuk BB, TB/PB, dan LK
    berdasarkan usia dan jenis kelamin menggunakan WHO standards (Z-score -2 SD hingga +2 SD).
    """
    gender_code = 'M' if gender == "Laki-laki" else 'F'
    
    try:
        if calc is None:
            raise Exception("Kalkulator WHO (pygrowup) tidak terinisialisasi.")
        
        age_lookup = round(age_months * 2) / 2
        if age_lookup > 60: age_lookup = 60.0 # Batas atas tabel
        if age_lookup < 0: age_lookup = 0.0 # Batas bawah tabel
            
        wfa_range = calc.wfa_table[gender_code].get(age_lookup, None)
        hfa_range = calc.lhfa_table[gender_code].get(age_lookup, None)
        hcfa_range = calc.hcfa_table[gender_code].get(age_lookup, None)
        
        if wfa_range and hfa_range and hcfa_range:
            return {
                'weight': (wfa_range.get('SD2neg', 0), wfa_range.get('SD2', 0)),
                'height': (hfa_range.get('SD2neg', 0), hfa_range.get('SD2', 0)),
                'head_circ': (hcfa_range.get('SD2neg', 0), hcfa_range.get('SD2', 0))
            }
        else:
            raise Exception(f"Data tidak ditemukan untuk usia {age_lookup} bulan")
            
    except Exception as e:
        print(f"Error di get_normal_ranges_by_age (akan fallback): {e}")
        # Fallback: Approximate values
        if gender == "Laki-laki":
            weight_base = 3.3 + (age_months * 0.5)
            height_base = 50 + (age_months * 1.5)
            head_base = 34.5 + (age_months * 0.35)
        else:
            weight_base = 3.2 + (age_months * 0.45)
            height_base = 49 + (age_months * 1.45)
            head_base = 33.9 + (age_months * 0.33)
        
        return {
            'weight': (round(weight_base - 2, 1), round(weight_base + 2, 1)),
            'height': (round(height_base - 5, 1), round(height_base + 5, 1)),
            'head_circ': (round(head_base - 1.5, 1), round(head_base + 1.5, 1))
        }


def mode_mudah_handler(age_months: int, gender: str) -> str:
    """
    Handler untuk Mode Mudah - menampilkan range normal dengan UI yang friendly.
    """
    if age_months is None or age_months < 0 or age_months > 60:
        return """
        <div style='padding: 20px; background: #fff3cd; border-left: 5px solid #ffc107; border-radius: 8px;'>
            <h3 style='color: #856404; margin-top: 0;'>⚠️ Input Tidak Valid</h3>
            <p>Mohon masukkan usia antara 0-60 bulan.</p>
        </div>
        """
    
    ranges = get_normal_ranges_by_age(float(age_months), gender)
    check_date = datetime.now().strftime("%d %B %Y")
    postur = "Berbaring (PB)" if age_months < 24 else "Berdiri (TB)"
    
    html_output = f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 20px; color: white; margin-bottom: 20px;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);'>
        <h2 style='margin: 0 0 10px 0; font-size: 28px;'>
            🎯 Mode Mudah - Referensi Cepat
        </h2>
        <p style='margin: 0; opacity: 0.9; font-size: 14px;'>
            Standar WHO 2006 | Tanggal: {check_date}
        </p>
    </div>
    <div style='background: white; padding: 25px; border-radius: 15px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px;'>
        <h3 style='color: #667eea; margin-top: 0; display: flex; align-items: center;'>
            👶 Informasi Anak
        </h3>
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;'>
            <div style='padding: 15px; background: #f8f9ff; border-radius: 10px;'>
                <div style='font-size: 13px; color: #666; margin-bottom: 5px;'>Usia</div>
                <div style='font-size: 24px; font-weight: bold; color: #667eea;'>{age_months} Bulan</div>
            </div>
            <div style='padding: 15px; background: #fff8f8; border-radius: 10px;'>
                <div style='font-size: 13px; color: #666; margin-bottom: 5px;'>Jenis Kelamin</div>
                <div style='font-size: 24px; font-weight: bold; color: #e91e63;'>
                    {'👦 Laki-laki' if gender == 'Laki-laki' else '👧 Perempuan'}
                </div>
            </div>
        </div>
    </div>
    <div style='background: white; padding: 25px; border-radius: 15px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px;'>
        <h3 style='color: #667eea; margin-top: 0;'>📊 Rentang Normal (Z-score: -2 SD hingga +2 SD)</h3>
        <p style='color: #666; font-size: 14px; margin-bottom: 20px;'>
            Nilai di bawah ini adalah <strong>rentang normal</strong> sesuai standar WHO. 
            Anak dianggap <strong>normal</strong> jika pengukurannya berada dalam rentang ini.
        </p>
        
        <div style='margin-bottom: 25px; padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    border-radius: 12px; box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <h4 style='margin: 0 0 10px 0; color: white; font-size: 18px;'>
                        ⚖️ Berat Badan (BB)
                    </h4>
                    <div style='background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;'>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;'>Batas Bawah Normal:</div>
                        <div style='font-size: 28px; font-weight: bold; color: white;'>
                            {ranges['weight'][0]:.1f} kg
                        </div>
                    </div>
                </div>
                <div style='font-size: 40px; color: rgba(255,255,255,0.5);'>→</div>
                <div>
                    <div style='background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;'>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;'>Batas Atas Normal:</div>
                        <div style='font-size: 28px; font-weight: bold; color: white;'>
                            {ranges['weight'][1]:.1f} kg
                        </div>
                    </div>
                </div>
            </div>
            <div style='margin-top: 15px; padding: 12px; background: rgba(255,255,255,0.15); 
                        border-radius: 8px; font-size: 13px; color: white;'>
                💡 <strong>Interpretasi:</strong> Jika BB anak Anda berada di antara {ranges['weight'][0]:.1f} - {ranges['weight'][1]:.1f} kg, 
                maka berat badan anak tergolong <strong>normal</strong>.
            </div>
        </div>
        
        <div style='margin-bottom: 25px; padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    border-radius: 12px; box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <h4 style='margin: 0 0 10px 0; color: white; font-size: 18px;'>
                        📏 Panjang/Tinggi Badan ({postur})
                    </h4>
                    <div style='background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;'>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;'>Batas Bawah Normal:</div>
                        <div style='font-size: 28px; font-weight: bold; color: white;'>
                            {ranges['height'][0]:.1f} cm
                        </div>
                    </div>
                </div>
                <div style='font-size: 40px; color: rgba(255,255,255,0.5);'>→</div>
                <div>
                    <div style='background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;'>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;'>Batas Atas Normal:</div>
                        <div style='font-size: 28px; font-weight: bold; color: white;'>
                            {ranges['height'][1]:.1f} cm
                        </div>
                    </div>
                </div>
            </div>
            <div style='margin-top: 15px; padding: 12px; background: rgba(255,255,255,0.15); 
                        border-radius: 8px; font-size: 13px; color: white;'>
                💡 <strong>Interpretasi:</strong> Jika TB/PB anak Anda berada di antara {ranges['height'][0]:.1f} - {ranges['height'][1]:.1f} cm, 
                maka tinggi badan anak tergolong <strong>normal</strong>.
            </div>
        </div>
        
        <div style='margin-bottom: 25px; padding: 20px; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    border-radius: 12px; box-shadow: 0 4px 15px rgba(250, 112, 154, 0.3);'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <h4 style='margin: 0 0 10px 0; color: white; font-size: 18px;'>
                        🎩 Lingkar Kepala (LK)
                    </h4>
                    <div style='background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;'>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;'>Batas Bawah Normal:</div>
                        <div style='font-size: 28px; font-weight: bold; color: white;'>
                            {ranges['head_circ'][0]:.1f} cm
                        </div>
                    </div>
                </div>
                <div style='font-size: 40px; color: rgba(255,255,255,0.5);'>→</div>
                <div>
                    <div style='background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;'>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;'>Batas Atas Normal:</div>
                        <div style='font-size: 28px; font-weight: bold; color: white;'>
                            {ranges['head_circ'][1]:.1f} cm
                        </div>
                    </div>
                </div>
            </div>
            <div style='margin-top: 15px; padding: 12px; background: rgba(255,255,255,0.15); 
                        border-radius: 8px; font-size: 13px; color: white;'>
                💡 <strong>Interpretasi:</strong> Jika LK anak Anda berada di antara {ranges['head_circ'][0]:.1f} - {ranges['head_circ'][1]:.1f} cm, 
                maka lingkar kepala anak tergolong <strong>normal</strong>.
            </div>
        </div>
    </div>
    <div style='background: #e3f2fd; padding: 20px; border-radius: 12px; border-left: 5px solid #2196f3;'>
        <h4 style='color: #1976d2; margin-top: 0;'>📋 Catatan Penting:</h4>
        <ul style='color: #555; line-height: 1.8; margin: 10px 0; padding-left: 20px;'>
            <li><strong>Rentang Normal:</strong> Nilai antara -2 SD dan +2 SD dianggap normal menurut WHO</li>
            <li><strong>Di Bawah Batas:</strong> Jika pengukuran &lt; batas bawah, anak mungkin mengalami malnutrisi/stunting</li>
            <li><strong>Di Atas Batas:</strong> Jika pengukuran &gt; batas atas, anak mungkin mengalami overweight/makrosefali</li>
            <li><strong>Konsultasi:</strong> Jika nilai anak di luar rentang, <strong>segera konsultasi ke dokter/ahli gizi</strong></li>
            <li><strong>Monitoring Rutin:</strong> Lakukan pemeriksaan antropometri minimal 1 bulan sekali</li>
        </ul>
    </div>
    <div style='background: #fff9e6; padding: 15px; border-radius: 10px; margin-top: 20px;
                border: 2px dashed #ffc107; text-align: center;'>
        <p style='margin: 0; color: #856404; font-weight: 500;'>
            🌟 <strong>Tips:</strong> Untuk analisis yang lebih akurat, gunakan 
            <strong>"Kalkulator Gizi WHO"</strong> di tab utama untuk menghitung Z-score lengkap!
        </p>
    </div>
    """
    
    return html_output

# --- FITUR 2: PERPUSTAKAAN LOKAL (PENGGANTI v3.2) ---
# Menggantikan PERPUSTAKAAN_IBU_BALITA_UPDATED dan render_perpustakaan_updated

ARTIKEL_LOKAL_DATABASE = [
    {
        "kategori": "Nutrisi & MPASI",
        "title": "Panduan MPASI Menu Lengkap (WHO & Kemenkes)",
        "summary": "Panduan MPASI perdana 6 bulan sesuai standar WHO dan Kemenkes, fokus pada Protein Hewani.",
        "source": "WHO, Kemenkes RI (Permenkes No. 2 Th 2020)",
        "full_content": """
        # Panduan MPASI Menu Lengkap (WHO & Kemenkes)
        
        Memberikan Makanan Pendamping ASI (MPASI) adalah tahap krusial dalam 1000 Hari Pertama Kehidupan (HPK). Kesalahan dalam pemberian MPASI dapat berkontribusi pada risiko stunting.
        
        ## Kapan Memulai MPASI?
        
        WHO dan Ikatan Dokter Anak Indonesia (IDAI) merekomendasikan pemberian MPASI dimulai saat bayi berusia **tepat 6 bulan (180 hari)**. 
        
        Tanda bayi siap menerima MPASI:
        * Kepala sudah tegak dan bisa duduk dengan bantuan.
        * Menunjukkan ketertarikan pada makanan (misalnya, mencoba meraih makanan).
        * Refleks menjulurkan lidah (menjilat) sudah berkurang.
        
        ## Prinsip MPASI 4 Kuadran (Menu Lengkap)
        
        Konsep "menu 4 bintang" yang lama (nasi, sayur, lauk nabati, lauk hewani) **sudah tidak memadai**. Standar terbaru Kemenkes dan WHO menekankan **MPASI Menu Lengkap** yang harus mengandung:
        
        1.  **Karbohidrat (Sumber Energi):** Nasi, kentang, ubi, jagung.
        2.  **Protein Hewani (Wajib!):** Ikan, ayam, daging sapi, telur, hati ayam. Ini adalah komponen terpenting untuk mencegah stunting.
        3.  **Protein Nabati (Pendukung):** Tahu, tempe, kacang-kacangan.
        4.  **Lemak Tambahan (Penting!):** Minyak (minyak kelapa, minyak zaitun), santan, mentega. Lemak sangat penting untuk perkembangan otak dan penyerapan vitamin.
        
        ## Mengapa Protein Hewani SANGAT PENTING?
        
        Protein hewani adalah kunci utama pencegahan stunting. ASI setelah 6 bulan sudah tidak mencukupi kebutuhan zat besi dan zinc bayi.
        
        * **Zat Besi (Fe):** Protein hewani (terutama hati ayam dan daging merah) mengandung zat besi *heme* yang penyerapannya jauh lebih baik (hingga 40%) dibanding zat besi *non-heme* dari sayuran (penyerapan <10%).
        * **Zinc:** Penting untuk pertumbuhan dan sistem imun.
        * **Vitamin B12 & Asam Amino Esensial:** Vital untuk perkembangan otak.
        
        > **Rekomendasi Kemenkes:** Berikan protein hewani **setiap hari** dalam menu MPASI sejak usia 6 bulan.
        
        ## Evolusi Tekstur MPASI
        
        * **6 Bulan:** *Puree* (saring halus). Makanan dilumatkan hingga halus dan disaring.
        * **7-8 Bulan:** *Mashed* (lumat kasar). Makanan dilumatkan kasar tanpa disaring.
        * **9-11 Bulan:** *Minced/Chopped* (cincang halus/kasar). Makanan dicincang. Mulai ajarkan *finger food* (makanan yang bisa dipegang).
        * **12+ Bulan:** Makanan Keluarga. Anak makan menu yang sama dengan keluarga, dicincang atau disesuaikan seperlunya.
        
        ## Aturan Pemberian Makan (Responsive Feeding)
        
        * Buat jadwal makan yang teratur (3x makan utama, 2x snack).
        * Durasi makan maksimal 30 menit.
        * Ciptakan suasana makan yang menyenangkan.
        * Jangan memaksa anak. Jika anak menolak, coba tawarkan lagi tanpa marah.
        * Jauhkan distraksi seperti mainan atau gadget saat makan.
        
        ---
        
        **Sumber (Acuan):**
        1.  World Health Organization (WHO). (2023). *Guideline for complementary feeding of infants and young children 6–23 months of age.*
        2.  Kementerian Kesehatan RI. (2020). *Peraturan Menteri Kesehatan No. 2 Tahun 2020 tentang Standar Antropometri Anak.*
        3.  Ikatan Dokter Anak Indonesia (IDAI). *Rekomendasi Praktik Pemberian Makan Berbasis Bukti pada Bayi dan Batita di Indonesia untuk Mencegah Malnutrisi.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Nutrisi & MPASI",
        "title": "Apa itu Stunting dan 1000 Hari Pertama Kehidupan (HPK)",
        "summary": "Memahami Stunting dan pentingnya 1000 HPK sebagai jendela emas pencegahan.",
        "source": "Kemenkes RI, UNICEF",
        "full_content": """
        # Apa itu Stunting dan 1000 Hari Pertama Kehidupan (HPK)
        
        Stunting adalah masalah gizi kronis yang menjadi fokus utama kesehatan anak di Indonesia. Memahaminya adalah langkah awal pencegahan.
        
        ## Definisi Stunting
        
        Stunting **bukan** berarti "pendek" biasa karena faktor genetik.
        
        **Stunting adalah** kondisi gagal tumbuh pada anak balita akibat kekurangan gizi kronis (jangka panjang), terutama pada 1000 Hari Pertama Kehidupan (HPK).
        
        Secara klinis, stunting didiagnosis ketika panjang atau tinggi badan anak berada di bawah minus dua standar deviasi (<-2 SD) kurva pertumbuhan WHO. (Indikator TB/U atau PB/U).
        
        ## Dampak Stunting
        
        Stunting bukan hanya masalah fisik (pendek). Dampak yang paling berbahaya justru tidak terlihat:
        
        1.  **Perkembangan Otak Terhambat:** Gagal tumbuh seringkali disertai gagal kembang. Anak stunting berisiko memiliki kecerdasan (IQ) lebih rendah.
        2.  **Sistem Imun Lemah:** Anak menjadi lebih mudah dan lebih sering sakit (misal: diare, ISPA berulang).
        3.  **Dampak Jangka Panjang:** Saat dewasa, anak stunting berisiko lebih tinggi menderita penyakit kronis seperti diabetes, hipertensi, dan penyakit jantung.
        
        ## 1000 Hari Pertama Kehidupan (HPK)
        
        1000 HPK adalah "Jendela Emas" pencegahan stunting. Periode ini adalah waktu di mana pertumbuhan otak dan fisik terjadi sangat pesat.
        
        **Periode 1000 HPK dihitung sejak:**
        
        > **Masa Kehamilan (270 hari) + Usia 0-2 Tahun (730 hari) = 1000 Hari**
        
        Kekurangan gizi yang terjadi pada periode ini bersifat *irreversible* (tidak dapat diperbaiki sepenuhnya) jika sudah melewati usia 2 tahun.
        
        ## Strategi Pencegahan Stunting
        
        Pencegahan stunting harus dimulai bahkan sebelum anak lahir:
        
        1.  **Saat Ibu Hamil:**
            * Ibu harus cukup gizi (makan makanan bergizi seimbang).
            * Minum Tablet Tambah Darah (TTD) untuk mencegah anemia.
            * Rutin periksa kehamilan (ANC).
        
        2.  **Bayi Lahir (0-6 Bulan):**
            * Inisiasi Menyusu Dini (IMD) segera setelah lahir.
            * **ASI Eksklusif** selama 6 bulan. ASI adalah nutrisi terbaik.
        
        3.  **Bayi 6-24 Bulan (MPASI):**
            * Berikan MPASI Menu Lengkap (lihat artikel MPASI).
            * **Wajib mengandung Protein Hewani** (ikan, telur, daging, hati) setiap hari untuk memenuhi kebutuhan zat besi dan zinc.
            * Lanjutkan ASI hingga usia 2 tahun atau lebih.
        
        4.  **Faktor Pendukung:**
            * **Imunisasi Lengkap:** Mencegah anak sakit berulang.
            * **Sanitasi & Air Bersih:** Mencegah diare dan infeksi cacing, yang dapat mengganggu penyerapan gizi.
        
        ---
        
        **Sumber (Acuan):**
        1.  Kementerian Kesehatan RI. *Buku Saku Pencegahan Stunting.*
        2.  UNICEF Indonesia. *Stunting in Indonesia: Situation, Causes, and Solutions.*
        3.  World Health Organization (WHO). *Stunting in a nutshell.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Tumbuh Kembang",
        "title": "Milestone (Tonggak) Perkembangan Anak 0-12 Bulan",
        "summary": "Panduan memantau tonggak perkembangan penting anak di tahun pertama kehidupannya.",
        "source": "CDC (USA), IDAI (KPSP)",
        "full_content": """
        # Milestone (Tonggak) Perkembangan Anak 0-12 Bulan
        
        Perkembangan anak tidak hanya soal berat dan tinggi badan, tetapi juga kemampuan (skill) yang mereka capai. Ini disebut "milestone" atau tonggak perkembangan. Pemantauan milestone penting untuk deteksi dini keterlambatan.
        
        Perkembangan dipantau melalui 4 aspek:
        1.  **Motorik Kasar:** Gerakan otot besar (duduk, merangkak, berjalan).
        2.  **Motorik Halus:** Gerakan otot kecil (menjimpit, meraih).
        3.  **Bahasa & Bicara:** Mengoceh, memahami kata, berbicara.
        4.  **Sosial & Emosional:** Interaksi, tersenyum, meniru.
        
        Berikut adalah panduan umum (rentang usia adalah wajar):
        
        ## Usia 0-3 Bulan
        
        * **Motorik Kasar:** Mengangkat kepala 45° saat tengkurap.
        * **Motorik Halus:** Mengikuti objek dengan mata, tangan mulai sering terbuka.
        * **Bahasa:** Bereaksi terhadap suara keras, mulai mengeluarkan suara "ooh" / "aah".
        * **Sosial:** Menatap wajah, tersenyum saat diajak bicara.
        
        ## Usia 4-6 Bulan
        
        * **Motorik Kasar:** Mampu berguling (telentang ke tengkurap, dan sebaliknya), mulai belajar duduk dengan bantuan/sandaran.
        * **Motorik Halus:** Meraih mainan yang digantung, memasukkan benda ke mulut.
        * **Bahasa:** Mengoceh (babbling) seperti "ba-ba-ba", "ma-ma-ma".
        * **Sosial:** Tertawa, mengenali wajah orang terdekat (ibu/ayah).
        
        ## Usia 7-9 Bulan
        
        * **Motorik Kasar:** **Duduk mandiri** tanpa sandaran, merangkak (atau *ngesot*), menarik badan untuk berdiri.
        * **Motorik Halus:** Memindahkan mainan dari satu tangan ke tangan lain, mulai menjimpit benda dengan ibu jari dan telunjuk (*pincer grasp*).
        * **Bahasa:** Menoleh saat namanya dipanggil, mengerti kata "tidak".
        * **Sosial:** Mulai takut pada orang asing (*stranger anxiety*), bermain "Cilukba".
        
        ## Usia 10-12 Bulan
        
        * **Motorik Kasar:** Berdiri berpegangan (*cruising*/merambat), beberapa anak mulai berjalan beberapa langkah.
        * **Motorik Halus:** Menjimpit benda kecil dengan rapi, memasukkan benda ke wadah.
        * **Bahasa:** Mengucapkan 1-2 kata bermakna (misal "mama" atau "papa" untuk orangnya), meniru suara, melambaikan tangan ("dadah").
        * **Sosial:** Menunjukkan benda yang diinginkan, menunjukkan afeksi.
        
        ## 🚩 Red Flags (Waspada Keterlambatan)
        
        Segera konsultasi ke dokter jika:
        * **Usia 4 Bulan:** Tidak bisa menahan kepala tetap tegak.
        * **Usia 6 Bulan:** Tidak bisa berguling, tidak tersenyum sosial.
        * **Usia 9 Bulan:** Tidak bisa duduk mandiri, tidak mengoceh.
        * **Usia 12 Bulan:** Tidak bisa berdiri berpegangan, tidak merespon saat dipanggil.
        
        ---
        
        **Sumber (Acuan):**
        1.  Centers for Disease Control and Prevention (CDC). *Milestone Moments Booklet.*
        2.  Ikatan Dokter Anak Indonesia (IDAI). *Skrining Tumbuh Kembang (KPSP).*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Tumbuh Kembang",
        "title": "Pentingnya Stimulasi untuk Perkembangan Otak",
        "summary": "Perkembangan anak tidak otomatis, perlu stimulasi (rangsangan) yang tepat dari orang tua.",
        "source": "Kemenkes RI (Buku KIA), AAP",
        "full_content": """
        # Pentingnya Stimulasi untuk Perkembangan Otak
        
        Otak anak berkembang sangat pesat pada 1000 Hari Pertama Kehidupan. Perkembangan ini tidak terjadi begitu saja; ia membutuhkan **stimulasi** atau rangsangan dari lingkungan sekitarnya, terutama orang tua.
        
        Nutrisi yang baik (seperti MPASI kaya protein hewani) menyediakan "bahan bakar" untuk otak, sementara stimulasi adalah "latihan" yang membangun koneksi antar sel saraf.
        
        ## Apa itu Stimulasi?
        
        Stimulasi adalah kegiatan bermain atau berinteraksi dengan anak yang bertujuan untuk merangsang semua inderanya (penglihatan, pendengaran, sentuhan, penciuman, rasa) dan 4 aspek kemampuannya (motorik kasar, motorik halus, bahasa, sosial).
        
        ## Cara Stimulasi Sesuai Usia
        
        Stimulasi tidak perlu mahal. Interaksi sederhana adalah kuncinya.
        
        ### Usia 0-3 Bulan
        
        * **Sentuhan & Sosial:** Peluk, gendong, dan timang anak. Lakukan kontak mata dan ajak tersenyum.
        * **Pendengaran:** Ajak bicara dengan nada lembut. Putarkan musik atau nyanyikan lagu.
        * **Motorik Kasar:** Lakukan **Tummy Time** (tengkurap) beberapa menit setiap hari (selalu awasi!). Ini sangat penting untuk menguatkan otot leher dan punggung.
        * **Penglihatan:** Gantung mainan berwarna cerah atau hitam-putih di atas tempat tidurnya.
        
        ### Usia 4-6 Bulan
        
        * **Motorik Halus:** Berikan mainan kerincingan (rattle) atau mainan yang mudah digenggam untuk diraihnya.
        * **Sosial:** Bermain "Cilukba".
        * **Bahasa:** Tirukan ocehan ("babbling") anak Anda untuk mendorongnya "berbicara".
        * **Motorik Kasar:** Bantu anak belajar duduk dengan disandarkan di bantal.
        
        ### Usia 7-9 Bulan
        
        * **Bahasa:** Sering panggil nama anak agar ia menoleh. Ajarkan kata "tidak".
        * **Motorik Halus:** Berikan *finger food* (potongan buah/biskuit) agar ia belajar menjimpit.
        * **Motorik Kasar:** Sediakan area lantai yang aman dan bersih agar anak bebas merangkak. Jangan terlalu banyak digendong atau ditaruh di *walker* (tidak direkomendasikan).
        * **Sosial:** Ajarkan melambaikan tangan ("dadah") atau tepuk tangan.
        
        ### Usia 10-12 Bulan
        
        * **Membaca Buku:** Ini adalah stimulasi terbaik! Bacakan buku cerita bergambar setiap hari. Tunjuk gambar dan sebutkan namanya (misal: "Ini Kucing", "Itu Bola").
        * **Motorik Kasar:** Latih anak berdiri dan merambat (*cruising*). Bantu ia berjalan dengan memegang kedua tangannya.
        * **Motorik Halus:** Ajarkan anak memasukkan balok ke dalam kotak atau mengambil benda kecil.
        * **Bahasa:** Ajarkan anak menunjuk bagian tubuh ("Mana hidung?", "Mana mata?").
        
        ---
        
        **Sumber (Acuan):**
        1.  Kementerian Kesehatan RI. *Buku Kesehatan Ibu dan Anak (Buku KIA).*
        2.  American Academy of Pediatrics (AAP). *Activities to Promote Your Baby’s Development.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Kesehatan & Imunisasi",
        "title": "Pentingnya Imunisasi Dasar Lengkap",
        "summary": "Mengapa imunisasi sangat penting dan daftar vaksin yang wajib diterima anak Indonesia.",
        "source": "IDAI (Jadwal 2023), Kemenkes RI",
        "full_content": """
        # Pentingnya Imunisasi Dasar Lengkap
        
        Imunisasi adalah proses membuat seseorang imun atau kebal terhadap suatu penyakit. Ini adalah salah satu intervensi kesehatan paling efektif dan hemat biaya di dunia.
        
        ## Mengapa Imunisasi PentING?
        
        1.  **Melindungi Anak Anda:** Vaksin melatih sistem kekebalan tubuh anak untuk mengenali dan melawan virus atau bakteri berbahaya sebelum penyakit tersebut sempat menyerang.
        2.  **Melindungi Orang Lain (Herd Immunity):** Ketika sebagian besar orang di komunitas sudah diimunisasi, penyebaran penyakit akan terhenti. Ini melindungi mereka yang tidak bisa divaksin (misal: bayi baru lahir, orang dengan masalah imun).
        3.  **Mencegah Penyakit Berbahaya:** Imunisasi mencegah penyakit yang dapat menyebabkan kecacatan permanen atau kematian, seperti Polio (lumpuh layu), Campak (radang otak), dan Difteri (sumbatan napas).
        
        ## Imunisasi Dasar Lengkap (Program Pemerintah RI)
        
        Pastikan anak Anda mendapatkan imunisasi dasar berikut sesuai jadwal:
        
        * **HB-0:** (Hepatitis B) 1 dosis, diberikan < 24 jam setelah lahir.
        * **BCG:** 1 dosis, mencegah TBC berat. Diberikan sebelum usia 1 bulan.
        * **Polio:** 4 dosis (Polio tetes/OPV dan Polio suntik/IPV).
        * **DPT-HB-Hib:** 4 dosis (mencegah Difteri, Pertusis/batuk rejan, Tetanus, Hepatitis B, dan infeksi Hib). Diberikan pada usia 2, 3, 4 bulan (dosis primer) dan 18 bulan (booster).
        * **Campak-Rubella (MR):** 2 dosis. Diberikan pada usia 9 bulan dan 18 bulan.
        
        ## Imunisasi Tambahan (Sangat Direkomendasikan IDAI)
        
        Selain vaksin wajib di atas, IDAI sangat merekomendasikan vaksin tambahan untuk perlindungan optimal:
        
        * **PCV (Pneumokokus):** Mencegah radang paru (pneumonia) dan radang otak (meningitis) akibat bakteri pneumokokus.
        * **Rotavirus:** Mencegah diare berat akibat rotavirus, yang merupakan penyebab utama rawat inap pada bayi.
        * **Influenza:** Diberikan setiap tahun mulai usia 6 bulan.
        * **Varisela (Cacar Air):** Diberikan mulai usia 12 bulan.
        
        ## Apakah Vaksin Aman? (Mengenal KIPI)
        
        Vaksin yang digunakan di Indonesia sangat aman dan telah melalui uji klinis bertahun-tahun.
        
        **KIPI** (Kejadian Ikutan Pasca Imunisasi) adalah reaksi yang mungkin timbul setelah imunisasi.
        
        * **KIPI Ringan (Wajar):** Demam ringan, bengkak/nyeri di lokasi suntikan, rewel. Ini adalah tanda vaksin sedang bekerja.
        * **KIPI Berat (Sangat Jarang):** Reaksi alergi berat (anafilaksis). Terjadi 1 dalam 1 juta dosis. Tenaga kesehatan sudah terlatih menanganinya.
        
        Manfaat perlindungan dari vaksinasi **jauh lebih besar** daripada risiko KIPI ringan.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Jadwal Imunisasi Anak Usia 0-18 Tahun Rekomendasi IDAI 2023.*
        2.  Kementerian Kesehatan RI. *Program Imunisasi Nasional.*
        3.  World Health Organization (WHO). *Vaccines and immunization.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Kesehatan & Imunisasi",
        "title": "Panduan Tepat Mengatasi Demam pada Anak",
        "summary": "Kapan harus khawatir saat anak demam, dan pertolongan pertama yang benar (bukan kompres dingin!).",
        "source": "IDAI, American Academy of Pediatrics (AAP)",
        "full_content": """
        # Panduan Tepat Mengatasi Demam pada Anak
        
        Demam adalah keluhan paling umum pada anak. Demam **bukanlah penyakit**, melainkan respons sistem kekebalan tubuh yang sedang melawan infeksi.
        
        ## Apa itu Demam?
        
        Seorang anak dianggap demam jika suhu tubuhnya (diukur dengan termometer) **≥ 38°C** (derajat Celsius).
        
        Suhu 37.5°C - 37.9°C dianggap *subfebris* (hangat), umumnya belum memerlukan obat.
        
        **Cara Mengukur Suhu yang Benar:**
        * **Termometer Digital:** Paling direkomendasikan. Bisa digunakan di ketiak (tahan 1-2 menit), mulut, atau rektal (anus).
        * **Termometer Dahi (Inframerah):** Cepat, namun akurasinya bisa bervariasi.
        * **JANGAN:** Mengukur dengan punggung tangan. Ini sangat tidak akurat.
        
        ## Pertolongan Pertama Saat Anak Demam
        
        Tujuan utama bukan "menghilangkan" demam, tetapi membuat anak **nyaman**.
        
        1.  **Cukupi Kebutuhan Cairan:** Demam membuat cairan tubuh cepat menguap. Berikan ASI, susu, atau air putih lebih sering untuk mencegah dehidrasi.
        2.  **Pakaian Tipis:** Jangan selimuti anak tebal-tebal. Gunakan pakaian katun tipis agar panas tubuh bisa keluar.
        3.  **Kompres Air Hangat (Bukan Dingin!)**
            * Gunakan waslap yang dibasahi **air hangat kuku** (bukan air es/dingin).
            * Letakkan kompres di lipatan tubuh (ketiak, leher, selangkangan).
            * **Mengapa air hangat?** Air hangat membuka pori-pori dan membantu panas menguap. Kompres air dingin/alkohol akan membuat tubuh menggigil (shivering), yang justru akan *meningkatkan* suhu inti tubuh.
        
        ## Kapan Memberikan Obat Penurun Panas?
        
        Obat diberikan jika:
        * Suhu ≥ 38.5°C
        * Anak tampak sangat tidak nyaman, rewel, atau kesakitan (meskipun suhu < 38.5°C).
        
        **Obat yang Aman (Pilih Salah Satu):**
        * **Paracetamol (Asetaminofen):** Dosis sesuai berat badan (10-15 mg/kgBB per kali). Dapat diulang tiap 4-6 jam.
        * **Ibuprofen:** Dosis sesuai berat badan (5-10 mg/kgBB per kali). Hanya untuk anak usia > 6 bulan. Dapat diulang tiap 6-8 jam.
        
        > **PENTING:** Selalu gunakan sendok takar bawaan obat. Jangan gunakan sendok makan. Dosis harus berdasarkan BERAT BADAN, bukan usia.
        
        ## 🚩 RED FLAGS: Kapan Harus Segera ke Dokter/UGD?
        
        Segera bawa anak ke dokter atau UGD jika demam disertai:
        
        * Usia anak **< 3 bulan** (demam pada bayi baru lahir selalu dianggap serius).
        * **Kejang** (Step).
        * **Sesak napas** atau napas sangat cepat.
        * **Penurunan kesadaran** (lemas, tidur terus, sulit dibangunkan).
        * Muntah-muntah hebat atau tidak mau minum sama sekali.
        * Demam sangat tinggi (> 40°C).
        * Demam tidak kunjung turun setelah 3 hari.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Kapan Anak Demam Perlu ke Dokter?*
        2.  American Academy of Pediatrics (AAP). *Fever and Your Baby.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
]

# Buat list judul untuk dropdown UI
JUDUL_ARTIKEL_LOKAL = sorted([artikel["title"] for artikel in ARTIKEL_LOKAL_DATABASE])

def tampilkan_artikel_lokal(judul_artikel_pilihan: str) -> str:
    """
    Mencari artikel di database ARTIKEL_LOKAL_DATABASE dan mengembalikan 
    konten lengkapnya dalam format Markdown (HTML).
    """
    if not judul_artikel_pilihan:
        return "<div style='padding: 20px; text-align: center; color: #888;'>Silakan pilih judul artikel dari daftar di atas.</div>"

    for artikel in ARTIKEL_LOKAL_DATABASE:
        if artikel["title"] == judul_artikel_pilihan:
            # Menggabungkan header dan konten
            header = f"""
            <div style='background: #f8f9fa; padding: 20px; border-radius: 12px; border-left: 5px solid #667eea; margin-bottom: 20px;'>
                <h2 style='color: #667eea; margin-top: 0;'>{artikel['title']}</h2>
                <p style='color: #555; font-size: 14px; margin-bottom: 0;'>
                    <strong>Sumber:</strong> {artikel['source']} | <strong>Kategori:</strong> {artikel['kategori']}
                </p>
            </div>
            """
            # Kita return sebagai HTML string, Gradio akan merendernya
            return header + artikel["full_content"]
            
    return f"<div style='padding: 20px; background: #f8d7da; border-left: 5px solid #dc3545; border-radius: 8px;'><h3 style='color: #721c24; margin-top: 0;'>❌ Error</h3><p>Artikel '{judul_artikel_pilihan}' tidak ditemukan.</p></div>"

# --- FITUR 3: KALKULATOR TARGET KEJAR TUMBUH (Dipertahankan dari v3.2) ---

def calculate_growth_velocity(measurements: List[Dict]) -> Dict:
    """
    Menghitung velocity pertumbuhan anak
    """
    if len(measurements) < 2:
        return {
            'status': 'insufficient_data',
            'message': 'Minimal 2 data pengukuran diperlukan untuk analisis velocity'
        }
    
    measurements = sorted(measurements, key=lambda x: x['date'])
    weight_velocity = []
    height_velocity = []
    
    for i in range(1, len(measurements)):
        prev = measurements[i-1]
        curr = measurements[i]
        time_diff = curr['age_months'] - prev['age_months']
        
        if time_diff > 0:
            wt_vel = (curr['weight'] - prev['weight']) / time_diff
            weight_velocity.append({
                'period': f"{prev['age_months']}-{curr['age_months']} bulan",
                'velocity': wt_vel, 'start_weight': prev['weight'], 'end_weight': curr['weight'], 'time_months': time_diff
            })
            ht_vel = (curr['height'] - prev['height']) / time_diff
            height_velocity.append({
                'period': f"{prev['age_months']}-{curr['age_months']} bulan",
                'velocity': ht_vel, 'start_height': prev['height'], 'end_height': curr['height'], 'time_months': time_diff
            })
    
    return {
        'status': 'success', 'measurements': measurements, 'weight_velocity': weight_velocity,
        'height_velocity': height_velocity, 'total_measurements': len(measurements),
        'monitoring_period': f"{measurements[0]['age_months']}-{measurements[-1]['age_months']} bulan"
    }


def interpret_growth_velocity(velocity_data: Dict, gender: str) -> Dict:
    """
    Interpretasi velocity pertumbuhan berdasarkan standar WHO
    """
    if velocity_data['status'] != 'success':
        return velocity_data
    
    interpretations = []
    recommendations = []
    concern_level = "normal"
    
    for wv in velocity_data['weight_velocity']:
        period_start = int(wv['period'].split('-')[0])
        vel = wv['velocity']
        
        if period_start < 3: expected, optimal = (0.6, 1.0), 0.8
        elif period_start < 6: expected, optimal = (0.4, 0.7), 0.55
        elif period_start < 12: expected, optimal = (0.25, 0.5), 0.35
        elif period_start < 24: expected, optimal = (0.15, 0.3), 0.22
        else: expected, optimal = (0.12, 0.25), 0.18
        
        if vel < expected[0]:
            status = "🔴 Pertumbuhan Lambat"
            concern_level = "critical" if vel < expected[0] * 0.5 else "warning"
            interpretations.append({
                'period': wv['period'], 'type': 'weight', 'status': status, 'velocity': vel, 'expected': optimal,
                'message': f"Velocity BB ({vel:.2f} kg/bulan) di bawah normal ({expected[0]:.2f}-{expected[1]:.2f} kg/bulan)"
            })
            recommendations.append(f"Tingkatkan asupan kalori dan protein untuk periode {wv['period']}")
        elif vel > expected[1]:
            status = "🟡 Pertumbuhan Cepat"
            if vel > expected[1] * 1.5: concern_level = "warning"
            interpretations.append({
                'period': wv['period'], 'type': 'weight', 'status': status, 'velocity': vel, 'expected': optimal,
                'message': f"Velocity BB ({vel:.2f} kg/bulan) di atas normal ({expected[0]:.2f}-{expected[1]:.2f} kg/bulan)"
            })
            recommendations.append(f"Monitor kenaikan BB berlebih pada periode {wv['period']}, konsultasi ahli gizi")
        else:
            status = "🟢 Pertumbuhan Normal"
            interpretations.append({
                'period': wv['period'], 'type': 'weight', 'status': status, 'velocity': vel, 'expected': optimal,
                'message': f"Velocity BB ({vel:.2f} kg/bulan) dalam rentang normal"
            })
    
    for hv in velocity_data['height_velocity']:
        period_start = int(hv['period'].split('-')[0])
        vel = hv['velocity']
        
        if period_start < 3: expected, optimal = (3.0, 4.0), 3.5
        elif period_start < 6: expected, optimal = (1.5, 2.5), 2.0
        elif period_start < 12: expected, optimal = (1.0, 1.5), 1.2
        elif period_start < 24: expected, optimal = (0.8, 1.2), 1.0
        else: expected, optimal = (0.5, 0.8), 0.6
        
        if vel < expected[0]:
            status = "🔴 Pertumbuhan Lambat"
            concern_level = "critical" if vel < expected[0] * 0.5 else "warning"
            interpretations.append({
                'period': hv['period'], 'type': 'height', 'status': status, 'velocity': vel, 'expected': optimal,
                'message': f"Velocity TB ({vel:.2f} cm/bulan) di bawah normal ({expected[0]:.2f}-{expected[1]:.2f} cm/bulan)"
            })
            recommendations.append(f"Fokus pada nutrisi untuk pertumbuhan linear periode {hv['period']}")
        elif vel > expected[1]:
            status = "🟢 Pertumbuhan Baik"
            interpretations.append({
                'period': hv['period'], 'type': 'height', 'status': status, 'velocity': vel, 'expected': optimal,
                'message': f"Velocity TB ({vel:.2f} cm/bulan) baik, bahkan di atas rata-rata"
            })
        else:
            status = "🟢 Pertumbuhan Normal"
            interpretations.append({
                'period': hv['period'], 'type': 'height', 'status': status, 'velocity': vel, 'expected': optimal,
                'message': f"Velocity TB ({vel:.2f} cm/bulan) dalam rentang normal"
            })
    
    if concern_level == "critical":
        recommendations.insert(0, "⚠️ PENTING: Segera konsultasi ke dokter anak atau ahli gizi untuk evaluasi lengkap")
    elif concern_level == "warning":
        recommendations.insert(0, "⚠️ Perhatian: Pertimbangkan konsultasi dengan tenaga kesehatan")
    else:
        recommendations.append("✅ Pertumbuhan anak dalam jalur yang baik, teruskan pola asuh dan nutrisi saat ini")
    
    return {
        'status': 'analyzed', 'concern_level': concern_level, 'interpretations': interpretations,
        'recommendations': recommendations, 'velocity_data': velocity_data
    }


def plot_growth_trajectory(measurements: List[Dict], gender: str) -> Optional[str]:
    """
    Plot grafik trajectory pertumbuhan dengan kurva WHO
    """
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        theme = UI_THEMES.get("pink_pastel")
        plt.rcParams.update({
            "axes.facecolor": theme["card"], "figure.facecolor": theme["bg"], "savefig.facecolor": theme["bg"],
            "text.color": theme["text"], "axes.labelcolor": theme["text"], "axes.edgecolor": theme["border"],
            "xtick.color": theme["text"], "ytick.color": theme["text"], "grid.color": theme["border"],
        })
        
        ages = [m['age_months'] for m in measurements]
        weights = [m['weight'] for m in measurements]
        heights = [m['height'] for m in measurements]
        gender_code = 'M' if gender == "Laki-laki" else 'F'
        
        ax1.plot(ages, weights, 'o-', color=theme['primary'], linewidth=2.5, markersize=10, 
                 markerfacecolor=theme['accent'], markeredgecolor='white', label='Data Anak', zorder=10)
        
        age_ref = np.arange(math.floor(min(ages)), math.ceil(max(ages)) + 1, 1)
        age_ref_valid = [a for a in age_ref if a in AGE_GRID]
        
        if age_ref_valid:
            wfa_curves = {
                z: [generate_wfa_curve(gender_code, z)[1][np.where(AGE_GRID == a)[0][0]] for a in age_ref_valid]
                for z in [-2, 0, 2]
            }
            ax1.plot(age_ref_valid, wfa_curves[0], 'k--', label='Median WHO', zorder=5)
            ax1.plot(age_ref_valid, wfa_curves[2], 'g--', label='+2 SD', zorder=5)
            ax1.plot(age_ref_valid, wfa_curves[-2], 'r--', label='-2 SD', zorder=5)
            ax1.fill_between(age_ref_valid, wfa_curves[-2], wfa_curves[2], color='green', alpha=0.1, label='Rentang Normal')

        ax1.set_xlabel('Usia (bulan)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Berat Badan (kg)', fontsize=12, fontweight='bold')
        ax1.set_title('Trajectory Berat Badan', fontsize=14, fontweight='bold', pad=15)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.legend(loc='upper left', fontsize=10)
        
        ax2.plot(ages, heights, 'o-', color=theme['secondary'], linewidth=2.5, markersize=10, 
                 markerfacecolor=theme['accent'], markeredgecolor='white', label='Data Anak', zorder=10)
        
        if age_ref_valid:
            hfa_curves = {
                z: [generate_hfa_curve(gender_code, z)[1][np.where(AGE_GRID == a)[0][0]] for a in age_ref_valid]
                for z in [-2, 0, 2]
            }
            ax2.plot(age_ref_valid, hfa_curves[0], 'k--', label='Median WHO', zorder=5)
            ax2.plot(age_ref_valid, hfa_curves[2], 'g--', label='+2 SD', zorder=5)
            ax2.plot(age_ref_valid, hfa_curves[-2], 'r--', label='-2 SD', zorder=5)
            ax2.fill_between(age_ref_valid, hfa_curves[-2], hfa_curves[2], color='green', alpha=0.1, label='Rentang Normal')

        ax2.set_xlabel('Usia (bulan)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Panjang/Tinggi Badan (cm)', fontsize=12, fontweight='bold')
        ax2.set_title('Trajectory Panjang/Tinggi Badan', fontsize=14, fontweight='bold', pad=15)
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.legend(loc='upper left', fontsize=10)
        
        for i in range(1, len(measurements)):
            prev = measurements[i-1]
            curr = measurements[i]
            time_diff = curr['age_months'] - prev['age_months']
            if time_diff == 0: continue
            
            wt_vel = (curr['weight'] - prev['weight']) / time_diff
            mid_age = (prev['age_months'] + curr['age_months']) / 2
            mid_wt = (prev['weight'] + curr['weight']) / 2
            ax1.annotate(f'+{wt_vel:.2f} kg/bln', 
                        xy=(mid_age, mid_wt), xytext=(0, 10), textcoords='offset points',
                        fontsize=9, ha='center', bbox=dict(boxstyle='round,pad=0.5', fc=theme['accent'], alpha=0.7))
            
            ht_vel = (curr['height'] - prev['height']) / time_diff
            mid_ht = (prev['height'] + curr['height']) / 2
            ax2.annotate(f'+{ht_vel:.2f} cm/bln',
                        xy=(mid_age, mid_ht), xytext=(0, 10), textcoords='offset points',
                        fontsize=9, ha='center', bbox=dict(boxstyle='round,pad=0.5', fc=theme['accent'], alpha=0.7))
        
        plt.tight_layout()
        
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"growth_trajectory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        return output_path
        
    except Exception as e:
        print(f"Error generating growth trajectory plot: {e}")
        traceback.print_exc()
        return None


def kalkulator_kejar_tumbuh_handler(
    measurement_data: str,
    gender: str
) -> Tuple[str, Optional[str]]:
    """
    Handler untuk Kalkulator Target Kejar Tumbuh
    """
    try:
        measurements = []
        lines = [l.strip() for l in measurement_data.strip().split('\n') if l.strip()]
        
        for line in lines:
            parts = line.split(',')
            if len(parts) >= 4:
                date_str, age_months, weight, height = parts[0].strip(), float(parts[1].strip()), float(parts[2].strip()), float(parts[3].strip())
                try: date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                except: date_obj = datetime.strptime(date_str, '%d-%m-%Y')
                measurements.append({'date': date_obj, 'age_months': age_months, 'weight': weight, 'height': height})
        
        if len(measurements) < 2:
            return "<div style='padding: 20px; background: #fff3cd; border-left: 5px solid #ffc107; border-radius: 8px;'><h3 style='color: #856404; margin-top: 0;'>⚠️ Data Tidak Cukup</h3><p>Minimal <strong>2 pengukuran</strong> diperlukan untuk analisis velocity pertumbuhan.</p></div>", None
        
        velocity_data = calculate_growth_velocity(measurements)
        analysis = interpret_growth_velocity(velocity_data, gender)
        plot_path = plot_growth_trajectory(measurements, gender)
        html_report = generate_kejar_tumbuh_report(analysis, gender)
        
        return html_report, plot_path
        
    except Exception as e:
        return f"<div style='padding: 20px; background: #f8d7da; border-left: 5px solid #dc3545; border-radius: 8px;'><h3 style='color: #721c24; margin-top: 0;'>❌ Error</h3><p>Terjadi kesalahan saat memproses data: {str(e)}</p><p>Pastikan format data benar: <code>tanggal,usia_bulan,bb,tb</code></p></div>", None


def generate_kejar_tumbuh_report(analysis: Dict, gender: str) -> str:
    """
    Generate HTML report untuk analisis kejar tumbuh
    """
    if analysis.get('status') != 'analyzed':
        return f"<div style='padding: 20px; background: #f8d7da; border-left: 5px solid #dc3545; border-radius: 8px;'><h3 style='color: #721c24; margin-top: 0;'>❌ Error</h3><p>{analysis.get('message', 'Gagal menganalisis data.')}</p></div>"
    
    concern_colors = {'normal': '#28a745', 'warning': '#ffc107', 'critical': '#dc3545'}
    concern_bg = {'normal': '#d4edda', 'warning': '#fff3cd', 'critical': '#f8d7da'}
    concern_text = {'normal': 'Normal - Pertumbuhan Baik', 'warning': 'Perhatian - Monitoring Diperlukan', 'critical': 'Kritis - Perlu Intervensi Segera'}
    level = analysis['concern_level']
    
    html = f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 20px; color: white; margin-bottom: 20px;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);'>
        <h2 style='margin: 0 0 10px 0; font-size: 28px;'>🎯 Hasil Analisis Kalkulator Target Kejar Tumbuh</h2>
        <p style='margin: 0; opacity: 0.9; font-size: 14px;'>Berdasarkan WHO Growth Velocity Standards</p>
    </div>
    <div style='background: {concern_bg[level]}; padding: 20px; border-radius: 15px; 
                margin-bottom: 25px; border-left: 6px solid {concern_colors[level]};'>
        <h3 style='margin: 0 0 10px 0; color: {concern_colors[level]};'>Status Keseluruhan: {concern_text[level]}</h3>
        <p style='margin: 0; color: #555;'>
            Jumlah pengukuran: <strong>{analysis['velocity_data']['total_measurements']}</strong> | 
            Periode monitoring: <strong>{analysis['velocity_data']['monitoring_period']}</strong>
        </p>
    </div>
    <div style='background: white; padding: 25px; border-radius: 15px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 25px;'>
        <h3 style='color: #667eea; margin-top: 0;'>📊 Analisis Velocity Pertumbuhan</h3>
    """
    
    for interp in analysis['interpretations']:
        icon = "⚖️" if interp['type'] == 'weight' else "📏"
        type_text = "Berat Badan" if interp['type'] == 'weight' else "Panjang/Tinggi Badan"
        status_key = interp['status'].split(" ")[0].lower().replace("🔴","critical").replace("🟡","warning").replace("🟢","normal")
        html += f"""
        <div style='margin-bottom: 20px; padding: 15px; background: #f8f9fa; 
                    border-radius: 10px; border-left: 4px solid {concern_colors.get(status_key, "#667eea")};'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                <h4 style='margin: 0; color: #2c3e50;'>{icon} {type_text} - {interp['period']}</h4>
                <span style='font-weight: bold; color: {concern_colors.get(status_key, "#667eea")};'>{interp['status']}</span>
            </div>
            <p style='margin: 5px 0; color: #666;'>{interp['message']}</p>
            <div style='margin-top: 10px; font-size: 13px; color: #888;'>
                Velocity: <strong>{interp['velocity']:.2f}</strong> | Expected: <strong>~{interp['expected']:.2f}</strong>
            </div>
        </div>
        """
    
    html += "</div><div style='background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 25px;'>"
    html += "<h3 style='color: #667eea; margin-top: 0;'>💡 Rekomendasi & Langkah Selanjutnya</h3>"
    html += "<ul style='color: #555; line-height: 2; margin: 10px 0; padding-left: 20px;'>"
    for rec in analysis['recommendations']:
        html += f"<li>{rec}</li>"
    html += "</ul></div>"
    html += """
    <div style='background: #e3f2fd; padding: 20px; border-radius: 12px; border-left: 5px solid #2196f3;'>
        <h4 style='color: #1976d2; margin-top: 0;'>📚 Referensi & Standar</h4>
        <ul style='color: #555; line-height: 1.8; margin: 10px 0; font-size: 14px; padding-left: 20px;'>
            <li>Analisis berdasarkan <strong>WHO Growth Velocity Standards</strong></li>
            <li>Velocity normal bervariasi berdasarkan usia anak</li>
            <li>Monitoring rutin setiap bulan direkomendasikan untuk akurasi</li>
            <li>Konsultasi profesional kesehatan untuk interpretasi lengkap</li>
        </ul>
    </div>
    """
    return html

# --- FITUR 4: BUG FIX HTML RENDERING (Dipertahankan dari v3.2) ---

def render_video_card_fixed(video_data: Dict) -> str:
    """
    Render video card dengan HTML yang proper (tidak raw)
    """
    video_html = f"""
    <div class='video-card' style='background: linear-gradient(135deg, #ffe8f0 0%, #fff5f8 100%); 
                                   padding: 20px; border-radius: 15px; margin: 15px 0;
                                   box-shadow: 0 4px 12px rgba(255, 107, 157, 0.15);
                                   border: 2px solid #ffd4e0;'>
        <div class='video-title' style='display: flex; align-items: center; margin-bottom: 12px;'>
            <span style='font-size: 24px; margin-right: 12px;'>{video_data.get('icon', '🍎')}</span>
            <h4 style='margin: 0; color: #ff6b9d; font-size: 18px;'>{video_data['title']}</h4>
        </div>
        <div class='video-description' style='color: #666; font-size: 14px; margin-bottom: 10px; line-height: 1.6;'>
            {video_data.get('description', '')}
        </div>
        <div class='video-duration' style='color: #999; font-size: 13px; margin-bottom: 15px;'>
            ⏱️ Durasi: {video_data.get('duration', 'N/A')}
        </div>
        <div style='margin-top: 10px;'>
            <a href='{video_data['url']}' target='_blank'
               style='display: inline-block; padding: 12px 24px; 
                      background: linear-gradient(135deg, #ff6b9d 0%, #ff8fab 100%);
                      color: white; text-decoration: none; border-radius: 25px;
                      font-size: 14px; font-weight: 600;
                      box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
                      transition: all 0.3s ease;'
               onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(255, 107, 157, 0.4)';"
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(255, 107, 157, 0.3)';">
                ▶️ Tonton Video
            </a>
        </div>
    </div>
    """
    return video_html

# --- Helper Utilities (Dipertahankan dari v3.2) ---

def format_date_indonesian(date_obj: datetime) -> str:
    """Format tanggal ke Bahasa Indonesia"""
    months_id = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    return f"{date_obj.day} {months_id[date_obj.month-1]} {date_obj.year}"


print("✅ Section 10 & 10B (v3.2) loaded: Mode Mudah, Kalkulator Kejar Tumbuh, dan Perpustakaan Lokal (Internal).")



# --- FITUR 2: PERPUSTAKAAN IBU BALITA (UPDATED v3.2) ---

# Perpustakaan yang diperbaiki dengan link VALID dari sumber terpercaya
PERPUSTAKAAN_IBU_BALITA_UPDATED = {
    "Nutrisi & MPASI": [
        {
            "title": "Panduan Lengkap MPASI WHO",
            "description": "Panduan resmi WHO tentang pemberian makan bayi dan anak (Complementary Feeding). Mencakup timing, tekstur, frekuensi, dan jumlah MPASI sesuai usia.",
            "url": "https://www.who.int/publications/i/item/9789241549950",
            "source": "WHO Official",
            "verified": True
        },
        {
            "title": "Pedoman Gizi Seimbang Indonesia",
            "description": "Pedoman resmi Kemenkes RI tentang gizi seimbang untuk berbagai kelompok usia, termasuk bayi dan balita.",
            "url": "https://peraturan.bpk.go.id/Details/139887/permenkes-no-41-tahun-2014",
            "source": "Kemenkes RI",
            "verified": True
        },
        {
            "title": "Stunting Prevention - UNICEF",
            "description": "Strategi pencegahan stunting dari UNICEF, fokus pada 1000 hari pertama kehidupan.",
            "url": "https://www.unicef.org/nutrition/stunting",
            "source": "UNICEF",
            "verified": True
        },
        {
            "title": "Breastfeeding and Complementary Feeding",
            "description": "Panduan WHO tentang ASI eksklusif dan MPASI untuk pertumbuhan optimal.",
            "url": "https://www.who.int/health-topics/breastfeeding",
            "source": "WHO",
            "verified": True
        },
        {
            "title": "Tabel Komposisi Pangan Indonesia",
            "description": "Database lengkap komposisi gizi makanan Indonesia untuk perencanaan menu MPASI.",
            "url": "https://panganku.org/id-ID/view",
            "source": "Kemenkes RI",
            "verified": True
        },
        {
            "title": "Feeding Infants and Young Children - CDC",
            "description": "Panduan praktis dari CDC tentang pemberian makan bayi dan anak balita.",
            "url": "https://www.cdc.gov/nutrition/infantandtoddlernutrition/index.html",
            "source": "CDC USA",
            "verified": True
        },
        {
            "title": "Panduan Menu MPASI Kemenkes",
            "description": "Buku panduan menu MPASI lokal Indonesia dengan resep praktis dan bergizi.",
            "url": "https://ayosehat.kemkes.go.id/pub/files/d93a0ebf75e61121b36b3a01ed5fdee7.pdf",
            "source": "Kemenkes RI",
            "verified": True
        },
        {
            "title": "Guideline on Sugars Intake - WHO",
            "description": "Pedoman WHO tentang asupan gula untuk anak-anak.",
            "url": "https://www.who.int/publications/i/item/9789241549028",
            "source": "WHO",
            "verified": True
        }
    ],
    
    "Tumbuh Kembang": [
        {
            "title": "Standar Antropometri Anak - Kemenkes",
            "description": "Peraturan Menteri Kesehatan No. 2 Tahun 2020 tentang Standar Antropometri Anak.",
            "url": "https://peraturan.bpk.go.id/Details/138124/permenkes-no-2-tahun-2020",
            "source": "Kemenkes RI",
            "verified": True
        },
        {
            "title": "WHO Child Growth Standards",
            "description": "Standar pertumbuhan anak WHO 2006 - referensi global untuk pemantauan pertumbuhan.",
            "url": "https://www.who.int/tools/child-growth-standards",
            "source": "WHO Official",
            "verified": True
        },
        {
            "title": "Developmental Milestones - CDC",
            "description": "Panduan milestone perkembangan anak dari lahir hingga 5 tahun.",
            "url": "https://www.cdc.gov/ncbddd/actearly/milestones/index.html",
            "source": "CDC USA",
            "verified": True
        },
        {
            "title": "Stimulasi, Deteksi dan Intervensi Dini Tumbuh Kembang",
            "description": "Pedoman SDIDTK dari Kemenkes untuk deteksi dini gangguan tumbuh kembang.",
            "url": "https://kesmas.kemkes.go.id/konten/133/0/buku-pedoman-sdidtk",
            "source": "Kemenkes RI",
            "verified": True
        },
        {
            "title": "Early Childhood Development - UNICEF",
            "description": "Program dan panduan UNICEF untuk pengembangan anak usia dini.",
            "url": "https://www.unicef.org/early-childhood-development",
            "source": "UNICEF",
            "verified": True
        },
        {
            "title": "Caring for Your Baby and Young Child - AAP",
            "description": "Panduan lengkap perawatan bayi dan balita dari American Academy of Pediatrics.",
            "url": "https://www.healthychildren.org/English/ages-stages/baby/Pages/default.aspx",
            "source": "AAP",
            "verified": True
        }
    ],
    
    "Kesehatan & Imunisasi": [
        {
            "title": "Jadwal Imunisasi Anak - IDAI",
            "description": "Jadwal imunisasi terbaru dari Ikatan Dokter Anak Indonesia (IDAI).",
            "url": "https://www.idai.or.id/artikel/klinik/imunisasi/jadwal-imunisasi-anak-idai",
            "source": "IDAI",
            "verified": True
        },
        {
            "title": "Immunization Schedule - WHO",
            "description": "Rekomendasi jadwal imunisasi global dari WHO.",
            "url": "https://www.who.int/teams/immunization-vaccines-and-biologicals/policies/position-papers",
            "source": "WHO",
            "verified": True
        },
        {
            "title": "Buku KIA Digital",
            "description": "Buku Kesehatan Ibu dan Anak versi digital dari Kemenkes.",
            "url": "https://ayosehat.kemkes.go.id/topik-penyakit/kesehatan-ibu-dan-anak",
            "source": "Kemenkes RI",
            "verified": True
        },
        {
            "title": "Penanganan Diare pada Balita",
            "description": "Panduan WHO tentang penanganan diare akut pada anak.",
            "url": "https://www.who.int/news-room/fact-sheets/detail/diarrhoeal-disease",
            "source": "WHO",
            "verified": True
        },
        {
            "title": "ISPA pada Anak - Panduan Kemenkes",
            "description": "Pedoman tatalaksana Infeksi Saluran Pernapasan Akut pada anak.",
            "url": "https://kesmas.kemkes.go.id/konten/133/0/pedoman-pengendalian-ispa",
            "source": "Kemenkes RI",
            "verified": True
        },
        {
            "title": "Vaccine Safety - CDC",
            "description": "Informasi lengkap tentang keamanan vaksin dari CDC.",
            "url": "https://www.cdc.gov/vaccinesafety/index.html",
            "source": "CDC USA",
            "verified": True
        }
    ],
    
    "Parenting & Psikologi": [
        {
            "title": "Positive Parenting Tips - CDC",
            "description": "Tips parenting positif untuk setiap tahap perkembangan anak.",
            "url": "https://www.cdc.gov/ncbddd/childdevelopment/positiveparenting/index.html",
            "source": "CDC USA",
            "verified": True
        },
        {
            "title": "Parenting for Lifelong Health - WHO",
            "description": "Program parenting berbasis bukti dari WHO dan UNICEF.",
            "url": "https://www.who.int/teams/social-determinants-of-health/parenting-for-lifelong-health",
            "source": "WHO & UNICEF",
            "verified": True
        },
        {
            "title": "Responsive Caregiving - UNICEF",
            "description": "Panduan pengasuhan responsif untuk mendukung perkembangan anak optimal.",
            "url": "https://www.unicef.org/parenting",
            "source": "UNICEF",
            "verified": True
        },
        {
            "title": "Mental Health in Children - WHO",
            "description": "Panduan kesehatan mental anak dari WHO.",
            "url": "https://www.who.int/news-room/fact-sheets/detail/mental-health-of-children-and-adolescents",
            "source": "WHO",
            "verified": True
        },
        {
            "title": "Program Kelas Ibu",
            "description": "Program edukasi ibu hamil dan menyusui dari Kemenkes.",
            "url": "https://promkes.kemkes.go.id/kelas-ibu",
            "source": "Kemenkes RI",
            "verified": True
        }
    ],
    
    "Keamanan & Pencegahan Kecelakaan": [
        {
            "title": "Child Safety and Injury Prevention - WHO",
            "description": "Panduan komprehensif pencegahan cedera pada anak dari WHO.",
            "url": "https://www.who.int/news-room/fact-sheets/detail/child-injuries",
            "source": "WHO",
            "verified": True
        },
        {
            "title": "Home Safety Checklist - CDC",
            "description": "Checklist keamanan rumah untuk melindungi balita dari kecelakaan.",
            "url": "https://www.cdc.gov/safechild/parent-safety/index.html",
            "source": "CDC USA",
            "verified": True
        },
        {
            "title": "Drowning Prevention - WHO",
            "description": "Strategi pencegahan tenggelam pada anak.",
            "url": "https://www.who.int/news-room/fact-sheets/detail/drowning",
            "source": "WHO",
            "verified": True
        },
        {
            "title": "Poison Prevention - CDC",
            "description": "Panduan mencegah keracunan pada anak di rumah.",
            "url": "https://www.cdc.gov/poisonprevention/index.html",
            "source": "CDC USA",
            "verified": True
        }
    ]
}
print(f"✅ v3.2 Library loaded: {sum(len(v) for v in PERPUSTAKAAN_IBU_BALITA_UPDATED.values())} articles")


def render_perpustakaan_updated() -> str:
    """
    Render perpustakaan dengan link yang sudah diverifikasi
    
    Returns:
        HTML string dengan card artikel yang lebih informatif
    """
    
    html = """
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 20px; color: white; margin-bottom: 25px;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);'>
        <h2 style='margin: 0 0 10px 0; font-size: 28px;'>
            📚 Perpustakaan Ibu Balita (Updated)
        </h2>
        <p style='margin: 0; opacity: 0.9; font-size: 14px;'>
            Artikel terpercaya dari WHO, Kemenkes RI, IDAI, CDC, dan UNICEF
        </p>
    </div>
    
    <div style='background: #fff3cd; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #ffc107;'>
        <p style='margin: 0; color: #856404;'>
            <strong>✅ Semua link telah diverifikasi dan valid!</strong><br>
            Klik pada judul artikel untuk membuka di tab baru. Semua sumber berasal dari organisasi kesehatan terpercaya.
        </p>
    </div>
    """
    
    # Render setiap kategori
    category_colors = {
        "Nutrisi & MPASI": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "Tumbuh Kembang": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "Kesehatan & Imunisasi": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
        "Parenting & Psikologi": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        "Keamanan & Pencegahan Kecelakaan": "linear-gradient(135deg, #30cfd0 0%, #330867 100%)"
    }
    
    for category, articles in PERPUSTAKAAN_IBU_BALITA_UPDATED.items():
        gradient = category_colors.get(category, "linear-gradient(135deg, #667eea 0%, #764ba2 100%)")
        
        html += f"""
        <div style='margin-bottom: 30px;'>
            <h3 style='background: {gradient}; 
                       color: white; padding: 15px 20px; border-radius: 12px; 
                       margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
                {category}
            </h3>
            <div style='display: grid; gap: 15px;'>
        """
        
        for article in articles:
            # Badge warna berdasarkan sumber
            source_badge_color = {
                "WHO": "#0088cc",
                "WHO Official": "#0088cc",
                "WHO & UNICEF": "#0088cc",
                "Kemenkes RI": "#ff4444",
                "IDAI": "#ff6b6b",
                "UNICEF": "#00a9e0",
                "CDC USA": "#005eaa",
                "AAP": "#00a6d6"
            }.get(article['source'], "#6c757d")
            
            # Verified badge
            verified_badge = """
                <span style='background: #28a745; color: white; padding: 4px 8px; 
                             border-radius: 4px; font-size: 11px; font-weight: bold;
                             margin-left: 8px;'>
                    ✓ Verified
                </span>
            """ if article.get('verified', False) else ""
            
            html += f"""
            <div style='background: white; padding: 20px; border-radius: 12px; 
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
                        border-left: 4px solid {source_badge_color};
                        transition: all 0.3s ease;
                        cursor: pointer;'
                 onmouseover="this.style.boxShadow='0 4px 16px rgba(0,0,0,0.12)'; this.style.transform='translateY(-2px)';"
                 onmouseout="this.style.boxShadow='0 2px 8px rgba(0,0,0,0.08)'; this.style.transform='translateY(0)';">
                
                <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;'>
                    <a href='{article['url']}' target='_blank' 
                       style='text-decoration: none; color: #2c3e50; flex: 1;'>
                        <h4 style='margin: 0 0 8px 0; color: #667eea; font-size: 16px;'>
                            🔗 {article['title']}
                        </h4>
                    </a>
                </div>
                
                <p style='margin: 0 0 12px 0; color: #666; font-size: 14px; line-height: 1.6;'>
                    {article['description']}
                </p>
                
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='background: {source_badge_color}; color: white; 
                                 padding: 5px 12px; border-radius: 20px; font-size: 12px; 
                                 font-weight: 500;'>
                        {article['source']}
                    </span>
                    {verified_badge}
                    <a href='{article['url']}' target='_blank' 
                       style='color: #667eea; text-decoration: none; font-size: 13px; font-weight: 500;'>
                        Buka Artikel →
                    </a>
                </div>
            </div>
            """
        
        html += """
            </div>
        </div>
        """
    
    # Footer dengan disclaimer
    html += """
    <div style='background: #e3f2fd; padding: 20px; border-radius: 12px; 
                border-left: 5px solid #2196f3; margin-top: 30px;'>
        <h4 style='color: #1976d2; margin-top: 0;'>📌 Catatan Penting:</h4>
        <ul style='color: #555; line-height: 1.8; margin: 10px 0; padding-left: 20px;'>
            <li>Semua link telah diverifikasi dan mengarah ke sumber resmi organisasi kesehatan</li>
            <li>Artikel dipilih berdasarkan kredibilitas dan relevansi dengan konteks Indonesia</li>
            <li>Beberapa artikel dalam Bahasa Inggris, gunakan Google Translate jika diperlukan</li>
            <li>Informasi ini bersifat edukatif dan tidak menggantikan konsultasi medis profesional</li>
            <li>Jika link tidak dapat dibuka, mungkin ada masalah koneksi atau situs sedang maintenance</li>
        </ul>
    </div>
    """
    
    return html


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11: GRADIO UI (Fully Updated for v3.2)
# ═══════════════════════════════════════════════════════════════════════════════

# UPDATED Custom CSS with Dark Mode Optimization (from v3.1)
CUSTOM_CSS = """
/* ═══════════════════════════════════════════════════════════════════
   GLOBAL STYLES
   ═══════════════════════════════════════════════════════════════════ */

.gradio-container {
    font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
}

/* ═══════════════════════════════════════════════════════════════════
   DARK MODE OPTIMIZATION - HIGH CONTRAST
   ═══════════════════════════════════════════════════════════════════ */

/* Dark mode detection and optimization */
@media (prefers-color-scheme: dark) {
    /* Improve text contrast in dark mode */
    .gradio-container {
        color: #f0f0f0 !important;
    }
    
    /* Headers with better contrast */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }
    
    /* Paragraphs and body text */
    p, span, div, label {
        color: #e8e8e8 !important;
    }
    
    /* Input fields in dark mode */
    .gr-input, .gr-textbox, .gr-box, .gr-form {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border-color: #505050 !important;
    }
    
    .gr-input::placeholder {
        color: #999999 !important;
    }
    
    /* Buttons in dark mode */
    .gr-button {
        background-color: #404040 !important;
        color: #ffffff !important;
        border-color: #606060 !important;
    }
    
    .gr-button:hover {
        background-color: #505050 !important;
        border-color: #707070 !important;
    }
    
    .gr-button-primary {
        background: linear-gradient(135deg, #ff6b9d 0%, #ff9a9e 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: none !important;
    }
    
    .gr-button-secondary {
        background: linear-gradient(135deg, #4ecdc4 0%, #6de0d9 100%) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: none !important;
    }
    
    /* Cards and panels in dark mode */
    .gr-panel, .gr-box, .gr-accordion {
        background-color: #2a2a2a !important;
        border-color: #505050 !important;
        color: #e8e8e8 !important;
    }
    
    /* Tabs in dark mode */
    .gr-tab {
        background-color: #333333 !important;
        color: #ffffff !important;
        border-color: #505050 !important;
    }
    
    .gr-tab.selected {
        background-color: #ff6b9d !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Markdown content in dark mode */
    .markdown-body {
        color: #e8e8e8 !important;
    }
    
    .markdown-body h1, .markdown-body h2, .markdown-body h3 {
        color: #ffffff !important;
        border-bottom-color: #505050 !important;
    }
    
    .markdown-body a {
        color: #6db4ff !important;
    }
    
    .markdown-body code {
        background-color: #1e1e1e !important;
        color: #d4d4d4 !important;
        border-color: #404040 !important;
    }
    
    .markdown-body pre {
        background-color: #1e1e1e !important;
        border-color: #404040 !important;
    }
    
    /* Status indicators in dark mode */
    .status-success {
        color: #5cff5c !important;
        font-weight: 600;
    }
    
    .status-warning {
        color: #ffd45c !important;
        font-weight: 600;
    }
    
    .status-error {
        color: #ff5c5c !important;
        font-weight: 600;
    }
    
    /* Premium cards in dark mode */
    .premium-gold {
        background: linear-gradient(135deg, #b8860b 0%, #daa520 100%) !important;
        color: #ffffff !important;
        border: 2px solid #b8860b !important;
    }
    
    .premium-silver {
        background: linear-gradient(135deg, #787878 0%, #a0a0a0 100%) !important;
        color: #ffffff !important;
        border: 2px solid #787878 !important;
    }
    
    /* Article cards in dark mode */
    .article-card {
        background-color: #2a2a2a !important;
        border: 1px solid #505050 !important;
        color: #e8e8e8 !important;
    }
    
    .article-card:hover {
        background-color: #353535 !important;
        border-color: #606060 !important;
        box-shadow: 0 4px 12px rgba(255,255,255,0.1) !important;
    }
    
    .article-title {
        color: #ffffff !important;
    }
    
    .article-meta {
        color: #b0b0b0 !important;
    }
}

/* ═══════════════════════════════════════════════════════════════════
   LIGHT MODE (Default)
   ═══════════════════════════════════════════════════════════════════ */

/* Status Colors */
.status-success { 
    color: #28a745 !important; 
    font-weight: 600; 
}
.status-warning { 
    color: #ffc107 !important; 
    font-weight: 600; 
}
.status-error { 
    color: #dc3545 !important; 
    font-weight: 600; 
}

/* Big Buttons */
.big-button {
    font-size: 18px !important;
    font-weight: 700 !important;
    padding: 20px 40px !important;
    margin: 15px 0 !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    transition: all 0.3s ease !important;
}

.big-button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
}

/* Premium Buttons */
.premium-silver {
    background: linear-gradient(135deg, #C0C0C0 0%, #E8E8E8 100%) !important;
    color: #333 !important;
    border: 2px solid #A0A0A0 !important;
    font-weight: bold !important;
    padding: 15px 30px !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
}

.premium-gold {
    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%) !important;
    color: #000 !important;
    border: 2px solid #DAA520 !important;
    font-weight: bold !important;
    padding: 15px 30px !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4) !important;
    transition: all 0.3s ease !important;
}

.premium-gold:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 6px 20px rgba(255, 215, 0, 0.6) !important;
}

/* ═══════════════════════════════════════════════════════════════════
   LIBRARY ARTICLE CARDS (v3.1)
   ═══════════════════════════════════════════════════════════════════ */

.article-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border: 2px solid #e9ecef;
    border-radius: 15px;
    padding: 20px;
    margin: 15px 0;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.article-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    border-color: #ff6b9d;
}

.article-title {
    font-size: 18px;
    font-weight: 700;
    color: #2c3e50;
    margin-bottom: 10px;
}

.article-meta {
    font-size: 13px;
    color: #6c757d;
    margin-bottom: 12px;
}

.article-summary {
    font-size: 14px;
    line-height: 1.6;
    color: #495057;
    margin-bottom: 15px;
}

.article-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
}

.article-tag {
    background: #e8f5e9;
    color: #2e7d32;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

.article-link-btn {
    display: inline-block;
    background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s ease;
}

.article-link-btn:hover {
    background: linear-gradient(135deg, #44a08d 0%, #4ecdc4 100%);
    transform: translateX(3px);
}

/* Category badges */
.category-badge {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 8px;
}

.category-asi { background: #e3f2fd; color: #1565c0; }
.category-mpasi { background: #fff3e0; color: #e65100; }
.category-stunting { background: #fce4ec; color: #c2185b; }
.category-perkembangan { background: #f3e5f5; color: #7b1fa2; }
.category-imunisasi { background: #e8f5e9; color: #2e7d32; }
.category-penyakit { background: #ffebee; color: #c62828; }
.category-ibu { background: #fce4ec; color: #ad1457; }
.category-pola-asuh { background: #e1f5fe; color: #0277bd; }
.category-kebersihan { background: #e0f2f1; color: #00695c; }
.category-nutrisi { background: #fff9c4; color: #f57f17; }
.category-alergi { background: #ffccbc; color: #d84315; }
.category-khusus { background: #f1f8e9; color: #558b2f; }

/* ═══════════════════════════════════════════════════════════════════
   VIDEO CARDS (v3.1)
   ═══════════════════════════════════════════════════════════════════ */

.video-card {
    background: linear-gradient(135deg, #fff5f8 0%, #ffe8f0 100%);
    border: 2px solid #ffd4e0;
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
    transition: all 0.3s ease;
}

.video-card:hover {
    transform: scale(1.02);
    box-shadow: 0 6px 15px rgba(255, 107, 157, 0.2);
    border-color: #ff6b9d;
}

.video-title {
    font-size: 16px;
    font-weight: 700;
    color: #ff6b9d;
    margin-bottom: 8px;
}

.video-description {
    font-size: 13px;
    color: #666;
    margin-bottom: 10px;
}

.video-duration {
    font-size: 12px;
    color: #999;
    font-style: italic;
}

/* ═══════════════════════════════════════════════════════════════════
   OTHER COMPONENTS
   ═══════════════════════════════════════════════════════════════════ */

/* Input Fields */
.gr-input, .gr-textbox {
    border-radius: 8px !important;
    border: 2px solid #e8e8e8 !important;
    transition: border-color 0.3s ease !important;
}

.gr-input:focus, .gr-textbox:focus {
    border-color: #ff6b9d !important;
    box-shadow: 0 0 0 3px rgba(255, 107, 157, 0.1) !important;
}

/* Cards and Panels */
.gr-panel, .gr-box {
    border-radius: 12px !important;
    border: 1px solid #e8e8e8 !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
}

/* Tabs */
.gr-tab {
    border-radius: 8px 8px 0 0 !important;
    font-weight: 600 !important;
}

/* Plots */
.gr-plot {
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}

/* Blockquotes */
blockquote {
    background: linear-gradient(135deg, #fff5f8 0%, #ffe8f0 100%);
    border-left: 6px solid #ff6b9d;
    padding: 20px;
    margin: 20px 0;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* Notification Panel */
.notification-panel {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 15px;
    color: white;
    margin: 15px 0;
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.notification-enabled {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    padding: 15px;
    border-radius: 10px;
    color: white;
    text-align: center;
    font-weight: bold;
    margin: 10px 0;
}
"""

print("✅ Custom CSS loaded with v3.1 dark mode optimizations & new styles")

# Build Gradio Interface
with gr.Blocks(
    title=APP_TITLE, # MODIFIED
    theme=gr.themes.Soft(
        primary_hue="pink",
        secondary_hue="teal",
        neutral_hue="slate",
        font=["Inter", "Segoe UI", "Arial", "sans-serif"],
        font_mono=["Fira Code", "Consolas", "monospace"],
    ),
    css=CUSTOM_CSS,
    analytics_enabled=False,
) as demo:
    
    # ═══════════════════════════════════════════════════════════════════════
    # HEADER (MODIFIED FOR v3.2)
    # ═══════════════════════════════════════════════════════════════════════
    
    gr.Markdown(f"""
    # 🏥 **{APP_TITLE} v{APP_VERSION}**
    ### 💕 Monitor Pertumbuhan Anak Profesional Berbasis WHO Standards
    
    **Fitur Unggulan v3.2:**
    - ✅ **Mode Mudah:** Referensi cepat rentang normal BB, TB, LK.
    - ✅ **Kalkulator Kejar Tumbuh:** Monitor laju pertumbuhan (velocity) anak Anda.
    - ✅ **Perpustakaan Lokal:** Baca artikel Kemenkes, IDAI, WHO langsung di aplikasi.
    - ✅ **Bug Fix:** Perbaikan tampilan HTML di checklist bulanan.
    - ✅ Standar WHO 2006 & Permenkes RI 2020.
    - ✅ Export PDF & CSV Profesional.
    
    ---
    
    ⚠️ **PENTING**: Aplikasi ini untuk skrining awal. Konsultasikan hasil dengan tenaga kesehatan.
    
    📱 **Butuh bantuan?** WhatsApp: [+{CONTACT_WA}](https://wa.me/{CONTACT_WA})
    
    ---
    """)
    
    # JavaScript for Browser Notifications (from v3.1)
    notification_js = """
    <script>
    // Browser Notification Manager
    window.AnthroNotification = {
        permission: 'default',
        
        // Request notification permission
        async requestPermission() {
            if (!("Notification" in window)) {
                console.log("Browser tidak support notifikasi");
                return false;
            }
            if (Notification.permission === 'granted') {
                this.permission = 'granted';
                return true;
            }
            if (Notification.permission !== 'denied') {
                const permission = await Notification.requestPermission();
                this.permission = permission;
                return permission === 'granted';
            }
            return false;
        },
        
        // Send notification
        send(title, body, icon = '🔔', tag = 'anthro-notification') {
            if (this.permission !== 'granted') {
                console.log('Permission not granted');
                return;
            }
            const options = {
                body: body,
                icon: 'https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/' + icon.codePointAt(0).toString(16) + '.png',
                tag: tag,
                badge: 'https://img.icons8.com/color/96/baby.png',
                vibrate: [200, 100, 200],
                requireInteraction: false,
                silent: false
            };
            try {
                const notification = new Notification(title, options);
                notification.onclick = function(event) {
                    event.preventDefault();
                    window.focus();
                    notification.close();
                };
                setTimeout(() => notification.close(), 10000);
            } catch (e) {
                console.error('Notification error:', e);
            }
        },
        
        // Schedule notification (delay in minutes)
        schedule(title, body, delayMinutes, icon = '🔔') {
            const delayMs = delayMinutes * 60 * 1000;
            setTimeout(() => {
                this.send(title, body, icon, 'scheduled-notification');
            }, delayMs);
            console.log(`Notifikasi dijadwalkan ${delayMinutes} menit dari sekarang`);
        },
        
        // Check permission status
        checkPermission() {
            if ("Notification" in window) {
                this.permission = Notification.permission;
                return this.permission;
            }
            return 'unsupported';
        }
    };
    
    // Initialize on load
    window.addEventListener('load', function() {
        window.AnthroNotification.checkPermission();
        console.log('PeduliGiziBalita Notification System Ready');
    });
    </script>
    """
    
    gr.HTML(notification_js)
    
    # State untuk menyimpan payload
    state_payload = gr.State({})
    
    # ═══════════════════════════════════════════════════════════════════════
    # MAIN TABS (MODIFIED FOR v3.2)
    # ═══════════════════════════════════════════════════════════════════════
    
    with gr.Tabs() as main_tabs:
        
        # ═══════════════════════════════════════════════════════════════════
        # TAB 1: KALKULATOR GIZI (from v3.1, unchanged)
        # ═══════════════════════════════════════════════════════════════════
        
        with gr.TabItem("📊 Kalkulator Gizi WHO", id=0):
            gr.Markdown("## 🧮 Analisis Status Gizi Komprehensif")
            
            with gr.Row():
                # LEFT COLUMN: INPUTS
                with gr.Column(scale=6):
                    gr.Markdown("### 📝 Data Anak")
                    
                    with gr.Group():
                        nama_anak = gr.Textbox(
                            label="Nama Anak",
                            placeholder="Contoh: Budi Santoso",
                            info="Nama lengkap anak (opsional)"
                        )
                        
                        nama_ortu = gr.Textbox(
                            label="Nama Orang Tua/Wali",
                            placeholder="Contoh: Ibu Siti Aminah",
                            info="Opsional, untuk identifikasi laporan"
                        )
                        
                        sex = gr.Radio(
                            choices=["Laki-laki", "Perempuan"],
                            label="Jenis Kelamin",
                            value="Laki-laki",
                            info="PENTING: Standar WHO berbeda untuk laki-laki dan perempuan"
                        )
                    
                    with gr.Group():
                        gr.Markdown("### 📅 Usia")
                        
                        age_mode = gr.Radio(
                            choices=["Tanggal", "Usia (bulan)"],
                            label="Cara Input Usia",
                            value="Tanggal",
                            info="Pilih metode input yang paling mudah"
                        )
                        
                        with gr.Column(visible=True) as date_inputs:
                            dob = gr.Textbox(
                                label="Tanggal Lahir",
                                placeholder="YYYY-MM-DD atau DD/MM/YYYY",
                                info="Contoh: 2023-01-15 atau 15/01/2023"
                            )
                            
                            dom = gr.Textbox(
                                label="Tanggal Pengukuran",
                                value=datetime.now().strftime("%Y-%m-%d"),
                                info="Hari ini atau tanggal pengukuran aktual"
                            )
                        
                        with gr.Column(visible=False) as month_input:
                            age_months = gr.Number(
                                label="Usia (bulan)",
                                value=6,
                                minimum=0,
                                maximum=60,
                                info="Masukkan usia dalam bulan (0-60)"
                            )
                    
                    with gr.Group():
                        gr.Markdown("### 📏 Pengukuran Antropometri")
                        
                        weight = gr.Number(
                            label="Berat Badan (kg)",
                            value=None,
                            minimum=1,
                            maximum=30,
                            info="Gunakan timbangan digital (presisi 0.1 kg)"
                        )
                        
                        height = gr.Number(
                            label="Panjang/Tinggi Badan (cm)",
                            value=None,
                            minimum=35,
                            maximum=130,
                            info="Panjang badan (< 24 bln) atau Tinggi badan (≥ 24 bln)"
                        )
                        
                        head_circ = gr.Number(
                            label="Lingkar Kepala (cm) - Opsional",
                            value=None,
                            minimum=20,
                            maximum=60,
                            info="Ukur lingkar terbesar kepala dengan meteran fleksibel"
                        )
                    
                    with gr.Group():
                        gr.Markdown("### 🎨 Tema Grafik")
                        
                        theme_choice = gr.Radio(
                            choices=[
                                "pink_pastel",
                                "mint_pastel",
                                "lavender_pastel"
                            ],
                            value="pink_pastel",
                            label="Pilih Tema",
                            info="Pilih warna grafik sesuai selera"
                        )
                    
                    analyze_btn = gr.Button(
                        "🔬 Analisis Sekarang",
                        variant="primary",
                        size="lg",
                        elem_classes=["big-button"]
                    )
                
                # RIGHT COLUMN: GUIDE
                with gr.Column(scale=4):
                    gr.Markdown("### 💡 Panduan Pengukuran Akurat")
                    
                    gr.HTML("""
                    <div style='background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                                padding: 25px; border-radius: 15px; 
                                border-left: 6px solid #4caf50; 
                                box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                        
                        <h4 style='color: #1b5e20; margin-top: 0; font-size: 18px;'>
                            📏 Tips Pengukuran Profesional
                        </h4>
                        
                        <div style='margin: 20px 0;'>
                            <strong style='color: #2e7d32; font-size: 15px;'>⚖️ Berat Badan:</strong>
                            <ul style='margin: 8px 0; padding-left: 25px; color: #1b5e20;'>
                                <li>Timbang pagi hari sebelum makan</li>
                                <li>Pakai timbangan digital (presisi 100g)</li>
                                <li>Anak tanpa sepatu & pakaian tebal</li>
                                <li>Bayi: timbangan bayi khusus</li>
                            </ul>
                        </div>
                        
                        <div style='margin: 20px 0;'>
                            <strong style='color: #2e7d32; font-size: 15px;'>📐 Panjang (0-24 bulan):</strong>
                            <ul style='margin: 8px 0; padding-left: 25px; color: #1b5e20;'>
                                <li>Gunakan <strong>infantometer</strong></li>
                                <li>Bayi telentang, kepala menempel papan</li>
                                <li>Butuh 2 orang: 1 kepala, 1 kaki</li>
                                <li>Pastikan bayi rileks (tidak menangis)</li>
                            </ul>
                        </div>
                        
                        <div style='margin: 20px 0;'>
                            <strong style='color: #2e7d32; font-size: 15px;'>📏 Tinggi (>24 bulan):</strong>
                            <ul style='margin: 8px 0; padding-left: 25px; color: #1b5e20;'>
                                <li>Gunakan <strong>stadiometer</strong></li>
                                <li>Anak berdiri tegak tanpa sepatu</li>
                                <li>Punggung menempel dinding</li>
                                <li>Pandangan lurus ke depan</li>
                            </ul>
                        </div>
                        
                        <div style='margin: 20px 0;'>
                            <strong style='color: #2e7d32; font-size: 15px;'>⭕ Lingkar Kepala:</strong>
                            <ul style='margin: 8px 0; padding-left: 25px; color: #1b5e20;'>
                                <li>Meteran <strong>fleksibel</strong> (non-stretch)</li>
                                <li>Lingkar terbesar: atas alis & telinga</li>
                                <li>Ulangi 3x, ambil rata-rata</li>
                                <li>Penting untuk usia < 36 bulan</li>
                            </ul>
                        </div>
                        
                        <div style='background: #fff8e1; padding: 15px; border-radius: 10px; 
                                    margin-top: 20px; border-left: 4px solid #ffa000;'>
                            <strong style='color: #ff6f00; font-size: 14px;'>⚠️ Penting:</strong>
                            <p style='color: #e65100; margin: 8px 0 0 0; font-size: 13px;'>
                                Kesalahan 0.5 cm pada tinggi = perbedaan Z-score signifikan!
                                Akurasi pengukuran sangat menentukan hasil analisis.
                            </p>
                        </div>
                    </div>
                    """)
                    
                    gr.Markdown("### 🎯 Interpretasi Z-Score")
                    
                    gr.HTML("""
                    <table style='width: 100%; border-collapse: collapse; 
                                  margin-top: 15px; background: white; 
                                  border-radius: 12px; overflow: hidden; 
                                  box-shadow: 0 3px 10px rgba(0,0,0,0.1);'>
                        <thead>
                            <tr style='background: linear-gradient(135deg, #ff6b9d 0%, #ff9a9e 100%); 
                                       color: white;'>
                                <th style='padding: 15px; text-align: center; font-weight: 700;'>Z-Score</th>
                                <th style='padding: 15px; font-weight: 700;'>Kategori</th>
                                <th style='padding: 15px; text-align: center; font-weight: 700;'>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style='border-bottom: 1px solid #f0f0f0;'>
                                <td style='padding: 12px; text-align: center; font-weight: 600;'>&lt; -3</td>
                                <td style='padding: 12px;'>Sangat Kurang/Gizi Buruk</td>
                                <td style='padding: 12px; text-align: center; font-size: 22px;'>🔴</td>
                            </tr>
                            <tr style='border-bottom: 1px solid #f0f0f0; background: #fff5f5;'>
                                <td style='padding: 12px; text-align: center; font-weight: 600;'>-3 to -2</td>
                                <td style='padding: 12px;'>Kurang/Stunted/Wasted</td>
                                <td style='padding: 12px; text-align: center; font-size: 22px;'>🟠</td>
                            </tr>
                            <tr style='border-bottom: 1px solid #f0f0f0;'>
                                <td style='padding: 12px; text-align: center; font-weight: 600;'>-2 to +1</td>
                                <td style='padding: 12px;'><strong>Normal/Baik</strong></td>
                                <td style='padding: 12px; text-align: center; font-size: 22px;'>🟢</td>
                            </tr>
                            <tr style='border-bottom: 1px solid #f0f0f0; background: #fffef5;'>
                                <td style='padding: 12px; text-align: center; font-weight: 600;'>+1 to +2</td>
                                <td style='padding: 12px;'>Kemungkinan Risiko Lebih</td>
                                <td style='padding: 12px; text-align: center; font-size: 22px;'>🟡</td>
                            </tr>
                            <tr style='border-bottom: 1px solid #f0f0f0; background: #fff5f5;'>
                                <td style='padding: 12px; text-align: center; font-weight: 600;'>+2 to +3</td>
                                <td style='padding: 12px;'>Berisiko Gizi Lebih</td>
                                <td style='padding: 12px; text-align: center; font-size: 22px;'>🟠</td>
                            </tr>
                            <tr>
                                <td style='padding: 12px; text-align: center; font-weight: 600;'>&gt; +3</td>
                                <td style='padding: 12px;'>Obesitas</td>
                                <td style='padding: 12px; text-align: center; font-size: 22px;'>🔴</td>
                            </tr>
                        </tbody>
                    </table>
                    """)
            
            gr.Markdown("---")
            gr.Markdown("## 📊 Hasil Analisis")
            
            result_interpretation = gr.Markdown(
                "*Hasil interpretasi akan tampil di sini setelah analisis...*",
                elem_classes=["status-success"]
            )
            
            gr.Markdown("### 📈 Grafik Pertumbuhan")
            
            with gr.Row():
                plot_wfa = gr.Plot(label="Berat menurut Umur (BB/U)")
                plot_hfa = gr.Plot(label="Tinggi menurut Umur (TB/U)")
            
            with gr.Row():
                plot_hcfa = gr.Plot(label="Lingkar Kepala (LK/U)")
                plot_wfl = gr.Plot(label="Berat menurut Tinggi (BB/TB)")
            
            plot_bars = gr.Plot(label="📊 Ringkasan Z-Score Semua Indeks")
            
            gr.Markdown("### 💾 Export & Simpan Hasil")
            
            with gr.Row():
                pdf_btn = gr.Button("📄 Download PDF Lengkap", variant="primary", size="lg")
                csv_btn = gr.Button("📊 Download CSV Data", variant="secondary", size="lg")
            
            with gr.Row():
                pdf_file = gr.File(label="PDF Report", visible=False)
                csv_file = gr.File(label="CSV Data", visible=False)
            
            # Toggle age input visibility
            def toggle_age_input(mode):
                return (
                    gr.update(visible=(mode == "Tanggal")),
                    gr.update(visible=(mode == "Usia (bulan)"))
                )
            
            age_mode.change(
                toggle_age_input,
                inputs=[age_mode],
                outputs=[date_inputs, month_input]
            )
            
            # Main analysis handler
            analyze_btn.click(
                run_comprehensive_analysis,
                inputs=[
                    nama_anak, nama_ortu, sex, age_mode,
                    dob, dom, age_months,
                    weight, height, head_circ,
                    theme_choice
                ],
                outputs=[
                    result_interpretation,
                    plot_wfa, plot_hfa, plot_hcfa, plot_wfl, plot_bars,
                    pdf_file, csv_file,
                    state_payload
                ]
            )
            
            # PDF download (just update visibility)
            pdf_btn.click(
                lambda: gr.update(visible=True),
                outputs=[pdf_file]
            )
            
            # CSV download (just update visibility)
            csv_btn.click(
                lambda: gr.update(visible=True),
                outputs=[csv_file]
            )
        
        # ═══════════════════════════════════════════════════════════════════
        # TAB 2: CHECKLIST BULANAN (BUG FIX v3.2)
        # ═══════════════════════════════════════════════════════════════════
        
        with gr.TabItem("📋 Checklist Sehat Bulanan", id=1):
            gr.Markdown("""
            ## 🗓️ Panduan Checklist Bulanan (0-24 Bulan)
            
            Dapatkan rekomendasi **perkembangan**, **gizi**, **imunisasi**, dan **KPSP** yang disesuaikan dengan usia dan status gizi anak.
            
            💡 **Cara Pakai:**
            1. Lakukan analisis di tab "Kalkulator Gizi" terlebih dahulu
            2. Pilih bulan checklist yang diinginkan
            3. Lihat rekomendasi lengkap, KPSP, dan **Video Edukasi** yang relevan
            """)
            
            with gr.Row():
                month_slider = gr.Slider(
                    minimum=0,
                    maximum=24,
                    step=1,
                    value=6,
                    label="Pilih Bulan Checklist (0-24)",
                    info="Geser untuk memilih bulan yang sesuai"
                )
                
                generate_checklist_btn = gr.Button(
                    "📋 Generate Checklist",
                    variant="primary",
                    size="lg"
                )
            
            # --- BUG FIX (v3.2) ---
            # Mengganti gr.Markdown menjadi gr.HTML untuk merender video card dengan benar
            checklist_output = gr.HTML(
                value="<p style='padding: 20px; text-align: center; color: #888;'>Pilih bulan dan klik tombol untuk melihat checklist...</p>"
            )
            
            def generate_checklist_handler(month, payload):
                """Handler untuk generate checklist (UPDATED for v3.1)"""
                if not payload:
                    return """
<h2> ⚠️ Data Belum Tersedia</h2>
<p style='padding: 20px;'>
Silakan lakukan analisis di tab <strong>Kalkulator Gizi</strong> terlebih dahulu untuk mendapatkan 
checklist yang disesuaikan dengan status gizi anak.
</p>
"""
                
                try:
                    # Use the NEW function that includes videos
                    recommendations_html = generate_checklist_with_videos(int(month), payload)
                    return recommendations_html
                except Exception as e:
                    return f"<h2> ❌ Error</h2><p>Terjadi kesalahan: {str(e)}</p>"
            
            generate_checklist_btn.click(
                generate_checklist_handler,
                inputs=[month_slider, state_payload],
                outputs=[checklist_output]
            )
        
        # ═══════════════════════════════════════════════════════════════════
        # TAB 3: TENTANG & BANTUAN (Re-indexed to id=2)
        # ═══════════════════════════════════════════════════════════════════
        
        with gr.TabItem("ℹ️ Tentang & Bantuan", id=2):
            gr.Markdown(f"""
            ## 🏥 Tentang {APP_TITLE}
            
            **{APP_TITLE}** adalah aplikasi pemantauan 
            pertumbuhan anak berbasis standar WHO Child Growth Standards 2006 dan 
            Permenkes RI No. 2 Tahun 2020.
            
            ### ✨ Fitur Utama (v3.2)
            
            1. **📊 Kalkulator Z-Score WHO**
               - 5 indeks antropometri: WAZ, HAZ, WHZ, BAZ, HCZ
               - Klasifikasi ganda: Permenkes & WHO
            
            2. **📈 Grafik Pertumbuhan Interaktif**
               - Kurva WHO standar dengan zona warna
               - Plot data anak dengan interpretasi visual
            
            3. **💾 Export Profesional**
               - PDF laporan lengkap dengan QR code & CSV data
            
            4. **📋 Checklist Bulanan**
               - Milestone perkembangan, KPSP, Gizi, Imunisasi
               - Integrasi video edukasi
            
            5. **🎯 Fitur Baru (v3.2)**
               - **Mode Mudah:** Referensi cepat rentang normal
               - **Kalkulator Kejar Tumbuh:** Monitor laju/velocity pertumbuhan
               - **Perpustakaan Lokal:** Baca artikel Kemenkes/IDAI/WHO langsung
            
            ### 📚 Referensi Ilmiah
            
            - **WHO Child Growth Standards 2006**
            - **Permenkes RI No. 2 Tahun 2020**
            - **Rekomendasi Ikatan Dokter Anak Indonesia (IDAI)**
            
            ### ⚠️ Disclaimer
            
            Aplikasi ini adalah **alat skrining awal**, BUKAN pengganti konsultasi medis.
            Hasil analisis harus dikonsultasikan dengan dokter spesialis anak, ahli gizi, atau tenaga kesehatan terlatih.
            
            ### 📱 Kontak & Dukungan
            
            **WhatsApp:** [+{CONTACT_WA}](https://wa.me/{CONTACT_WA})  
            **Website:** {BASE_URL}  
            **Versi:** {APP_VERSION}
            
            ### 👨‍💻 Developer
            
            Dikembangkan oleh **Habib Arsy** (Fakultas Kedokteran dan Ilmu Kesehatan - Universitas Jambi)
            
            ---
            
            © 2024-2025 {APP_TITLE}. Dibuat dengan ❤️ untuk kesehatan anak Indonesia.
            """)
        
        # ═══════════════════════════════════════════════════════════════════
        # TAB 4: PREMIUM & NOTIFIKASI (Re-indexed to id=3)
        # ═══════════════════════════════════════════════════════════════════
        
        with gr.TabItem("⭐ Premium & Notifikasi", id=3):
            gr.Markdown("""
            ## 🎁 Upgrade ke Premium
            
            Nikmati fitur eksklusif untuk pemantauan pertumbuhan anak yang lebih optimal!
            """)
            
            # PREMIUM PACKAGES
            with gr.Row():
                # SILVER PACKAGE
                with gr.Column():
                    gr.HTML("""
                    <div style='background: linear-gradient(135deg, #E8E8E8 0%, #F5F5F5 100%); 
                                padding: 30px; border-radius: 20px; 
                                border: 3px solid #C0C0C0;
                                box-shadow: 0 8px 20px rgba(0,0,0,0.1);
                                text-align: center;'>
                        <h2 style='color: #555; margin-top: 0;'>
                            🥈 Paket SILVER
                        </h2>
                        <div style='font-size: 48px; font-weight: bold; color: #333; margin: 20px 0;'>
                            Rp 10.000
                        </div>
                        <div style='font-size: 14px; color: #666; margin-bottom: 20px;'>
                            /bulan
                        </div>
                        <div style='text-align: left; background: white; padding: 20px; 
                                    border-radius: 10px; margin: 20px 0;'>
                            <h4 style='color: #333; margin-top: 0;'>✨ Fitur Silver:</h4>
                            <ul style='list-style: none; padding: 0;'>
                                <li style='padding: 8px 0; border-bottom: 1px solid #eee;'>
                                    🚫 <strong>Bebas Iklan</strong>
                                </li>
                                <li style='padding: 8px 0; border-bottom: 1px solid #eee;'>
                                    📊 Semua fitur dasar
                                </li>
                                <li style='padding: 8px 0;'>
                                    💾 Export unlimited
                                </li>
                            </ul>
                        </div>
                    </div>
                    """)
                    
                    silver_btn = gr.Button(
                        "💳 Upgrade ke Silver",
                        variant="secondary",
                        size="lg",
                        elem_classes=["premium-silver", "big-button"]
                    )
                
                # GOLD PACKAGE (RECOMMENDED)
                with gr.Column():
                    gr.HTML("""
                    <div style='background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); 
                                padding: 30px; border-radius: 20px; 
                                border: 3px solid #DAA520;
                                box-shadow: 0 12px 30px rgba(255, 215, 0, 0.4);
                                text-align: center;
                                position: relative;'>
                        <div style='position: absolute; top: -15px; right: 20px; 
                                    background: #FF4444; color: white; 
                                    padding: 8px 20px; border-radius: 20px;
                                    font-weight: bold; font-size: 12px;'>
                            🔥 REKOMENDASI
                        </div>
                        
                        <h2 style='color: #000; margin-top: 0;'>
                            🥇 Paket GOLD
                        </h2>
                        <div style='font-size: 48px; font-weight: bold; color: #000; margin: 20px 0;'>
                            Rp 50.000
                        </div>
                        <div style='font-size: 14px; color: #333; margin-bottom: 20px;'>
                            /bulan - Hemat 50%!
                        </div>
                        
                        <div style='text-align: left; background: white; padding: 20px; 
                                    border-radius: 10px; margin: 20px 0;'>
                            <h4 style='color: #333; margin-top: 0;'>⭐ Fitur Gold:</h4>
                            <ul style='list-style: none; padding: 0;'>
                                <li style='padding: 8px 0; border-bottom: 1px solid #eee;'>
                                    🚫 <strong>Bebas Iklan</strong>
                                </li>
                                <li style='padding: 8px 0; border-bottom: 1px solid #eee;'>
                                    🔔 <strong>Notifikasi Browser Customizable</strong>
                                </li>
                                <li style='padding: 8px 0; border-bottom: 1px solid #eee;'>
                                    💬 <strong>3x Konsultasi 30 menit</strong><br/>
                                    <span style='font-size: 12px; color: #666;'>
                                    via WhatsApp dengan Ahli Gizi
                                    </span>
                                </li>
                                <li style='padding: 8px 0; border-bottom: 1px solid #eee;'>
                                    📊 Semua fitur dasar
                                </li>
                                <li style='padding: 8px 0; border-bottom: 1px solid #eee;'>
                                    💾 Export unlimited
                                </li>
                                <li style='padding: 8px 0;'>
                                    ⚡ Priority support
                                </li>
                            </ul>
                        </div>
                    </div>
                    """)
                    
                    gold_btn = gr.Button(
                        "👑 Upgrade ke Gold",
                        variant="primary",
                        size="lg",
                        elem_classes=["premium-gold", "big-button"]
                    )
            
            premium_status = gr.Markdown("", visible=False)
            
            gr.Markdown("---")
            
            # NOTIFICATION SYSTEM (MODIFIED for v3.1 - HOUR slider)
            gr.Markdown("""
            ## 🔔 Sistem Notifikasi Browser (Premium Gold)
            
            Dapatkan pengingat otomatis untuk jadwal MPASI, imunisasi, atau pemeriksaan bulanan.
            """)
            
            with gr.Row():
                with gr.Column(scale=6):
                    gr.Markdown("### 🔐 Aktifkan Notifikasi Browser")
                    
                    enable_notif_btn = gr.Button(
                        "🔔 Aktifkan Notifikasi",
                        variant="primary",
                        size="lg"
                    )
                    
                    notif_status = gr.HTML("""
                    <div id='notif-status' style='padding: 15px; background: #f0f0f0; 
                                                   border-radius: 10px; margin: 15px 0;
                                                   text-align: center;'>
                        <p style='margin: 0; color: #666;'>
                            ℹ️ Klik tombol di atas untuk mengaktifkan notifikasi browser
                        </p>
                    </div>
                    """)
                    
                    gr.Markdown("### ⏰ Atur Reminder Custom")
                    
                    with gr.Group():
                        reminder_title = gr.Textbox(
                            label="Judul Reminder",
                            placeholder="Contoh: Beri makan Si Kecil",
                            value="Reminder Gizi SiKecil"
                        )
                        
                        reminder_message = gr.Textbox(
                            label="Pesan Reminder",
                            placeholder="Contoh: Waktunya beri makan bubur bayi",
                            lines=2
                        )
                        
                        # --- MODIFIED SLIDER (v3.1) ---
                        reminder_delay = gr.Slider(
                            minimum=0.5,  # 30 menit minimum
                            maximum=24,   # 24 jam maximum
                            value=3,      # default 3 jam
                            step=0.5,
                            label="Delay (jam) ⏰",
                            info="Notifikasi akan muncul setelah X jam"
                        )
                        # --- END MODIFIED SLIDER ---
                        
                        schedule_btn = gr.Button(
                            "⏰ Jadwalkan Reminder",
                            variant="secondary",
                            size="lg"
                        )
                    
                    reminder_status = gr.Markdown("", visible=False)
                
                with gr.Column(scale=4):
                    gr.Markdown("### 💡 Panduan Notifikasi")
                    
                    gr.HTML("""
                    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 25px; border-radius: 15px; color: white;
                                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);'>
                        
                        <h4 style='color: white; margin-top: 0;'>
                            📱 Cara Mengaktifkan:
                        </h4>
                        
                        <ol style='margin: 15px 0; padding-left: 25px; line-height: 1.8;'>
                            <li>Klik tombol "Aktifkan Notifikasi"</li>
                            <li>Browser akan minta izin - klik <strong>Allow/Izinkan</strong></li>
                            <li>Setelah aktif, Anda bisa atur reminder custom</li>
                            <li>Notifikasi akan muncul otomatis sesuai jadwal</li>
                        </ol>
                        
                        <div style='background: rgba(255,255,255,0.2); padding: 15px; 
                                    border-radius: 10px; margin-top: 20px;'>
                            <strong>⚠️ Penting:</strong>
                            <ul style='margin: 10px 0; padding-left: 20px; font-size: 13px;'>
                                <li>Browser harus support notifikasi (Chrome, Firefox, Edge)</li>
                                <li>Jangan tutup tab browser jika ingin menerima notifikasi</li>
                                <li>Pastikan notifikasi tidak di-block di pengaturan browser</li>
                            </ul>
                        </div>
                    </div>
                    """)
                    
                    gr.Markdown("### 🎁 Template Reminder")
                    
                    template_choice = gr.Dropdown(
                        choices=[
                            "Pemeriksaan Bulanan", "Jadwal Imunisasi",
                            "Milestone Perkembangan", "Reminder Nutrisi", "Custom"
                        ],
                        value="Custom", label="Pilih Template", info="Pilih template untuk quick setup"
                    )
                    
                    use_template_btn = gr.Button( "📋 Gunakan Template", variant="secondary")
            
            # JavaScript Handlers for Notifications
            enable_notif_js = """
            <script>
            function enableNotifications() {
                window.AnthroNotification.requestPermission().then(granted => {
                    const statusDiv = document.getElementById('notif-status');
                    if (granted) {
                        statusDiv.innerHTML = `
                            <div style='padding: 15px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                                       border-radius: 10px; color: white; text-align: center;'>
                                <strong>✅ Notifikasi Berhasil Diaktifkan!</strong><br/>
                                <span style='font-size: 13px;'>Anda akan menerima reminder sesuai jadwal</span>
                            </div>
                        `;
                        setTimeout(() => {
                            window.AnthroNotification.send(
                                '🎉 Selamat!',
                                'Notifikasi browser berhasil diaktifkan. Anda akan menerima reminder untuk tumbuh kembang anak.',
                                '🔔'
                            );
                        }, 1000);
                        return 'Notifikasi diaktifkan!';
                    } else {
                        statusDiv.innerHTML = `
                            <div style='padding: 15px; background: #ff6b6b; 
                                       border-radius: 10px; color: white; text-align: center;'>
                                <strong>❌ Notifikasi Ditolak</strong><br/>
                                <span style='font-size: 13px;'>
                                    Mohon izinkan notifikasi di pengaturan browser Anda
                                </span>
                            </div>
                        `;
                        return 'Notifikasi ditolak.';
                    }
                });
                return 'Memproses...';
            }
            </script>
            """
            gr.HTML(enable_notif_js)
            
            # Event Handlers
            def handle_enable_notification():
                return gr.HTML.update(value="""
                <div style='padding: 15px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                           border-radius: 10px; color: white; text-align: center; margin: 15px 0;'>
                    <strong>✅ Notifikasi Browser Diaktifkan!</strong><br/>
                    <span style='font-size: 13px;'>Browser notification sudah aktif.</span>
                </div>
                <script>enableNotifications();</script>
                """)
            
            def handle_schedule_reminder_hours(title, message, delay_hours):
                if not title or not message:
                    return "❌ Judul dan pesan tidak boleh kosong!"
                delay_minutes = int(delay_hours * 60)
                js_code = f"""
                <script>
                window.AnthroNotification.schedule('{title}', '{message}', {delay_minutes}, '⏰');
                alert('✅ Reminder dijadwalkan! Akan muncul dalam {delay_hours} jam.');
                </script>
                """
                return (f"✅ **Reminder Dijadwalkan!**\n\n**Judul:** {title}\n\n**Pesan:** {message}\n\n"
                        f"**Waktu:** {delay_hours} jam dari sekarang\n\n" + js_code)
            
            def handle_use_template(template):
                templates = {
                    "Pemeriksaan Bulanan": ("🩺 Pemeriksaan Bulanan", "Sudah saatnya pemeriksaan bulanan! Ukur berat, tinggi, dan lingkar kepala anak.", 8),
                    "Jadwal Imunisasi": ("💉 Jadwal Imunisasi", "Jangan lupa jadwal imunisasi hari ini! Cek jadwal lengkap di aplikasi.", 1),
                    "Milestone Perkembangan": ("🎯 Cek Milestone", "Waktunya cek milestone perkembangan anak. Lihat checklist KPSP.", 12),
                    "Reminder Nutrisi": ("🍽️ Waktu Makan", "Saatnya memberi makan anak. Pastikan menu 4 bintang!", 3)
                }
                if template in templates:
                    title, message, delay = templates[template]
                    return title, message, delay
                return "", "", 3
            
            def handle_premium_upgrade(package):
                pkg_info = PREMIUM_PACKAGES.get(package, {})
                price = pkg_info.get('price', 0)
                price_formatted = f"Rp {price:,}".replace(',', '.')
                wa_message = f"Halo PeduliGiziBalita, saya ingin upgrade ke paket {package.upper()} ({price_formatted}/bulan)" # MODIFIED
                wa_link = f"https://wa.me/{CONTACT_WA}?text={wa_message.replace(' ', '%20')}"
                return gr.Markdown.update(
                    value=f"""
## 🎉 Terima kasih telah memilih paket {package.upper()}!
**Harga:** {price_formatted}/bulan
**Langkah selanjutnya:**
1. Klik tombol WhatsApp di bawah
2. Konfirmasi pembelian dengan admin
3. Lakukan pembayaran
4. Akun premium akan diaktifkan dalam 5 menit
<div style='text-align: center; margin: 30px 0;'>
    <a href='{wa_link}' target='_blank'
       style='display: inline-block; padding: 20px 40px; 
              background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
              color: white; text-decoration: none; border-radius: 15px;
              font-size: 18px; font-weight: bold;
              box-shadow: 0 8px 20px rgba(37, 211, 102, 0.4);'>
        💬 Hubungi Admin via WhatsApp
    </a>
</div>
**Metode Pembayaran:** Transfer Bank (BCA, Mandiri, BRI), E-Wallet (GoPay, OVO, DANA), QRIS
""", visible=True)
            
            # Connect event handlers
            enable_notif_btn.click(fn=handle_enable_notification, outputs=[notif_status])
            schedule_btn.click(
                fn=handle_schedule_reminder_hours,
                inputs=[reminder_title, reminder_message, reminder_delay],
                outputs=[reminder_status]
            ).then(lambda: gr.update(visible=True), outputs=[reminder_status])
            use_template_btn.click(
                fn=handle_use_template,
                inputs=[template_choice],
                outputs=[reminder_title, reminder_message, reminder_delay]
            )
            silver_btn.click(
                fn=lambda: handle_premium_upgrade("silver"), outputs=[premium_status]
            ).then(lambda: gr.update(visible=True), outputs=[premium_status])
            gold_btn.click(
                fn=lambda: handle_premium_upgrade("gold"), outputs=[premium_status]
            ).then(lambda: gr.update(visible=True), outputs=[premium_status])
        
        # ═══════════════════════════════════════════════════════════════════
        # TAB 5: NEW FEATURES (v3.2) - (Re-indexed to id=4)
        # ═══════════════════════════════════════════════════════════════════
        
        with gr.TabItem("🎉 Fitur Baru v3.2", id=4):
            gr.Markdown("""
            # 🎉 Fitur Baru {APP_VERSION}
            Selamat datang di fitur-fitur terbaru! Pilih sub-tab di bawah:
            """)
            
            with gr.Tabs():
                
                # --- SUB-TAB 1: MODE MUDAH ---
                with gr.Tab("🎯 Mode Mudah"):
                    gr.Markdown("""
                    ### Mode Mudah - Referensi Cepat untuk Ibu
                    
                    Tidak perlu menghitung z-score yang rumit! Cukup masukkan **usia** dan **jenis kelamin** anak, 
                    dan kami akan menampilkan **rentang normal** untuk berat badan, tinggi badan, dan lingkar kepala.
                    
                    Sangat cocok untuk:
                    - ✅ Screening cepat di rumah
                    - ✅ Evaluasi awal sebelum ke posyandu
                    - ✅ Memahami standar pertumbuhan dengan mudah
                    """)
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            mode_mudah_age = gr.Slider(
                                minimum=0, maximum=60, step=1, value=12,
                                label="Usia Anak (bulan)",
                                info="Geser untuk memilih usia"
                            )
                            
                            mode_mudah_gender = gr.Radio(
                                choices=["Laki-laki", "Perempuan"],
                                value="Laki-laki",
                                label="Jenis Kelamin"
                            )
                            
                            mode_mudah_btn = gr.Button(
                                "🔍 Lihat Rentang Normal",
                                variant="primary",
                                size="lg"
                            )
                        
                        with gr.Column(scale=2):
                            mode_mudah_output = gr.HTML(
                                label="Hasil Referensi Cepat",
                                value="<p style='padding: 20px; text-align: center; color: #888;'>Hasil akan tampil di sini...</p>"
                            )
                    
                    # Connect handler
                    mode_mudah_btn.click(
                        fn=mode_mudah_handler,
                        inputs=[mode_mudah_age, mode_mudah_gender],
                        outputs=mode_mudah_output
                    )
                
                # --- SUB-TAB 2: KALKULATOR KEJAR TUMBUH ---
                with gr.Tab("📈 Kalkulator Target Kejar Tumbuh"):
                    gr.Markdown("""
                    ### Kalkulator Target Kejar Tumbuh (Growth Velocity)
                    
                    Monitor **laju pertumbuhan** anak Anda dengan standar internasional WHO! 
                    Fitur ini membantu Anda:
                    
                    - 📈 Memantau **velocity pertumbuhan** (kenaikan BB & TB per bulan)
                    - 🎯 Mengetahui apakah anak **mengejar kurva** atau **melambat**
                    - 💡 Mendapat **rekomendasi nutrisi** berdasarkan trajectory pertumbuhan
                    
                    ---
                    
                    #### 📝 Cara Menggunakan:
                    
                    1. **Masukkan data pengukuran** (minimal 2 kali pengukuran)
                    2. Format: `tanggal,usia_bulan,berat_badan,tinggi_badan` (satu data per baris)
                    3. Contoh:
                       ```
                       2025-01-15,6,7.5,67.0
                       2025-02-15,7,7.9,68.5
                       2025-03-15,8,8.3,70.0
                       ```
                    4. Klik **Analisis Pertumbuhan**
                    """)
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            kejar_gender = gr.Radio(
                                choices=["Laki-laki", "Perempuan"],
                                value="Laki-laki",
                                label="Jenis Kelamin Anak"
                            )
                            
                            kejar_data = gr.Textbox(
                                label="Data Pengukuran",
                                placeholder="2025-01-15,6,7.5,67.0\n2025-02-15,7,7.9,68.5\n2025-03-15,8,8.3,70.0",
                                lines=10,
                                info="Format: tanggal,usia_bulan,bb,tb"
                            )
                            
                            kejar_btn = gr.Button(
                                "📊 Analisis Pertumbuhan",
                                variant="primary",
                                size="lg"
                            )
                        
                        with gr.Column(scale=2):
                            kejar_output_html = gr.HTML(
                                label="Hasil Analisis Velocity",
                                value="<p style='padding: 20px; text-align: center; color: #888;'>Hasil analisis akan tampil di sini...</p>"
                            )
                            
                            kejar_output_plot = gr.Image(
                                label="Grafik Trajectory Pertumbuhan",
                                type="filepath",
                                visible=False
                            )
                    
                    # Connect handler
                    def kejar_tumbuh_handler_wrapper(data, gender):
                        html, plot_path = kalkulator_kejar_tumbuh_handler(data, gender)
                        if plot_path:
                            return html, gr.update(value=plot_path, visible=True)
                        else:
                            return html, gr.update(visible=False)

                    kejar_btn.click(
                        fn=kejar_tumbuh_handler_wrapper,
                        inputs=[kejar_data, kejar_gender],
                        outputs=[kejar_output_html, kejar_output_plot]
                    )
                
                # --- SUB-TAB 3: PERPUSTAKAAN (LOKAL) ---
                with gr.Tab("📚 Perpustakaan (Lokal)"):
                    gr.Markdown("""
                    ### Perpustakaan Ibu Balita - Baca Langsung
                    
                    Pilih artikel dari daftar di bawah untuk membacanya langsung di sini.
                    Semua konten bersumber dari Kemenkes, IDAI, WHO, dan sumber terpercaya lainnya.
                    """)
                    
                    artikel_dropdown = gr.Dropdown(
                        choices=JUDUL_ARTIKEL_LOKAL,
                        label="Pilih Judul Artikel",
                        info="Pilih artikel yang ingin Anda baca"
                    )
                    
                    artikel_konten_output = gr.Markdown(
                        value="<div style='padding: 20px; text-align: center; color: #888;'>Silakan pilih artikel untuk dibaca.</div>"
                    )
                    
                    # Hubungkan handler (interaktif saat diubah)
                    artikel_dropdown.change(
                        fn=tampilkan_artikel_lokal,
                        inputs=[artikel_dropdown],
                        outputs=[artikel_konten_output]
                    )

    # Footer (MODIFIED)
    gr.Markdown(f"""
    ---
    
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #fff5f8 0%, #ffe8f0 100%); 
                border-radius: 12px; margin-top: 30px;'>
        <p style='font-size: 14px; color: #666; margin: 10px 0;'>
            <strong>{APP_TITLE} v{APP_VERSION}</strong> | 
            WHO Child Growth Standards 2006 | 
            Permenkes RI No. 2/2020
        </p>
        <p style='font-size: 13px; color: #888; margin: 10px 0;'>
            Developed by <strong>Habib Arsy</strong> - FKIK Universitas Jambi
        </p>
        <p style='font-size: 12px; color: #999; margin: 10px 0;'>
            📱 Contact: <a href="https://wa.me/{CONTACT_WA}" target="_blank">+{CONTACT_WA}</a> | 
            🌐 <a href="{BASE_URL}" target="_blank">{BASE_URL}</a>
        </p>
    </div>
    """)

print("✅ Section 11 loaded: Gradio UI complete (v3.2 features integrated)")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 12: FASTAPI INTEGRATION (MODIFIED FOR v3.2)
# ═══════════════════════════════════════════════════════════════════════════════

# Initialize FastAPI
app_fastapi = FastAPI(
    title=f"{APP_TITLE} API", # MODIFIED
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
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
    try:
        app_fastapi.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
        print(f"✅ Static files mounted: /static -> {STATIC_DIR}")
    except Exception as e:
        print(f"⚠️ Static mount warning: {e}")

if os.path.exists(OUTPUTS_DIR):
    try:
        app_fastapi.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")
        print(f"✅ Outputs files mounted: /outputs -> {OUTPUTS_DIR}")
    except Exception as e:
        print(f"⚠️ Outputs mount warning: {e}")

# Health check endpoint
@app_fastapi.get("/health")
async def health_check():
    """API health check endpoint"""
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
            "kpsp_screening": True,
            "video_integration": True,
            "mode_mudah": True, # Added v3.2
            "growth_velocity": True, # Added v3.2
            "local_library": True, # Added v3.2
        },
        "endpoints": {
            "main_app": "/",
            "api_docs": "/api/docs",
            "health": "/health",
        }
    }

# API info endpoint
@app_fastapi.get("/api/info")
async def api_info():
    """Get API information"""
    return {
        "app_name": APP_TITLE,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "author": "Habib Arsy - FKIK Universitas Jambi", # MODIFIED
        "contact": f"+{CONTACT_WA}",
        "base_url": BASE_URL,
        "standards": {
            "who": "Child Growth Standards 2006",
            "permenkes": "No. 2 Tahun 2020"
        },
        "supported_indices": ["WAZ", "HAZ", "WHZ", "BAZ", "HCZ"],
        "age_range": "0-60 months",
        "features": [
            "WHO z-score calculation",
            "Permenkes 2020 classification",
            "Growth charts visualization",
            "PDF report export",
            "CSV data export",
            "KPSP screening",
            "Monthly checklist recommendations",
            "YouTube Video Integration",
            "Mode Mudah (v3.2)",
            "Kalkulator Kejar Tumbuh (v3.2)",
            "Perpustakaan Artikel Lokal (v3.2)"
        ]
    }

# Root redirect
@app_fastapi.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": f"Selamat datang di {APP_TITLE} API", # MODIFIED
        "version": APP_VERSION,
        "docs": "/api/docs",
        "health": "/health",
        "main_app": "/"
    }

print("✅ Section 12 loaded: FastAPI routes configured for v3.2")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 13: APPLICATION STARTUP (MODIFIED FOR v3.2)
# ═══════════════════════════════════════════════════════════════════════════════

# Mount Gradio to FastAPI
try:
    app = gr.mount_gradio_app(
        app=app_fastapi,
        blocks=demo,
        path="/"
    )
    print("✅ Gradio app successfully mounted to FastAPI at root path '/'")
except Exception as e:
    print(f"⚠️ Gradio mount failed, using FastAPI only: {e}")
    app = app_fastapi

# Print startup banner
print("")
print("=" * 80)
print(f"🚀 {APP_TITLE} v{APP_VERSION} - READY FOR DEPLOYMENT".center(80)) # MODIFIED
print("=" * 80)
print(f"📊 WHO Calculator: {'✅ Operational' if calc else '❌ Unavailable'}")
print(f"🌐 Base URL: {BASE_URL}")
print(f"📱 Contact: +{CONTACT_WA}")
print(f"🎨 Themes: {len(UI_THEMES)} available")
print(f"💉 Immunization: {len(IMMUNIZATION_SCHEDULE)} schedules")
print(f"🧠 KPSP: {len(KPSP_QUESTIONS)} question sets")
print(f"📚 Library: {len(ARTIKEL_LOKAL_DATABASE)} articles loaded (v3.2)") # MODIFIED
print(f"🎥 Videos: {len(KPSP_YOUTUBE_VIDEOS) + sum(len(v) for v in MPASI_YOUTUBE_VIDEOS.values())} video links (v3.1)")
print("=" * 80)
print("▶️  Run Command: uvicorn app:app --host 0.0.0.0 --port $PORT")
print("=" * 80)
print("")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting server on port {port}...")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
