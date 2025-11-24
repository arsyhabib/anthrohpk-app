#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#==============================================================================#
#                         PeduliGiziBalita v3.2 - PRODUCTION                   #
#                  Aplikasi Pemantauan Pertumbuhan Anak Profesional            #
#                                                                              #
#  Author:   Habib Arsy                                                       #
#  Version:  3.2.0 (NEW FEATURES UPDATE)                                      #
#  Standards: WHO Child Growth Standards 2006 + Permenkes RI No. 2 Tahun 2020 #
#  License:  Educational & Healthcare Use                                      #
#==============================================================================#

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

# ===============================================================================
# SECTION 1: IMPORTS & ENVIRONMENT SETUP
# ===============================================================================

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
from pydantic import BaseModel
import gspread
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from oauth2client.service_account import ServiceAccountCredentials

# --- KONFIGURASI GOOGLE SHEETS (Tambahkan di Section 2 Global Config) ---
SHEET_NAME = "AnthroHPK_DB" # Pastikan nama file Google Sheet Anda sesuai ini
GOOGLE_CREDS_FILE = "credentials.json"
SHEET_SCOPE = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
               "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

def get_google_sheet_client():
    """Helper untuk koneksi aman ke Google Sheets"""
    try:
        if not os.path.exists(GOOGLE_CREDS_FILE):
            print("⚠️ File credentials.json tidak ditemukan. Fitur Cloud non-aktif.")
            return None
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_FILE, SHEET_SCOPE)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"❌ Error koneksi Google Sheets: {e}")
        return None


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
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Gradio UI
import gradio as gr

# HTTP Requests
import requests

print("✅ All imports successful")

# ===============================================================================
# SECTION 2: GLOBAL CONFIGURATION
# ===============================================================================

# Application Metadata
APP_VERSION = "3.2.3" # MODIFIED (Perpustakaan Fix)
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

# ===============================================================================
# SECTION 2B: YOUTUBE VIDEO LIBRARY & EDUCATIONAL CONTENT (from v3.1)
# ===============================================================================

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

# ===============================================================================
# SECTION 2C: PERPUSTAKAAN IBU BALITA (REPLACED by v3.2)
# ===============================================================================

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

# ===============================================================================
# SECTION 3: WHO CALCULATOR INITIALIZATION
# ===============================================================================

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


# ===============================================================================
# SECTION 4: UTILITY FUNCTIONS (from v3.0)
# ===============================================================================

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


# ===============================================================================
# SECTION 5: WHO Z-SCORE CALCULATIONS (from v3.0)
# ===============================================================================

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

# ===============================================================================
# SECTION 6: GROWTH CURVE GENERATION (from v3.0/v3.1)
# ===============================================================================

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


# ===============================================================================
# SECTION 7: MATPLOTLIB PLOTTING FUNCTIONS (from v3.0/v3.1)
# ===============================================================================

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


def cleanup_matplotlib_figures(figures: Union[Figure, List[Figure]]):
    """
    Properly cleanup matplotlib figures to prevent memory leaks.

    Args:
        figures: Bisa satu Figure, atau list[Figure].
    """
    from matplotlib.figure import Figure as _Fig

    if figures is None:
        return

    # Kalau yang dikirim satu Figure → jadikan list
    if isinstance(figures, _Fig):
        figures = [figures]

    for fig in figures:
        if fig is not None:
            plt.close(fig)



print("✅ Section 7B loaded: WFL plotting, bar chart & figure cleanup")


# ===============================================================================
# SECTION 8: EXPORT FUNCTIONS (PDF & CSV) (from v3.0/v3.1)
# ===============================================================================

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
            writer.writerow(['==========================================================='])
            writer.writerow(['PeduliGiziBalita - LAPORAN ANALISIS PERTUMBUHAN ANAK']) # MODIFIED
            writer.writerow(['Based on WHO Child Growth Standards 2006 & Permenkes RI 2020'])
            writer.writerow(['==========================================================='])
            writer.writerow([])
            
            # Child information
            writer.writerow(['=== INFORMASI ANAK ==='])
            writer.writerow(['Nama Anak', payload.get('name_child', '-')])
            writer.writerow(['Nama Orang Tua/Wali', payload.get('name_parent', '-')])
            writer.writerow(['Jenis Kelamin', payload.get('sex_text', '-')])
            writer.writerow(['Usia (bulan)', f"{payload.get('age_mo', 0):.2f}"])
            writer.writerow(['Usia (hari)', payload.get('age_days', 0)])
            writer.writerow(['Tanggal Lahir', payload.get('dob', '-')])
            writer.writerow(['Tanggal Pengukuran', payload.get('dom', '-')])
            writer.writerow([])
            
            # Anthropometric measurements
            writer.writerow(['=== PENGUKURAN ANTROPOMETRI ==='])
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
            writer.writerow(['=== HASIL ANALISIS Z-SCORE ==='])
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
            writer.writerow(['=== METADATA ==='])
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
        
        # ========= PAGE 1: SUMMARY & DATA =========
        
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
        
        # ========= PAGES 2-6: CHARTS =========
        
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

# ===============================================================================
# SECTION 9: ANALYSIS HANDLER & INTERPRETATION (from v3.0/v3.1)
# ===============================================================================

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

# --- FUNGSI BARU: LOGIKA CLOUD STORAGE ---

def save_analysis_to_cloud(payload):
    """Menyimpan hasil analisis ke Google Sheets (Tab 'logs')"""
    client = get_google_sheet_client()
    if not client: return
    
    try:
        sheet = client.open(SHEET_NAME)
        # Coba akses tab 'logs', jika tidak ada buat baru (opsional, manual lebih aman)
        try:
            worksheet = sheet.worksheet("logs")
        except:
            print("⚠️ Tab 'logs' tidak ditemukan di Google Sheet.")
            return

        # Data privasi terjaga (Tanpa Nama Anak/Ortu)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        z_scores = payload.get('z', {})
        
        row_data = [
            timestamp,
            "Kalkulator Gizi",              # Fitur
            payload.get('sex', '-'),        # Gender Code (M/F)
            payload.get('age_mo', 0),       # Umur Bulan
            payload.get('w', 0),            # Berat
            payload.get('h', 0),            # Tinggi
            payload.get('hc', 0),           # Lingkar Kepala
            format_zscore(z_scores.get('waz')), # WAZ
            format_zscore(z_scores.get('haz')), # HAZ
            format_zscore(z_scores.get('whz'))  # WHZ
        ]
        worksheet.append_row(row_data)
        print("✅ Data tersimpan di Cloud")
    except Exception as e:
        print(f"❌ Gagal simpan ke cloud: {e}")

def get_history_charts():
    """Mengambil data riwayat dan membuat grafik Plotly"""
    client = get_google_sheet_client()
    if not client:
        return None, None, "<p>Gagal koneksi database.</p>"
    
    try:
        sheet = client.open(SHEET_NAME)
        worksheet = sheet.worksheet("logs")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty:
            return None, None, "<p>Belum ada data riwayat.</p>"

        # Filter: Pastikan kolom angka terbaca sebagai numerik
        df['Berat (kg)'] = pd.to_numeric(df['Berat (kg)'], errors='coerce')
        df['Umur (Bulan)'] = pd.to_numeric(df['Umur (Bulan)'], errors='coerce')
        
        # Grafik 1: Sebaran Berat Badan vs Umur
        fig1 = px.scatter(
            df, x='Umur (Bulan)', y='Berat (kg)', color='Jenis Kelamin',
            title='Sebaran Populasi Pengguna (BB/Umur)',
            template='plotly_white',
            labels={'Jenis Kelamin': 'Gender'}
        )
        
        # Grafik 2: Histogram Status Gizi (Perlu parsing kolom hasil jika ada, disini contoh sederhana)
        # Kita pakai distribusi umur saja sebagai contoh data yang pasti ada
        fig2 = px.histogram(
            df, x='Umur (Bulan)', color='Jenis Kelamin',
            title='Distribusi Usia Anak Pengguna Aplikasi',
            template='plotly_white'
        )
        
        # Tabel Data (Tanpa Nama - Privasi Aman)
        # Ambil 50 data terakhir saja agar ringan
        df_display = df.tail(50).iloc[::-1] 
        
        return fig1, fig2, df_display
        
    except Exception as e:
        print(f"Error history: {e}")
        return None, None, f"<p>Error memuat data: {e}</p>"

def submit_feedback_to_cloud(performa, manfaat, profesi, kendala, saran):
    """Menyimpan kuesioner ke Google Sheets (Tab 'feedback')"""
    client = get_google_sheet_client()
    if not client: return "❌ Gagal koneksi ke server database."
    
    try:
        sheet = client.open(SHEET_NAME)
        worksheet = sheet.worksheet("feedback")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_data = [timestamp, performa, manfaat, profesi, kendala, saran]
        
        worksheet.append_row(row_data)
        return "✅ Terima kasih! Masukan Anda telah tersimpan dan sangat berharga bagi kami."
    except Exception as e:
        return f"❌ Terjadi kesalahan saat menyimpan: {e}"
        
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

interpretation = create_interpretation_text(payload)
    
    # === TAMBAHKAN KODE INI (INTEGRASI CLOUD) ===
    # Simpan data ke Google Sheet secara otomatis (background process)
    save_analysis_to_cloud(payload)
        
        return (
            error_msg,
            None, None, None, None, None,
            gr.update(visible=False), gr.update(visible=False),
            {}
        )


print("✅ Section 9 loaded: Analysis handler & interpretation engine")

# ===============================================================================
# SECTION 10: CHECKLIST & KPSP FUNCTIONS (from v3.1)
# ===============================================================================

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
    
    # === ADD YOUTUBE VIDEOS ===
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
    
    # === EXISTING CHECKLIST CONTENT ===
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

# ===============================================================================
# SECTION 10B: NEW FEATURES v3.2 (Termasuk Modifikasi Perpustakaan Lokal v3.2.2)
# ===============================================================================

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
            <h3 style='color: #856404; margin-top: 0;'⚠️ Input Tidak Valid</h3>
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

# ===============================================================================
# SECTION 10B: NEW FEATURES v3.2 (Termasuk Modifikasi Perpustakaan Lokal v3.2.2)
# ===============================================================================

# --- FITUR 1: MODE MUDAH (Dipertahankan dari v3.2) ---
# ... (Semua kode Mode Mudah dan Kejar Tumbuh Anda tetap di sini) ...
# ... (Fungsi get_normal_ranges_by_age, mode_mudah_handler, dll. TIDAK BERUBAH) ...


# --- FITUR 2: PERPUSTAKAAN LOKAL (PENGGANTI v3.2) ---
# Database artikel lokal baru dengan total 40 artikel
# ================================================================
# MULAI REVISI DI SINI
# ================================================================

# ==============================================================================
# DATABASE ARTIKEL ANTHROHPK (REVISED IMAGE URLS)
# File ini berisi konten artikel untuk fitur Perpustakaan Ibu Balita.
# URL Gambar telah diperbarui agar kompatibel dengan Render & Gradio.
# ==============================================================================

ARTIKEL_LOKAL_DATABASE = [
    # ============================================================
    # KATEGORI: NUTRISI & MPASI
    # ============================================================
    {
        "kategori": "Nutrisi & MPASI",
        "title": "Panduan MPASI Menu Lengkap (WHO & Kemenkes)",
        "summary": "Panduan MPASI perdana 6 bulan sesuai standar WHO dan Kemenkes, fokus pada Protein Hewani.",
        "source": "Kemenkes RI | WHO",
        # URL Baru: Bayi makan (High reliability)
        "image_url": "https://kimi-web-img.moonshot.cn/img/media.cnn.com/35257acbcc0204f1b337e3615145018206d00f9c.jpg",
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
        "source": "Kemenkes RI | UNICEF",
        # URL Baru: Pengukuran tinggi badan anak (Contextual)
        "image_url": "https://kimi-web-img.moonshot.cn/img/smartmedia.digital4danone.com/36cb4d9217479a8733b674ba2e5b907f0dfef7a1",
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
        "kategori": "Nutrisi & MPASI",
        "title": "Mengatasi Gerakan Tutup Mulut (GTM) pada Anak",
        "summary": "Strategi menghadapi anak yang GTM atau menjadi *picky eater*.",
        "source": "IDAI",
        # URL Baru: Anak menolak makan/messy eating
        "image_url": "https://kimi-web-img.moonshot.cn/img/images.ctfassets.net/a2ac6a0ac4238134035c89d13125673cf4c0432a.jpg",
        "full_content": """
        # Mengatasi Gerakan Tutup Mulut (GTM) pada Anak
        
        Gerakan Tutup Mulut (GTM) atau *picky eating* (pilih-pilih makanan) adalah fase normal yang sering dialami balita, biasanya dimulai pada usia 1-2 tahun. Ini adalah bagian dari perkembangan otonomi mereka.
        
        ## Penyebab Umum GTM
        
        * **Bosan:** Menu atau suasana makan yang monoton.
        * **Trauma:** Dipaksa makan, dimarahi saat makan.
        * **Kenyang:** Jadwal makan terlalu dekat dengan jadwal susu, atau porsi terlalu besar.
        * **Tidak Nyaman:** Sedang tumbuh gigi, sariawan, atau tidak enak badan.
        * **Neofobia:** Takut terhadap makanan baru (ini adalah fase normal).
        
        ## Strategi Menghadapi GTM (Feeding Rules)
        
        Kunci utamanya adalah **sabar** dan **konsisten** menerapkan *Feeding Rules* yang direkomendasikan IDAI:
        
        1.  **Jadwal Teratur:** Buat jadwal makan utama dan snack yang konsisten. 3x makan utama, 2x snack.
        
        2.  **Batasi Durasi Makan:** Makan tidak boleh lebih dari **30 menit**. Selesai atau tidak selesai, akhiri proses makan.
        
        3.  **Lingkungan Netral:** Ciptakan suasana makan yang menyenangkan. Hindari memaksa, membentak, atau mengancam anak.
        
        4.  **Tidak Ada Distraksi:** **JANGAN** makan sambil nonton TV, bermain *gadget*, atau sambil bermain mainan. Anak harus fokus pada makanannya.
        
        5.  **Biarkan Lapar:** Di antara jam makan, hanya berikan air putih. Jangan berikan camilan, permen, atau susu di luar jadwal. Biarkan anak merasakan lapar alami saat jam makan tiba.
        
        6.  **Porsi Kecil:** Sajikan makanan dalam porsi kecil tapi sering.
        
        7.  **Paparan Berulang:** Anak mungkin perlu mencoba makanan baru 10-15 kali sebelum ia mau menerimanya. Tawarkan terus secara berkala tanpa memaksa.
        
        ## Kapan Harus Khawatir?
        
        GTM biasa umumnya tidak memengaruhi pertumbuhan. Segera konsultasi ke dokter jika:
        
        * Berat badan anak **tidak naik (stagnan)** atau **turun** dalam 1-2 bulan terakhir.
        * Anak menolak *seluruh* kelompok makanan (misal: tidak mau makan semua jenis protein, atau semua sayur).
        * Anak tampak sangat lemas dan pucat.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Pemberian Makanan pada Anak: Kapan, Apa, dan Bagaimana?*
        2.  Ikatan Dokter Anak Indonesia (IDAI). *Sulit Makan pada Batita.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Nutrisi & MPASI",
        "title": "Peran Lemak dalam MPASI",
        "summary": "Mengapa lemak sangat penting untuk bayi dan sering dilupakan dalam MPASI.",
        "source": "WHO | IDAI",
        # URL Baru: Makanan kaya lemak (Alpukat/Salmon)
        "image_url": "https://kimi-web-img.moonshot.cn/img/mylittleeater.com/3202d889029656d599a775332b9c0243c4bebb3c.png",
        "full_content": """
        # Peran Penting Lemak dalam MPASI
        
        Banyak orang tua fokus pada karbohidrat dan protein, namun melupakan lemak. Padahal, lemak adalah komponen krusial untuk bayi di bawah 2 tahun.
        
        ## Mengapa Bayi Butuh Banyak Lemak?
        
        1.  **Perkembangan Otak:** Sekitar 60% otak manusia terdiri dari lemak. Bayi membutuhkan asupan lemak (terutama Omega-3 dan 6) untuk membangun miliaran koneksi saraf di otaknya.
        2.  **Penyerapan Vitamin:** Vitamin A, D, E, dan K adalah vitamin yang larut dalam lemak. Tanpa lemak yang cukup, vitamin-vitamin ini tidak dapat diserap oleh tubuh, meskipun sudah dikonsumsi.
        3.  **Sumber Kalori Padat:** Perut bayi sangat kecil. Lemak menyediakan kalori paling padat (9 kkal/gram) dibandingkan karbohidrat atau protein (4 kkal/gram). Ini membantu bayi mendapatkan cukup energi dalam porsi makan yang kecil.
        
        ## Berapa Kebutuhan Lemak?
        
        WHO merekomendasikan bahwa 30-45% dari total kalori MPASI bayi berasal dari lemak.
        
        * **0-6 Bulan:** Kebutuhan lemak terpenuhi dari ASI.
        * **6-24 Bulan:** Kebutuhan lemak harus dipenuhi dari ASI dan MPASI.
        
        ## Sumber Lemak Sehat untuk MPASI
        
        Tambahkan "Lemak Tambahan" pada setiap menu MPASI anak:
        
        * **Lemak Nabati:**
            * Minyak (minyak zaitun *EVOO*, minyak kelapa, minyak kanola)
            * Alpukat
            * Santan (peras murni)
        
        * **Lemak Hewani:**
            * Kuning telur
            * Mentega (unsalted butter)
            * Keju (pilih yang rendah garam)
            * Ikan berlemak (salmon, kembung, sarden)
            * Daging berlemak
        
        > **Rekomendasi Praktis:** Tambahkan sekitar 1/2 hingga 1 sendok teh lemak tambahan ke setiap porsi makan utama MPASI bayi.
        
        ---
        
        **Sumber (Acuan):**
        1.  World Health Organization (WHO). *Fats and fatty acids in human nutrition.*
        2.  Ikatan Dokter Anak Indonesia (IDAI). *Pentingnya Lemak untuk MPASI.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Nutrisi & MPASI",
        "title": "ASI Eksklusif dan Manajemen Laktasi",
        "summary": "Panduan sukses ASI eksklusif 6 bulan dan cara mengatasi masalah menyusui.",
        "source": "Kemenkes RI | IDAI",
        # URL Baru: Ibu Menyusui (Contextual)
        "image_url": "https://kimi-web-img.moonshot.cn/img/www.measurement-toolkit.org/8b0f5b8e932bdacd7b99b5815459f90e6a594ffa.png",
        "full_content": """
        # Panduan Sukses ASI Eksklusif dan Manajemen Laktasi
        
        ASI adalah standar emas nutrisi bayi. WHO dan Kemenkes RI merekomendasikan ASI eksklusif selama 6 bulan pertama, dilanjutkan hingga 2 tahun.
        
        ## Apa itu ASI Eksklusif?
        
        Bayi hanya menerima ASI, **tanpa tambahan cairan atau makanan lain** (termasuk air putih, madu, atau teh), kecuali obat-obatan atau vitamin atas anjuran dokter.
        
        ## Kunci Sukses Laktasi
        
        1.  **Inisiasi Menyusu Dini (IMD):** Segera setelah lahir (dalam 1 jam pertama), letakkan bayi di dada ibu agar ia bisa mencari puting sendiri.
        2.  **Posisi dan Pelekatan (Perlekatan):** Ini adalah kunci terpenting.
            * **Posisi:** Tubuh bayi menempel lurus ke ibu (perut ketemu perut).
            * **Pelekatan:** Mulut bayi terbuka lebar, **area areola (bagian hitam) sebagian besar masuk ke mulut bayi**, bukan hanya putingnya. Dagu bayi menempel ke payudara.
        3.  **Menyusui Sesuai Permintaan (On Demand):** Susui bayi kapanpun ia menunjukkan tanda lapar (mulut mengecap, mencari-cari puting, memasukkan tangan ke mulut). Jangan menunggu sampai bayi menangis.
        4.  **Prinsip Supply and Demand:** Semakin sering ASI dikeluarkan (dihisap bayi atau dipompa), semakin banyak ASI yang akan diproduksi oleh tubuh.
        
        ## Masalah Umum Laktasi dan Solusinya
        
        * **Puting Lecet:**
            * **Penyebab:** Perlekatan yang salah (bayi hanya mengisap puting).
            * **Solusi:** Perbaiki perlekatan. Oleskan sedikit ASI ke puting setelah menyusui dan biarkan mengering.
        
        * **ASI Terasa Kurang:**
            * **Penyebab:** Frekuensi menyusui kurang, perlekatan salah, stres pada ibu.
            * **Solusi:** Susui lebih sering (tiap 2-3 jam), pastikan perlekatan benar, ibu harus rileks, cukup minum, dan makan bergizi.
        
        * **Payudara Bengkak (Engorgement):**
            * **Penyebab:** Terjadi di hari-hari awal saat produksi ASI melimpah tapi belum lancar keluar.
            * **Solusi:** Kompres hangat sebelum menyusui (agar lancar) dan kompres dingin setelah menyusui (mengurangi bengkak). Susui bayi sesering mungkin.
        
        ---
        
        **Sumber (Acuan):**
        1.  Kementerian Kesehatan RI. *Manajemen Laktasi.*
        2.  Ikatan Dokter Anak Indonesia (IDAI). *Lima Musuh Utama ASI Eksklusif.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Nutrisi & MPASI",
        "title": "Mitos dan Fakta Seputar MPASI",
        "summary": "Meluruskan miskonsepsi umum tentang pemberian makan bayi.",
        "source": "IDAI | AAP",
        # URL Baru: Makanan bayi beragam
        "image_url": "https://kimi-web-img.moonshot.cn/img/images.agoramedia.com/ab0681b83828cfca6c291bb5e79c49de6038d9d2.jpg",
        "full_content": """
        # Mitos dan Fakta Seputar MPASI
        
        Banyak informasi keliru beredar seputar MPASI. Berikut adalah klarifikasi berdasarkan panduan medis.
        
        **MITOS 1: Bayi di atas 6 bulan boleh diberi susu UHT/susu sapi.**
        
        **FAKTA:** **TIDAK.** Susu sapi (termasuk UHT, pasteurisasi, atau susu formula lanjutan) **tidak boleh** diberikan sebagai minuman utama sebelum anak berusia 1 tahun. Susu sapi memiliki kadar protein dan mineral yang terlalu tinggi untuk ginjal bayi, serta rendah zat besi. ASI atau susu formula (tahap 1) tetap menjadi susu utama. Keju dan yogurt boleh diberikan sebagai bagian dari MPASI.
        
        **MITOS 2: MPASI harus dimulai dengan buah manis agar bayi suka makan.**
        
        **FAKTA:** **TIDAK.** Tidak ada aturan harus memulai dengan buah. Justru, mengenalkan rasa manis terlebih dahulu dikhawatirkan membuat bayi menolak rasa lain (gurih atau hambar). Anda boleh memulai dengan bubur sereal (nasi) yang diperkaya zat besi, atau sayuran yang dilumatkan.
        
        **MITOS 3: Menunda makanan alergen (telur, seafood, kacang) bisa mencegah alergi.**
        
        **FAKTA:** **SALAH.** Penelitian terbaru menunjukkan bahwa menunda pengenalan makanan alergen justru dapat *meningkatkan* risiko alergi. IDAI dan AAP merekomendasikan pengenalan makanan alergen (seperti telur, ikan, dan olahan kacang) boleh dimulai sejak usia 6 bulan, setelah makanan lain diperkenalkan. Berikan satu per satu dan amati reaksi selama 3-4 hari.
        
        **MITOS 4: Bayi tidak boleh diberi garam dan gula sama sekali.**
        
        **FAKTA:** **HAMPIR BENAR.** Bayi di bawah 1 tahun **tidak boleh** diberi tambahan gula. Untuk garam (natrium), bayi sudah mendapatkannya dari ASI dan bahan makanan. Penambahan sedikit sekali garam (seujung sendok teh) untuk perasa *diperbolehkan* oleh beberapa ahli, namun Kemenkes merekomendasikan "tanpa gula garam" untuk membiasakan anak pada rasa asli makanan.
        
        **MITOS 5: Makanan instan (fortifikasi) itu berbahaya dan tidak bergizi.**
        
        **FAKTA:** **SALAH.** MPASI instan komersial yang terdaftar di BPOM telah difortifikasi (ditambahkan) zat gizi mikro penting, terutama **Zat Besi** dan **Zinc**, dalam jumlah yang terukur dan sesuai kebutuhan bayi. MPASI instan aman dan sangat membantu memenuhi kebutuhan zat besi yang seringkali sulit dicapai oleh MPASI buatan rumah (homemade) saja. Kombinasi MPASI homemade dan MPASI fortifikasi seringkali direkomendasikan.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Mitos dan Fakta Seputar MPASI.*
        2.  American Academy of Pediatrics (AAP). *Starting Solid Foods.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Nutrisi & MPASI",
        "title": "Bahaya Anemia Defisiensi Besi (ADB) pada Bayi",
        "summary": "Mengenali bahaya kekurangan zat besi dan mengapa MPASI harus kaya zat besi.",
        "source": "IDAI | WHO",
        # URL Baru: Sumber Zat Besi (Daging/Hati)
        "image_url": "https://kimi-web-img.moonshot.cn/img/singing-river.com/8db5f6bf9fde2886825237f575d4b04fedcff1a6.jpg",
        "full_content": """
        # Bahaya Anemia Defisiensi Besi (ADB) pada Bayi
        
        Anemia Defisiensi Besi (ADB) adalah masalah nutrisi paling umum pada bayi dan anak-anak, dengan dampak serius pada perkembangan otak.
        
        ## Mengapa Zat Besi Penting?
        
        Zat besi (Fe) adalah komponen utama hemoglobin dalam sel darah merah, yang berfungsi mengangkut oksigen ke seluruh tubuh, termasuk ke otak. Otak bayi yang sedang berkembang pesat sangat membutuhkan pasokan oksigen yang stabil.
        
        ## Mengapa Bayi Rentan ADB?
        
        * **Cadangan Menipis:** Bayi lahir dengan cadangan zat besi dari ibunya. Cadangan ini akan **habis** saat bayi berusia sekitar 6 bulan (atau lebih cepat untuk bayi prematur/BBLR).
        * **ASI Tidak Cukup (setelah 6 bulan):** ASI adalah makanan terbaik, namun setelah 6 bulan, kandungan zat besi dalam ASI sudah tidak mencukupi kebutuhan bayi yang sedang tumbuh pesat.
        * **MPASI Salah:** Banyak MPASI *homemade* pertama (misal: bubur beras + sayur) memiliki kandungan zat besi yang sangat rendah.
        
        ## Dampak ADB pada Anak
        
        Kekurangan zat besi, bahkan sebelum terjadi anemia, dapat menyebabkan:
        
        * **Gangguan Perkembangan Otak:** Menurunkan kemampuan kognitif (kecerdasan), memori, dan fungsi motorik.
        * **Dampak Permanen:** Kerusakan perkembangan kognitif akibat ADB di 2 tahun pertama kehidupan seringkali bersifat *irreversible* (permanen).
        * **Gejala Lain:** Anak tampak pucat, lemas, kurang aktif, mudah sakit, dan nafsu makan menurun (yang memperburuk kondisi).
        
        ## Pencegahan ADB
        
        1.  **Skrining:** IDAI merekomendasikan skrining (tes darah) ADB untuk semua bayi pada usia 9-12 bulan.
        2.  **Suplementasi:** Bayi ASI eksklusif (terutama prematur) mungkin memerlukan suplemen zat besi tetes (konsultasikan dengan dokter).
        3.  **MPASI Kaya Zat Besi (Wajib!):**
            * Berikan sumber zat besi *heme* (mudah diserap) setiap hari: **Hati ayam, daging merah, ikan.**
            * Berikan sumber zat besi *non-heme* (dibutuhkan vitamin C untuk penyerapannya): Tahu, tempe, bayam.
            * Gunakan sereal atau bubur bayi fortifikasi yang sudah ditambahkan zat besi.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Anemia Defisiensi Besi pada Bayi dan Anak.*
        2.  World Health Organization (WHO). *Iron Deficiency Anaemia.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Nutrisi & MPASI",
        "title": "Mengenal Alergi Makanan pada Bayi",
        "summary": "Membedakan alergi dan intoleransi, serta cara mengenalkan makanan alergen.",
        "source": "IDAI | AAP",
        # URL Baru: Konsep Alergi (Kacang/Telur)
        "image_url": "https://kimi-web-img.moonshot.cn/img/mnmomma.com/1a70c54942c50a703023cbaf59b621da326270ae.jpg",
        "full_content": """
        # Mengenal Alergi Makanan pada Bayi
        
        Memperkenalkan makanan baru selalu mendebarkan, terutama terkait risiko alergi.
        
        ## Alergi vs Intoleransi
        
        Ini adalah dua hal yang berbeda:
        
        * **Alergi Makanan:** Reaksi **sistem imun** tubuh yang menganggap protein makanan sebagai ancaman. Gejalanya bisa cepat (menit/jam) dan melibatkan banyak sistem (kulit, napas, pencernaan). Bisa berbahaya.
        * **Intoleransi Makanan:** Masalah **pencernaan**. Tubuh tidak memiliki enzim untuk mencerna makanan (misal: intoleransi laktosa). Gejala biasanya hanya di pencernaan (kembung, diare, gas) dan tidak mengancam nyawa.
        
        ## Gejala Alergi Makanan
        
        Gejala bisa ringan hingga berat:
        
        * **Kulit (Paling Umum):** Gatal-gatal, biduran (urtikaria), kemerahan, eksim, bengkak di bibir atau kelopak mata.
        * **Pencernaan:** Muntah, diare (kadang berlendir/berdarah), sakit perut.
        * **Pernapasan:** Hidung meler, bersin-bersin, mengi (napas berbunyi), batuk, sesak napas.
        * **Anafilaksis (Berat & Darurat):** Gabungan gejala di atas yang terjadi cepat, menyebabkan sulit bernapas dan penurunan kesadaran. Segera ke UGD.
        
        ## Makanan Alergen Paling Umum
        
        Sekitar 90% alergi disebabkan oleh kelompok makanan ini:
        
        1.  Susu Sapi
        2.  Telur
        3.  Kacang Tanah & Kacang Pohon (Mede, Almond)
        4.  Gandum
        5.  Kedelai
        6.  Ikan
        7.  Kerang-kerangan (Udang, Kepiting)
        
        ## Cara Mengenalkan Makanan Alergen
        
        Panduan lama (menunda) sudah **ditinggalkan**. Panduan baru justru menganjurkan pengenalan dini.
        
        * **Kapan:** Boleh dimulai sejak usia 6 bulan, setelah bayi terbiasa dengan MPASI pertamanya.
        * **Aturan 4 Hari (Rule of 4):**
            1.  Kenalkan **satu** makanan alergen baru (misal: telur rebus matang sempurna, lumatkan).
            2.  Berikan dalam jumlah sedikit di hari pertama.
            3.  Tunggu dan amati reaksi selama 3-4 hari.
            4.  Jika tidak ada reaksi, makanan tersebut aman dan boleh dilanjutkan.
            5.  Baru kenalkan makanan alergen berikutnya.
        * **PENTING:** Jika ada riwayat alergi berat di keluarga, konsultasikan dulu dengan dokter anak.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Mengenal Alergi Makanan pada Anak.*
        2.  American Academy of Pediatrics (AAP). *Preventing Food Allergies in Babies and Toddlers.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Nutrisi & MPASI",
        "title": "Keamanan Pangan MPASI (Food Safety)",
        "summary": "Cara menyimpan dan mengolah MPASI agar terhindar dari bakteri berbahaya.",
        "source": "WHO (Five Keys to Safer Food)",
        # URL Baru: Mencuci tangan/persiapan makanan
        "image_url": "https://kimi-web-img.moonshot.cn/img/www.olivaclinic.com/701ae72186a50beede96d7ec25e95516b1caf6e9.jpg",
        "full_content": """
        # 5 Kunci Keamanan Pangan (Food Safety) untuk MPASI
        
        Sistem imun bayi belum sempurna, sehingga mereka sangat rentan terhadap keracunan makanan. Menyiapkan MPASI yang bergizi saja tidak cukup, harus **aman** dan **higienis**.
        
        WHO merilis 5 kunci keamanan pangan yang wajib diterapkan saat menyiapkan MPASI:
        
        ## 1. Jaga Kebersihan (Keep Clean)
        
        * **Cuci Tangan:** Selalu cuci tangan pakai sabun sebelum menyiapkan makanan dan sebelum menyuapi bayi.
        * **Cuci Peralatan:** Cuci bersih semua peralatan makan bayi (mangkuk, sendok, talenan, blender) dengan sabun dan air mengalir. Sterilisasi (rebus/steam) jika perlu, terutama untuk bayi di bawah 6 bulan.
        * **Area Dapur:** Jaga kebersihan meja dapur dan area penyimpanan.
        
        ## 2. Pisahkan Mentah dan Matang (Separate)
        
        * **Talenan & Pisau:** Gunakan talenan dan pisau yang **berbeda** untuk bahan mentah (daging, ayam, ikan) dan makanan matang/siap makan (buah, sayur rebus).
        * **Penyimpanan:** Simpan daging mentah di wadah tertutup di bagian bawah kulkas agar cairannya tidak menetes ke makanan lain.
        
        ## 3. Masak Hingga Matang Sempurna (Cook Thoroughly)
        
        * Bakteri berbahaya mati pada suhu panas.
        * **Daging & Unggas:** Pastikan dimasak hingga matang sempurna (tidak ada bagian yang masih merah/pink).
        * **Telur:** Masak hingga kuning dan putihnya **padat** (matang sempurna). Bayi tidak boleh diberi telur setengah matang.
        * **MPASI Beku:** Panaskan kembali MPASI hingga benar-benar panas (mendidih/beruap), lalu dinginkan sebelum diberikan.
        
        ## 4. Simpan Makanan pada Suhu Aman (Keep at Safe Temperatures)
        
        Bakteri berkembang biak sangat cepat di "Zona Bahaya" (5°C - 60°C).
        
        * **Aturan 2 Jam:** Makanan matang **tidak boleh** berada di suhu ruang lebih dari 2 jam.
        * **Kulkas (Chiller):** Simpan MPASI yang akan digunakan dalam 1-2 hari di kulkas (suhu < 5°C).
        * **Freezer:** Untuk penyimpanan lama (hingga 3 bulan), bekukan MPASI di freezer (suhu < -18°C). Beri label tanggal.
        * **Mencairkan (Thawing):** Pindahkan MPASI beku ke kulkas (chiller) semalaman. **Jangan** mencairkan di suhu ruang.
        
        ## 5. Gunakan Air dan Bahan Baku yang Aman (Use Safe Water)
        
        * **Air:** Gunakan air matang atau air kemasan terpercaya untuk memasak dan mencuci buah/sayur yang akan dimakan langsung.
        * **Bahan Baku:** Cuci bersih sayur dan buah, terutama jika dimakan mentah. Pilih bahan makanan yang segar.
        
        ---
        
        **Sumber (Acuan):**
        1.  World Health Organization (WHO). *Five keys to safer food.*
        2.  Kementerian Kesehatan RI. *Pedoman Pemberian Makanan Pendamping ASI.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Nutrisi & MPASI",
        "title": "Bahaya Pemberian Madu pada Bayi di Bawah 1 Tahun",
        "summary": "Peringatan serius mengapa madu bisa berakibat fatal bagi bayi.",
        "source": "IDAI | CDC",
        # URL Baru: Toples Madu (Simbolis)
        "image_url": "https://kimi-web-img.moonshot.cn/img/images.ctfassets.net/c0dfc032e26306d6a2a215c2dacce092a63d987b.png",
        "full_content": """
        # Bahaya Pemberian Madu pada Bayi di Bawah 1 Tahun
        
        Meskipun madu dikenal sebagai pemanis alami yang sehat untuk orang dewasa, madu bisa menjadi **racun mematikan** bagi bayi di bawah usia 12 bulan.
        
        ## Apa Bahayanya?
        
        Madu (baik mentah maupun olahan) dapat mengandung spora bakteri bernama ***Clostridium botulinum***.
        
        Pada orang dewasa dan anak di atas 1 tahun, sistem pencernaan sudah cukup matang untuk membunuh spora ini.
        
        Namun, pada bayi di bawah 1 tahun, sistem pencernaannya belum sempurna. Spora *Clostridium botulinum* dapat tumbuh dan berkembang biak di dalam usus bayi, lalu melepaskan racun (toksin) yang sangat berbahaya.
        
        ## Botulisme Bayi (Infant Botulism)
        
        Kondisi keracunan ini disebut **Botulisme Bayi**. Racun ini menyerang sistem saraf dan dapat menyebabkan:
        
        * **Kelemahan Otot:** Bayi tampak "lemas" (floppy) seperti boneka kain.
        * **Tangisan Lemah:** Tangisan tidak sekuat biasanya.
        * **Sulit Menelan:** Kesulitan mengisap ASI atau susu.
        * **Sembelit (Konstipasi):** Seringkali menjadi gejala awal.
        * **Ekspresi Wajah Datar:** Wajah tidak berekspresi.
        * **Gagal Napas:** Pada kasus yang parah, racun ini dapat melumpuhkan otot pernapasan dan menyebabkan kematian.
        
        ## Poin Penting
        
        * **KAPAN:** Larangan ini berlaku untuk bayi usia **0 hingga 12 bulan**. Setelah 1 tahun, sistem pencernaan anak sudah aman untuk mengonsumsi madu.
        * **JENIS MADU:** Berlaku untuk **SEMUA JENIS** madu, termasuk madu mentah, madu olahan, madu pasteurisasi, dan makanan yang mengandung madu (misal: sereal). Proses pemanasan biasa tidak cukup untuk membunuh spora.
        * **TINDAKAN:** Jangan pernah memberikan madu dalam bentuk apa pun kepada bayi di bawah 1 tahun.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Waspada, Madu Berbahaya untuk Bayi Anda.*
        2.  Centers for Disease Control and Prevention (CDC). *Botulism Prevention.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    
    # ============================================================
    # KATEGORI: TUMBUH KEMBANG
    # ============================================================
    {
        "kategori": "Tumbuh Kembang",
        "title": "Milestone (Tonggak) Perkembangan Anak 0-12 Bulan",
        "summary": "Panduan memantau tonggak perkembangan penting anak di tahun pertama kehidupannya.",
        "source": "CDC | IDAI (KPSP)",
        # URL Baru: Bayi merangkak/bermain
        "image_url": "https://kimi-web-img.moonshot.cn/img/vinitfit.com/5cdc1172cccaef60b780ee06b4c22c223f9fe8c1.jpg",
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
        "source": "Kemenkes RI | AAP",
        # URL Baru: Bermain Balok (Stimulasi)
        "image_url": "https://kimi-web-img.moonshot.cn/img/www.proeves.com/14a2145d2a127207e1682be429ea6b207ac1d5a6.jpg",
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
        "kategori": "Tumbuh Kembang",
        "title": "Milestone (Tonggak) Perkembangan Anak 1-2 Tahun",
        "summary": "Memantau perkembangan anak usia 12-24 bulan, dari berjalan hingga berbicara.",
        "source": "CDC | IDAI (KPSP)",
        # URL Baru: Anak berjalan (Toddler walking)
        "image_url": "https://kimi-web-img.moonshot.cn/img/www.kidsclubchildcare.com.au/fb498680696c882d4b24aff295ddf3669469bacc.png",
        "full_content": """
        # Milestone (Tonggak) Perkembangan Anak 1-2 Tahun (12-24 Bulan)
        
        Memasuki usia satu tahun, anak Anda akan menunjukkan kemajuan pesat, terutama dalam kemampuan berjalan dan berbicara.
        
        ## Usia 12 - 18 Bulan
        
        * **Motorik Kasar:**
            * **Berjalan mandiri.** Ini adalah pencapaian terbesar di rentang usia ini.
            * Mulai belajar naik tangga sambil merangkak atau dibantu.
            * Menarik mainan sambil berjalan.
        * **Motorik Halus:**
            * Mencoret-coret menggunakan krayon atau pensil.
            * Mampu menumpuk 2-3 balok.
            * Mulai bisa makan menggunakan sendok (meski masih berantakan).
        * **Bahasa:**
            * Mengucapkan 3-10+ kata yang bermakna.
            * Menunjuk bagian tubuh (hidung, mata, mulut) jika diminta.
            * Mengikuti perintah sederhana (misal: "Ambil bola").
        * **Sosial:**
            * Meniru pekerjaan rumah (misal: pura-pura menyapu, menelpon).
            * Mulai menunjukkan tanda-tanda kemandirian.
        
        ## Usia 18 - 24 Bulan
        
        * **Motorik Kasar:**
            * Berlari dengan stabil.
            * Naik turun tangga (mungkin masih dengan 2 kaki per langkah).
            * Menendang bola ke depan.
        * **Motorik Halus:**
            * Menumpuk 4-6 balok.
            * Membalik halaman buku satu per satu.
            * Menggambar garis lurus (vertikal/horizontal).
        * **Bahasa:**
            * Kosakata "meledak" (bisa mencapai 50+ kata).
            * Mulai **menggabungkan 2 kata** (misal: "mau susu", "mama pergi").
            * Menyebut nama benda-benda yang familiar.
        * **Sosial:**
            * Mulai menunjukkan emosi yang lebih kompleks (marah, frustrasi, *tantrum*).
            * Bermain paralel (bermain di samping anak lain, tapi belum bermain bersama).
            * Mulai tertarik untuk *toilet training*.
        
        ## 🚩 Red Flags (Waspada Keterlambatan)
        
        Segera konsultasi ke dokter jika:
        
        * **Usia 18 Bulan:**
            * **Belum bisa berjalan mandiri.**
            * Tidak bisa menunjuk benda yang diinginkan.
            * Tidak mengucapkan minimal 6 kata bermakna.
        * **Usia 24 Bulan:**
            * **Tidak bisa merangkai 2 kata** (misal: "minum susu").
            * Tidak bisa mengikuti perintah 2 langkah (misal: "Ambil bola dan berikan ke Papa").
            * Tidak meniru aksi atau kata-kata orang lain.
        
        ---
        
        **Sumber (Acuan):**
        1.  Centers for Disease Control and Prevention (CDC). *Milestone Moments Booklet.*
        2.  Ikatan Dokter Anak Indonesia (IDAI). *Skrining Tumbuh Kembang (KPSP) usia 15, 18, 21, 24 bulan.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Tumbuh Kembang",
        "title": "Red Flags Keterlambatan Bicara (Speech Delay)",
        "summary": "Mengenali tanda bahaya keterlambatan bicara dan kapan harus intervensi.",
        "source": "IDAI | AAP",
        # URL Baru: Orang tua bicara pada bayi
        "image_url": "https://kimi-web-img.moonshot.cn/img/m.media-amazon.com/e4a24cf20a913e70afbeb7037916c1c62334064b.jpg",
        "full_content": """
        # Red Flags Keterlambatan Bicara (Speech Delay)
        
        Kemampuan bicara adalah salah satu indikator penting perkembangan kognitif anak. Penting untuk mengenali tanda bahaya (red flags) agar intervensi dapat dilakukan sedini mungkin.
        
        ## Tanda Bahaya (Red Flags) Keterlambatan Bicara Sesuai Usia
        
        Segera konsultasikan ke Dokter Spesialis Anak jika anak Anda menunjukkan tanda-tanda berikut:
        
        **Usia 6-9 Bulan:**
        * Tidak menoleh ke arah sumber suara.
        * Tidak ada *babbling* (mengoceh "ba-ba-ba", "da-da-da").
        
        **Usia 12 Bulan (1 Tahun):**
        * Tidak merespon saat namanya dipanggil.
        * Tidak bisa menunjuk (pointing) benda yang diinginkan.
        * Tidak mengucapkan 1-2 kata bermakna (seperti "mama" atau "papa" secara spesifik).
        * Tidak ada kontak mata.
        
        **Usia 18 Bulan:**
        * Tidak bisa mengucapkan minimal 6-10 kata bermakna.
        * Tidak bisa mengikuti perintah sederhana (misal: "Ambil sepatu").
        * Tidak bisa menunjuk bagian tubuh.
        
        **Usia 24 Bulan (2 Tahun):**
        * **Belum bisa merangkai 2 kata** (misal: "mau minum", "bola besar"). Ini adalah *red flag* paling umum.
        * Kosakata kurang dari 50 kata.
        * Bicara tidak jelas sehingga tidak dimengerti oleh anggota keluarga.
        
        ## Penyebab Umum Keterlambatan Bicara
        
        1.  **Gangguan Pendengaran:** Paling sering, akibat infeksi telinga tengah berulang (otitis media). Anak tidak bisa meniru suara yang tidak ia dengar dengan jelas.
        2.  **Kurang Stimulasi:** Anak terlalu banyak dibiarkan pasif (misal: nonton TV/gadget) dan kurang diajak bicara 2 arah.
        3.  **Gangguan Spektrum Autisme (GSA):** Seringkali disertai kesulitan interaksi sosial dan kontak mata.
        4.  **Gangguan Oral-Motor:** Ada masalah pada otot lidah atau mulut.
        
        ## Apa yang Harus Dilakukan?
        
        * **Jangan Menunggu:** Mitos "nanti juga bisa bicara sendiri" itu berbahaya. Semakin dini intervensi, semakin baik hasilnya.
        * **Tes Pendengaran:** Langkah pertama adalah memastikan pendengaran anak normal.
        * **Kurangi Screen Time:** IDAI dan AAP merekomendasikan **nol screen time** untuk anak di bawah 18 bulan (kecuali video call) dan maksimal 1 jam/hari untuk 2-5 tahun.
        * **Ajak Bicara & Membaca:** Ajak anak bicara sesering mungkin, narasikan kegiatan Anda ("Adik mandi pakai sabun wangi"), dan bacakan buku cerita setiap hari.
        * **Konsultasi & Terapi:** Temui dokter anak untuk evaluasi. Jika perlu, anak akan dirujuk untuk terapi wicara.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Keterlambatan Bicara pada Anak.*
        2.  American Academy of Pediatrics (AAP). *Language Development: 8 to 12 Months.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Tumbuh Kembang",
        "title": "Pentingnya Tummy Time untuk Bayi",
        "summary": "Apa itu tummy time, mengapa sangat penting, dan bagaimana cara melakukannya dengan aman.",
        "source": "AAP",
        # URL Baru: Bayi Tummy Time
        "image_url": "https://kimi-web-img.moonshot.cn/img/lingokids.com/0d9500b483f06b54f2012a2b85ae59cc840c5d70.jpg",
        "full_content": """
        # Pentingnya Tummy Time untuk Bayi
        
        *Tummy time* (waktu tengkurap) adalah salah satu aktivitas stimulasi paling awal dan paling penting untuk bayi Anda.
        
        ## Apa itu Tummy Time?
        
        *Tummy time* adalah waktu dimana bayi diletakkan dalam posisi tengkurap (di atas perutnya) saat ia **bangun dan diawasi penuh**.
        
        American Academy of Pediatrics (AAP) merekomendasikan *tummy time* dimulai sesegera mungkin setelah bayi pulang dari rumah sakit.
        
        ## Mengapa Tummy Time Sangat Penting?
        
        Sejak kampanye *Back to Sleep* (tidur telentang) untuk mencegah SIDS, bayi menghabiskan lebih banyak waktu telentang. *Tummy time* sangat penting untuk mengimbanginya.
        
        1.  **Menguatkan Otot:** Ini adalah latihan utama untuk menguatkan otot leher, bahu, punggung, dan lengan.
        2.  **Mencegah Kepala Peyang (Plagiocephaly):** Mengurangi tekanan pada satu sisi kepala akibat tidur telentang terus-menerus.
        3.  **Mencapai Milestone Motorik:** Kekuatan otot dari *tummy time* adalah fondasi untuk milestone berikutnya, seperti berguling, duduk, dan merangkak.
        4.  **Melatih Sensorik:** Memberikan bayi perspektif visual yang berbeda tentang dunia.
        
        ## Cara Melakukan Tummy Time
        
        * **Mulai Segera:** Mulai dengan durasi sangat singkat, 2-3 kali sehari selama 3-5 menit.
        * **Tempat:** Lakukan di permukaan yang rata dan bersih, seperti di lantai beralas matras tipis atau di dada orang tua.
        * **Waktu:** Lakukan saat bayi bangun, ceria, dan tidak lapar (misal: setelah ganti popok atau setelah mandi). Jangan lakukan sesaat setelah menyusu.
        * **Selalu Awasi:** **JANGAN PERNAH** meninggalkan bayi sendirian saat *tummy time*, bahkan sedetik pun.
        * **Tingkatkan Durasi:** Tambah durasi secara bertahap. Targetkan total 30-60 menit per hari saat bayi mencapai usia 3-4 bulan.
        
        ## Bayi Benci Tummy Time?
        
        Ini sangat wajar! Posisi ini adalah "kerja keras" bagi mereka.
        
        * Gunakan mainan berwarna cerah atau cermin yang tidak bisa pecah untuk menarik perhatiannya.
        * Berbaringlah di lantai menghadap bayi Anda, ajak ia bicara atau bernyanyi.
        * Lakukan *tummy time* di dada Anda.
        * Gulung handuk kecil dan letakkan di bawah dada bayi untuk sedikit membantu.
        
        ---
        
        **Sumber (Acuan):**
        1.  American Academy of Pediatrics (AAP). *Tummy Time: How to Help Your Baby Get Started.*
        2.  Ikatan Dokter Anak Indonesia (IDAI). *Pentingnya Tengkurap untuk Bayi.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    # ----- BATAS BAGIAN 1 (LANJUT KE BAGIAN 2) -----
{
        "kategori": "Tumbuh Kembang",
        "title": "Manfaat Membacakan Buku Sejak Dini",
        "summary": "Mengapa membacakan buku (read aloud) adalah salah satu stimulasi terbaik untuk otak.",
        "source": "AAP | Kemenkes RI",
        # URL Baru: Membaca buku dengan anak
        "image_url": "https://kimi-web-img.moonshot.cn/img/c8.alamy.com/48710544b0d8132433804fcf16bfcdb02fe00e59.jpg",
        "full_content": """
        # Manfaat Ajaib Membacakan Buku Sejak Dini (Read Aloud)
        
        Membacakan buku untuk bayi sering dianggap "percuma" karena bayi belum mengerti. Padahal, ini adalah salah satu stimulasi terpenting untuk perkembangan otaknya.
        
        American Academy of Pediatrics (AAP) merekomendasikan orang tua membacakan buku untuk anak mereka **sejak hari pertama kelahiran**.
        
        ## Mengapa Membaca Sejak Bayi?
        
        1.  **Stimulasi Bahasa:** Ini adalah cara terbaik untuk "memandikan" otak bayi dengan kosakata. Bayi mendengar ritme, intonasi, dan kata-kata baru yang tidak ia dengar dalam percakapan sehari-hari.
        2.  **Membangun Koneksi Otak:** Aktivitas mendengar cerita sambil melihat gambar membangun koneksi saraf yang menjadi fondasi kemampuan membaca dan belajar kelak.
        3.  **Bonding Emosional:** Momen meringkuk bersama sambil membaca buku membangun rasa aman dan ikatan emosional yang kuat antara orang tua dan anak.
        4.  **Melatih Fokus:** Membantu melatih rentang perhatian (fokus) bayi secara bertahap.
        5.  **Menumbuhkan Minat Baca:** Anak yang dibacakan buku sejak bayi cenderung akan mencintai buku saat ia besar nanti.
        
        ## Tips Membacakan Buku untuk Bayi
        
        * **0-6 Bulan:**
            * Pilih buku kain (*soft book*) atau *board book* yang tebal.
            * Fokus pada buku dengan kontras tinggi (hitam-putih) atau warna-warni cerah.
            * Tidak perlu membaca teksnya. Cukup tunjuk gambar dan sebutkan namanya ("Lihat, ini bola!").
            * Biarkan bayi menyentuh, menggigit, atau memegang buku.
        
        * **6-12 Bulan:**
            * Pilih buku dengan gambar besar benda-benda familiar (binatang, mainan, buah).
            * Gunakan intonasi dan ekspresi wajah yang heboh. Tirukan suara binatang ("Moo!").
            * Libatkan anak: "Di mana kucing?" dan bantu ia menunjuk.
            * Jadikan rutinitas, misalnya 10 menit setiap malam sebelum tidur.
        
        * **12-24 Bulan:**
            * Anak mulai bisa memilih bukunya sendiri.
            * Minta anak menunjuk gambar yang Anda sebutkan.
            * Bacalah cerita pendek berulang-ulang. Pengulangan adalah cara anak belajar.
        
        Tidak ada kata terlalu dini untuk mulai membaca. Jadikan ini kebiasaan harian yang menyenangkan.
        
        ---
        
        **Sumber (Acuan):**
        1.  American Academy of Pediatrics (AAP). *Reading Books to Babies.*
        2.  Kementerian Kesehatan RI. *Stimulasi Membaca untuk Anak.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Tumbuh Kembang",
        "title": "Perkembangan Penglihatan Bayi dari Lahir hingga 1 Tahun",
        "summary": "Bagaimana penglihatan bayi berkembang, dari buram hingga fokus.",
        "source": "American Academy of Ophthalmology (AAO)",
        # URL Baru: Wajah bayi (Eye contact)
        "image_url": "https://kimi-web-img.moonshot.cn/img/www.bfsuccess.com/78adc29db11b8520968d55ba0122a732e589730e.jpg",
        "full_content": """
        # Perkembangan Penglihatan Bayi dari Lahir hingga 1 Tahun
        
        Bayi tidak lahir dengan penglihatan sempurna seperti orang dewasa. Kemampuan melihat mereka berkembang secara bertahap.
        
        ## Baru Lahir (0-1 Bulan)
        
        * **Buram (Blurry):** Penglihatan bayi baru lahir sangat buram.
        * **Jarak Pandang:** Mereka hanya bisa fokus pada objek berjarak sekitar 20-30 cm (kira-kira jarak dari wajah ibu saat menyusui).
        * **Kontras Tinggi:** Bayi paling tertarik pada pola kontras tinggi (hitam-putih) dan wajah manusia.
        * **Mata Juling:** Adalah normal jika mata bayi sesekali tampak juling atau tidak sinkron di minggu-minggu pertama.
        
        ## Usia 2-4 Bulan
        
        * **Koordinasi Mata:** Mata bayi mulai bekerja sama dengan lebih baik. Mereka mulai bisa mengikuti objek bergerak dengan kedua mata (tracking).
        * **Melihat Warna:** Kemampuan melihat warna berkembang pesat. Mereka mulai bisa membedakan warna-warna primer, terutama merah dan hijau.
        * **Stimulasi:** Gantung mainan berwarna-warni di atas tempat tidurnya.
        
        ## Usia 5-8 Bulan
        
        * **Persepsi Kedalaman (3D):** Bayi mulai mengembangkan penglihatan 3D. Mereka bisa menilai seberapa jauh sebuah objek.
        * **Koordinasi Mata-Tangan:** Penglihatan memandu tangan mereka untuk meraih dan mengambil benda dengan lebih akurat.
        * **Mengenali Wajah:** Bayi sudah sangat baik dalam mengenali wajah orang-orang terdekatnya.
        
        ## Usia 9-12 Bulan
        
        * **Menilai Jarak:** Kemampuan menilai jarak semakin baik, yang penting saat mereka belajar merangkak dan berjalan.
        * **Menjimpit:** Bayi dapat melihat benda yang sangat kecil dan mencoba mengambilnya (menjimpit).
        * **Fokus Tajam:** Penglihatan bayi sudah hampir setajam orang dewasa.
        
        ## 🚩 Red Flags (Waspada Gangguan Penglihatan)
        
        Segera konsultasi ke dokter jika:
        
        * **Usia 3-4 Bulan:** Bayi tidak mengikuti objek bergerak dengan matanya.
        * **Usia 6 Bulan:** Mata masih sering terlihat juling (salah satu mata melihat ke arah berbeda).
        * Bayi sering mengucek mata, sangat sensitif terhadap cahaya, atau kelopak matanya tampak "jatuh".
        * Pupil (bagian hitam di tengah mata) tampak berwarna putih atau keruh.
        
        ---
        
        **Sumber (Acuan):**
        1.  American Academy of Ophthalmology (AAO). *Infant Vision Development: What Can Babies See?*
        2.  Ikatan Dokter Anak Indonesia (IDAI). *Skrining Penglihatan pada Anak.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Tumbuh Kembang",
        "title": "Bahaya 'Baby Walker' dan Mengapa Dilarang",
        "summary": "Mengapa baby walker tidak membantu anak berjalan dan justru berbahaya.",
        "source": "IDAI | AAP",
        # URL Baru: Bayi berdiri/berjalan aman (kaki bayi)
        "image_url": "https://kimi-web-img.moonshot.cn/img/storytoys.com/347c008ea360b9fad503230d6e920b7ce5d21a9f.jpg",
        "full_content": """
        # Bahaya 'Baby Walker' dan Mengapa Dilarang
        
        *Baby walker* (alat bantu jalan beroda) masih sering dianggap sebagai alat yang dapat mempercepat anak berjalan. Faktanya, Ikatan Dokter Anak Indonesia (IDAI) dan American Academy of Pediatrics (AAP) **melarang keras** penggunaannya karena berbahaya dan tidak bermanfaat.
        
        ## Mengapa Baby Walker Berbahaya?
        
        1.  **Risiko Cedera Serius:**
            * **Jatuh dari Tangga:** Ini adalah kecelakaan paling umum dan paling fatal. *Walker* memberi bayi kecepatan dan mobilitas untuk mencapai tepi tangga sebelum orang tua sempat bereaksi.
            * **Menjangkau Benda Berbahaya:** Bayi bisa menjangkau benda yang lebih tinggi yang sebelumnya aman, seperti kompor panas, taplak meja (menarik benda berat di atasnya), atau cairan beracun.
            * **Terguling:** *Walker* mudah terbalik jika menabrak karpet atau permukaan yang tidak rata.
        
        2.  **Menghambat Perkembangan Motorik:**
            * *Baby walker* **tidak mengajarkan anak berjalan**. Berjalan membutuhkan keseimbangan dan koordinasi otot batang tubuh dan kaki.
            * Di dalam *walker*, anak "menggantung" dan hanya menggunakan ujung jarinya (berjinjit) untuk mendorong. Ini justru mengajarkan pola berjalan yang salah.
            * Anak yang menggunakan *walker* seringkali justru mengalami keterlambatan berjalan mandiri dibandingkan yang tidak.
        
        ## Alternatif yang Lebih Aman dan Bermanfaat
        
        Jika Anda ingin memberikan anak area bermain yang aman saat Anda sibuk, gunakan:
        
        * **Playpen (Pagar Bermain):** Sediakan area di lantai yang aman, beralaskan matras, dan dibatasi pagar bermain. Isi dengan mainan yang sesuai usianya.
        * **Activity Center (Stasioner):** Ini adalah mainan yang kursinya bisa berputar namun **tidak memiliki roda**. Anak bisa bermain dengan mainan di sekelilingnya tanpa bisa bergerak ke tempat berbahaya.
        * **Biarkan di Lantai:** Cara terbaik bagi bayi untuk belajar adalah bereksplorasi di lantai yang bersih dan aman. Ini adalah stimulasi terbaik untuk berguling, duduk, merangkak, dan menarik diri untuk berdiri.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Amankah Baby Walker untuk Bayi Anda?*
        2.  American Academy of Pediatrics (AAP). *Baby Walkers: A Dangerous Choice.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    
    # ============================================================
    # KATEGORI: KESEHATAN & IMUNISASI
    # ============================================================
    {
        "kategori": "Kesehatan & Imunisasi",
        "title": "Pentingnya Imunisasi Dasar Lengkap",
        "summary": "Mengapa imunisasi sangat penting dan daftar vaksin yang wajib diterima anak Indonesia.",
        "source": "IDAI | Kemenkes RI",
        # URL Baru: Dokter/Vaksin
        "image_url": "https://kimi-web-img.moonshot.cn/img/lovingthetoddlerlife.com/7e45aa73aab8cecf7ef3e3b660b6850feae934bc.jpg",
        "full_content": """
        # Pentingnya Imunisasi Dasar Lengkap
        
        Imunisasi adalah proses membuat seseorang imun atau kebal terhadap suatu penyakit. Ini adalah salah satu intervensi kesehatan paling efektif dan hemat biaya di dunia.
        
        ## Mengapa Imunisasi Penting?
        
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
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Kesehatan & Imunisasi",
        "title": "Panduan Tepat Mengatasi Demam pada Anak",
        "summary": "Kapan harus khawatir saat anak demam, dan pertolongan pertama yang benar (bukan kompres dingin!).",
        "source": "IDAI | AAP",
        # URL Baru: Anak demam/diukur suhu
        "image_url": "https://kimi-web-img.moonshot.cn/img/www.olivaclinic.com/701ae72186a50beede96d7ec25e95516b1caf6e9.jpg",
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
    {
        "kategori": "Kesehatan & Imunisasi",
        "title": "Mengenal Batuk Pilek (ISPA) pada Anak",
        "summary": "Membedakan batuk pilek biasa (virus) dan kapan harus waspada infeksi bakteri.",
        "source": "IDAI | CDC",
        # URL Baru: Anak sakit/tidur
        "image_url": "https://kimi-web-img.moonshot.cn/img/utknoxvilledentists.com/1a2450821aa5916c93a450902c3f76a7e91dbb9f.jpg",
        "full_content": """
        # Mengenal Batuk Pilek (ISPA) pada Anak
        
        Batuk pilek (juga dikenal sebagai *common cold* atau ISPA atas) adalah penyakit paling umum pada anak. Anak balita bisa mengalaminya 6-8 kali dalam setahun, dan ini normal.
        
        ## Penyebab
        
        Lebih dari 90% batuk pilek disebabkan oleh **Virus**. Karena disebabkan oleh virus, penyakit ini **tidak memerlukan antibiotik** dan akan sembuh sendiri (*self-limiting disease*) dalam 7-14 hari.
        
        ## Gejala
        
        * Hidung meler (ingus awalnya bening, bisa menjadi kental dan kuning/hijau di hari ke-3 sampai ke-5, ini normal).
        * Hidung tersumbat.
        * Bersin-bersin.
        * Batuk (biasanya batuk berdahak).
        * Demam ringan (biasanya di 3 hari pertama).
        
        ## Perawatan di Rumah (Tanpa Obat)
        
        Fokus perawatan adalah membuat anak nyaman, bukan "menyembuhkan" pileknya.
        
        1.  **Cairan yang Cukup:** Pastikan anak banyak minum (ASI, susu, air putih) untuk mengencerkan dahak dan ingus.
        2.  **Lembapkan Udara:** Gunakan *humidifier* (pelembap udara) di kamar anak untuk membantu melegakan hidung tersumbat.
        3.  **Cuci Hidung (Nasal Wash):** Gunakan cairan saline (NaCl 0.9%) tetes atau semprot untuk membersihkan lendir dari hidung bayi agar ia bisa bernapas dan menyusu lebih mudah.
        4.  **Uap Air:** Menemani anak di kamar mandi yang telah diisi uap air panas (dari shower) selama 10-15 menit dapat membantu melegakan napas.
        
        ## Kapan Perlu Obat?
        
        * **Obat Batuk Pilek (OTC):** IDAI dan AAP **tidak merekomendasikan** pemberian obat batuk pilek yang dijual bebas untuk anak di bawah usia 6 tahun karena efektivitasnya tidak terbukti dan risiko efek sampingnya.
        * **Obat Demam:** Berikan Paracetamol atau Ibuprofen (sesuai dosis) **hanya jika** anak demam tinggi atau tampak sangat tidak nyaman.
        
        ## 🚩 RED FLAGS: Kapan Harus Segera ke Dokter?
        
        Batuk pilek biasa umumnya ringan. Waspadai tanda-tanda infeksi bakteri sekunder atau Pneumonia (radang paru):
        
        * **Napas Cepat (Tanda Utama):** Hitung napas anak saat ia tenang/tidur selama 1 menit penuh.
            * Usia < 2 bulan: > 60 kali/menit
            * Usia 2-12 bulan: > 50 kali/menit
            * Usia 1-5 tahun: > 40 kali/menit
        * **Tarikan Dinding Dada (Retraksi):** Terlihat cekungan di bawah tulang rusuk atau di leher saat anak bernapas.
        * Demam tinggi > 39°C yang tidak membaik.
        * Anak terlihat sangat lemas, tidak mau minum, atau sulit dibangunkan.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Batuk Pilek pada Anak.*
        2.  Centers for Disease Control and Prevention (CDC). *Common Colds: Protect Yourself and Others.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Kesehatan & Imunisasi",
        "title": "Mengatasi Diare Akut pada Balita",
        "summary": "Kunci utama mengatasi diare adalah rehidrasi (cairan) untuk mencegah dehidrasi.",
        "source": "WHO | Kemenkes RI",
        # URL Baru: Anak minum air (Rehidrasi)
        "image_url": "https://kimi-web-img.moonshot.cn/img/blog.lovevery.com/ccdb76cd6aad9483bc6a402958a19eb1c99d9169.jpg",
        "full_content": """
        # Mengatasi Diare Akut pada Balita
        
        Diare (mencret) adalah kondisi di mana anak buang air besar (BAB) lebih sering (>3 kali sehari) dengan konsistensi cair. Diare paling sering disebabkan oleh infeksi virus (seperti Rotavirus).
        
        ## Bahaya Utama: Dehidrasi
        
        Bahaya terbesar dari diare bukanlah diarenya itu sendiri, tetapi **dehidrasi** (kehilangan cairan tubuh). Dehidrasi berat pada bayi dapat menyebabkan syok dan kematian dengan cepat.
        
        **Tanda-tanda Dehidrasi yang Harus Diwaspadai:**
        * **Ringan-Sedang:** Anak rewel, tampak haus, mata sedikit cekung, buang air kecil (BAK) berkurang (popok tidak cepat penuh).
        * **Berat (DARURAT):** Anak lemas/tidur terus, mata sangat cekung, tidak mau minum, BAK sangat sedikit/tidak ada, cubitan kulit perut kembali lambat. **Segera ke UGD!**
        
        ## Pertolongan Pertama: LINTAS (Lima Langkah Tuntaskan Diare)
        
        Ini adalah program resmi Kemenkes untuk penanganan diare di rumah:
        
        1.  **Beri ORALIT:**
            * Ini adalah langkah terpenting untuk mengganti cairan dan elektrolit yang hilang.
            * Beri oralit setiap kali anak mencret.
            * Takaran: Usia < 1 tahun (50-100 ml), Usia > 1 tahun (100-200 ml).
            * Berikan sedikit-sedikit tapi sering (misal: 1 sendok teh setiap 1-2 menit) jika anak muntah.
        
        2.  **Beri ZINC:**
            * Tablet Zinc (Zink) terbukti dapat mengurangi durasi dan keparahan diare.
            * Berikan Zinc 1 kali sehari selama **10 hari berturut-turut** (meskipun diare sudah berhenti).
            * Dosis: Usia < 6 bulan (10 mg/hari), Usia > 6 bulan (20 mg/hari).
        
        3.  **Lanjutkan ASI / Makanan:**
            * **Jangan puasakan anak!**
            * Lanjutkan pemberian ASI atau susu formula seperti biasa.
            * Lanjutkan MPASI/makanan biasa. Makanan membantu memulihkan dinding usus.
        
        4.  **Beri Antibiotik (HANYA ATAS RESEP DOKTER):**
            * **Jangan** beri antibiotik sendiri. Sebagian besar diare disebabkan virus, yang tidak mempan antibiotik. Antibiotik yang tidak tepat justru memperburuk diare.
        
        5.  **Nasihat Kapan Kembali:**
            * Segera ke dokter jika muncul tanda dehidrasi berat, diare berdarah, atau demam tinggi.
        
        ## Pencegahan Diare
        
        * Cuci tangan pakai sabun.
        * Minum air matang.
        * Imunisasi Rotavirus.
        
        ---
        
        **Sumber (Acuan):**
        1.  Kementerian Kesehatan RI. *LINTAS Diare (Lima Langkah Tuntaskan Diare).*
        2.  World Health Organization (WHO). *Diarrhoeal disease - Fact Sheet.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Kesehatan & Imunisasi",
        "title": "Jadwal Imunisasi Rekomendasi IDAI 2023",
        "summary": "Jadwal imunisasi lengkap yang direkomendasikan Ikatan Dokter Anak Indonesia (IDAI).",
        "source": "IDAI",
        # URL Baru: Pemeriksaan dokter/imunisasi
        "image_url": "https://kimi-web-img.moonshot.cn/img/childrens-dental.com/cfb293d7a09681b46861c0930fccee2c0d796035.jpg",
        "full_content": """
        # Jadwal Imunisasi Anak Rekomendasi IDAI 2023
        
        Ikatan Dokter Anak Indonesia (IDAI) setiap beberapa tahun mengeluarkan rekomendasi jadwal imunisasi. Jadwal ini seringkali lebih lengkap daripada program wajib pemerintah (PPI) karena memasukkan vaksin-vaksin non-program yang dianggap penting.
        
        Berikut adalah rangkuman jadwal imunisasi untuk bayi 0-12 bulan:
        
        | Usia | Vaksin yang Direkomendasikan |
        | :--- | :--- |
        | **Lahir (<24 jam)** | Hepatitis B (HB-1), Polio 0 |
        | **1 Bulan** | BCG |
        | **2 Bulan** | DPT-HB-Hib 1, Polio 1, **Rotavirus 1**, **PCV 1** |
        | **3 Bulan** | DPT-HB-Hib 2, Polio 2 |
        | **4 Bulan** | DPT-HB-Hib 3, Polio 3, **Rotavirus 2**, **PCV 2** |
        | **6 Bulan** | **PCV 3**, **Influenza 1** (mulai usia 6 bulan, 2 dosis dengan jarak 1 bulan) |
        | **7 Bulan** | **Influenza 2** |
        | **9 Bulan** | Campak/MR 1 |
        | **12 Bulan** | **PCV 4 (Booster)**, **Varisela (Cacar Air) 1** |
        
        *(Vaksin yang di-**bold** adalah vaksin non-program PPI yang sangat direkomendasikan IDAI)*
        
        ## Penjelasan Vaksin Non-Program (Sangat Penting)
        
        * **PCV (Pneumokokus):**
            * **Mencegah:** Radang paru (Pneumonia), radang otak (Meningitis), dan infeksi telinga berat yang disebabkan bakteri *Streptococcus pneumoniae*.
            * **Jadwal:** 2, 4, 6, dan 12-15 bulan.
        
        * **Rotavirus:**
            * **Mencegah:** Diare berat akibat Rotavirus. Ini adalah penyebab utama dehidrasi berat dan rawat inap pada bayi.
            * **Jadwal:** Diberikan 2 atau 3 kali (tergantung merek vaksin), dimulai usia 6-12 minggu, dan harus selesai sebelum usia 8 bulan. Diberikan via tetes oral.
        
        * **Influenza:**
            * **Mencegah:** Flu berat. Pada anak kecil, influenza bisa menyebabkan komplikasi serius.
            * **Jadwal:** Dimulai usia 6 bulan, diberikan 2 dosis di tahun pertama (jarak 1 bulan), lalu diulang **1 kali setiap tahun**.
        
        * **Varisela (Cacar Air):**
            * **Mencegah:** Cacar air.
            * **Jadwal:** Dosis pertama di usia 12-18 bulan.
        
        ## Apa itu Vaksin Kombinasi (Hexa/Penta)?
        
        Vaksin kombinasi menggabungkan beberapa vaksin dalam satu suntikan, sehingga mengurangi jumlah suntikan pada bayi.
        
        * **Vaksin Pemerintah (Pentavalent):** DPT-HB-Hib
        * **Vaksin Swasta (Hexavalent):** DPT-HB-Hib + IPV (Polio suntik). Jika bayi mendapat vaksin ini, ia tidak perlu Polio tetes/suntik terpisah di bulan tersebut.
        
        Diskusikan jadwal terbaik untuk anak Anda dengan dokter spesialis anak.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Jadwal Imunisasi Anak Usia 0-18 Tahun Rekomendasi IDAI 2023.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Kesehatan & Imunisasi",
        "title": "Mengenal Kejang Demam (Step)",
        "summary": "Apa yang harus dilakukan dan apa yang TIDAK boleh dilakukan saat anak kejang demam.",
        "source": "IDAI | AAP",
        # URL Baru: Ibu menggendong anak sakit
        "image_url": "https://kimi-web-img.moonshot.cn/img/cdn.dental.dev/0ad79032153cffdaaed4ebdce5066acee86d9eca.jpg",
        "full_content": """
        # Mengenal Kejang Demam (Step)
        
        Kejang demam (KD) atau "step" adalah kejang yang terjadi pada anak usia 6 bulan hingga 5 tahun, yang dipicu oleh kenaikan suhu tubuh (demam) > 38°C.
        
        Meskipun terlihat sangat menakutkan, **kejang demam sederhana (KDS)** umumnya **tidak berbahaya**, tidak merusak otak, dan bukan epilepsi.
        
        ## Apa yang Harus Dilakukan Saat Anak Kejang
        
        Tetap tenang adalah kunci.
        
        1.  **Amankan Posisi Anak:**
            * Letakkan anak di permukaan yang **rata dan aman** (misal: lantai beralas karpet).
            * **JANGAN** gendong atau tahan gerakan kejangnya.
            * Jauhkan benda keras atau tajam di sekitarnya.
        
        2.  **Miringkan Tubuh Anak:**
            * Segera miringkan tubuh anak (posisi miring mantap) ke salah satu sisi.
            * **Tujuan:** Mencegah air liur atau muntahan masuk ke saluran napas (tersedak).
        
        3.  **Longgarkan Pakaian:** Longgarkan pakaian anak, terutama di sekitar leher.
        
        4.  **Amati dan Catat Waktu:**
            * Lihat jam. Catat berapa lama kejang berlangsung.
            * Kejang demam sederhana biasanya berlangsung **kurang dari 5 menit**.
        
        5.  **Tetap Bersama Anak:** Dampingi anak hingga kejang berhenti dan ia sadar sepenuhnya.
        
        ## Apa yang TIDAK BOLEH Dilakukan
        
        * **JANGAN** memasukkan apa pun ke dalam mulut anak (sendok, jari, kain). Ini dapat menyumbat jalan napas, merusak gigi, atau mencederai jari Anda. Anak tidak akan menelan lidahnya.
        * **JANGAN** memberi kopi, minuman, atau obat apa pun saat anak sedang kejang.
        * **JANGAN** merendam anak di air dingin atau mengompres dengan alkohol.
        
        ## Kapan Harus ke UGD?
        
        Bawa anak ke UGD **SEGERA** jika:
        
        * Ini adalah kejang demam **pertama** kalinya.
        * Kejang berlangsung **lebih dari 5 menit**.
        * Anak tampak **sulit bernapas** atau wajah/bibirnya membiru.
        * Anak tampak sangat lemas, kaku leher, atau muntah hebat setelah kejang (curiga meningitis).
        * Kejang terjadi berulang dalam 24 jam.
        
        Setelah kejang berhenti, Anda tetap harus membawa anak ke dokter untuk memastikan penyebab demamnya.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Kejang Demam: Yang Perlu Diketahui Orangtua.*
        2.  American Academy of Pediatrics (AAP). *Febrile Seizures: What Parents Need to Know.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Kesehatan & Imunisasi",
        "title": "Perawatan Gigi Pertama Bayi (Karies Botol)",
        "summary": "Merawat gigi bayi sejak gigi pertama tumbuh untuk mencegah karies (gigi berlubang).",
        "source": "IDAI | AAPD",
        # URL Baru: Anak menyikat gigi/tersenyum
        "image_url": "https://kimi-web-img.moonshot.cn/img/cdn11.bigcommerce.com/690bbc8a72c0b7182d3ee4ff941d5066c9789158.jpg",
        "full_content": """
        # Perawatan Gigi Pertama Bayi (Mencegah Karies Botol)
        
        Merawat kesehatan gigi anak harus dimulai bahkan sebelum gigi pertamanya tumbuh.
        
        ## Kapan Memulai?
        
        * **Usia 0-6 Bulan (Belum Tumbuh Gigi):**
            * Bersihkan gusi bayi setiap hari.
            * Gunakan kain kasa bersih atau waslap yang dibasahi air matang.
            * Lilitkan di jari Anda dan usap gusi bayi dengan lembut setelah menyusu.
        
        * **Usia 6+ Bulan (Gigi Pertama Tumbuh):**
            * Gigi susu pertama biasanya tumbuh sekitar usia 6-10 bulan.
            * Segera setelah gigi pertama muncul, mulailah menyikat gigi.
        
        ## Cara Menyikat Gigi Bayi
        
        1.  **Peralatan:** Gunakan sikat gigi bayi (bulu sangat lembut, kepala kecil) atau sikat gigi jari (silikon).
        2.  **Pasta Gigi:**
            * Gunakan pasta gigi **ber-fluoride**. Fluoride sangat penting untuk mencegah gigi berlubang.
            * **Dosis (PENTING):**
                * Usia < 3 tahun: Seukuran **biji beras**.
                * Usia 3-6 tahun: Seukuran **biji kacang polong**.
            * Tidak apa-apa jika bayi menelan pasta gigi dalam jumlah tersebut.
        3.  **Frekuensi:** Sikat gigi 2 kali sehari (pagi setelah sarapan dan malam sebelum tidur).
        
        ## Mencegah Karies Botol (Baby Bottle Tooth Decay)
        
        Karies botol adalah kerusakan gigi parah yang terjadi pada bayi/balita.
        
        **Penyebab:**
        Cairan manis (susu formula, ASI, jus) yang "menggenang" di mulut bayi saat ia tertidur. Gula dalam cairan tersebut diubah bakteri menjadi asam yang merusak email gigi.
        
        **Cara Mencegah:**
        
        * **JANGAN** biarkan bayi tidur sambil *ngedot* (minum dari botol).
        * Jika bayi harus minum susu sebelum tidur, pastikan ia menelannya dan jangan biarkan botol tertinggal di mulutnya saat ia tertidur.
        * Usahakan bersihkan gigi/gusi bayi setelah menyusu terakhir sebelum tidur.
        * Setelah usia 1 tahun, ajarkan anak minum susu dari cangkir/gelas.
        
        ## Kapan Kunjungan Pertama ke Dokter Gigi?
        
        American Academy of Pediatric Dentistry (AAPD) dan IDAI merekomendasikan kunjungan pertama ke dokter gigi adalah **saat gigi pertama tumbuh**, atau paling lambat saat anak berusia **1 tahun**.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Merawat Gigi Anak Sejak Dini.*
        2.  American Academy of Pediatric Dentistry (AAPD). *Dental Home.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy)*
        """
    },
    {
        "kategori": "Kesehatan & Imunisasi",
        "title": "Sanitasi & Cuci Tangan: Kunci Cegah Stunting",
        "summary": "Hubungan tak terduga antara toilet bersih, cuci tangan, dan stunting.",
        "source": "Kemenkes RI | WHO",
        # URL Baru: Mencuci tangan
        "image_url": "https://kimi-web-img.moonshot.cn/img/thumbs.dreamstime.com/a08507d4f9080f3cd55fc1a97fa5fddb262c0b0d.jpg",
        "full_content": """
        # Sanitasi & Cuci Tangan: Kunci Tersembunyi Pencegahan Stunting
        
        Pencegahan stunting tidak hanya soal makanan bergizi. Dua faktor yang sering terlewat adalah **sanitasi (jamban sehat)** dan **cuci tangan pakai sabun (CTPS)**.
        
        ## Lingkaran Setan: Infeksi dan Malnutrisi
        
        Stunting disebabkan oleh kekurangan gizi kronis. Salah satu penyebab utama kekurangan gizi adalah infeksi berulang, terutama diare dan cacingan.
        
        1.  **Sanitasi Buruk:** BAB sembarangan atau toilet yang tidak higienis mencemari sumber air dan lingkungan dengan bakteri (seperti *E. coli*) dan telur cacing.
        2.  **Air & Tangan Tercemar:** Bakteri dan telur cacing ini pindah ke tangan, mainan, atau makanan.
        3.  **Infeksi:** Anak memasukkan tangan/mainan ke mulut, lalu terinfeksi.
        4.  **Diare & Cacingan:** Anak menderita diare atau cacingan berulang.
        5.  **Malnutrisi:** Saat diare, penyerapan nutrisi di usus terganggu. Cacingan "mencuri" nutrisi dari makanan anak.
        6.  **Gagal Tumbuh:** Karena nutrisi tidak terserap optimal, anak mengalami gagal tumbuh (stunting).
        
        Lingkaran setan ini terus berulang, membuat anak sulit mengejar ketertinggalan gizinya.
        
        ## 5 Waktu Kritis Cuci Tangan Pakai Sabun (CTPS)
        
        Memutus rantai ini sangat mudah, yaitu dengan CTPS pada 5 waktu kritis:
        
        1.  **Sebelum** menyiapkan makanan/MPASI.
        2.  **Sebelum** makan/menyuapi anak.
        3.  **Setelah** dari toilet (BAB/BAK).
        4.  **Setelah** membersihkan anak yang habis BAB (mengganti popok).
        5.  **Setelah** memegang hewan atau sampah.
        
        ## Apa itu Jamban Sehat?
        
        Pastikan keluarga memiliki akses ke jamban sehat, yaitu:
        
        * Tipe leher angsa (bukan cemplung terbuka).
        * Memiliki *septic tank* yang tertutup dan tidak mencemari sumber air.
        * Tersedia air bersih dan sabun untuk membersihkan diri.
        
        Memberi anak makanan bergizi tinggi (seperti protein hewani) akan sia-sia jika nutrisinya "bocor" akibat infeksi berulang dari lingkungan yang tidak bersih.
        
        ---
        
        **Sumber (Acuan):**
        1.  Kementerian Kesehatan RI. *Sanitasi Total Berbasis Masyarakat (STBM).*
        2.  World Health Organization (WHO). *Sanitation, Hygiene and Stunting.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    
    # ============================================================
    # KATEGORI: POLA ASUH & PSIKOLOGI
    # ============================================================
    {
        "kategori": "Pola Asuh & Psikologi",
        "title": "Bahaya 'Screen Time' Berlebihan pada Balita",
        "summary": "Rekomendasi IDAI dan AAP mengenai batasan penggunaan gadget/TV untuk anak.",
        "source": "IDAI | AAP",
        # URL Baru: Anak melihat layar/gadget
        "image_url": "https://kimi-web-img.moonshot.cn/img/images.squarespace-cdn.com/1dd3112c34c51fc75b2d4f1e1addc4669373e8f0.jpg",
        "full_content": """
        # Bahaya 'Screen Time' Berlebihan pada Balita
        
        *Screen time* adalah waktu yang dihabiskan untuk menonton layar, termasuk TV, tablet, smartphone, atau game. Penggunaan yang berlebihan dan tidak tepat pada balita terbukti berdampak negatif pada perkembangan.
        
        ## Rekomendasi Batasan Screen Time (Usia)
        
        Ikatan Dokter Anak Indonesia (IDAI) dan American Academy of Pediatrics (AAP) memberikan panduan ketat:
        
        * **Usia < 18 Bulan:**
            * **NOL (0) screen time.**
            * **Pengecualian:** *Video call* dengan keluarga (misal: kakek-nenek), dengan pendampingan penuh orang tua.
            * **Mengapa?** Otak bayi di usia ini belum bisa memproses gambar 2D di layar. Mereka belajar dari interaksi 3D di dunia nyata (sentuhan, suara, respons).
        
        * **Usia 18 - 24 Bulan:**
            * Jika ingin diperkenalkan, pilih **konten edukasi berkualitas tinggi** (misal: program belajar kata).
            * Wajib ditonton **bersama orang tua** (co-viewing), bukan dibiarkan sendiri.
            * Durasi sangat singkat.
        
        * **Usia 2 - 5 Tahun:**
            * Batasi maksimal **1 jam per hari**.
            * Tetap pilih konten berkualitas dan dampingi anak.
            * Jelaskan apa yang sedang ditonton.
        
        ## Dampak Negatif Screen Time Berlebihan
        
        1.  **Keterlambatan Bicara (Speech Delay):**
            * Anak belajar bicara dari interaksi 2 arah (merespon orang tua). Layar hanya 1 arah.
            * Setiap jam screen time berlebih pada balita terbukti mengurangi jumlah kosakata yang ia dengar dan ucapkan.
        
        2.  **Gangguan Tidur:**
            * Cahaya biru (blue light) dari layar menekan hormon melatonin (hormon tidur), membuat anak sulit tidur dan tidur tidak nyenyak.
        
        3.  **Masalah Perilaku:**
            * Dihubungkan dengan rentang fokus yang lebih pendek, sulit mengontrol emosi, dan risiko ADHD.
        
        4.  **Risiko Obesitas:**
            * Waktu menonton (pasif) mengurangi waktu bermain aktif (bergerak).
            * Sering disertai *ngemil* makanan tidak sehat saat menonton.
        
        ## Tips Sehat Menggunakan Gadget
        
        * **Jadikan "Waktu Main Bersama":** Gunakan gadget sebagai alat interaksi, bukan sebagai "babysitter" digital.
        * **Zona Bebas Gadget:** Terapkan aturan "Tidak ada gadget di meja makan" dan "Tidak ada gadget 1 jam sebelum tidur".
        * **Orang Tua adalah Contoh:** Anak akan meniru kebiasaan orang tuanya. Kurangi penggunaan gadget pribadi Anda saat sedang bersama anak.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Rekomendasi Screen Time pada Anak.*
        2.  American Academy of Pediatrics (AAP). *Media and Young Minds.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    # ----- BATAS BAGIAN 2 (LANJUT KE BAGIAN 3) -----
{
        "kategori": "Pola Asuh & Psikologi",
        "title": "Memahami 'Tantrum' pada Toddler (1-3 Tahun)",
        "summary": "Mengapa anak tantrum dan bagaimana cara orang tua meresponsnya dengan tepat.",
        "source": "CDC | AAP",
        # URL Baru: Anak menangis/emosional
        "image_url": "https://kimi-web-img.moonshot.cn/img/media.istockphoto.com/384d9b74cce8190e605803f972f9edfc86a1a951.jpg",
        "full_content": """
        # Memahami 'Tantrum' pada Toddler (1-3 Tahun)
        
        Tantrum (ledakan emosi) adalah perilaku normal pada anak usia *toddler* (1-3 tahun). Ini bukanlah tanda anak "nakal" atau "cengeng", melainkan tanda frustrasi.
        
        ## Mengapa Anak Tantrum?
        
        Tantrum terjadi karena "badai" di dalam otak anak. Ini adalah ledakan emosi akibat:
        
        1.  **Keterbatasan Bahasa:** Anak sudah memiliki keinginan kuat (misal: "mau biskuit itu"), tapi belum mampu menyampaikannya dengan kata-kata.
        2.  **Frustrasi:** Keinginan tidak terpenuhi (misal: dilarang bermain).
        3.  **Kondisi Fisik:** Anak sedang **LAPAR**, **MENGANTUK/LELAH**, atau **SAKIT**. Ini adalah pemicu paling umum.
        4.  **Perkembangan Otonomi:** Anak sedang dalam fase "aku bisa sendiri" dan ingin mengontrol lingkungannya.
        
        ## Cara Merespons Tantrum (Do's and Don'ts)
        
        Respons orang tua saat tantrum sangat krusial.
        
        ### YANG HARUS DILAKUKAN (Do's):
        
        1.  **Tetap Tenang:** Tarik napas. Emosi Anda akan memengaruhi anak. Jika Anda panik atau marah, tantrum akan semakin menjadi.
        2.  **Validasi Emosi:** Beri nama emosinya. "Adik marah ya karena mainannya diambil," atau "Kakak sedih ya karena kita harus pulang." Ini membantu anak belajar mengenali emosi.
        3.  **Pastikan Aman:** Jauhkan anak dari benda berbahaya. Jika ia memukul, tahan tangannya dengan lembut sambil berkata, "Boleh marah, tapi tidak boleh memukul."
        4.  **Alihkan Perhatian (Jika masih ringan):** Coba alihkan perhatiannya ke hal lain yang menarik.
        5.  **Abaikan (Jika tantrum berat):** Jika tantrum sudah meledak, terkadang yang terbaik adalah tetap berada di dekatnya (agar ia tahu Anda ada) tapi tidak merespon ledakannya. Tunggu hingga reda.
        
        ### YANG TIDAK BOLEH DILAKUKAN (Don'ts):
        
        1.  **JANGAN Ikut Marah:** Membentak atau memukul anak hanya akan memperburuk situasi dan mengajarkan bahwa kekerasan adalah solusi.
        2.  **JANGAN Memberi Apa yang Ia Inginkan:** Jika anak tantrum karena ingin permen, dan Anda memberikannya agar ia diam, Anda baru saja mengajarinya bahwa "Tantrum adalah cara ampuh mendapatkan sesuatu."
        3.  **JANGAN Mengancam atau Menakut-nakuti:** (misal: "Awas ada polisi," "Nanti Mama tinggal"). Ini akan merusak rasa amannya.
        
        Setelah tantrum reda, peluk anak. Bicarakan dengan singkat apa yang terjadi ("Tadi Kakak marah sekali ya. Lain kali kalau mau mainan, bilang baik-baik").
        
        ---
        
        **Sumber (Acuan):**
        1.  Centers for Disease Control and Prevention (CDC). *Temper Tantrums.*
        2.  American Academy of Pediatrics (AAP). *How to Handle Tantrums.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Pola Asuh & Psikologi",
        "title": "Pentingnya Ayah dalam Pengasuhan (Father's Role)",
        "summary": "Peran ayah bukan hanya mencari nafkah, tapi esensial untuk perkembangan anak.",
        "source": "AAP | UNICEF",
        # URL Baru: Ayah dan anak
        "image_url": "https://kimi-web-img.moonshot.cn/img/allsmilesdentalgroup.com/7964df7aee6ac7661d1733bab76b2ee0925c6259.jpg",
        "full_content": """
        # Pentingnya Ayah dalam Pengasuhan (Father's Role)
        
        Pengasuhan anak seringkali masih dianggap sebagai tugas utama ibu. Padahal, keterlibatan ayah secara aktif memiliki dampak luar biasa bagi perkembangan anak, baik laki-laki maupun perempuan.
        
        ## Dampak Positif Keterlibatan Ayah
        
        Penelitian menunjukkan anak-anak yang ayahnya terlibat aktif dalam pengasuhan cenderung:
        
        1.  **Memiliki Kecerdasan Kognitif Lebih Tinggi:** Ayah yang sering mengajak anak bermain dan membaca buku (stimulasi) terbukti meningkatkan skor IQ anak.
        2.  **Lebih Baik dalam Regulasi Emosi:** Anak belajar cara mengelola emosi dan stres dengan lebih baik.
        3.  **Lebih Percaya Diri dan Mandiri:** Merasa didukung oleh kedua orang tua, anak tumbuh lebih berani mengeksplorasi dunia.
        4.  **Memiliki Keterampilan Sosial yang Baik:** Anak lebih mudah bergaul dan berempati terhadap orang lain.
        
        ## Gaya Bermain Ayah yang Khas
        
        Ayah dan Ibu memiliki gaya interaksi yang berbeda, dan anak membutuhkan keduanya.
        
        * **Ibu** cenderung lebih verbal, menenangkan, dan menggunakan mainan terstruktur.
        * **Ayah** cenderung lebih **fisik** (mengajak "terbang", gulat ringan, lempar bola), lebih spontan, dan mendorong anak untuk mengambil risiko yang aman.
        
        Gaya bermain ayah yang "kasar" (rough-and-tumble play) ini sangat penting untuk mengajarkan anak regulasi diri (kapan harus berhenti), batasan, dan cara mengelola kegembiraan.
        
        ## Bagaimana Ayah Bisa Terlibat (Sejak Hari Pertama)?
        
        * **Saat Bayi Baru Lahir:**
            * Menggendong bayi (skin-to-skin contact).
            * Menggantikan popok.
            * Memandikan bayi.
            * Menemani ibu saat menyusui (misal: memijat punggung ibu).
        
        * **Saat Fase MPASI:**
            * Ikut menyuapi anak.
            * Bermain saat ibu menyiapkan makanan.
        
        * **Saat Balita:**
            * Membacakan buku cerita sebelum tidur.
            * Bermain aktif di luar rumah (main bola, lari-larian).
            * Mendengarkan cerita anak tentang harinya.
        
        Keterlibatan ayah bukan hanya "membantu ibu", tetapi merupakan **kebutuhan dasar** anak.
        
        ---
        
        **Sumber (Acuan):**
        1.  American Academy of Pediatrics (AAP). *The Power of Play: How Fun and Games Help Children Thrive.*
        2.  UNICEF. *Why fathers’ involvement in their children’s lives is so important.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Pola Asuh & Psikologi",
        "title": "Melatih Tidur Mandiri (Sleep Training)",
        "summary": "Membantu bayi belajar tidur nyenyak sepanjang malam tanpa bantuan.",
        "source": "AAP",
        # URL Baru: Bayi tidur nyenyak
        "image_url": "https://kimi-web-img.moonshot.cn/img/www.parents.com/bac01729c34d249dbbc2fd5a5f947b9d545e75b9.png",
        "full_content": """
        # Melatih Tidur Mandiri (Sleep Training)
        
        *Sleep training* adalah proses mengajarkan bayi untuk bisa tenang dan tertidur **secara mandiri** tanpa bantuan (seperti digendong, diayun, atau menyusu). Tujuannya agar bayi bisa tidur nyenyak sepanjang malam.
        
        ## Kapan Boleh Memulai?
        
        Sebagian besar ahli setuju bahwa *sleep training* aman dimulai saat bayi berusia **4 hingga 6 bulan**.
        
        * **Mengapa menunggu?** Sebelum usia 4 bulan, bayi secara fisik masih membutuhkan makan di malam hari dan pola tidurnya belum teratur.
        
        PENTING: Selalu konsultasikan dengan dokter anak Anda sebelum memulai metode *sleep training* apa pun.
        
        ## Persiapan Kunci: Rutinitas Tidur
        
        Sebelum memulai *training*, ciptakan **rutinitas waktu tidur** yang konsisten selama 1-2 minggu. Bayi menyukai prediksi.
        
        Contoh rutinitas (lakukan 20-30 menit setiap malam dalam urutan yang sama):
        1.  Mandi air hangat.
        2.  Pijat bayi.
        3.  Ganti popok dan pakaikan baju tidur.
        4.  Menyusu (pastikan ini dilakukan di awal rutinitas, bukan sebagai "alat" menidurkan).
        5.  Redupkan lampu.
        6.  Bacakan buku cerita.
        7.  Nyanyikan lagu nina bobo.
        8.  Ucapkan "selamat tidur".
        9.  **Letakkan bayi di tempat tidurnya saat ia MENGANTUK, tapi MASIH SADAR.**
        
        ## Metode Sleep Training Populer
        
        Tidak ada satu cara yang benar. Pilih yang sesuai dengan kenyamanan Anda.
        
        1.  **Cry It Out (CIO) / Extinction:**
            * Letakkan bayi di tempat tidur (setelah rutinitas), ucapkan selamat tidur, dan keluar kamar.
            * Anda tidak kembali lagi sampai pagi (kecuali untuk keadaan darurat).
            * Metode ini cepat (biasanya 3-4 hari) tapi sulit secara emosional bagi orang tua.
        
        2.  **Metode Ferber (Check-and-Console):**
            * Sama seperti CIO, tapi Anda kembali ke kamar untuk menenangkan bayi (mengusap, bicara lembut) dalam interval waktu yang semakin lama.
            * Misal: Hari 1 (interval 3, 5, 10 menit), Hari 2 (5, 10, 12 menit).
            * **PENTING:** Jangan gendong bayi saat interval cek.
        
        3.  **Metode Kursi (Fading):**
            * Duduk di kursi di samping tempat tidur bayi sampai ia tertidur.
            * Setiap beberapa malam, geser kursi Anda semakin jauh dari tempat tidur, hingga akhirnya Anda berada di luar pintu.
            * Ini metode paling lembut, tapi butuh waktu paling lama (bisa berminggu-minggu).
        
        Kuncinya adalah **Konsistensi**. Apa pun metode yang dipilih, Anda dan pasangan harus konsisten melakukannya setidaknya selama 1 minggu.
        
        ---
        
        **Sumber (Acuan):**
        1.  American Academy of Pediatrics (AAP). *Sleep Training Your Baby.*
        2.  Buku: *Solve Your Child's Sleep Problems* oleh Dr. Richard Ferber.
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Pola Asuh & Psikologi",
        "title": "Membesarkan Anak di Era Digital",
        "summary": "Tantangan dan strategi pengasuhan modern di tengah gempuran teknologi.",
        "source": "AAP",
        # URL Baru: Anak dengan gadget
        "image_url": "https://kimi-web-img.moonshot.cn/img/us.images.westend61.de/e1698918418c1b1f315b7bec64183e83ae06941d.jpg",
        "full_content": """
        # Mengasuh Anak di Era Digital
        
        Teknologi adalah alat. Seperti pisau, ia bisa bermanfaat di dapur atau berbahaya jika disalahgunakan. Mengajari anak menggunakan media digital secara bijak adalah keterampilan hidup yang penting di abad ke-21.
        
        ## Masalah: "Babysitter Digital"
        
        Tantangan terbesar adalah penggunaan gadget (HP/Tablet) sebagai "penenang" instan. Saat anak rewel atau tantrum, orang tua memberikan gadget agar anak diam.
        
        **Bahayanya:** Anak tidak pernah belajar cara mengelola emosi negatif (bosan, marah, sedih) secara mandiri. Mereka belajar bahwa "solusi untuk stres adalah lari ke layar". Ini dapat membentuk pola kecanduan di kemudian hari.
        
        ## Strategi Pengasuhan Digital (Rekomendasi AAP)
        
        American Academy of Pediatrics (AAP) merekomendasikan "Family Media Plan" (Rencana Media Keluarga).
        
        1.  **Buat Aturan yang Jelas:**
            * **"Kapan" boleh:** Misal, hanya di sore hari selama 1 jam.
            * **"Di mana" boleh:** Misal, hanya di ruang keluarga.
            * **Zona Bebas Layar:** Terapkan aturan "Tidak ada gadget di meja makan" dan "Tidak ada gadget di kamar tidur".
            * **Waktu Bebas Layar:** Minimal 1 jam sebelum tidur, gadget harus dimatikan untuk menjaga kualitas tidur.
        
        2.  **Orang Tua adalah Mentor, Bukan Sekadar Pengawas:**
            * **Dampingi (Co-View):** Tonton bersama anak. Tanyakan, "Apa yang kamu pelajari?", "Kenapa dia sedih?". Jadikan tontonan sebagai bahan diskusi.
            * **Pilih Konten Berkualitas:** Pilih aplikasi atau tontonan yang edukatif, interaktif, dan sesuai usia.
        
        3.  **Prioritaskan Aktivitas Offline:**
            * Pastikan waktu layar tidak menggantikan waktu esensial lainnya:
                * Tidur yang cukup.
                * Bermain aktif di luar ruangan.
                * Interaksi sosial tatap muka.
                * Membaca buku fisik.
        
        4.  **Jadilah Teladan (Role Model):**
            * Ini adalah bagian tersulit. Anak meniru apa yang Anda lakukan, bukan apa yang Anda katakan.
            * Tunjukkan kebiasaan digital yang sehat. Letakkan HP Anda saat berbicara dengan anak. Tunjukkan bahwa interaksi manusia lebih penting daripada notifikasi.
        
        ---
        
        **Sumber (Acuan):**
        1.  American Academy of Pediatrics (AAP). *Media and Children Communication Toolkit.*
        2.  American Academy of Pediatrics (AAP). *Family Media Plan.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Pola Asuh & Psikologi",
        "title": "Disiplin Positif: Menghargai Sambil Mengarahkan",
        "summary": "Cara mendisiplinkan anak tanpa perlu membentak, mengancam, atau memukul.",
        "source": "AAP | UNICEF",
        # URL Baru: Ibu dan anak (gentle parenting)
        "image_url": "https://kimi-web-img.moonshot.cn/img/www.prevea.com/720e0e1603c03c77fdad604118e8295ea70641de.jpg",
        "full_content": """
        # Disiplin Positif: Menghargai Sambil Mengarahkan
        
        Disiplin sering disalahartikan sebagai "hukuman". Padahal, akar kata disiplin adalah "murid" (*disciple*). Tujuan disiplin adalah **mengajar**, bukan menyakiti.
        
        Disiplin Positif adalah metode pengasuhan yang berfokus pada rasa saling menghargai dan mencari solusi bersama, tanpa menggunakan hukuman fisik atau verbal.
        
        ## Mengapa Hukuman (Bentakan/Pukulan) Tidak Efektif?
        
        * **Efek Jangka Pendek:** Bentakan mungkin membuat anak berhenti (karena takut), tapi ia tidak belajar *mengapa* perilakunya salah.
        * **Mengajarkan Hal yang Salah:** Mengajarkan anak bahwa "yang lebih besar dan kuat boleh menyakiti yang lebih kecil" atau "kekerasan adalah cara menyelesaikan masalah".
        * **Merusak Hubungan:** Menciptakan rasa takut, bukan rasa hormat. Anak mungkin akan berbohong di kemudian hari untuk menghindari hukuman.
        
        ## 5 Prinsip Kunci Disiplin Positif
        
        1.  **Validasi Emosi, Batasi Perilaku:**
            * "Mama tahu kamu marah, tapi kita tidak melempar mainan."
            * "Boleh merasa kesal, tapi kita tidak memukul adik."
        
        2.  **Koneksi Sebelum Koreksi (Connect Before Correct):**
            * Saat anak melakukan kesalahan, jangan langsung memarahinya.
            * Dekati anak, sejajarkan mata Anda, dan berikan sentuhan (jongkok, pegang bahunya).
            * Setelah anak merasa terhubung dan tenang, baru berikan arahan.
        
        3.  **Fokus pada Solusi, Bukan Hukuman:**
            * **Situasi:** Anak menumpahkan susu.
            * **Hukuman:** "Kamu ini! Tidak hati-hati! Mama hukum berdiri di pojok!"
            * **Disiplin Positif:** "Wah, susunya tumpah. Yuk kita ambil lap bersama untuk membersihkannya." (Mengajarkan tanggung jawab dan cara memperbaiki).
        
        4.  **Berikan Arahan Positif (Katakan Apa yang HARUS Dilakukan):**
            * **Negatif:** "Jangan lari-lari!" (Otak anak hanya mendengar "lari-lari").
            * **Positif:** "Tolong, jalan pelan-pelan ya."
            * **Negatif:** "Jangan teriak-teriak!"
            * **Positif:** "Tolong gunakan suara yang lebih pelan."
        
        5.  **Konsisten dan Sabar:**
            * Disiplin positif membutuhkan kesabaran yang luar biasa dari orang tua.
            * Anda tidak akan melihat hasil dalam satu malam, tetapi Anda sedang membangun fondasi karakter jangka panjang.
        
        ---
        
        **Sumber (Acuan):**
        1.  American Academy of Pediatrics (AAP). *Positive Discipline & Guidance for Children.*
        2.  UNICEF. *Positive Discipline in Everyday Parenting.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy berdasarkan panduan nasional dan internasional.*

        """
    },
    {
        "kategori": "Pola Asuh & Psikologi",
        "title": "Kapan Anak Siap 'Toilet Training'?",
        "summary": "Tanda-tanda kesiapan anak untuk belajar buang air di toilet.",
        "source": "AAP",
        # URL Baru: Kamar mandi bersih/anak cuci tangan
        "image_url": "https://kimi-web-img.moonshot.cn/img/www.nichd.nih.gov/ca85e11d01086a50846d14fc2726961804db6d28.jpg",
        "full_content": """
        # Kapan Anak Siap 'Toilet Training'?
        
        *Toilet training* (latih toilet) adalah proses besar bagi anak dan orang tua. Memulai terlalu dini saat anak belum siap hanya akan berakhir dengan stres dan kegagalan.
        
        **Tidak ada "usia emas" yang pasti.** Sebagian besar anak menunjukkan tanda kesiapan antara usia **18 bulan hingga 3 tahun**. Kesiapan fisik dan emosional lebih penting daripada usia.
        
        ## Tanda-Tanda Anak Siap
        
        Amati tanda-tanda berikut pada anak Anda:
        
        1.  **Kesiapan Fisik:**
            * Bisa berjalan dan berlari dengan stabil.
            * Popok tetap kering setidaknya selama 2 jam di siang hari (menunjukkan kandung kemihnya sudah bisa menahan).
            * Memiliki jadwal BAB yang teratur dan dapat diprediksi.
            * Bisa jongkok dan berdiri kembali.
        
        2.  **Kesiapan Kognitif (Pikiran):**
            * Bisa mengikuti perintah sederhana 1-2 langkah (misal: "Ambil mainanmu").
            * Memahami konsep "basah" dan "kering", "kotor" dan "bersih".
            * Bisa menunjuk bagian tubuh.
        
        3.  **Kesiapan Emosional & Bahasa:**
            * Menunjukkan minat ("Aku mau pipis di toilet seperti Papa/Mama").
            * Merasa tidak nyaman saat popoknya basah atau kotor (minta segera diganti).
            * Bisa memberi tahu Anda **sebelum** atau **saat** ia sedang pipis/BAB.
            * Menunjukkan tanda kemandirian ("Aku bisa sendiri").
        
        ## Tips Memulai Toilet Training
        
        * **Gunakan Pispot (Potty Chair):** Mulailah dengan pispot kecil di lantai, bukan langsung di toilet besar (yang mungkin menakutkan bagi anak).
        * **Biasakan:** Biarkan anak berkenalan dengan pispotnya. Ajak ia duduk di pispot (meskipun masih memakai popok) di waktu-waktu rutin (misal: setelah bangun tidur, setelah makan).
        * **Lepas Popok:** Saat latihan intensif di rumah, lepaskan popok anak dan gunakan celana latihan.
        * **Apresiasi, Bukan Hukuman:** Berikan pujian dan apresiasi (pelukan, tos) setiap kali ia berhasil (atau bahkan hanya *mencoba*) menggunakan pispot.
        * **Wajar Jika "Kecelakaan":** Jika anak mengompol, jangan memarahinya. Bersihkan tanpa drama dan katakan, "Lain kali kita coba ke pispot ya."
        
        Kunci sukses *toilet training* adalah **kesabaran** dan **waktu yang tepat**.
        
        ---
        
        **Sumber (Acuan):**
        1.  American Academy of Pediatrics (AAP). *Toilet Training: Signs of Readiness.*
        2.  Ikatan Dokter Anak Indonesia (IDAI). *Toilet Training pada Anak.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy)
        """
    },
    
    # ============================================================
    # KATEGORI: KEAMANAN & PENCEGAHAN
    # ============================================================
    {
        "kategori": "Keamanan & Pencegahan",
        "title": "Mencegah Sindrom Kematian Bayi Mendadak (SIDS)",
        "summary": "Panduan 'Back to Sleep' dan praktik tidur aman untuk bayi.",
        "source": "AAP | CDC",
        # URL Baru: Bayi tidur di crib (Safe sleep)
        "image_url": "https://kimi-web-img.moonshot.cn/img/www.thecapcenter.org/24162c46acf2f2ada993411c3114663893fe09d6.jpg",
        "full_content": """
        # Mencegah Sindrom Kematian Bayi Mendadak (SIDS)
        
        Sindrom Kematian Bayi Mendadak (SIDS) adalah kematian mendadak yang tidak dapat dijelaskan pada bayi di bawah usia 1 tahun. Meskipun penyebab pastinya tidak diketahui, ada langkah-langkah jelas untuk mengurangi risikonya.
        
        ## Kampanye 'Back to Sleep' (Tidur Telentang)
        
        Rekomendasi paling penting dari American Academy of Pediatrics (AAP) adalah:
        
        > **Bayi harus selalu ditidurkan dalam posisi TELENTANG (Back to Sleep) untuk setiap tidur (tidur malam dan tidur siang), hingga ia berusia 1 tahun.**
        
        * **Mengapa?** Tidur telentang menjaga jalan napas bayi tetap terbuka dan bersih.
        * **Bagaimana jika bayi berguling sendiri?** Jika bayi sudah bisa berguling dari telentang ke tengkurap dan sebaliknya dengan lancar, Anda tidak perlu membalikkannya kembali ke posisi telentang. Namun, tetap mulai tidur dalam posisi telentang.
        
        ## Lingkungan Tidur yang Aman (ABC)
        
        Ingat prinsip **A-B-C**:
        
        * **A = Alone (Sendirian):** Bayi harus tidur di area tidurnya sendiri.
        * **B = Back (Telentang):** Selalu tidurkan dalam posisi telentang.
        * **C = Crib (Tempat Tidur Bayi):** Gunakan tempat tidur bayi (crib), boks, atau bassinet yang memenuhi standar keamanan.
        
        ## Yang HARUS Dilakukan (Do's)
        
        1.  **Permukaan Rata & Keras:** Gunakan kasur yang keras dan rata, ditutup dengan sprei yang pas (tidak longgar).
        2.  **Room-Sharing (Bukan Bed-Sharing):** Letakkan tempat tidur bayi di kamar Anda (room-sharing) setidaknya selama 6 bulan pertama. Ini terbukti mengurangi risiko SIDS hingga 50%.
        3.  **Gunakan Empeng (Pacifier):** Menawarkan empeng saat tidur (setelah ASI mapan, sekitar 3-4 minggu) dapat mengurangi risiko SIDS.
        4.  **Jaga Suhu Kamar:** Jangan pakaikan baju terlalu tebal atau membuat kamar terlalu panas. Bayi tidak boleh kepanasan.
        
        ## Yang TIDAK BOLEH Dilakukan (Don'ts)
        
        1.  **JANGAN Bed-Sharing:** Jangan tidur bersama bayi di sofa, kursi, atau tempat tidur Anda. Risiko terhimpit atau sesak napas sangat tinggi.
        2.  **JANGAN Ada Benda Apapun di Boks:** Boks bayi harus **kosong**, kecuali bayi dan kasur + sprei pas.
            * **Tidak boleh** ada selimut longgar.
            * **Tidak boleh** ada bantal (termasuk bantal peyang).
            * **Tidak boleh** ada guling.
            * **Tidak boleh** ada mainan lunak (boneka).
            * **Tidak boleh** ada *crib bumpers* (pelindung tepi boks).
        3.  **JANGAN Merokok:** Jauhkan bayi dari paparan asap rokok (selama kehamilan dan setelah lahir).
        
        ---
        
        **Sumber (Acuan):**
        1.  American Academy of Pediatrics (AAP). *How to Keep Your Sleeping Baby Safe: AAP Policy Explained.*
        2.  Centers for Disease Control and Prevention (CDC). *Safe Sleep for Babies.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Keamanan & Pencegahan",
        "title": "Keamanan Rumah: Mencegah Anak Terjatuh",
        "summary": "Cara membuat rumah aman dari risiko jatuh (tangga, jendela, furnitur).",
        "source": "CDC | AAP",
        # URL Baru: Anak bermain di dalam ruangan
        "image_url": "https://kimi-web-img.moonshot.cn/img/www.dshs.texas.gov/7e8f9c426750bbf3d0b1bc4470c455175b584000.jpg",
        "full_content": """
        # Keamanan Rumah: Mencegah Anak Terjatuh
        
        Jatuh adalah penyebab utama cedera non-fatal pada balita. Saat anak mulai merangkak dan berjalan, rasa ingin tahu mereka menempatkan mereka pada risiko.
        
        ## 1. Keamanan Tangga
        
        * **Pagar Pengaman (Safety Gates):** Ini adalah wajib.
        * Pasang pagar pengaman yang **dipasang dengan baut/sekrup** (hardware-mounted) di **atas tangga**.
        * Pagar yang dipasang dengan tekanan (pressure-mounted) hanya boleh digunakan di **bawah tangga** atau antar ruangan.
        * Selalu tutup pagar, bahkan jika Anda hanya pergi sebentar.
        
        ## 2. Keamanan Jendela
        
        * **Jendela adalah Bahaya:** Jendela, bahkan yang tertutup kasa nyamuk, tidak aman. Kasa nyamuk tidak dirancang untuk menahan berat badan anak.
        * **Jaga Jarak Furnitur:** Jauhkan tempat tidur, kursi, dan furnitur lain dari jendela agar anak tidak bisa memanjat.
        * **Pasang Pelindung Jendela (Window Guards):** Ini adalah palang pengaman yang dipasang di jendela, menyisakan celah kecil yang tidak bisa dilewati anak.
        * **Pasang Window Stops:** Alat ini mencegah jendela dibuka lebih dari 10 cm.
        
        ## 3. Keamanan Furnitur (Mencegah Tertimpa)
        
        * **Jangkar Furnitur (Anchor It):** Ini sangat penting!
        * Gunakan *anti-tip brackets* atau *furniture anchors* (jangkar furnitur) untuk mengikat lemari buku, laci, dan TV ke dinding.
        * Furnitur yang berat (seperti TV tabung lama) di atas laci adalah risiko tinggi.
        * **Atur Laci:** Letakkan barang terberat di laci paling bawah. Jangan buka banyak laci sekaligus.
        
        ## 4. Tips Keamanan Lainnya
        
        * **Sudut Tajam:** Gunakan pelindung sudut (corner guards) pada meja kopi, meja TV, atau furnitur dengan sudut tajam.
        * **Lantai:** Jaga lantai tetap kering dan bebas dari mainan atau kabel yang berserakan (bahaya tersandung).
        * **Kamar Mandi:** Gunakan matras anti-slip di dalam bak mandi/shower dan di lantai kamar mandi.
        
        ---
        
        **Sumber (Acuan):**
        1.  Centers for Disease Control and Prevention (CDC). *Preventing Falls in Children.*
        2.  American Academy of Pediatrics (AAP). *Making Your Home Safe for Baby.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Keamanan & Pencegahan",
        "title": "Mencegah Keracunan pada Anak",
        "summary": "Cara menyimpan obat, produk pembersih, dan zat berbahaya lainnya.",
        "source": "CDC | Kemenkes RI",
        # URL Baru: Bahan pembersih (Safety warning)
        "image_url": "https://kimi-web-img.moonshot.cn/img/media.sciencephoto.com/4378c3744ef590668df10323a4e4d2e8fa02a88d.jpg",
        "full_content": """
        # Keamanan Rumah: Mencegah Keracunan pada Anak
        
        Balita mengeksplorasi dunia dengan memasukkan segala sesuatu ke dalam mulut mereka. Mencegah akses ke zat beracun adalah kunci utama.
        
        ## 1. Simpan di Tempat Tinggi dan Terkunci
        
        Aturan utama: **"Up and Away"** (Tinggi dan Jauh).
        
        * **Obat-obatan:** Simpan SEMUA obat (termasuk vitamin, suplemen, obat herbal) di lemari yang tinggi dan **terkunci**. Jangan pernah menyimpannya di meja samping tempat tidur atau di dalam tas.
        * **Produk Pembersih:** Simpan deterjen, pembersih lantai, pemutih, dan bahan kimia rumah tangga di lemari yang tinggi dan terkunci, idealnya jauh dari dapur.
        * **Racun Lainnya:** Termasuk kosmetik, cat, pestisida, dan baterai kancing (sangat berbahaya jika tertelan).
        
        ## 2. Selalu Simpan di Wadah Asli
        
        * **JANGAN** memindahkan cairan pembersih ke botol air mineral bekas. Anak mungkin mengiranya minuman.
        * Selalu simpan produk dalam kemasan aslinya dengan label yang jelas.
        * Pastikan tutup pengaman (child-resistant caps) selalu tertutup rapat.
        
        ## 3. Bahaya yang Sering Terlewat
        
        * **Tas Tangan:** Tas tamu atau tas Anda sendiri mungkin berisi obat-obatan, kosmetik, atau permen karet nikotin. Jauhkan tas dari jangkauan anak.
        * **Baterai Kancing (Button Batteries):** Sangat berbahaya. Jika tertelan, dapat menyebabkan luka bakar kimia parah di kerongkongan dalam waktu 2 jam. Simpan alat (remote, mainan) yang menggunakan baterai ini jauh dari jangkauan.
        * **Deterjen Pod (Cair Kapsul):** Terlihat seperti permen. Simpan di wadah tertutup rapat dan tinggi.
        * **Tanaman Hias:** Beberapa tanaman hias (seperti Philodendron, Dieffenbachia) beracun jika dimakan. Cari tahu keamanan tanaman Anda.
        
        ## 4. Jika Terjadi Keracunan
        
        * **Tetap Tenang.** Ambil produk yang dicurigai dari anak.
        * **Jangan Paksa Muntah:** Memaksa muntah (misal: dengan air garam atau memasukkan jari) bisa lebih berbahaya.
        * **Segera ke UGD:** Bawa anak dan sisa produk (atau kemasannya) ke Unit Gawat Darurat (UGD) terdekat.
        
        ---
        
        **Sumber (Acuan):**
        1.  Centers for Disease Control and Prevention (CDC). *Poison Proof Your Home.*
        2.  Kementerian Kesehatan RI. *Pedoman Pencegahan Keracunan di Rumah Tangga.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Keamanan & Pencegahan",
        "title": "Mencegah Anak Tenggelam (Drowning)",
        "summary": "Bahaya tenggelam di bak mandi, ember, dan kolam renang.",
        "source": "WHO | AAP",
        # URL Baru: Mandi bayi (Bath time safety)
        "image_url": "https://kimi-web-img.moonshot.cn/img/media.istockphoto.com/b85d954734a34a89df1e9ef86b81a27d02e61a94.jpg",
        "full_content": """
        # Mencegah Anak Tenggelam (Drowning)
        
        Tenggelam adalah penyebab utama kematian akibat cedera pada anak usia 1-4 tahun. Tenggelam bisa terjadi **dengan cepat (kurang dari 2 menit)** dan **tanpa suara**, di air sedalam beberapa sentimeter saja.
        
        ## Bahaya di Dalam Rumah
        
        Anak kecil paling sering tenggelam di dalam rumah. Waspadai:
        
        1.  **Bak Mandi (Bathtub):**
            * **JANGAN PERNAH** meninggalkan bayi atau balita sendirian di bak mandi, bahkan "hanya sedetik" untuk mengambil handuk.
            * Jika Anda harus meninggalkan kamar mandi, **bawa anak Anda** (bungkus dengan handuk).
            * Selalu kosongkan bak mandi segera setelah selesai digunakan.
        
        2.  **Ember dan Bak Air:**
            * Ember berisi air (untuk mengepel atau menampung air hujan) sangat berbahaya. Balita bisa terjatuh dengan kepala lebih dulu ke dalam ember dan tidak bisa keluar.
            * **Selalu kosongkan ember** dan balikkan saat tidak digunakan.
        
        3.  **Toilet:**
            * Selalu tutup penutup toilet. Gunakan kunci pengaman toilet (toilet lock) jika perlu.
        
        ## Bahaya di Luar Rumah (Kolam Renang)
        
        Jika Anda memiliki atau mengunjungi rumah dengan kolam renang:
        
        1.  **Pagar 4 Sisi:** Kolam harus dikelilingi pagar 4 sisi (memisahkan kolam dari rumah) yang tingginya minimal 1,2 meter.
        2.  **Pintu Pagar:** Pintu pagar harus bisa menutup dan mengunci sendiri (self-closing and self-latching), dengan kunci di bagian atas (di luar jangkauan anak).
        3.  **Alarm:** Pasang alarm di pintu yang menuju ke area kolam.
        
        ## Pengawasan adalah Kunci
        
        * **Pengawasan Aktif:** Saat anak berada di dekat air, pengawasan berarti **sentuhan konstan** (touch supervision). Anda harus cukup dekat untuk bisa menyentuh anak.
        * **Jangan Terdistraksi:** Jangan bermain HP, membaca buku, atau mengobrol. Fokus 100% pada anak.
        
        ---
        
        **Sumber (Acuan):**
        1.  World Health Organization (WHO). *Drowning - Fact Sheet.*
        2.  American Academy of Pediatrics (AAP). *Prevent Drowning.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Keamanan & Pencegahan",
        "title": "Mencegah Luka Bakar pada Anak",
        "summary": "Menjaga keamanan di dapur, bahaya air panas, dan stopkontak.",
        "source": "WHO | IDAI",
        # URL Baru: Dapur (Kitchen safety)
        "image_url": "https://kimi-web-img.moonshot.cn/img/riverwoodhealthcare.org/65152ba7d00c5d3902914207d72041485fa8540f.jpg",
        "full_content": """
        # Mencegah Luka Bakar pada Anak
        
        Kulit bayi dan balita jauh lebih tipis daripada kulit dewasa, sehingga mereka bisa terbakar pada suhu yang lebih rendah dan dalam waktu yang lebih singkat. Luka bakar air panas (scalding) adalah yang paling umum.
        
        ## 1. Keamanan Dapur
        
        Dapur adalah area paling berbahaya untuk luka bakar.
        
        * **Jadikan Zona Terlarang:** Idealnya, jadikan dapur sebagai zona "dilarang bermain" untuk balita, terutama saat Anda memasak. Gunakan pagar pengaman jika perlu.
        * **Gagang Panci:** Selalu putar gagang panci ke arah **belakang kompor**, jangan menghadap ke depan.
        * **Kompor:** Gunakan tungku bagian belakang terlebih dahulu.
        * **Kabel Peralatan:** Jangan biarkan kabel (rice cooker, teko listrik, setrika) menggantung di tepi meja.
        
        ## 2. Bahaya Cairan Panas (Scalds)
        
        * **Kopi/Teh/Sup:** **JANGAN PERNAH** menggendong anak sambil memegang minuman atau makanan panas.
        * **Taplak Meja:** Jangan gunakan taplak meja. Anak dapat menariknya dan menumpahkan cairan panas di atasnya.
        * **Microwave:** Aduk rata makanan yang dipanaskan di microwave, karena bisa ada "hot spots" (titik panas) yang tidak merata.
        
        ## 3. Keamanan Air Mandi
        
        * **Atur Pemanas Air (Water Heater):** Atur suhu maksimal pemanas air Anda di 49°C (120°F) atau lebih rendah.
        * **Tes Suhu:** Selalu tes suhu air dengan siku atau pergelangan tangan Anda sebelum memasukkan bayi ke bak mandi. Air harus terasa hangat, bukan panas.
        * **Urutan Mengisi:** Isi bak dengan air dingin dulu, baru tambahkan air panas. Aduk rata.
        
        ## 4. Keamanan Listrik
        
        * **Tutup Stopkontak:** Gunakan penutup pengaman (outlet covers) pada semua stopkontak yang tidak terpakai.
        * **Kabel:** Periksa kabel dari kerusakan. Sembunyikan kabel di belakang furnitur.
        
        ---
        
        **Sumber (Acuan):**
        1.  World Health Organization (WHO). *Burns - Fact Sheet.*
        2.  Ikatan Dokter Anak Indonesia (IDAI). *Mencegah Luka Bakar pada Anak.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Keamanan & Pencegahan",
        "title": "Keamanan di Mobil (Car Seat)",
        "summary": "Pentingnya penggunaan 'car seat' yang benar sesuai usia.",
        "source": "AAP | WHO",
        # URL Baru: Car Seat
        "image_url": "https://kimi-web-img.moonshot.cn/img/www.shutterstock.com/d4e16fdd245154cbfe34b0bef92fc619b932a9a1.jpg",
        "full_content": """
        # Keamanan di Mobil (Car Seat)
        
        Kecelakaan lalu lintas adalah salah satu penyebab utama kematian pada anak. Penggunaan *car seat* (kursi pengaman mobil) yang benar adalah cara terbaik untuk melindungi anak Anda.
        
        **Fakta Penting:** Menggendong anak di pangkuan Anda **tidak aman**. Saat terjadi benturan, Anda tidak akan mampu menahan anak.
        
        ## Tahap 1: Rear-Facing (Menghadap Belakang)
        
        * **Siapa:** Dari baru lahir hingga usia 2-4 tahun (atau selama mungkin).
        * **Aturan:** Anak harus tetap menghadap belakang **sampai ia mencapai batas berat atau tinggi maksimal** yang diizinkan oleh produsen *car seat* tersebut.
        * **Mengapa?** Posisi menghadap belakang adalah yang paling aman. Ini melindungi kepala, leher, dan tulang belakang bayi yang masih rapuh saat terjadi benturan.
        * **Kaki Menekuk?** Tidak masalah jika kaki anak tampak menekuk. Itu jauh lebih aman daripada risiko cedera leher.
        
        ## Tahap 2: Forward-Facing (Menghadap Depan)
        
        * **Siapa:** Setelah anak melebihi batas *rear-facing*.
        * **Aturan:** Gunakan *car seat* menghadap depan dengan 5-point harness (sabuk 5 titik) sampai anak mencapai batas berat atau tinggi *car seat* (biasanya sekitar 25-30 kg).
        
        ## Tahap 3: Booster Seat
        
        * **Siapa:** Setelah anak melebihi batas *forward-facing harness*.
        * **Aturan:** Gunakan *booster seat* agar sabuk pengaman mobil (seat belt) pas di tubuh anak (melintang di dada, bukan leher; dan di pinggul, bukan perut).
        
        ## Poin Penting Lainnya
        
        * **Kursi Belakang:** Semua anak di bawah usia 13 tahun harus duduk di **kursi belakang**.
        * **Pemasangan yang Benar:** Baca buku panduan *car seat* DAN buku panduan mobil Anda. *Car seat* yang tidak dipasang dengan benar tidak akan melindungi anak.
        * **JANGAN Gunakan Car Seat Bekas:** Jangan gunakan *car seat* bekas jika Anda tidak tahu riwayatnya (misal: pernah kecelakaan) atau jika sudah kedaluwarsa.
        
        ---
        
        **Sumber (Acuan):**
        1.  American Academy of Pediatrics (AAP). *Car Seats: Information for Families.*
        2.  World Health Organization (WHO). *Road traffic injuries - Child safety.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    },
    {
        "kategori": "Keamanan & Pencegahan",
        "title": "Pencegahan Gigitan Nyamuk (Demam Berdarah)",
        "summary": "Cara melindungi bayi dari gigitan nyamuk Aedes aegypti.",
        "source": "IDAI | CDC",
        # URL Baru: Alam terbuka/hijau (Simbolis lingkungan)
        "image_url": "https://kimi-web-img.moonshot.cn/img/i.pinimg.com/c15b12050424847ac6e2e2d66938e62645738538.jpg",
        "full_content": """
        # Pencegahan Gigitan Nyamuk (Demam Berdarah & Lainnya)
        
        Bayi dan balita sangat rentan terhadap gigitan nyamuk, yang tidak hanya gatal tetapi juga bisa menularkan penyakit berbahaya seperti Demam Berdarah Dengue (DBD), Chikungunya, dan Zika (semua ditularkan oleh nyamuk *Aedes aegypti*).
        
        ## 1. Perlindungan Lingkungan (Pemberantasan Sarang Nyamuk)
        
        Ini adalah langkah terpenting. Nyamuk *Aedes aegypti* berkembang biak di air jernih yang tergenang. Lakukan **3M Plus**:
        
        * **Menguras:** Kuras bak mandi, tempat penampungan air, dan vas bunga minimal seminggu sekali.
        * **Menutup:** Tutup rapat semua tempat penampungan air.
        * **Mengubur/Mendaur Ulang:** Kubur barang bekas yang bisa menampung air (ban bekas, kaleng).
        * **Plus:**
            * Pasang kawat kasa di ventilasi dan jendela.
            * Pelihara ikan pemakan jentik (jika punya kolam).
            * Hindari menggantung baju bekas pakai terlalu lama (disukai nyamuk).
        
        ## 2. Perlindungan Fisik (Pakaian & Kelambu)
        
        * **Kelambu:** Cara teraman melindungi bayi saat tidur (siang dan malam). Pasang kelambu di tempat tidur bayi atau *stroller*.
        * **Pakaian:** Pakaikan anak pakaian lengan panjang dan celana panjang yang longgar dan berwarna terang, terutama saat beraktivitas di luar rumah pada jam "sibuk" nyamuk (pagi dan sore hari).
        
        ## 3. Perlindungan Kimia (Repellent / Losion Anti Nyamuk)
        
        Gunakan *repellent* dengan hati-hati pada bayi.
        
        * **Usia < 2 Bulan:** **JANGAN** gunakan *repellent* dalam bentuk apa pun. Hanya gunakan perlindungan fisik (kelambu, pakaian).
        
        * **Usia > 2 Bulan:**
            * **Pilih Bahan yang Aman:**
                * **DEET:** Konsentrasi 10-30%. Sangat efektif. (Rekomendasi AAP & CDC).
                * **Picaridin:** Konsentrasi 5-20%.
                * **Minyak Alami (Eucalyptus, Citronella):** Kurang efektif, harus lebih sering dioleskan ulang, dan **tidak direkomendasikan** untuk bayi di bawah 3 tahun karena risiko iritasi.
            * **Cara Pemakaian yang Benar:**
                1.  **JANGAN** semprotkan/oleskan di tangan, mata, atau mulut bayi.
                2.  **JANGAN** oleskan di kulit yang luka atau iritasi.
                3.  **SEMPROTKAN DI TANGAN ANDA** terlebih dahulu, baru oleskan tipis-tipis ke kulit bayi yang terbuka (hindari area wajah dan tangan).
                4.  Cuci tangan Anda setelah mengoleskan.
                5.  Segera cuci kulit bayi dengan sabun dan air setelah kembali ke dalam ruangan.
        
        ---
        
        **Sumber (Acuan):**
        1.  Ikatan Dokter Anak Indonesia (IDAI). *Melindungi Anak dari Gigitan Nyamuk.*
        2.  Centers for Disease Control and Prevention (CDC). *Prevent Mosquito Bites.*
        
        *Artikel ini adalah rangkuman edukasi yang disintesis oleh Tim PeduliGiziBalita (Author: Habib Arsy) berdasarkan panduan nasional dan internasional.*
        """
    }
] # END OF ARTIKEL_LOKAL_DATABASE

# ================================================
# FUNGSI HELPER BARU UNTUK PERPUSTAKAAN & API
# (Tambahkan ini di SECTION 10B, setelah database artikel)
# ================================================

def get_local_library_filters():
    """
    (FUNGSI BARU - MEMPERBAIKI BUG API)
    Helper untuk mengambil kategori & sumber unik dari DB lokal.
    """
    categories = set()
    sources = set()
    for art in ARTIKEL_LOKAL_DATABASE:
        if art.get("kategori"):
            categories.add(art.get("kategori"))
        if art.get("source"):
            for s in art.get("source").split("|"):
                s = s.strip()
                if s:
                    sources.add(s)
    # Mengembalikan list kategori yang unik dan sudah diurutkan
    return sorted(list(categories)), sorted(list(sources))

def get_library_categories_list():
    """ (FUNGSI BARU) Mengambil daftar kategori untuk dropdown Gradio """
    categories, _ = get_local_library_filters()
    return ["Semua Kategori"] + categories

# ===================================================================
# GANTI FUNGSI 'update_library_display' & 'load_initial_articles'
# DI SECTION 10B DENGAN KODE BARU INI
# ===================================================================

def update_library_display(search_term: str, category: str):
    """
    (REVISI UI v3.2.5 - MEMPERBAIKI INDEKS CSS)
    Fungsi ini sekarang menggunakan 'idx' ASLI dari database.
    """
    search_term = search_term.lower().strip()
    
    # --- PERBAIKAN DATABASE DUPLIKAT ---
    # Kita hanya ambil 40 artikel pertama untuk menghindari duplikat
    # Dan kita enumerate DATABASE ASLI
    articles_to_process = ARTIKEL_LOKAL_DATABASE[:40] 
    
    filtered_articles = []
    
    # Gunakan enumerate PADA DATABASE ASLI
    for idx, art in enumerate(articles_to_process): 
        
        # --- MULAI FILTER ---
        if category != "Semua Kategori" and art.get("kategori") != category:
            continue
        
        title = art.get("title", "").lower()
        summary = art.get("summary", "").lower()
        content = art.get("full_content", "").lower()
        
        if search_term and not (search_term in title or search_term in summary or search_term in content):
            continue
        # --- AKHIR FILTER ---
            
        # Simpan artikel DAN INDEKS ASLINYA
        filtered_articles.append((idx, art)) 

    if not filtered_articles:
        return "<div style='padding: 20px; text-align: center;'><h3>🔍 Tidak ada artikel ditemukan</h3><p>Coba ganti kata kunci pencarian atau filter kategori Anda.</p></div>"

    html_output_list = []
    html_output_list.append(f"<p style='text-align:center; font-weight:bold; color:#333;'>Menampilkan {len(filtered_articles)} artikel:</p>")
    html_output_list.append("<div class='library-grid-container'>")
    
    # Loop melalui artikel yang sudah difilter
    # 'idx' di sini adalah INDEKS ASLI (0-39)
    for idx, art in filtered_articles:
        
        title_safe = art.get('title', 'Tanpa Judul').replace('<', '&lt;').replace('>', '&gt;')
        summary_safe = art.get('summary', '').replace('<', '&lt;').replace('>', '&gt;')
        kategori_safe = art.get('kategori', 'N/A').replace('<', '&lt;').replace('>', '&gt;')
        source_safe = art.get('source', 'N/A').replace('<', '&lt;').replace('>', '&gt;')
        
        # --- PERBAIKAN KONTEN HTML (REGEX FIX) ---
        content_html = art.get('full_content', 'Konten tidak tersedia.')
        content_html = content_html.replace('\n\n', '</p><p>')
        content_html = content_html.replace('---', '<hr style="margin: 15px 0; border: 0; border-top: 1px solid #eee;">')
        content_html = content_html.replace('\n', '<br>')
        content_html = content_html.replace('# ', '<h2>')
        content_html = content_html.replace('## ', '<h3>')
        content_html = content_html.replace('### ', '<h4>')
        
        import re
        content_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content_html)
        
        # Perbaikan regex list (lebih kuat)
        # Ubah baris yang dimulai dengan '* ' menjadi <li>...</li>
        content_html = re.sub(r'(<br>|^)\* (.*?)(<br>|$)', r'\1<li>\2</li>', content_html)
        # Hapus <br> ekstra di antara <li>
        content_html = content_html.replace('</li><br><li>', '</li><li>') 
        # Bungkus grup <li> dengan <ul>
        content_html = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', content_html, flags=re.DOTALL)
        # Bersihkan <ul> ganda
        content_html = content_html.replace('</ul><br><ul>', '')
        content_html = content_html.replace('</p><br><ul>', '</p><ul>')
        content_html = content_html.replace('</ul><br><p>', '</ul><p>')

        
        html_output_list.append(f"""
        <div class="article-card-v3-2-3">
            
            <div class="article-image article-img-{idx}"></div>
            
            <div class="article-summary-content">
                <span class="article-category">{kategori_safe}</span>
                <h3 class="article-title">{title_safe}</h3>
                <p class="article-summary">{summary_safe}</p>
            </div>
            
            <details class="article-details-dropdown">
                <summary class="article-details-toggle">Baca Selengkapnya</summary>
                <div class="article-full-content-wrapper">
                    {content_html}
                    <span class="article-source">Sumber: {source_safe}</span>
                </div>
            </details>
            
        </div>
        """)

    html_output_list.append("</div>")
    return "".join(html_output_list)


def load_initial_articles():
    """ (PERBAIKAN #4) Memuat semua artikel (versi perbaikan indeks) """
    return update_library_display(search_term="", category="Semua Kategori")


def load_initial_articles():
    """ (PERBAIKAN #3) Memuat semua artikel sebagai string HTML """
    # Fungsi ini tidak perlu diubah, karena sudah memanggil update_library_display
    return update_library_display(search_term="", category="Semua Kategori")




print(f"✅ Section 10B v3.2.2 loaded: 40 Artikel Lokal (Internal) siap digunakan.")



    









    






# =========================================
# SECTION 10B – Perpustakaan Ibu Balita
# Styling global (CSS saja, tanpa JS bridge)
# =========================================






    

    
    


# ===============================================================================
# ===============================================================================
# SECTION 11: GRADIO UI (REVISI TOTAL - Perbaikan Perpustakaan)
# ===============================================================================

# UPDATED Custom CSS (v3.2.3)
# CSS Perpustakaan lama (penyebab error) telah dihapus.
CUSTOM_CSS = """
/* ===================================================================
   GLOBAL STYLES
   =================================================================== */

.gradio-container {
    font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
}

/* ===================================================================
   DARK MODE OPTIMIZATION - HIGH CONTRAST (v3.1)
   =================================================================== */

@media (prefers-color-scheme: dark) {
    .gradio-container { color: #f0f0f0 !important; }
    h1, h2, h3, h4, h5, h6 { color: #ffffff !important; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }
    p, span, div, label { color: #e8e8e8 !important; }
    .gr-input, .gr-textbox, .gr-box, .gr-form { background-color: #2d2d2d !important; color: #ffffff !important; border-color: #505050 !important; }
    .gr-input::placeholder { color: #999999 !important; }
    .gr-button { background-color: #404040 !important; color: #ffffff !important; border-color: #606060 !important; }
    .gr-button:hover { background-color: #505050 !important; border-color: #707070 !important; }
    .gr-button-primary { background: linear-gradient(135deg, #ff6b9d 0%, #ff9a9e 100%) !important; color: #ffffff !important; font-weight: 600 !important; border: none !important; }
    .gr-button-secondary { background: linear-gradient(135deg, #4ecdc4 0%, #6de0d9 100%) !important; color: #ffffff !important; font-weight: 600 !important; border: none !important; }
    
    /* Perbaikan Dark Mode untuk Accordion (Perpustakaan Baru) */
    .gr-panel, .gr-box, .gr-accordion { background-color: #2a2a2a !important; border-color: #505050 !important; color: #e8e8e8 !important; }
    .gr-accordion .label-wrap { background-color: #3a3a3a !important; }
    .gr-accordion .label-wrap:hover { background-color: #4a4a4a !important; }
    
    .gr-tab { background-color: #333333 !important; color: #ffffff !important; border-color: #505050 !important; }
    .gr-tab.selected { background-color: #ff6b9d !important; color: #ffffff !important; font-weight: 600 !important; }
    .markdown-body { color: #e8e8e8 !important; }
    .markdown-body h1, .markdown-body h2, .markdown-body h3 { color: #ffffff !important; border-bottom-color: #505050 !important; }
    .markdown-body a { color: #6db4ff !important; }
    .markdown-body code { background-color: #1e1e1e !important; color: #d4d4d4 !important; border-color: #404040 !important; }
    .markdown-body pre { background-color: #1e1e1e !important; border-color: #404040 !important; }
    .status-success { color: #5cff5c !important; }
    .status-warning { color: #ffd45c !important; }
    .status-error { color: #ff5c5c !important; }
    .premium-gold { background: linear-gradient(135deg, #b8860b 0%, #daa520 100%) !important; color: #ffffff !important; border: 2px solid #b8860b !important; }
    .premium-silver { background: linear-gradient(135deg, #787878 0%, #a0a0a0 100%) !important; color: #ffffff !important; border: 2px solid #787878 !important; }
    .article-card { background-color: #2a2a2a !important; border: 1px solid #505050 !important; color: #e8e8e8 !important; }
    .article-card:hover { background-color: #353535 !important; border-color: #606060 !important; box-shadow: 0 4px 12px rgba(255,255,255,0.1) !important; }
    .article-title { color: #ffffff !important; }
    .article-meta { color: #b0b0b0 !important; }
    
    /* CSS Perpustakaan lama (penyebab error) telah dihapus */
}

/* ===================================================================
   LIGHT MODE (Default)
   =================================================================== */

.status-success { color: #28a745 !important; font-weight: 600; }
.status-warning { color: #ffc107 !important; font-weight: 600; }
.status-error { color: #dc3545 !important; font-weight: 600; }

.big-button {
    font-size: 18px !important; padding: 20px 40px !important; margin: 15px 0 !important;
    border-radius: 12px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    transition: all 0.3s ease !important;
}
.big-button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important; }

.premium-silver {
    background: linear-gradient(135deg, #C0C0C0 0%, #E8E8E8 100%) !important; color: #333 !important;
    border: 2px solid #A0A0A0 !important; font-weight: bold !important; padding: 15px 30px !important;
    border-radius: 10px !important; transition: all 0.3s ease !important;
}
.premium-gold {
    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%) !important; color: #000 !important;
    border: 2px solid #DAA520 !important; font-weight: bold !important; padding: 15px 30px !important;
    border-radius: 10px !important; box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4) !important;
    transition: all 0.3s ease !important;
}
.premium-gold:hover { transform: scale(1.05) !important; box-shadow: 0 6px 20px rgba(255, 215, 0, 0.6) !important; }

/* ===================================================================
   VIDEO CARDS (v3.1)
   =================================================================== */

.video-card {
    background: linear-gradient(135deg, #fff5f8 0%, #ffe8f0 100%); border: 2px solid #ffd4e0;
    border-radius: 12px; padding: 15px; margin: 10px 0; transition: all 0.3s ease;
}
.video-card:hover { transform: scale(1.02); box-shadow: 0 6px 15px rgba(255, 107, 157, 0.2); border-color: #ff6b9d; }
.video-title { font-size: 16px; font-weight: 700; color: #ff6b9d; margin-bottom: 8px; }
.video-description { font-size: 13px; color: #666; margin-bottom: 10px; }
.video-duration { font-size: 12px; color: #999; font-style: italic; }

/* ===================================================================
   PERPUSTAKAAN INTERAKTIF (BARU v3.2.3) - DIHAPUS
   =================================================================== */
/* Semua CSS .library-filter-bar, .article-card-v3, dll. telah dihapus */


/* ===================================================================
   OTHER COMPONENTS
   =================================================================== */

.gr-input, .gr-textbox {
    border-radius: 8px !important; border: 2px solid #e8e8e8 !important;
    transition: border-color 0.3s ease !important;
}
.gr-input:focus, .gr-textbox:focus {
    border-color: #ff6b9d !important;
    box-shadow: 0 0 0 3px rgba(255, 107, 157, 0.1) !important;
}
.gr-panel, .gr-box {
    border-radius: 12px !important; border: 1px solid #e8e8e8 !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
}
.gr-tab { border-radius: 8px 8px 0 0 !important; font-weight: 600 !important; }
.gr-plot {
    border-radius: 12px !important; overflow: hidden !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}
blockquote {
    background: linear-gradient(135deg, #fff5f8 0%, #ffe8f0 100%);
    border-left: 6px solid #ff6b9d; padding: 20px; margin: 20px 0;
    border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.notification-panel {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px; border-radius: 15px; color: white; margin: 15px 0;
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}
.notification-enabled {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    padding: 15px; border-radius: 10px; color: white;
    text-align: center; font-weight: bold; margin: 10px 0;
}
# ===============================================================================
# SECTION 11: GRADIO UI (REVISI TOTAL - Perbaikan Perpustakaan)
# ===============================================================================

# ... (Pastikan semua CSS Anda yang ada sebelumnya tetap di sini) ...
# ... (Termasuk .gradio-container, DARK MODE, .video-card, dll.) ...

# TAMBAHKAN BLOK CSS BARU INI
# ===================================================================
# PERPUSTAKAAN v3.2.3 (MODERN UI REVISION - DENGAN GAMBAR)
# ===================================================================
.library-grid-container {
    /* Ini adalah wrapper yang akan dibuat oleh fungsi Python */
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 24px;
    padding: 10px 0;
}

.article-card-v3-2-3 {
    background: #ffffff;
    border-radius: 16px;
    border: 1px solid #e8e8e8;
    margin-bottom: 0; /* Diatur oleh grid-gap */
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    overflow: hidden; /* Penting untuk image border-radius */
    transition: all 0.3s ease;
    display: flex;
    flex-direction: column; /* Mengatur layout card */
    height: 100%; /* Membuat kartu sama tinggi di grid */
}
.article-card-v3-2-3:hover {
    box-shadow: 0 7px 20px rgba(0,0,0,0.08);
    transform: translateY(-3px);
}
.article-image {
    width: 100%;
    height: 180px; /* Ukuran pas untuk card */
    background-size: cover; /* GANTI DARI object-fit */
    background-position: center center; /* TAMBAHKAN INI */
    background-repeat: no-repeat; /* TAMBAHKAN INI */
    border-bottom: 1px solid #eee;
}
.article-summary-content {
    padding: 20px;
    flex-grow: 1; /* Mendorong dropdown ke bawah */
}
.article-category {
    display: inline-block;
    background: #fff5f8;
    color: #ff6b9d;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 12px;
    border: 1px solid #ffdde5;
}
.article-title {
    font-size: 18px; /* Ukuran pas untuk card mobile */
    font-weight: 700;
    color: #2c3e50;
    margin: 0 0 8px 0;
    line-height: 1.4; /* Keterbacaan */
}
.article-summary {
    font-size: 14px; /* Font mobile-friendly */
    color: #555;
    line-height: 1.6;
    margin: 0;
}
.article-details-dropdown {
    border-top: 1px solid #f0f0f0;
    margin-top: auto; /* Mendorong ke bagian bawah card */
}
.article-details-toggle {
    padding: 16px 20px;
    cursor: pointer;
    font-size: 15px;
    font-weight: 600;
    color: #3498db;
    list-style: none; /* Hapus panah default */
    transition: background 0.2s ease;
    display: block; /* Agar full width */
    text-align: center;
}
.article-details-toggle:hover {
    background: #f9f9f9;
}
/* Style panah custom (mudah dilihat) */
.article-details-toggle::before {
    content: '▼';
    margin-right: 10px;
    font-size: 12px;
    display: inline-block;
    transition: transform 0.2s ease;
}
.article-details-toggle {
    list-style-type: none; /* Menghilangkan panah default di semua browser */
}
details[open] > .article-details-toggle::before {
    transform: rotate(-180deg);
}
.article-full-content-wrapper {
    padding: 0 20px 20px 20px;
    line-height: 1.7; /* Font mudah dibaca */
    color: #333;
    font-size: 15px; /* Font mobile-friendly */
    background: #fafafa;
}
.article-full-content-wrapper h2,
.article-full-content-wrapper h3,
.article-full-content-wrapper h4 {
    color: #2c3e50;
    margin-top: 20px;
}
.article-full-content-wrapper ul,
.article-full-content-wrapper ol {
    padding-left: 25px;
}
.article-full-content-wrapper li {
    margin-bottom: 10px;
}
.article-full-content-wrapper strong {
    color: #ff6b9d; /* Highlight poin penting */
}
.article-source {
    font-size: 13px;
    color: #666;
    font-style: italic;
    display: block;
    margin-top: 15px;
    background: #f0f0f0;
    padding: 10px;
    border-radius: 8px;
}

/* =================================================================== */
/* PERPUSTAKAAN v3.2.4 - IMAGE URLS (STATIC IN CSS) */
/* =================================================================== */
.article-img-0 { background-image: url('https://images.unsplash.com/photo-1600857592429-06388147aa0e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-1 { background-image: url('https://images.unsplash.com/photo-1544385191-a8d83c0c0910?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-2 { background-image: url('https://images.unsplash.com/photo-1519733224424-a78932641e1c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-3 { background-image: url('https://images.unsplash.com/photo-1591160623347-0622c71a3a2d?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-4 { background-image: url('https://images.unsplash.com/photo-1606823354313-a4f1232c4533?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-5 { background-image: url('https://images.unsplash.com/photo-1589139121857-a5735161394a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-6 { background-image: url('https://images.unsplash.com/photo-1598993685548-e0420d75765d?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-7 { background-image: url('https://images.unsplash.com/photo-1582235880501-f2e519c636ce?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-8 { background-image: url('https://images.unsplash.com/photo-1604719212028-a3d1d236369c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-9 { background-image: url('https://images.unsplash.com/photo-1558220938-f91d0a3311c3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-10 { background-image: url('https://images.unsplash.com/photo-1518610368143-69091b3ab806?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-11 { background-image: url('https://images.unsplash.com/photo-1546015026-6132b138026d?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-12 { background-image: url('https://images.unsplash.com/photo-1519062136015-659f0f633d3b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-13 { background-image: url('https://images.unsplash.com/photo-1518717758339-39B3c607eb42?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-14 { background-image: url('https://images.unsplash.com/photo-1546820389-0822369cbf34?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-15 { background-image: url('https://images.unsplash.com/photo-1519362351240-d69b552f5071?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-16 { background-image: url('https://images.unsplash.com/photo-1557941733-27d6dbb8b209?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-17 { background-image: url('https://plus.unsplash.com/premium_photo-1664301530062-83b33375b426?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-18 { background-image: url('https://images.unsplash.com/photo-1605681145151-c0b3d6c7104b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-19 { background-image: url('https://images.unsplash.com/photo-1599599933544-672e4798c807?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-20 { background-image: url('https://images.unsplash.com/photo-1620336214302-1a4c38d4c1d7?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-21 { background-image: url('https://images.unsplash.com/photo-1554734867-bf3c00a49371?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-22 { background-image: url('https://images.unsplash.com/photo-1579684385127-1ef15d508118?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=880&q=80'); }
.article-img-23 { background-image: url('https://plus.unsplash.com/premium_photo-1661766820235-3c96bc13f938?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-24 { background-image: url('https://images.unsplash.com/photo-1606838837238-57688313508c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-25 { background-image: url('https://images.unsplash.com/photo-1584610356248-81d3d66b596f?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-26 { background-image: url('https://images.unsplash.com/photo-1522889639-6B4912BA542A?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-27 { background-image: url('https://images.unsplash.com/photo-1566004100631-35d015d6a491?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-28 { background-image: url('https://images.unsplash.com/photo-1484665754824-1d8e1469956e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-29 { background-image: url('https://images.unsplash.com/photo-1472090278799-d7c2a7156d68?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=869&q=80'); }
.article-img-30 { background-image: url('https://images.unsplash.com/photo-1499781350138-d0f31a207612?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-31 { background-image: url('https://images.unsplash.com/photo-1506869639733-11215c54f5c6?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-32 { background-image: url('https://images.unsplash.com/photo-1599522190924-d5f2a1d2112a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=869&q=80'); }
.article-img-33 { background-image: url('https://images.unsplash.com/photo-1596707849382-e56d4001150f?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-34 { background-image: url('https://images.unsplash.com/photo-1574023240294-f2549f8a816a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-35 { background-image: url('https://images.unsplash.com/photo-1600813160814-1f3f615306e6?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-36 { background-image: url('https://images.unsplash.com/photo-1610481977931-36f73357b10a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-37 { background-image: url('https://images.unsplash.com/photo-1590240472421-5a50e932fe40?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
.article-img-38 { background-image: url('https://images.unsplash.com/photo-1570228062259-e36c6c5188c0?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=871&q=80'); }
.article-img-39 { background-image: url('https://images.unsplash.com/photo-1543083326-14c049e3a348?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=870&q=80'); }
/* =================================================================== */
/* AKHIR BLOK IMAGE URLS */
/* =================================================================== */


/* Dark Mode overrides for new card */
@media (prefers-color-scheme: dark) {
    .article-card-v3-2-3 {
        background: #2d2d2d;
        border-color: #505050;
    }
    .article-image { border-bottom-color: #505050; }
    .article-category {
        background: #4a3a41;
        color: #ff9ac9;
        border-color: #5c4a52;
    }
    .article-title { color: #ffffff; }
    .article-summary { color: #e0e0e0; }
    .article-details-dropdown { border-top-color: #505050; }
    .article-details-toggle { color: #6db4ff; }
    .article-details-toggle:hover { background: #3a3a3a; }
    
    .article-full-content-wrapper {
        color: #e8e8e8;
        background: #252525;
    }
    .article-full-content-wrapper h2,
    .article-full-content-wrapper h3,
    .article-full-content-wrapper h4 {
        color: #ffffff;
    }
    .article-full-content-wrapper strong {
        color: #ff9ac9; /* Highlight dark mode */
    }
    .article-source {
        color: #b0b0b0;
        background: #333333;
    }
}
"""
# ... (CUSTOM_CSS Anda berlanjut) ...


print("✅ Custom CSS (v3.2.3) loaded: CSS Perpustakaan lama (penyebab error) telah dihapus.")

# ===============================================================================
# SECTION 10B-EXTRA: MISSING FUNCTIONS FOR KEJAR TUMBUH
# (Ini adalah bagian dari SECTION 10B, tapi di file Anda diletakkan di sini)
# ===============================================================================

def toggle_kejar_tumbuh_mode(mode: str):
    """Toggle input mode untuk Kalkulator Kejar Tumbuh"""
    if mode == "Tanggal Lahir":
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
    else:  # Usia Langsung
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)


def tambah_data_kejar_tumbuh(data_state, mode, dob, dom, usia_manual, bb, tb):
    """
    Menambahkan data pengukuran ke state untuk Kalkulator Kejar Tumbuh
    
    Args:
        data_state: List data pengukuran yang sudah ada
        mode: Mode input ("Tanggal Lahir" atau "Usia Langsung")
        dob: Tanggal lahir
        dom: Tanggal pengukuran
        usia_manual: Usia dalam bulan (jika mode usia langsung)
        bb: Berat badan (kg)
        tb: Tinggi badan (cm)
    
    Returns:
        Tuple: (updated_data_state, display_html, cleared_inputs...)
    """
    if data_state is None:
        data_state = []
    
    # Validasi input
    if bb is None or bb <= 0:
        return data_state, "⚠️ Masukkan berat badan yang valid", None, None, None, None
    
    if tb is None or tb <= 0:
        return data_state, "⚠️ Masukkan tinggi badan yang valid", None, None, None, None
    
    # Hitung usia
    if mode == "Tanggal Lahir":
        if not dob or not dom:
            return data_state, "⚠️ Masukkan tanggal lahir dan tanggal pengukuran", None, None, None, None
        
        try:
            # Gunakan 'parse_date' yang sudah Anda buat
            dob_date = parse_date(dob) 
            dom_date = parse_date(dom)
            
            if dob_date is None or dom_date is None:
                raise ValueError("Format tanggal tidak valid (gunakan YYYY-MM-DD atau DD/MM/YYYY)")

            if dom_date < dob_date:
                return data_state, "⚠️ Tanggal pengukuran tidak boleh sebelum tanggal lahir", None, None, None, None
            
            # Hitung usia dalam bulan
            age_days = (dom_date - dob_date).days
            age_months = age_days / 30.4375
        except Exception as e:
            return data_state, f"⚠️ Error Tanggal: {e}", None, None, None, None
    else:
        if usia_manual is None or usia_manual < 0:
            return data_state, "⚠️ Masukkan usia yang valid", None, None, None, None
        age_months = usia_manual
    
    # Tambahkan data baru
    new_data = {
        'usia_bulan': round(age_months, 1),
        'bb': round(bb, 2),
        'tb': round(tb, 1)
    }
    
    data_state.append(new_data)
    
    # Sort berdasarkan usia
    data_state = sorted(data_state, key=lambda x: x['usia_bulan'])
    
    # Generate display HTML
    display_html = "<div style='padding: 15px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 10px;'>"
    display_html += f"<h4 style='margin-top: 0; color: #2c3e50;'>📊 Data Terinput: {len(data_state)} pengukuran</h4>"
    display_html += "<table style='width: 100%; border-collapse: collapse;'>"
    display_html += "<tr style='background: #3498db; color: white;'>"
    display_html += "<th style='padding: 8px; border: 1px solid #ddd;'>No</th>"
    display_html += "<th style='padding: 8px; border: 1px solid #ddd;'>Usia (bulan)</th>"
    display_html += "<th style='padding: 8px; border: 1px solid #ddd;'>BB (kg)</th>"
    display_html += "<th style='padding: 8px; border: 1px solid #ddd;'>TB (cm)</th>"
    display_html += "</tr>"
    
    for i, data in enumerate(data_state):
        bg_color = "#ecf0f1" if i % 2 == 0 else "#ffffff"
        display_html += f"<tr style='background: {bg_color};'>"
        display_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{i+1}</td>"
        display_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{data['usia_bulan']}</td>"
        display_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{data['bb']}</td>"
        display_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{data['tb']}</td>"
        display_html += "</tr>"
    
    display_html += "</table>"
    display_html += "<p style='margin-top: 10px; color: #27ae60; font-weight: bold;'>✅ Data berhasil ditambahkan!</p>"
    display_html += "</div>"
    
    # Return updated state, display, and clear input fields
    return data_state, display_html, None, None, None, None


def hitung_kejar_tumbuh(data_state):
    """
    Menghitung laju pertumbuhan dari data yang sudah diinput
    
    Args:
        data_state: List data pengukuran
    
    Returns:
        HTML report dengan analisis laju pertumbuhan
    """
    if not data_state or len(data_state) < 2:
        return "<p style='color: #e74c3c; padding: 20px;'>⚠️ Minimal 2 data pengukuran diperlukan untuk menghitung laju pertumbuhan.</p>"
    
    # Hitung velocity
    results = []
    for i in range(len(data_state) - 1):
        data1 = data_state[i]
        data2 = data_state[i + 1]
        
        delta_months = data2['usia_bulan'] - data1['usia_bulan']
        delta_bb = data2['bb'] - data1['bb']
        delta_tb = data2['tb'] - data1['tb']
        
        if delta_months > 0:
            velocity_bb = delta_bb / delta_months  # kg/bulan
            velocity_tb = delta_tb / delta_months  # cm/bulan
            
            results.append({
                'periode': f"{data1['usia_bulan']:.1f} - {data2['usia_bulan']:.1f} bulan",
                'delta_months': delta_months,
                'velocity_bb': velocity_bb,
                'velocity_tb': velocity_tb,
                'delta_bb': delta_bb,
                'delta_tb': delta_tb
            })
    
    if not results:
        return "<p style='color: #e74c3c; padding: 20px;'>⚠️ Data tidak memadai untuk menghitung laju pertumbuhan (perlu interval waktu positif).</p>"

    # Generate HTML report
    html = "<div style='padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>"
    html += "<h3 style='color: #2c3e50; margin-top: 0;'>📈 Analisis Laju Pertumbuhan (Growth Velocity)</h3>"
    
    html += "<table style='width: 100%; border-collapse: collapse; margin: 20px 0;'>"
    html += "<tr style='background: #3498db; color: white;'>"
    html += "<th style='padding: 10px; border: 1px solid #ddd;'>Periode</th>"
    html += "<th style='padding: 10px; border: 1px solid #ddd;'>Durasi</th>"
    html += "<th style='padding: 10px; border: 1px solid #ddd;'>Δ BB</th>"
    html += "<th style='padding: 10px; border: 1px solid #ddd;'>Velocity BB</th>"
    html += "<th style='padding: 10px; border: 1px solid #ddd;'>Δ TB</th>"
    html += "<th style='padding: 10px; border: 1px solid #ddd;'>Velocity TB</th>"
    html += "<th style='padding: 10px; border: 1px solid #ddd;'>Status</th>"
    html += "</tr>"
    
    for i, result in enumerate(results):
        bg_color = "#ecf0f1" if i % 2 == 0 else "#ffffff"
        
        # Evaluasi velocity BB (rule of thumb: 0.5-1 kg/bulan untuk bayi)
        if result['velocity_bb'] < 0:
            bb_status = "⚠️ Penurunan"
            bb_color = "#e74c3c"
        elif result['velocity_bb'] < 0.3:
            bb_status = "⚠️ Lambat"
            bb_color = "#f39c12"
        elif result['velocity_bb'] <= 1.5:
            bb_status = "✅ Normal"
            bb_color = "#27ae60"
        else:
            bb_status = "ℹ️ Cepat"
            bb_color = "#3498db"
        
        # Evaluasi velocity TB (rule of thumb: 2-3 cm/bulan untuk bayi)
        if result['velocity_tb'] < 0:
            tb_status = "⚠️ Penurunan"
            tb_color = "#e74c3c"
        elif result['velocity_tb'] < 1:
            tb_status = "⚠️ Lambat"
            tb_color = "#f39c12"
        elif result['velocity_tb'] <= 4:
            tb_status = "✅ Normal"
            tb_color = "#27ae60"
        else:
            tb_status = "ℹ️ Cepat"
            tb_color = "#3498db"
        
        overall_status = "✅ Baik" if "✅" in bb_status and "✅" in tb_status else "⚠️ Perlu Perhatian"
        overall_color = "#27ae60" if "✅" in overall_status else "#f39c12"
        
        html += f"<tr style='background: {bg_color};'>"
        html += f"<td style='padding: 10px; border: 1px solid #ddd;'>{result['periode']}</td>"
        html += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: center;'>{result['delta_months']:.1f} bln</td>"
        html += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: center;'>{result['delta_bb']:+.2f} kg</td>"
        html += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: center; color: {bb_color}; font-weight: bold;'>{result['velocity_bb']:.2f} kg/bln<br><small>{bb_status}</small></td>"
        html += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: center;'>{result['delta_tb']:+.1f} cm</td>"
        html += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: center; color: {tb_color}; font-weight: bold;'>{result['velocity_tb']:.2f} cm/bln<br><small>{tb_status}</small></td>"
        html += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: center; color: {overall_color}; font-weight: bold;'>{overall_status}</td>"
        html += "</tr>"
    
    html += "</table>"
    
    # Summary statistics
    avg_velocity_bb = sum(r['velocity_bb'] for r in results) / len(results)
    avg_velocity_tb = sum(r['velocity_tb'] for r in results) / len(results)
    
    html += "<div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 20px;'>"
    html += "<h4 style='color: #2c3e50; margin-top: 0;'>📊 Rata-rata Laju Pertumbuhan</h4>"
    html += f"<p><strong>Berat Badan:</strong> {avg_velocity_bb:.2f} kg/bulan</p>"
    html += f"<p><strong>Tinggi Badan:</strong> {avg_velocity_tb:.2f} cm/bulan</p>"
    html += "</div>"
    
    html += "<div style='background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #ffc107;'>"
    html += "<p style='margin: 0;'><strong>ℹ️ Catatan:</strong> Interpretasi ini bersifat umum. Konsultasikan dengan dokter anak untuk evaluasi yang lebih akurat.</p>"
    html += "</div>"
    
    html += "</div>"
    
    return html


def reset_kejar_tumbuh():
    """Reset semua data dan input Kalkulator Kejar Tumbuh"""
    return [], "<p style='color: #7f8c8d; padding: 20px;'>Tidak ada data. Silakan tambahkan data pengukuran.</p>", None, None, None, None, ""


def hapus_data_terakhir(data_state):
    """
    Menghapus data pengukuran terakhir dari Kalkulator Kejar Tumbuh
    
    Args:
        data_state: List data pengukuran
    
    Returns:
        Tuple: (updated_data_state, updated_display_html)
    """
    if not data_state or len(data_state) == 0:
        return [], "<p style='color: #7f8c8d; padding: 20px;'>Tidak ada data untuk dihapus.</p>"
    
    # Hapus data terakhir
    data_state.pop()
    
    # Generate updated display
    if len(data_state) == 0:
        display_html = "<p style='color: #7f8c8d; padding: 20px;'>Tidak ada data. Silakan tambahkan data pengukuran.</p>"
    else:
        display_html = "<div style='padding: 15px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 10px;'>"
        display_html += f"<h4 style='margin-top: 0; color: #2c3e50;'>📊 Data Terinput: {len(data_state)} pengukuran</h4>"
        display_html += "<table style='width: 100%; border-collapse: collapse;'>"
        display_html += "<tr style='background: #3498db; color: white;'>"
        display_html += "<th style='padding: 8px; border: 1px solid #ddd;'>No</th>"
        display_html += "<th style='padding: 8px; border: 1px solid #ddd;'>Usia (bulan)</th>"
        display_html += "<th style='padding: 8px; border: 1px solid #ddd;'>BB (kg)</th>"
        display_html += "<th style='padding: 8px; border: 1px solid #ddd;'>TB (cm)</th>"
        display_html += "</tr>"
        
        for i, data in enumerate(data_state):
            bg_color = "#ecf0f1" if i % 2 == 0 else "#ffffff"
            display_html += f"<tr style='background: {bg_color};'>"
            display_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{i+1}</td>"
            display_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{data['usia_bulan']}</td>"
            display_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{data['bb']}</td>"
            display_html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{data['tb']}</td>"
            display_html += "</tr>"
        
        display_html += "</table>"
        display_html += "<p style='margin-top: 10px; color: #e67e22; font-weight: bold;'>🗑️ Data terakhir berhasil dihapus!</p>"
        display_html += "</div>"
    
    return data_state, display_html

# =========================================
# SECTION 10B – Extra
# Plot Kejar Tumbuh (versi smooth)
# =========================================

def plot_kejar_tumbuh_trajectory(
    data_list: List[Dict],
    gender: str,
    theme_name: str = "pink_pastel",
) -> Optional[str]:
    """
    Versi baru plot Kejar Tumbuh:
    - Tetap memakai kurva rujukan WHO (WFA & HFA).
    - Trajectory anak digambar dengan garis SMOOTH (cubic spline)
      sehingga bentuk kurva mendekati grafik referensi,
      bukan garis patah-patah antar titik.
    """
    import numpy as np

    if not data_list or len(data_list) < 2:
        # Minimal 2 titik agar ada bentuk kurva
        return None

    theme = apply_matplotlib_theme(theme_name)
    sex_code = "M" if gender.lower().startswith("l") else "F"

    ages = np.array([float(d.get("usia_bulan", 0.0)) for d in data_list], dtype=float)
    weights = np.array([float(d.get("bb", 0.0)) for d in data_list], dtype=float)
    heights = np.array([float(d.get("tb", 0.0)) for d in data_list], dtype=float)

    # Urutkan berdasarkan usia untuk mencegah garis bolak-balik
    order = np.argsort(ages)
    ages = ages[order]
    weights = weights[order]
    heights = heights[order]

    # Batasi rentang usia agar tidak keluar jauh dari data anak
    min_age = max(0.0, float(ages.min()) - 1.0)
    max_age = min(60.0, float(ages.max()) + 1.0)
    plot_age_grid = AGE_GRID[(AGE_GRID >= min_age) & (AGE_GRID <= max_age)]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharex=True)
    ax1, ax2 = axes

    # --- Kurva rujukan WFA WHO ---
    wfa_curves = {}
    for sd in range(-3, 4):
        x, y = generate_wfa_curve(sex_code, sd)
        mask = (x >= min_age) & (x <= max_age)
        wfa_curves[sd] = (x[mask], y[mask])

    # --- Kurva rujukan HFA WHO ---
    hfa_curves = {}
    for sd in range(-3, 4):
        x, y = generate_hfa_curve(sex_code, sd)
        mask = (x >= min_age) & (x <= max_age)
        hfa_curves[sd] = (x[mask], y[mask])

    local_age_grid = plot_age_grid

    # Zona WFA
    _fill_zone_between_curves(
        ax1, local_age_grid,
        wfa_curves[-2][1], wfa_curves[-1][1],
        "#FFEBEE", 0.55, "Sangat Kurus"
    )
    _fill_zone_between_curves(
        ax1, local_age_grid,
        wfa_curves[-1][1], wfa_curves[1][1],
        "#E8F5E9", 0.35, "Normal"
    )
    _fill_zone_between_curves(
        ax1, local_age_grid,
        wfa_curves[1][1], wfa_curves[2][1],
        "#FFF3CD", 0.35, "Risiko BB Lebih"
    )

    for sd, (x, y) in wfa_curves.items():
        ax1.plot(
            x, y,
            linestyle="--" if abs(sd) == 2 else "-",
            linewidth=1,
            alpha=0.8,
            label=f"BB z={sd}" if sd in (-2, 0, 2) else None,
        )

    # Zona HFA
    _fill_zone_between_curves(
        ax2, local_age_grid,
        hfa_curves[-2][1], hfa_curves[-1][1],
        "#FFEBEE", 0.55, "Sangat Pendek"
    )
    _fill_zone_between_curves(
        ax2, local_age_grid,
        hfa_curves[-1][1], hfa_curves[2][1],
        "#E8F5E9", 0.45, "Normal"
    )
    _fill_zone_between_curves(
        ax2, local_age_grid,
        hfa_curves[2][1],  hfa_curves[3][1],
        "#FFF3CD", 0.35, "Tinggi"
    )

    for sd, (x, y) in hfa_curves.items():
        ax2.plot(
            x, y,
            linestyle="--" if abs(sd) == 2 else "-",
            linewidth=1,
            alpha=0.8,
            label=f"TB z={sd}" if sd in (-2, 0, 2) else None,
        )

    # --- Trajectory anak: smoothing dengan cubic spline ---
    try:
        from scipy.interpolate import make_interp_spline

        # Pilih derajat spline sesuai jumlah titik
        if len(ages) >= 4:
            k = 3
        elif len(ages) == 3:
            k = 2
        else:
            k = 1  # fallback hampir linear (mirip garis biasa)

        age_smooth = np.linspace(float(ages.min()), float(ages.max()), 200)

        w_spline = make_interp_spline(ages, weights, k=k)
        w_smooth = w_spline(age_smooth)

        h_spline = make_interp_spline(ages, heights, k=k)
        h_smooth = h_spline(age_smooth)
    except Exception:
        # Kalau SciPy tidak tersedia atau ada error lain → pakai garis biasa
        age_smooth = ages
        w_smooth = weights
        h_smooth = heights

    primary = theme.get("primary", "#ff6b9d")

    # BB vs usia: garis smooth + titik pengukuran
    ax1.plot(
        age_smooth, w_smooth,
        color=primary,
        linewidth=2.4,
        label="Trajectory BB (smooth)",
        zorder=10,
    )
    ax1.scatter(
        ages, weights,
        color="#111827",
        s=28,
        zorder=11,
    )

    # TB vs usia: garis smooth + titik pengukuran
    ax2.plot(
        age_smooth, h_smooth,
        color=primary,
        linewidth=2.4,
        label="Trajectory TB (smooth)",
        zorder=10,
    )
    ax2.scatter(
        ages, heights,
        color="#111827",
        s=28,
        zorder=11,
    )

    # Label & grid
    ax1.set_title("Kejar Tumbuh BB vs Usia")
    ax1.set_xlabel("Usia (bulan)")
    ax1.set_ylabel("Berat Badan (kg)")
    ax1.grid(True, which="both", linestyle=":", alpha=0.4)

    ax2.set_title("Kejar Tumbuh TB vs Usia")
    ax2.set_xlabel("Usia (bulan)")
    ax2.set_ylabel("Tinggi/Panjang Badan (cm)")
    ax2.grid(True, which="both", linestyle=":", alpha=0.4)

    ax1.legend(fontsize=7, loc="upper left")
    ax2.legend(fontsize=7, loc="upper left")

    fig.suptitle(f"Trajectory Kejar Tumbuh — {gender}", fontsize=11, y=0.98)

    # Simpan gambar ke OUTPUTS_DIR
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"kejar_tumbuh_{timestamp}.png"
    filepath = os.path.join(OUTPUTS_DIR, filename)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(filepath, dpi=160)
    cleanup_matplotlib_figures(fig)

    return filepath


def kalkulator_kejar_tumbuh_handler(data_list: List[Dict], gender: str) -> Tuple[str, Optional[str]]:
    """
    (BARU DITAMBAHKAN)
    Handler utama untuk Kalkulator Kejar Tumbuh.
    Menghasilkan HTML analisis dan path ke plot.
    """
    if not data_list or len(data_list) < 2:
        html = "<p style='color: #e74c3c; padding: 20px;'>⚠️ Minimal 2 data pengukuran diperlukan untuk menghitung laju pertumbuhan dan membuat grafik.</p>"
        return html, None
    
    try:
        # 1. Hitung analisis velocity (HTML)
        html_report = hitung_kejar_tumbuh(data_list)
        
        # 2. Buat plot trajectory (PNG)
        plot_path = plot_kejar_tumbuh_trajectory(data_list, gender)
        
        return html_report, plot_path
        
    except Exception as e:
        print(f"❌ Error in kalkulator_kejar_tumbuh_handler: {e}")
        traceback.print_exc()
        return f"<p style='color: #e74c3c; padding: 20px;'>Terjadi error saat analisis: {e}</p>", None

print("✅ Section 10B-Extra loaded: Kejar Tumbuh functions defined")

# Build Gradio Interface
with gr.Blocks(
    title=APP_TITLE,
    theme=gr.themes.Soft(
        primary_hue="pink",
        secondary_hue="teal",
        neutral_hue="slate",
        # --- PERBAIKAN DI BAWAH INI ---
        font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("Fira Code"), "monospace"],
        # --- AKHIR PERBAIKAN ---
    ),
    css=CUSTOM_CSS, 
    analytics_enabled=False,
) as demo:
    
    # =======================================================================
    # HEADER (MODIFIED FOR v3.2.2)
    # =======================================================================
    
    gr.Markdown(f"""
    # 🏥 **{APP_TITLE} v3.2.2**
    ### 💕 Monitor Pertumbuhan Anak Profesional Berbasis WHO Standards
    
    **Fitur Unggulan v3.2.2 (Revisi):**
    - ✅ **Mode Mudah:** Referensi cepat rentang normal BB, TB, LK.
    - ✅ **Kalkulator Kejar Tumbuh:** Monitor laju pertumbuhan (velocity) anak Anda.
    - ✅ **Perpustakaan Interaktif:** Fitur baru dengan 40 artikel, search, filter, dan UI profesional.
    - ✅ Bug Fix & Peningkatan UI.
    - ✅ Standar WHO 2006 & Permenkes RI 2020.
    
    ---
    
    ⚠️ **PENTING**: Aplikasi ini untuk skrining awal. Konsultasikan hasil dengan tenaga kesehatan.
    
    📱 **Butuh bantuan?** WhatsApp: [+{CONTACT_WA}](https://wa.me/{CONTACT_WA})
    
    ---
    """)
    
    # JavaScript for Browser Notifications (from v3.1)
    # DIGABUNG dengan JavaScript Perpustakaan Interaktif (v3.2.2)
    
    # JavaScript for Browser Notifications (from v3.1)
    # DIGABUNG dengan JavaScript Perpustakaan Interaktif (v3.2.2)
    
    # Define notification_js
    notification_js = """
<script>
// Browser Notification System for AnthroHPK
window.AnthroNotification = {
    isSupported: function() {
        return ('Notification' in window);
    },
    requestPermission: async function() {
        if (!this.isSupported()) {
            return Promise.resolve(false);
        }
        if (Notification.permission === 'granted') {
            return Promise.resolve(true);
        }
        if (Notification.permission !== 'denied') {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        }
        return Promise.resolve(false);
    },
    send: function(title, options = {}) {
        if (!this.isSupported() || Notification.permission !== 'granted') {
            return null;
        }
        const defaultOptions = {
            icon: '/static/icon.png',
            badge: '/static/badge.png',
            requireInteraction: false,
            silent: false
        };
        const notificationOptions = { ...defaultOptions, ...options };
        try {
            return new Notification(title, notificationOptions);
        } catch (error) {
            console.error('Notification error:', error);
            return null;
        }
    },
    scheduleReminder: function(title, body, date) {
        const now = new Date();
        const scheduledTime = new Date(date);
        const delay = scheduledTime - now;
        if (delay > 0) {
            setTimeout(() => {
                this.send(title, { body: body });
            }, delay);
            return true;
        }
        return false;
    },
    getPermission: function() {
        if (!this.isSupported()) {
            return 'unsupported';
        }
        return Notification.permission;
    }
};
document.addEventListener('DOMContentLoaded', function() {
    console.log('AnthroNotification initialized');
});
</script>
"""
    
    combined_js = notification_js 
    gr.HTML(combined_js)
    
    # State untuk menyimpan payload
    state_payload = gr.State({})
    
    # =======================================================================
    # MAIN TABS (MODIFIED FOR v3.2.2 - RE-ORDERED)
    # =======================================================================
    
    with gr.Tabs() as main_tabs:
        
        # ===================================================================
        # TAB 1: KALKULATOR GIZI WHO
        # ===================================================================
        
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
        
        # ===================================================================
        # TAB 2: MODE MUDAH (BARU v3.2)
        # ===================================================================
        
        with gr.TabItem("🎯 Mode Mudah", id=1):
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

        # ===================================================================
        # TAB 3: CHECKLIST SEHAT BULANAN (BUG FIX v3.2)
        # ===================================================================
        
        with gr.TabItem("📋 Checklist Sehat Bulanan", id=2):
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
        
        # ===================================================================
        # TAB 4: KALKULATOR TARGET KEJAR TUMBUH (BARU v3.2)
        # ===================================================================
        
        with gr.TabItem("📈 Kalkulator Target Kejar Tumbuh", id=3):
            gr.Markdown("""
            ### Kalkulator Target Kejar Tumbuh (Growth Velocity)
            
            Monitor **laju pertumbuhan** anak Anda dengan standar internasional WHO! 
            Fitur ini membantu Anda:
            
            - 📈 Memantau **velocity pertumbuhan** (kenaikan BB & TB per bulan)
            - 🎯 Mengetahui apakah anak **mengejar kurva** atau **melambat**
            - 💡 Mendapat **rekomendasi nutrisi** berdasarkan trajectory pertumbuhan
            
            ---
            
            #### 📝 Cara Menggunakan:
            
            1.  Pilih **Jenis Kelamin** dan **Mode Input** (Tanggal atau Usia).
            2.  Jika mode "Tanggal", isi **Tanggal Lahir** (cukup sekali).
            3.  Isi formulir **"Input Data Pengukuran"** (Tanggal/Usia, BB, TB).
            4.  Klik **"Tambah Data"**. Ulangi untuk setiap pengukuran (minimal 2 data).
            5.  Data yang Anda tambahkan akan muncul di tabel **"Data Terinput"**.
            6.  Jika salah, klik **"Hapus Data Terakhir"**.
            7.  Setelah semua data terisi, klik **"Analisis Pertumbuhan"**.
            """)
            
            # State untuk menyimpan list data
            kejar_tumbuh_data_state = gr.State([])
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 1. Informasi Dasar Anak")
                    kejar_gender = gr.Radio(
                        choices=["Laki-laki", "Perempuan"],
                        value="Laki-laki",
                        label="Jenis Kelamin Anak"
                    )
                    kejar_tumbuh_mode = gr.Radio(
                        choices=["Tanggal", "Usia (bulan)"],
                        value="Tanggal",
                        label="Mode Input Data",
                        info="Pilih cara Anda memasukkan data"
                    )
                    kejar_tumbuh_dob = gr.Textbox(
                        label="Tanggal Lahir Anak (DOB)",
                        placeholder="YYYY-MM-DD atau DD/MM/YYYY",
                        info="Diperlukan jika mode 'Tanggal'",
                        visible=True
                    )
                    
                    gr.Markdown("#### 2. Input Data Pengukuran")
                    with gr.Group():
                        kejar_tumbuh_dom = gr.Textbox(
                            label="Tanggal Pengukuran (DOM)",
                            placeholder="YYYY-MM-DD atau DD/MM/YYYY",
                            info="Tanggal saat anak diukur",
                            visible=True
                        )
                        kejar_tumbuh_usia = gr.Number(
                            label="Usia (bulan)",
                            info="Usia anak saat diukur",
                            visible=False
                        )
                        kejar_tumbuh_bb = gr.Number(
                            label="Berat Badan (kg)",
                        )
                        kejar_tumbuh_tb = gr.Number(
                            label="Panjang/Tinggi Badan (cm)",
                        )
                    
                    with gr.Row():
                        tambah_data_btn = gr.Button("➕ Tambah Data", variant="secondary")
                        hapus_data_btn = gr.Button("🗑️ Hapus Data Terakhir")
                    
                    gr.Markdown("#### 3. Analisis")
                    kejar_btn = gr.Button(
                        "📊 Analisis Pertumbuhan",
                        variant="primary",
                        size="lg"
                    )

                with gr.Column(scale=2):
                    gr.Markdown("#### Data Terinput")
                    data_terinput_display = gr.HTML(
                        "<p style='text-align: center; color: #888; padding: 10px;'>Belum ada data yang ditambahkan.</p>"
                    )
                    
                    gr.Markdown("---")
                    gr.Markdown("#### Hasil Analisis")
                    
                    kejar_output_html = gr.HTML(
                        label="Hasil Analisis Velocity",
                        value="<p style='padding: 20px; text-align: center; color: #888;'>Hasil analisis akan tampil di sini...</p>"
                    )
                    
                    kejar_output_plot = gr.Image(
                        label="Grafik Trajectory Pertumbuhan",
                        type="filepath",
                        visible=False
                    )

            # --- Handlers untuk UI Kejar Tumbuh ---
            
            # Toggle visibilitas input Tanggal vs Usia
            def toggle_kejar_tumbuh_mode(mode):
                is_tanggal_mode = (mode == "Tanggal")
                return (
                    gr.update(visible=is_tanggal_mode), # DOB
                    gr.update(visible=is_tanggal_mode), # DOM
                    gr.update(visible=not is_tanggal_mode) # Usia
                )
            
            kejar_tumbuh_mode.change(
                fn=toggle_kejar_tumbuh_mode,
                inputs=[kejar_tumbuh_mode],
                outputs=[kejar_tumbuh_dob, kejar_tumbuh_dom, kejar_tumbuh_usia]
            )
            
            # Handler Tombol "Tambah Data"
            tambah_data_btn.click(
                fn=tambah_data_kejar_tumbuh,
                inputs=[
                    kejar_tumbuh_data_state, kejar_tumbuh_mode, kejar_tumbuh_dob,
                    kejar_tumbuh_dom, kejar_tumbuh_usia, kejar_tumbuh_bb, kejar_tumbuh_tb
                ],
                outputs=[
                    kejar_tumbuh_data_state, data_terinput_display,
                    kejar_tumbuh_dom, kejar_tumbuh_usia, kejar_tumbuh_bb, kejar_tumbuh_tb
                ]
            )
            
            # Handler Tombol "Hapus Data Terakhir"
            hapus_data_btn.click(
                fn=hapus_data_terakhir,
                inputs=[kejar_tumbuh_data_state],
                outputs=[kejar_tumbuh_data_state, data_terinput_display]
            )
            
            # Handler Tombol "Analisis Pertumbuhan"
            # Handler Tombol "Analisis Pertumbuhan"
            def kejar_tumbuh_wrapper_fixed(data_list, gender):
                """
                Wrapper baru untuk memanggil handler yang benar dan mengatur visibilitas plot.
                """
                # Ini memanggil fungsi baru yang Anda tambahkan di Langkah 2
                html, plot_path = kalkulator_kejar_tumbuh_handler(data_list, gender) 
                
                if plot_path:
                    # Jika plot berhasil dibuat, kirim HTML dan buat plot terlihat
                    return html, gr.update(value=plot_path, visible=True)
                else:
                    # Jika plot gagal (misal < 2 data), kirim HTML error dan sembunyikan plot
                    return html, gr.update(visible=False)

            kejar_btn.click(
                fn=kejar_tumbuh_wrapper_fixed,  # <-- Pastikan menggunakan nama fungsi wrapper yang baru
                inputs=[kejar_tumbuh_data_state, kejar_gender],
                outputs=[kejar_output_html, kejar_output_plot]
            )
            
        # ===================================================================
        # TAB 5: PERPUSTAKAAN IBU BALITA (REVISI TOTAL)
        # ===================================================================
       
        with gr.TabItem("📚 Perpustakaan", id=4) as tab_perpustakaan: # ID diubah ke 4
            gr.Markdown("""
            ## 📚 Perpustakaan Ibu Balita
            Temukan 40+ artikel terkurasi mengenai nutrisi, tumbuh kembang, dan kesehatan anak.
            Gunakan filter di bawah untuk mencari artikel yang Anda butuhkan.
            """)
            
            with gr.Row():
                # Filter 1: Pencarian
                library_search = gr.Textbox(
                    label="🔍 Cari Artikel",
                    placeholder="Ketik kata kunci (misal: stunting, MPASI, demam)..."
                )
                
                # Filter 2: Kategori
                library_category = gr.Dropdown(
                    label="📁 Filter Kategori",
                    choices=get_library_categories_list(), # Memanggil fungsi baru dari Langkah 2
                    value="Semua Kategori"
                )
            
            # Tombol untuk memicu pencarian
            library_search_btn = gr.Button("Cari Artikel", variant="primary")
            
            gr.Markdown("---")
            
            # Area output untuk daftar artikel
            # INI ADALAH PERBAIKAN DARI ERROR ANDA:
            # Kita tidak bisa mengupdate 'children' dari 'gr.Column'
            # Solusinya: Kita buat 'gr.Column' sebagai OUTPUT, dan fungsi Python
            # akan mengembalikan 'gr.Column.update(...)'
            
# Area output untuk daftar artikel
            # KEMBALIKAN ke gr.HTML
            library_output = gr.HTML(
                value="<p style='text-align: center; color: #888; padding: 20px;'>Silakan klik 'Cari Artikel' untuk memuat.</p>"
            )

            # --- Event Handlers untuk Tab Perpustakaan ---
            
            # 1. Memicu pencarian ketika tombol diklik
            library_search_btn.click(
                fn=update_library_display, # Memanggil fungsi baru dari Langkah 2
                inputs=[library_search, library_category],
                outputs=[library_output]
            )
            
            # 2. (PENTING) Memuat semua artikel saat tab perpustakaan dipilih
            tab_perpustakaan.select(
                fn=load_initial_articles, # Memanggil fungsi baru dari Langkah 2
                inputs=None,
                outputs=[library_output]
            )


# ===================================================================
        # TAB 5: RIWAYAT PENGGUNAAN (CLOUD) - BARU
        # ===================================================================
        with gr.TabItem("📈 Riwayat & Statistik", id=5):
            gr.Markdown("""
            ## 📊 Dashboard Riwayat Penggunaan (Cloud)
            Data di bawah ini diambil secara *real-time* dari database Google Sheets.
            **Privasi Terjamin:** Data ditampilkan tanpa nama anak maupun orang tua.
            """)
            
            with gr.Row():
                refresh_history_btn = gr.Button("🔄 Muat / Segarkan Data", variant="primary")
            
            with gr.Row():
                hist_plot1 = gr.Plot(label="Analisis Sebaran Pertumbuhan")
                hist_plot2 = gr.Plot(label="Demografi Pengguna")
            
            gr.Markdown("### 📋 Tabel Data Terakhir (Anonymized)")
            hist_table = gr.Dataframe(
                headers=["Timestamp", "Fitur", "Gender", "Umur", "BB", "TB", "Z-Score..."],
                datatype=["str", "str", "str", "number", "number", "number", "str"],
                interactive=False
            )
            
            # Event Handler
            refresh_history_btn.click(
                fn=get_history_charts,
                inputs=[],
                outputs=[hist_plot1, hist_plot2, hist_table]
            )

        # ===================================================================
        # TAB 6: KUESIONER FEEDBACK - BARU
        # ===================================================================
        with gr.TabItem("📝 Kuesioner & Feedback", id=6):
            gr.Markdown("""
            ## 🗳️ Evaluasi & Masukan Pengguna
            Bantu kami meningkatkan kualitas aplikasi dengan mengisi kuesioner singkat ini.
            """)
            
            with gr.Row():
                with gr.Column():
                    q_performa = gr.Radio(
                        ["1 (Buruk)", "2", "3", "4", "5 (Sangat Baik)"],
                        label="Bagaimana performa (kecepatan) aplikasi?",
                        value="5 (Sangat Baik)"
                    )
                    q_manfaat = gr.Radio(
                        ["1 (Kurang)", "2", "3", "4", "5 (Sangat Bermanfaat)"],
                        label="Seberapa besar dampak/manfaat aplikasi ini?",
                        value="5 (Sangat Bermanfaat)"
                    )
                    q_profesi = gr.Dropdown(
                        ["Dokter", "Bidan", "Ahli Gizi", "Kader Posyandu", "Orang Tua", "Mahasiswa", "Lainnya"],
                        label="Profesi Anda",
                        value="Orang Tua"
                    )
                
                with gr.Column():
                    q_kendala = gr.Textbox(
                        label="Kendala yang ditemui",
                        placeholder="Ceritakan jika ada error atau kesulitan...",
                        lines=3
                    )
                    q_saran = gr.Textbox(
                        label="Saran Pengembangan",
                        placeholder="Fitur apa yang perlu ditambahkan?",
                        lines=3
                    )
                    
                    submit_feedback_btn = gr.Button("✉️ Kirim Masukan", variant="primary", size="lg")
                    feedback_status = gr.Markdown("")
            
            # Event Handler
            submit_feedback_btn.click(
                fn=submit_feedback_to_cloud,
                inputs=[q_performa, q_manfaat, q_profesi, q_kendala, q_saran],
                outputs=[feedback_status]
            )


        # ===================================================================
        # TAB 6: PREMIUM & NOTIFIKASI
        # ===================================================================
        
        with gr.TabItem("⭐ Premium & Notifikasi", id=5):
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
                wa_link = f"httpska://wa.me/{CONTACT_WA}?text={wa_message.replace(' ', '%20')}"
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

        # ===================================================================
        # TAB 7: TENTANG & BANTUAN
        # ===================================================================
        
        with gr.TabItem("ℹ️ Tentang & Bantuan", id=6):
            gr.Markdown(f"""
            ## 🏥 Tentang {APP_TITLE}
            
            **{APP_TITLE}** adalah aplikasi pemantauan 
            pertumbuhan anak berbasis standar WHO Child Growth Standards 2006 dan 
            Permenkes RI No. 2 Tahun 2020.
            
            ### ✨ Fitur Utama (v3.2.2)
            
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
            
            5. **🎯 Fitur Baru (v3.2.2)**
               - **Mode Mudah:** Referensi cepat rentang normal
               - **Kalkulator Kejar Tumbuh:** Monitor laju/velocity pertumbuhan
               - **Perpustakaan Interaktif:** 40 artikel dengan search & filter
            
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

# === REVISI: PERBAIKAN LOGIKA INISIALISASI TAB ===
    # (Handler perpustakaan (id=4) telah dipindahkan ke dalam
    # definisi TabItem-nya sendiri menggunakan tab_perpustakaan.select()
    # untuk logika yang lebih bersih dan terisolasi)
    
# === AKHIR BLOK REVISI ===

    
# Footer (MODIFIED)
    gr.Markdown(f"""
    ---
    
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #fff5f8 0%, #ffe8f0 100%); 
    border-top: 2px solid #ffdde5;'>
        <p style='margin: 0; color: #555; font-size: 14px;'>
            {APP_TITLE} v{APP_VERSION} © 2024-2025 | Dibuat oleh <strong>Habib Arsy</strong>
        </p>
        <p style='margin: 5px 0 0 0; color: #888; font-size: 12px;'>
            Bukan pengganti konsultasi medis. Selalu konfirmasi dengan tenaga kesehatan.
        </p>
    </div>
    """) # <-- INI ADALAH PENUTUP YANG HILANG

print("✅ Section 11 (Gradio UI) dimodifikasi: Perpustakaan Interaktif v3.2.2 terintegrasi.")



# ===============================================================================
# SECTION 12: FASTAPI INTEGRATION (MODIFIED FOR v3.2.2)
# ===============================================================================

# Initialize FastAPI
app_fastapi = FastAPI(
    title=f"{APP_TITLE} API", # MODIFIED
    description=APP_DESCRIPTION,
    version="3.2.2", # MODIFIED
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# -------------------------------------------------------------------
# Helper: Filter artikel perpustakaan untuk API JSON
# -------------------------------------------------------------------

def _filter_library_items_for_api(
    q: str = "",
    kategori: str = "",
    sumber: str = "",
) -> List[Dict[str, Any]]:
    """
    Filter ARTIKEL_LOKAL_DATABASE untuk keperluan endpoint JSON.

    q        : keyword bebas (judul, ringkasan, isi)
    kategori : harus persis sama dengan field 'kategori' (jika diisi)
    sumber   : harus cocok dengan salah satu elemen pada 'source' (dipisah '|')
    """
    q = (q or "").strip().lower()
    kategori = (kategori or "").strip()
    sumber = (sumber or "").strip()

    results: List[Dict[str, Any]] = []

    for idx, art in enumerate(ARTIKEL_LOKAL_DATABASE):
        title = str(art.get("title", ""))
        summary = str(art.get("summary", ""))
        full_content = str(art.get("full_content", ""))
        art_kategori = str(art.get("kategori", ""))
        art_source_raw = str(art.get("source", ""))

        # Filter kategori (jika diminta)
        if kategori and art_kategori != kategori:
            continue

        # Filter sumber (jika diminta)
        if sumber:
            sources = [
                s.strip()
                for s in art_source_raw.split("|")
                if s.strip()
            ]
            if sumber not in sources:
                continue

        # Filter keyword (judul / summary / full)
        if q:
            combined = " ".join([title, summary, full_content]).lower()
            if q not in combined:
                continue

        # Untuk API list, kita tidak kirim full_content (biar ringkas)
        results.append(
            {
                "id": idx,
                "title": title,
                "kategori": art_kategori,
                "source": art_source_raw,
                "summary": summary,
            }
        )

    return results


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
        "version": "3.2.2", # MODIFIED
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
            "mode_mudah": True, 
            "growth_velocity": True, 
            "interactive_library_v3_2_2": True, # MODIFIED
        },
        "endpoints": {
            "main_app": "/",
            "api_docs": "/api/docs",
            "health": "/health",
        }
    }

# -------------------------------------------------------------------
# Pydantic Models untuk API Kejar Tumbuh
# -------------------------------------------------------------------

class KejarTumbuhDataPoint(BaseModel):
    usia_bulan: float
    bb: float
    tb: float


class KejarTumbuhRequest(BaseModel):
    gender: str  # "Laki-laki" atau "Perempuan"
    data: List[KejarTumbuhDataPoint]
    theme: Optional[str] = "pink_pastel"


# -------------------------------------------------------------------
# Endpoint API: Perpustakaan Ibu Balita (JSON)
# -------------------------------------------------------------------

@app_fastapi.get("/api/library/meta")
async def library_meta():
    """
    Metadata singkat Perpustakaan Ibu Balita:
    - jumlah artikel
    - daftar kategori
    - daftar sumber
    """
    try:
        kategori_list, sumber_list = get_local_library_filters()
        kategori_unik = sorted(set(kategori_list))
        sumber_unik = sorted(set(sumber_list))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal membaca metadata perpustakaan: {e}",
        )

    return {
        "jumlah_artikel": len(ARTIKEL_LOKAL_DATABASE),
        "kategori": kategori_unik,
        "sumber": sumber_unik,
    }


@app_fastapi.get("/api/library")
async def library_list(
    q: str = Query("", alias="q", description="Kata kunci bebas (judul, ringkasan, isi)"),
    kategori: str = Query("", alias="kategori", description="Filter kategori (opsional)"),
    sumber: str = Query("", alias="sumber", description="Filter sumber (opsional, persis teks sumber)"),
):
    """
    Mengembalikan daftar artikel Perpustakaan Ibu Balita dalam bentuk JSON.

    Contoh:
      - /api/library             -> semua artikel
      - /api/library?q=stunting  -> semua artikel yang mengandung kata 'stunting'
      - /api/library?kategori=Gizi
      - /api/library?sumber=Kemenkes RI
    """
    try:
        items = _filter_library_items_for_api(q=q, kategori=kategori, sumber=sumber)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal memproses filter perpustakaan: {e}",
        )

    return {
        "count": len(items),
        "items": items,
    }


@app_fastapi.get("/api/library/{item_id}")
async def library_detail(item_id: int):
    """
    Ambil detail satu artikel perpustakaan berdasarkan index (0-based).

    Catatan:
    - `item_id` di sini sama dengan index yang dipakai di front-end (kartu).
    """
    try:
        art = ARTIKEL_LOKAL_DATABASE[item_id]
    except (IndexError, TypeError):
        raise HTTPException(
            status_code=404,
            detail="Artikel perpustakaan tidak ditemukan",
        )

    return {
        "id": item_id,
        "title": art.get("title", ""),
        "kategori": art.get("kategori", ""),
        "source": art.get("source", ""),
        "summary": art.get("summary", ""),
        "full_content": art.get("full_content", ""),
    }

# -------------------------------------------------------------------
# Endpoint API: Kalkulator Kejar Tumbuh
# -------------------------------------------------------------------

@app_fastapi.post("/api/kejar-tumbuh/analyze")
async def kejar_tumbuh_analyze(payload: KejarTumbuhRequest):
    """
    Analisis Kejar Tumbuh via API.
    
    Body (JSON) contoh:
    {
      "gender": "Laki-laki",
      "theme": "pink_pastel",
      "data": [
        {"usia_bulan": 6.0, "bb": 7.2, "tb": 66.0},
        {"usia_bulan": 9.0, "bb": 7.8, "tb": 70.0}
      ]
    }
    """
    # Konversi Pydantic → list dict seperti yang digunakan kalkulator
    data_list = [
        {
            "usia_bulan": float(p.usia_bulan),
            "bb": float(p.bb),
            "tb": float(p.tb),
        }
        for p in payload.data
    ]

    if len(data_list) < 2:
        raise HTTPException(
            status_code=400,
            detail="Minimal diperlukan 2 pengukuran untuk analisis Kejar Tumbuh."
        )

    gender = payload.gender
    # Handler UI sudah menggunakan gender dalam bahasa Indonesia ("Laki-laki"/"Perempuan")
    html, plot_path = kalkulator_kejar_tumbuh_handler(data_list, gender)

    return {
        "gender": gender,
        "theme": payload.theme or "pink_pastel",
        "poin_pengukuran": len(data_list),
        "html": html,
        "plot_path": plot_path,  # path relatif di server (jika ingin diakses via /outputs)
    }


@app_fastapi.post("/api/kejar-tumbuh/plot")
async def kejar_tumbuh_plot(payload: KejarTumbuhRequest):
    """
    Menghasilkan file PNG grafik Kejar Tumbuh via API.

    Menggunakan fungsi plot_kejar_tumbuh_trajectory() yang sudah ada
    (versi CURVE SMOOTH yang kamu pasang di Part 1).
    """
    data_list = [
        {
            "usia_bulan": float(p.usia_bulan),
            "bb": float(p.bb),
            "tb": float(p.tb),
        }
        for p in payload.data
    ]

    if len(data_list) < 2:
        raise HTTPException(
            status_code=400,
            detail="Minimal diperlukan 2 pengukuran untuk membuat grafik Kejar Tumbuh."
        )

    gender = payload.gender
    theme = payload.theme or "pink_pastel"

    # Memakai fungsi plot yang sudah ada (tidak mengubah logic internal)
    plot_path = plot_kejar_tumbuh_trajectory(data_list, gender, theme_name=theme)

    if not plot_path or not os.path.exists(plot_path):
        raise HTTPException(
            status_code=500,
            detail="Gagal menghasilkan grafik Kejar Tumbuh."
        )

    filename = os.path.basename(plot_path)

    return FileResponse(
        plot_path,
        media_type="image/png",
        filename=filename,
    )


# API info endpoint
@app_fastapi.get("/api/info")
async def api_info():
    """Get API information"""
    return {
        "app_name": APP_TITLE,
        "version": "3.2.2", # MODIFIED
        "description": APP_DESCRIPTION,
        "author": "Habib Arsy - FKIK Universitas Jambi",
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
            "Perpustakaan Artikel Interaktif (v3.2.2)" # MODIFIED
        ]
    }

# Root redirect
@app_fastapi.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": f"Selamat datang di {APP_TITLE} API",
        "version": "3.2.2", # MODIFIED
        "docs": "/api/docs",
        "health": "/health",
        "main_app": "/"
    }

print("✅ Section 12 (FastAPI) dimodifikasi: API info v3.2.2 terkonfigurasi.")


# ===============================================================================
# SECTION 13: APPLICATION STARTUP (MODIFIED FOR v3.2.2)
# ===============================================================================

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

# Print startup banner (MODIFIED)
print("")
print("=" * 80)
print(f"🚀 {APP_TITLE} v3.2.2 - READY FOR DEPLOYMENT".center(80))
print("=" * 80)
print(f"📊 WHO Calculator: {'✅ Operational' if calc else '❌ Unavailable'}")
print(f"🌐 Base URL: {BASE_URL}")
print(f"📱 Contact: +{CONTACT_WA}")
print(f"🎨 Themes: {len(UI_THEMES)} available")
print(f"💉 Immunization: {len(IMMUNIZATION_SCHEDULE)} schedules")
print(f"🧠 KPSP: {len(KPSP_QUESTIONS)} question sets")
print(f"📚 Perpustakaan Ibu Balita: {len(ARTIKEL_LOKAL_DATABASE)} artikel lokal")  # MODIFIED
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

