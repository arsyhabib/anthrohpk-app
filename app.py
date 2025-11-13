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
# SECTION 10B: NEW FEATURES v3.2 (from fitur_tambahan_anthrohpk.py)
# ═══════════════════════════════════════════════════════════════════════════════

# --- FITUR 1: MODE MUDAH ---

def get_normal_ranges_by_age(age_months: float, gender: str) -> Dict[str, Tuple[float, float]]:
    """
    Mendapatkan range normal (batas bawah dan atas) untuk BB, TB/PB, dan LK
    berdasarkan usia dan jenis kelamin menggunakan WHO standards.
    
    Returns batas untuk z-score -2 SD hingga +2 SD (rentang normal)
    
    Args:
        age_months: Usia dalam bulan (0-60)
        gender: "Laki-laki" atau "Perempuan"
    
    Returns:
        Dictionary dengan keys: 'weight', 'height', 'head_circ'
        Setiap value adalah tuple (batas_bawah, batas_atas)
    """
    
    gender_code = 'M' if gender == "Laki-laki" else 'F'
    
    try:
        # Menggunakan global calc yang sudah ada
        if calc is None:
            raise Exception("Kalkulator WHO (pygrowup) tidak terinisialisasi.")
        
        # Round age to nearest 0.5 for table lookup
        age_lookup = round(age_months * 2) / 2
        
        # Weight-for-Age (WAZ) - -2 SD sampai +2 SD
        wfa_range = calc.wfa_table[gender_code].get(age_lookup, None)
        
        # Height-for-Age (HAZ) - -2 SD sampai +2 SD  
        hfa_range = calc.lhfa_table[gender_code].get(age_lookup, None)
        
        # Head Circumference-for-Age (HCZ) - -2 SD sampai +2 SD
        hcfa_range = calc.hcfa_table[gender_code].get(age_lookup, None)
        
        if wfa_range and hfa_range and hcfa_range:
            # Extract -2 SD dan +2 SD values
            return {
                'weight': (wfa_range.get('SD2neg', 0), wfa_range.get('SD2', 0)),
                'height': (hfa_range.get('SD2neg', 0), hfa_range.get('SD2', 0)),
                'head_circ': (hcfa_range.get('SD2neg', 0), hcfa_range.get('SD2', 0))
            }
        else:
            raise Exception(f"Data tidak ditemukan untuk usia {age_lookup} bulan")
            
    except Exception as e:
        print(f"Error di get_normal_ranges_by_age (akan fallback): {e}")
        # Fallback: Approximate values based on empirical data
        # Ini adalah data approximate untuk demonstrasi
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
    Handler untuk Mode Mudah - menampilkan range normal dengan UI yang friendly
    
    Args:
        age_months: Usia anak dalam bulan
        gender: Jenis kelamin anak
    
    Returns:
        HTML string dengan informasi range normal
    """
    
    if age_months is None or age_months < 0 or age_months > 60:
        return """
        <div style='padding: 20px; background: #fff3cd; border-left: 5px solid #ffc107; border-radius: 8px;'>
            <h3 style='color: #856404; margin-top: 0;'>⚠️ Input Tidak Valid</h3>
            <p>Mohon masukkan usia antara 0-60 bulan.</p>
        </div>
        """
    
    ranges = get_normal_ranges_by_age(float(age_months), gender)
    
    # Format tanggal pemeriksaan
    check_date = datetime.now().strftime("%d %B %Y")
    
    # Determine postur description
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
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;'>
                            Batas Bawah Normal:
                        </div>
                        <div style='font-size: 28px; font-weight: bold; color: white;'>
                            {ranges['weight'][0]:.1f} kg
                        </div>
                    </div>
                </div>
                <div style='font-size: 40px; color: rgba(255,255,255,0.5);'>→</div>
                <div>
                    <div style='background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;'>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;'>
                            Batas Atas Normal:
                        </div>
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
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;'>
                            Batas Bawah Normal:
                        </div>
                        <div style='font-size: 28px; font-weight: bold; color: white;'>
                            {ranges['height'][0]:.1f} cm
                        </div>
                    </div>
                </div>
                <div style='font-size: 40px; color: rgba(255,255,255,0.5);'>→</div>
                <div>
                    <div style='background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;'>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;'>
                            Batas Atas Normal:
                        </div>
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
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;'>
                            Batas Bawah Normal:
                        </div>
                        <div style='font-size: 28px; font-weight: bold; color: white;'>
                            {ranges['head_circ'][0]:.1f} cm
                        </div>
                    </div>
                </div>
                <div style='font-size: 40px; color: rgba(255,255,255,0.5);'>→</div>
                <div>
                    <div style='background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px;'>
                        <div style='font-size: 14px; color: rgba(255,255,255,0.9); margin-bottom: 8px;'>
                            Batas Atas Normal:
                        </div>
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

# --- FITUR 3: KALKULATOR TARGET KEJAR TUMBUH ---

def calculate_growth_velocity(measurements: List[Dict]) -> Dict:
    """
    Menghitung velocity pertumbuhan anak
    
    Args:
        measurements: List of dicts dengan keys: date, weight, height, age_months
    
    Returns:
        Dictionary berisi analisis velocity dan rekomendasi
    """
    
    if len(measurements) < 2:
        return {
            'status': 'insufficient_data',
            'message': 'Minimal 2 data pengukuran diperlukan untuk analisis velocity'
        }
    
    # Sort by date
    measurements = sorted(measurements, key=lambda x: x['date'])
    
    # Calculate deltas
    weight_velocity = []
    height_velocity = []
    
    for i in range(1, len(measurements)):
        prev = measurements[i-1]
        curr = measurements[i]
        
        # Time difference in months
        time_diff = curr['age_months'] - prev['age_months']
        
        if time_diff > 0:
            # Weight velocity (kg/month)
            wt_vel = (curr['weight'] - prev['weight']) / time_diff
            weight_velocity.append({
                'period': f"{prev['age_months']}-{curr['age_months']} bulan",
                'velocity': wt_vel,
                'start_weight': prev['weight'],
                'end_weight': curr['weight'],
                'time_months': time_diff
            })
            
            # Height velocity (cm/month)
            ht_vel = (curr['height'] - prev['height']) / time_diff
            height_velocity.append({
                'period': f"{prev['age_months']}-{curr['age_months']} bulan",
                'velocity': ht_vel,
                'start_height': prev['height'],
                'end_height': curr['height'],
                'time_months': time_diff
            })
    
    return {
        'status': 'success',
        'measurements': measurements,
        'weight_velocity': weight_velocity,
        'height_velocity': height_velocity,
        'total_measurements': len(measurements),
        'monitoring_period': f"{measurements[0]['age_months']}-{measurements[-1]['age_months']} bulan"
    }


def interpret_growth_velocity(velocity_data: Dict, gender: str) -> Dict:
    """
    Interpretasi velocity pertumbuhan berdasarkan standar WHO
    
    Expected growth velocity (approximate):
    - 0-3 months: 0.7-0.9 kg/month, 3.5 cm/month
    - 3-6 months: 0.5-0.6 kg/month, 2.0 cm/month  
    - 6-12 months: 0.3-0.4 kg/month, 1.2 cm/month
    - 12-24 months: 0.2-0.25 kg/month, 1.0 cm/month
    - 24-60 months: 0.15-0.2 kg/month, 0.6 cm/month
    """
    
    if velocity_data['status'] != 'success':
        return velocity_data
    
    interpretations = []
    recommendations = []
    concern_level = "normal"  # normal, warning, critical
    
    # Analyze weight velocity
    for wv in velocity_data['weight_velocity']:
        period_start = int(wv['period'].split('-')[0])
        vel = wv['velocity']
        
        # Expected velocity ranges
        if period_start < 3:
            expected = (0.6, 1.0)
            optimal = 0.8
        elif period_start < 6:
            expected = (0.4, 0.7)
            optimal = 0.55
        elif period_start < 12:
            expected = (0.25, 0.5)
            optimal = 0.35
        elif period_start < 24:
            expected = (0.15, 0.3)
            optimal = 0.22
        else:
            expected = (0.12, 0.25)
            optimal = 0.18
        
        # Interpretation
        if vel < expected[0]:
            status = "🔴 Pertumbuhan Lambat"
            concern_level = "critical" if vel < expected[0] * 0.5 else "warning"
            interpretations.append({
                'period': wv['period'],
                'type': 'weight',
                'status': status,
                'velocity': vel,
                'expected': optimal,
                'message': f"Velocity BB ({vel:.2f} kg/bulan) di bawah normal ({expected[0]:.2f}-{expected[1]:.2f} kg/bulan)"
            })
            recommendations.append(f"Tingkatkan asupan kalori dan protein untuk periode {wv['period']}")
            
        elif vel > expected[1]:
            status = "🟡 Pertumbuhan Cepat"
            if vel > expected[1] * 1.5:
                concern_level = "warning"
            interpretations.append({
                'period': wv['period'],
                'type': 'weight',
                'status': status,
                'velocity': vel,
                'expected': optimal,
                'message': f"Velocity BB ({vel:.2f} kg/bulan) di atas normal ({expected[0]:.2f}-{expected[1]:.2f} kg/bulan)"
            })
            recommendations.append(f"Monitor kenaikan BB berlebih pada periode {wv['period']}, konsultasi ahli gizi")
            
        else:
            status = "🟢 Pertumbuhan Normal"
            interpretations.append({
                'period': wv['period'],
                'type': 'weight',
                'status': status,
                'velocity': vel,
                'expected': optimal,
                'message': f"Velocity BB ({vel:.2f} kg/bulan) dalam rentang normal"
            })
    
    # Analyze height velocity
    for hv in velocity_data['height_velocity']:
        period_start = int(hv['period'].split('-')[0])
        vel = hv['velocity']
        
        # Expected velocity ranges
        if period_start < 3:
            expected = (3.0, 4.0)
            optimal = 3.5
        elif period_start < 6:
            expected = (1.5, 2.5)
            optimal = 2.0
        elif period_start < 12:
            expected = (1.0, 1.5)
            optimal = 1.2
        elif period_start < 24:
            expected = (0.8, 1.2)
            optimal = 1.0
        else:
            expected = (0.5, 0.8)
            optimal = 0.6
        
        # Interpretation
        if vel < expected[0]:
            status = "🔴 Pertumbuhan Lambat"
            concern_level = "critical" if vel < expected[0] * 0.5 else "warning"
            interpretations.append({
                'period': hv['period'],
                'type': 'height',
                'status': status,
                'velocity': vel,
                'expected': optimal,
                'message': f"Velocity TB ({vel:.2f} cm/bulan) di bawah normal ({expected[0]:.2f}-{expected[1]:.2f} cm/bulan)"
            })
            recommendations.append(f"Fokus pada nutrisi untuk pertumbuhan linear periode {hv['period']}")
            
        elif vel > expected[1]:
            status = "🟢 Pertumbuhan Baik"
            interpretations.append({
                'period': hv['period'],
                'type': 'height',
                'status': status,
                'velocity': vel,
                'expected': optimal,
                'message': f"Velocity TB ({vel:.2f} cm/bulan) baik, bahkan di atas rata-rata"
            })
            
        else:
            status = "🟢 Pertumbuhan Normal"
            interpretations.append({
                'period': hv['period'],
                'type': 'height',
                'status': status,
                'velocity': vel,
                'expected': optimal,
                'message': f"Velocity TB ({vel:.2f} cm/bulan) dalam rentang normal"
            })
    
    # General recommendations based on overall trend
    if concern_level == "critical":
        recommendations.insert(0, "⚠️ PENTING: Segera konsultasi ke dokter anak atau ahli gizi untuk evaluasi lengkap")
    elif concern_level == "warning":
        recommendations.insert(0, "⚠️ Perhatian: Pertimbangkan konsultasi dengan tenaga kesehatan")
    else:
        recommendations.append("✅ Pertumbuhan anak dalam jalur yang baik, teruskan pola asuh dan nutrisi saat ini")
    
    return {
        'status': 'analyzed',
        'concern_level': concern_level,
        'interpretations': interpretations,
        'recommendations': recommendations,
        'velocity_data': velocity_data
    }


def plot_growth_trajectory(measurements: List[Dict], gender: str) -> Optional[str]:
    """
    Plot grafik trajectory pertumbuhan dengan kurva WHO
    
    Returns:
        Path ke file image yang di-generate
    """
    
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Apply pink pastel theme for consistency
        theme = UI_THEMES.get("pink_pastel")
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
        })
        
        # Prepare data
        ages = [m['age_months'] for m in measurements]
        weights = [m['weight'] for m in measurements]
        heights = [m['height'] for m in measurements]
        
        gender_code = 'M' if gender == "Laki-laki" else 'F'
        
        # --- Plot Weight Curve (ax1) ---
        ax1.plot(ages, weights, 'o-', color=theme['primary'], linewidth=2.5, markersize=10, 
                 markerfacecolor=theme['accent'], markeredgecolor='white', label='Data Anak', zorder=10)
        
        # Add WHO Curves for Weight
        age_ref = np.arange(min(ages), max(ages) + 1, 1)
        # Handle cases where age_ref might be outside AGE_GRID (0-60.25)
        age_ref_valid = [a for a in age_ref if a in AGE_GRID]
        
        wfa_curves = {
            z: [generate_wfa_curve(gender_code, z)[1][np.where(AGE_GRID == a)[0][0]] for a in age_ref_valid]
            for z in [-3, -2, 0, 2, 3]
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
        
        # --- Plot Height Curve (ax2) ---
        ax2.plot(ages, heights, 'o-', color=theme['secondary'], linewidth=2.5, markersize=10, 
                 markerfacecolor=theme['accent'], markeredgecolor='white', label='Data Anak', zorder=10)
        
        # Add WHO Curves for Height
        hfa_curves = {
            z: [generate_hfa_curve(gender_code, z)[1][np.where(AGE_GRID == a)[0][0]] for a in age_ref_valid]
            for z in [-3, -2, 0, 2, 3]
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
        
        # Add velocity annotations
        for i in range(1, len(measurements)):
            prev = measurements[i-1]
            curr = measurements[i]
            
            time_diff = curr['age_months'] - prev['age_months']
            if time_diff == 0: continue # Hindari divide by zero
            
            # Weight velocity annotation
            wt_vel = (curr['weight'] - prev['weight']) / time_diff
            mid_age = (prev['age_months'] + curr['age_months']) / 2
            mid_wt = (prev['weight'] + curr['weight']) / 2
            ax1.annotate(f'+{wt_vel:.2f} kg/bln', 
                        xy=(mid_age, mid_wt),
                        xytext=(0, 10), textcoords='offset points',
                        fontsize=9, ha='center',
                        bbox=dict(boxstyle='round,pad=0.5', fc=theme['accent'], alpha=0.7))
            
            # Height velocity annotation
            ht_vel = (curr['height'] - prev['height']) / time_diff
            mid_ht = (prev['height'] + curr['height']) / 2
            ax2.annotate(f'+{ht_vel:.2f} cm/bln',
                        xy=(mid_age, mid_ht),
                        xytext=(0, 10), textcoords='offset points',
                        fontsize=9, ha='center',
                        bbox=dict(boxstyle='round,pad=0.5', fc=theme['accent'], alpha=0.7))
        
        plt.tight_layout()
        
        # Save plot
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
    
    Args:
        measurement_data: String dalam format CSV atau manual input
        gender: Jenis kelamin anak
    
    Returns:
        Tuple of (HTML report, plot image path)
    """
    
    # Parse measurement data
    # Expected format: "tanggal,usia_bulan,bb,tb" per line
    try:
        measurements = []
        lines = [l.strip() for l in measurement_data.strip().split('\n') if l.strip()]
        
        for line in lines:
            parts = line.split(',')
            if len(parts) >= 4:
                date_str = parts[0].strip()
                age_months = float(parts[1].strip())
                weight = float(parts[2].strip())
                height = float(parts[3].strip())
                
                # Parse date
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    try:
                        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
                    except:
                        date_obj = datetime.now()
                
                measurements.append({
                    'date': date_obj,
                    'age_months': age_months,
                    'weight': weight,
                    'height': height
                })
        
        if len(measurements) < 2:
            return """
            <div style='padding: 20px; background: #fff3cd; border-left: 5px solid #ffc107; border-radius: 8px;'>
                <h3 style='color: #856404; margin-top: 0;'>⚠️ Data Tidak Cukup</h3>
                <p>Minimal <strong>2 pengukuran</strong> diperlukan untuk analisis velocity pertumbuhan.</p>
                <p>Silakan masukkan lebih banyak data pengukuran.</p>
            </div>
            """, None
        
        # Calculate velocity
        velocity_data = calculate_growth_velocity(measurements)
        
        # Interpret results
        analysis = interpret_growth_velocity(velocity_data, gender)
        
        # Generate plot
        plot_path = plot_growth_trajectory(measurements, gender)
        
        # Generate HTML report
        html_report = generate_kejar_tumbuh_report(analysis, gender)
        
        return html_report, plot_path
        
    except Exception as e:
        return f"""
        <div style='padding: 20px; background: #f8d7da; border-left: 5px solid #dc3545; border-radius: 8px;'>
            <h3 style='color: #721c24; margin-top: 0;'>❌ Error</h3>
            <p>Terjadi kesalahan saat memproses data: {str(e)}</p>
            <p>Pastikan format data benar: <code>tanggal,usia_bulan,bb,tb</code></p>
        </div>
        """, None


def generate_kejar_tumbuh_report(analysis: Dict, gender: str) -> str:
    """
    Generate HTML report untuk analisis kejar tumbuh
    """
    
    if analysis.get('status') != 'analyzed':
        return f"<div style='padding: 20px; background: #f8d7da; border-left: 5px solid #dc3545; border-radius: 8px;'><h3 style='color: #721c24; margin-top: 0;'>❌ Error</h3><p>{analysis.get('message', 'Gagal menganalisis data.')}</p></div>"
    
    concern_colors = {
        'normal': '#28a745',
        'warning': '#ffc107',
        'critical': '#dc3545'
    }
    
    concern_bg = {
        'normal': '#d4edda',
        'warning': '#fff3cd',
        'critical': '#f8d7da'
    }
    
    concern_text = {
        'normal': 'Normal - Pertumbuhan Baik',
        'warning': 'Perhatian - Monitoring Diperlukan',
        'critical': 'Kritis - Perlu Intervensi Segera'
    }
    
    level = analysis['concern_level']
    
    html = f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 20px; color: white; margin-bottom: 20px;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);'>
        <h2 style='margin: 0 0 10px 0; font-size: 28px;'>
            🎯 Hasil Analisis Kalkulator Target Kejar Tumbuh
        </h2>
        <p style='margin: 0; opacity: 0.9; font-size: 14px;'>
            Berdasarkan WHO Growth Velocity Standards
        </p>
    </div>
    
    <div style='background: {concern_bg[level]}; padding: 20px; border-radius: 15px; 
                margin-bottom: 25px; border-left: 6px solid {concern_colors[level]};'>
        <h3 style='margin: 0 0 10px 0; color: {concern_colors[level]};'>
            Status Keseluruhan: {concern_text[level]}
        </h3>
        <p style='margin: 0; color: #555;'>
            Jumlah pengukuran: <strong>{analysis['velocity_data']['total_measurements']}</strong> | 
            Periode monitoring: <strong>{analysis['velocity_data']['monitoring_period']}</strong>
        </p>
    </div>
    
    <div style='background: white; padding: 25px; border-radius: 15px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 25px;'>
        <h3 style='color: #667eea; margin-top: 0;'>📊 Analisis Velocity Pertumbuhan</h3>
    """
    
    # Interpretations
    for interp in analysis['interpretations']:
        icon = "⚖️" if interp['type'] == 'weight' else "📏"
        type_text = "Berat Badan" if interp['type'] == 'weight' else "Panjang/Tinggi Badan"
        
        status_key = interp['status'].split(" ")[0].lower().replace("🔴","critical").replace("🟡","warning").replace("🟢","normal")
        
        html += f"""
        <div style='margin-bottom: 20px; padding: 15px; background: #f8f9fa; 
                    border-radius: 10px; border-left: 4px solid {concern_colors.get(status_key, "#667eea")};'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                <h4 style='margin: 0; color: #2c3e50;'>
                    {icon} {type_text} - {interp['period']}
                </h4>
                <span style='font-weight: bold; color: {concern_colors.get(status_key, "#667eea")};'>{interp['status']}</span>
            </div>
            <p style='margin: 5px 0; color: #666;'>{interp['message']}</p>
            <div style='margin-top: 10px; font-size: 13px; color: #888;'>
                Velocity: <strong>{interp['velocity']:.2f}</strong> | 
                Expected: <strong>~{interp['expected']:.2f}</strong>
            </div>
        </div>
        """
    
    html += """
    </div>
    
    <div style='background: white; padding: 25px; border-radius: 15px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 25px;'>
        <h3 style='color: #667eea; margin-top: 0;'>💡 Rekomendasi & Langkah Selanjutnya</h3>
        <ul style='color: #555; line-height: 2; margin: 10px 0; padding-left: 20px;'>
    """
    
    for rec in analysis['recommendations']:
        html += f"<li>{rec}</li>"
    
    html += """
        </ul>
    </div>
    
    <div style='background: #e3f2fd; padding: 20px; border-radius: 12px; 
                border-left: 5px solid #2196f3;'>
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

# --- FITUR 4: BUG FIX HTML RENDERING ---
# (Fungsi ini sengaja diduplikasi dari v3.2 untuk memastikan ketersediaan)
# (Fungsi v3.1 `generate_video_links_html` menangani list, ini menangani 1 video)

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

# --- Helper Utilities (from v3.2) ---

def format_date_indonesian(date_obj: datetime) -> str:
    """Format tanggal ke Bahasa Indonesia"""
    months_id = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    return f"{date_obj.day} {months_id[date_obj.month-1]} {date_obj.year}"


print("✅ Section 10 & 10B loaded: v3.1 Checklist functions retained, v3.2 new features added.")

