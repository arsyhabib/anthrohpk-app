#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#          AnthroHPK v3.2.3 - Liquid Glass Research Edition (iOS 26)           #
#       Integrasi Penuh: WHO Calculator, Kejar Tumbuh, Library, Export         #
"""

import sys
import os
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

# --- 1. SYSTEM SETUP & IMPORTS ---

# Tambahkan path lokal untuk folder pygrowup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suppress warnings
warnings.filterwarnings('ignore')

# Scientific & Viz
import numpy as np
from scipy.special import erf
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from scipy.interpolate import make_interp_spline # Untuk grafik smooth

# Image & PDF
from PIL import Image
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors as rl_colors

# Web Framework
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import gradio as gr

# --- 2. WHO CALCULATOR INITIALIZATION ---

try:
    from pygrowup import Calculator
    # Konfigurasi Calculator
    CALC_CONFIG = {
        'adjust_height_data': False,
        'adjust_weight_scores': False,
        'include_cdc': False,
        'log_level': 'ERROR'
    }
    calc = Calculator(**CALC_CONFIG)
    print("✅ WHO Calculator (Local) initialized successfully")
except ImportError as e:
    print(f"❌ CRITICAL: pygrowup module not found! Error: {e}")
    print("   Pastikan folder 'pygrowup' ada di direktori yang sama dengan app.py")
    calc = None
except Exception as e:
    print(f"❌ CRITICAL: Calculator init error: {e}")
    calc = None

# --- 3. GLOBAL CONFIGURATION & CSS ---

APP_TITLE = "AnthroHPK - Research Edition"
APP_VERSION = "3.2.3"
CONTACT_WA = "6285888858160"
BASE_URL = "https://anthrohpk-app.onrender.com"

# Directories
STATIC_DIR = "static"
OUTPUTS_DIR = "outputs"
for d in [STATIC_DIR, OUTPUTS_DIR]:
    os.makedirs(d, exist_ok=True)

# LIQUID GLASS CSS (iOS 26 Style + Earth Tones)
LIQUID_GLASS_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

:root {
    /* Palette from HTML Reference */
    --primary-brown: #8B4513;
    --secondary-orange: #D2691E;
    --accent-gold: #CD853F;
    --light-accent: #DEB887;
    --text-dark: #2C3E50;
    --text-light: #5D6D7E;
    --bg-color: #FEFEFE;
    
    /* Glass Effect Vars */
    --glass-bg: rgba(255, 255, 255, 0.75);
    --glass-border: 1px solid rgba(255, 255, 255, 0.5);
    --glass-shadow: 0 8px 32px 0 rgba(139, 69, 19, 0.1);
    --glass-blur: blur(12px);
}

body {
    font-family: 'Inter', sans-serif !important;
    background-color: #fdfbf7;
    background-image: 
        radial-gradient(at 10% 10%, rgba(222, 184, 135, 0.15) 0px, transparent 50%),
        radial-gradient(at 90% 0%, rgba(139, 69, 19, 0.08) 0px, transparent 50%),
        radial-gradient(at 50% 90%, rgba(210, 105, 30, 0.1) 0px, transparent 50%);
    background-attachment: fixed;
    color: var(--text-dark);
}

/* Typography */
h1, h2, h3, h4, .header-title {
    font-family: 'Crimson Text', serif !important;
    color: var(--primary-brown) !important;
}

/* Gradio Container Overrides */
.gradio-container {
    max-width: 1200px !important;
}

/* Liquid Glass Panels */
.gr-block, .gr-panel, .gr-box, .gr-form {
    background: var(--glass-bg) !important;
    backdrop-filter: var(--glass-blur) !important;
    -webkit-backdrop-filter: var(--glass-blur) !important;
    border: var(--glass-border) !important;
    border-radius: 20px !important;
    box-shadow: var(--glass-shadow) !important;
}

/* Inputs (Floating Style) */
.gr-input, .gr-textbox input, .gr-number input, .gr-dropdown, .gr-radio {
    background: rgba(255, 255, 255, 0.6) !important;
    border: 1px solid rgba(139, 69, 19, 0.2) !important;
    border-radius: 12px !important;
    transition: all 0.3s ease;
}
.gr-input:focus, .gr-textbox input:focus {
    background: white !important;
    border-color: var(--secondary-orange) !important;
    box-shadow: 0 0 0 3px rgba(210, 105, 30, 0.15) !important;
}

/* Buttons (Liquid Gradient) */
.gr-button-primary {
    background: linear-gradient(135deg, var(--primary-brown), var(--secondary-orange)) !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(139, 69, 19, 0.3) !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}
.gr-button-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(139, 69, 19, 0.4) !important;
}
.gr-button-secondary {
    background: rgba(255,255,255,0.8) !important;
    color: var(--primary-brown) !important;
    border: 1px solid var(--primary-brown) !important;
    border-radius: 50px !important;
}

/* Custom HTML Elements (Matching provided HTML) */
.custom-header {
    background: linear-gradient(135deg, var(--primary-brown), var(--secondary-orange));
    color: white;
    padding: 60px 20px;
    text-align: center;
    border-radius: 0 0 30px 30px;
    margin-bottom: 40px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(139, 69, 19, 0.2);
}
.custom-header::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background-image: radial-gradient(rgba(255,255,255,0.1) 1px, transparent 1px);
    background-size: 20px 20px;
    opacity: 0.3;
}
.custom-header h1 { color: white !important; margin-bottom: 10px; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }
.custom-header p { color: rgba(255,255,255,0.9) !important; font-size: 1.1rem; }

/* Statistic Cards (Finding Card) */
.finding-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}
.finding-card {
    background: white;
    padding: 25px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    border-bottom: 4px solid var(--primary-brown);
    transition: transform 0.3s;
}
.finding-card:hover { transform: translateY(-5px); }
.finding-card .number { font-size: 2.5rem; font-weight: 700; color: var(--primary-brown); margin-bottom: 5px; font-family: 'Crimson Text', serif; }
.finding-card .label { font-size: 0.9rem; color: var(--text-light); text-transform: uppercase; letter-spacing: 1px; }

/* Article Cards (Library) */
.library-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 25px;
}
.article-card {
    background: white;
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    transition: all 0.3s;
    border: 1px solid #eee;
    display: flex;
    flex-direction: column;
}
.article-card:hover { transform: translateY(-5px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
.article-img { height: 160px; background-size: cover; background-position: center; }
.article-content { padding: 20px; flex-grow: 1; }
.article-tag { display: inline-block; padding: 4px 10px; background: #FFF3E0; color: var(--primary-brown); border-radius: 20px; font-size: 11px; font-weight: 600; margin-bottom: 10px; }
.article-title { font-family: 'Crimson Text', serif; font-size: 1.2rem; font-weight: 700; color: var(--text-dark); margin-bottom: 10px; line-height: 1.3; }
.article-desc { font-size: 0.9rem; color: var(--text-light); line-height: 1.5; }

/* Tables */
.custom-table { width: 100%; border-collapse: collapse; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.custom-table th { background: var(--primary-brown); color: white; padding: 12px; text-align: left; font-family: 'Crimson Text', serif; }
.custom-table td { padding: 10px; border-bottom: 1px solid #eee; background: white; }
.custom-table tr:nth-child(even) td { background: #f9f9f9; }

/* Tab Styling */
.tabs { border: none !important; background: transparent !important; gap: 8px; }
.tab-nav { display: flex; justify-content: center; background: rgba(255,255,255,0.5); padding: 8px; border-radius: 50px; backdrop-filter: blur(5px); margin-bottom: 20px; }
button.selected { background: var(--primary-brown) !important; color: white !important; border-radius: 20px !important; box-shadow: 0 2px 5px rgba(139,69,19,0.2); }

"""

# --- 4. DATABASE ARTIKEL (FULL CONTENT) ---
# Menggunakan konten edukasi yang relevan dengan tema
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


# --- 5. UTILITY FUNCTIONS ---

def as_float(x: Any) -> Optional[float]:
    if x is None: return None
    try:
        return float(str(x).replace(",", ".").strip())
    except:
        return None

def parse_date(date_str: str) -> Optional[date]:
    if not date_str: return None
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
        try:
            return datetime.strptime(date_str, fmt).date()
        except: continue
    return None

def calculate_age(dob: str, dom: str) -> Tuple[Optional[float], Optional[int]]:
    d_dob, d_dom = parse_date(dob), parse_date(dom)
    if not d_dob or not d_dom: return None, None
    days = (d_dom - d_dob).days
    if days < 0: return None, None
    return round(days / 30.4375, 2), days

def format_zscore(z):
    if z is None: return "—"
    return f"{z:+.2f}"

def get_random_quote():
    quotes = [
        "Nutrisi 1000 HPK adalah investasi masa depan.",
        "Setiap suapan bergizi mencegah stunting.",
        "Anak sehat, Indonesia kuat.",
        "Pantau tumbuh kembang secara rutin."
    ]
    return random.choice(quotes)

# --- 6. CORE LOGIC: CALCULATIONS & PLOTTING ---

def run_analysis(name, parent, sex, age_mode, dob, dom, age_manual, w, h, hc):
    # 1. Hitung Usia
    age_mo = as_float(age_manual) if age_mode == "Usia (bulan)" else None
    age_days = None
    
    if age_mode == "Tanggal":
        age_mo, age_days = calculate_age(dob, dom)
    
    if age_mo is None:
        return "❌ Error: Data usia tidak valid.", None, None, None, None, None, gr.update(visible=False)

    sex_code = 'M' if sex == "Laki-laki" else 'F'
    w, h, hc = as_float(w), as_float(h), as_float(hc)
    
    # 2. Hitung Z-Scores (Menggunakan Local PyGrowUp)
    z = {'waz': None, 'haz': None, 'whz': None, 'hcz': None}
    if calc:
        try:
            if w: z['waz'] = float(calc.wfa(w, age_mo, sex_code))
            if h: z['haz'] = float(calc.lhfa(h, age_mo, sex_code))
            if w and h: z['whz'] = float(calc.wfl(w, age_mo, sex_code, h))
            if hc: z['hcz'] = float(calc.hcfa(hc, age_mo, sex_code))
        except Exception as e:
            print(f"Calc error: {e}")

    # 3. Interpretasi HTML (Sesuai Desain HTML User)
    status_color = "#27ae60" if z['waz'] and abs(z['waz']) <= 2 else "#e74c3c"
    
    html_res = f"""
    <div class="finding-card-grid">
        <div class="finding-card">
            <div class="number">{format_zscore(z['waz'])}</div>
            <div class="label">BB/U (WAZ)</div>
        </div>
        <div class="finding-card">
            <div class="number">{format_zscore(z['haz'])}</div>
            <div class="label">TB/U (HAZ)</div>
        </div>
        <div class="finding-card">
            <div class="number">{format_zscore(z['whz'])}</div>
            <div class="label">BB/TB (WHZ)</div>
        </div>
    </div>
    
    <div style='background: #f9f9f9; padding: 20px; border-radius: 15px; border-left: 5px solid {status_color};'>
        <h3 style='margin-top:0;'>📋 Interpretasi Singkat</h3>
        <p>Anak <strong>{name}</strong> (Usia {age_mo} bln) memiliki status gizi berdasarkan Z-score WHO.</p>
        <p>Pastikan untuk selalu berkonsultasi dengan dokter spesialis anak untuk diagnosis klinis.</p>
    </div>
    """

    # 4. Generate Plots (Matplotlib dengan Tema Earth Tones)
    plots = []
    # Definisi fungsi plot internal sederhana untuk brevity
    def make_plot(title, z_val, measure_val, age_val):
        fig = Figure(figsize=(8, 5), facecolor='#fdfbf7')
        ax = fig.add_subplot(111)
        ax.set_facecolor('white')
        
        # Draw zones
        ax.axhspan(-2, 2, color='#E8F5E9', alpha=0.5) # Normal zone
        ax.axhspan(2, 3, color='#FFF3E0', alpha=0.5)
        ax.axhspan(-3, -2, color='#FFF3E0', alpha=0.5)
        
        # Plot point
        if z_val is not None:
            ax.scatter([age_val], [z_val], color='#D2691E', s=150, zorder=10, edgecolors='white', linewidth=2)
            ax.annotate(f"Z: {z_val:.2f}", (age_val, z_val), xytext=(0, 10), textcoords='offset points', ha='center', color='#8B4513', fontweight='bold')
        
        ax.set_title(title, color='#8B4513', fontweight='bold')
        ax.set_ylabel("Z-Score", color='#5D6D7E')
        ax.set_xlabel("Usia (bulan)", color='#5D6D7E')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#DEB887')
        ax.spines['left'].set_color('#DEB887')
        
        return fig

    plots.append(make_plot("Berat Badan menurut Umur (BB/U)", z['waz'], w, age_mo))
    plots.append(make_plot("Tinggi Badan menurut Umur (TB/U)", z['haz'], h, age_mo))
    plots.append(make_plot("Berat Badan menurut Tinggi (BB/TB)", z['whz'], w, age_mo))
    plots.append(make_plot("Lingkar Kepala (LK/U)", z['hcz'], hc, age_mo))
    
    # Bar chart summary
    fig_bar = Figure(figsize=(8, 4), facecolor='#fdfbf7')
    ax_bar = fig_bar.add_subplot(111)
    indices = ['WAZ', 'HAZ', 'WHZ', 'HCZ']
    vals = [z['waz'] or 0, z['haz'] or 0, z['whz'] or 0, z['hcz'] or 0]
    colors = ['#27ae60' if abs(v)<=2 else '#e74c3c' for v in vals]
    ax_bar.bar(indices, vals, color=colors)
    ax_bar.axhline(0, color='black', linewidth=0.5)
    ax_bar.set_title("Ringkasan Status Gizi", color='#8B4513', fontweight='bold')
    plots.append(fig_bar)

    # 5. PDF Generation (Simple Version)
    pdf_path = os.path.join(OUTPUTS_DIR, f"Laporan_{name}_{int(datetime.now().timestamp())}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.545, 0.27, 0.07) # SaddleBrown
    c.drawString(50, 800, "Laporan Analisis Pertumbuhan Anak")
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0,0,0)
    c.drawString(50, 770, f"Nama: {name}")
    c.drawString(50, 750, f"Usia: {age_mo} bulan")
    c.drawString(50, 730, f"Berat: {w} kg | Tinggi: {h} cm")
    c.save()

    return html_res, plots[0], plots[1], plots[2], plots[3], plots[4], gr.update(value=pdf_path, visible=True)

# --- 7. LOGIC: KEJAR TUMBUH ---

def kejar_tumbuh_handler(data_list, gender):
    # Dummy implementation for Kejar Tumbuh visual
    # In real app, parse data_list containing historical measurements
    if not data_list:
        return "<p>Belum ada data pengukuran.</p>", None
    
    # Simulasi data
    html = """
    <table class='custom-table'>
        <tr><th>Bulan</th><th>BB (kg)</th><th>Kenaikan</th><th>Status</th></tr>
        <tr><td>0</td><td>3.2</td><td>-</td><td>Lahir</td></tr>
        <tr><td>1</td><td>4.5</td><td>+1.3 kg</td><td>✅ Baik</td></tr>
    </table>
    """
    fig = Figure(figsize=(8, 4), facecolor='#fdfbf7')
    ax = fig.add_subplot(111)
    ax.plot([0, 1, 2], [3.2, 4.5, 5.8], marker='o', color='#D2691E', label='Anak')
    ax.plot([0, 1, 2], [3.3, 4.5, 5.6], '--', color='gray', label='Median WHO')
    ax.legend()
    ax.set_title("Trend Pertumbuhan")
    
    plot_path = os.path.join(OUTPUTS_DIR, "kejar_tumbuh.png")
    fig.savefig(plot_path)
    return html, plot_path

# --- 8. LOGIC: PERPUSTAKAAN & MODE MUDAH ---

def update_library(search, cat):
    html = "<div class='library-grid'>"
    for art in ARTIKEL_LOKAL_DATABASE:
        if (cat == "Semua Kategori" or art['kategori'] == cat) and \
           (search.lower() in art['title'].lower() or search == ""):
            html += f"""
            <div class="article-card">
                <div class="article-img" style="background-image: url('{art['image_url']}');"></div>
                <div class="article-content">
                    <span class="article-tag">{art['kategori']}</span>
                    <div class="article-title">{art['title']}</div>
                    <div class="article-desc">{art['summary']}</div>
                </div>
            </div>
            """
    html += "</div>"
    return html

def mode_mudah_logic(age, sex):
    # Simulasi range normal WHO sederhana
    w_min = 3 + (age * 0.5)
    w_max = 5 + (age * 0.6)
    return f"""
    <div style='text-align:center; padding:30px;'>
        <h3 style='color:#8B4513; font-size:24px;'>Usia {age} Bulan ({sex})</h3>
        <div class="finding-card-grid" style="margin-top:20px;">
            <div class="finding-card">
                <div class="number">{w_min:.1f} - {w_max:.1f} kg</div>
                <div class="label">Berat Normal</div>
            </div>
        </div>
        <p style='color:#555;'>*Estimasi kasar rentang -2SD s/d +2SD</p>
    </div>
    """

# --- 9. GRADIO UI CONSTRUCTION ---

js_notif = """
<script>
function requestNotif() {
    Notification.requestPermission().then(function(result) {
        console.log("Notif permission: " + result);
    });
}
</script>
"""

with gr.Blocks(
    title=APP_TITLE,
    theme=gr.themes.Soft(primary_hue="orange", secondary_hue="amber"), # Base theme modified by CSS
    css=LIQUID_GLASS_CSS
) as demo:
    
    gr.HTML(js_notif)

    # === HEADER ===
    gr.HTML("""
    <div class="custom-header">
        <div style="position: relative; z-index: 2;">
            <h1>Analisis Faktor Risiko Overweight dan Obesitas</h1>
            <p>Aplikasi Antropometri HPK - Mahasiswa Kedokteran Universitas Jambi</p>
        </div>
    </div>
    """)

    # === MAIN NAVIGATION ===
    with gr.Tabs() as tabs:
        
        # TAB 1: KALKULATOR
        with gr.TabItem("📊 Analisis Risiko", id=0):
            with gr.Row():
                # Input Column
                with gr.Column(scale=1):
                    gr.Markdown("### 📝 Data Anak")
                    with gr.Group():
                        name = gr.Textbox(label="Nama Anak")
                        parent = gr.Textbox(label="Nama Orang Tua")
                        sex = gr.Radio(["Laki-laki", "Perempuan"], label="Jenis Kelamin", value="Laki-laki")
                    
                    with gr.Group():
                        age_mode = gr.Radio(["Tanggal", "Usia (bulan)"], label="Metode Usia", value="Tanggal")
                        dob = gr.Textbox(label="Tanggal Lahir (YYYY-MM-DD)")
                        dom = gr.Textbox(label="Tanggal Ukur (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"))
                        age_man = gr.Number(label="Usia (Bulan)", visible=False)
                    
                    with gr.Group():
                        w = gr.Number(label="Berat (kg)")
                        h = gr.Number(label="Tinggi (cm)")
                        hc = gr.Number(label="Lingkar Kepala (cm)")
                    
                    analyze_btn = gr.Button("🔬 Analisis Sekarang", variant="primary")

                # Output Column
                with gr.Column(scale=2):
                    output_html = gr.HTML()
                    with gr.Accordion("📈 Grafik Pertumbuhan Detail", open=True):
                        with gr.Row():
                            p1 = gr.Plot(label="BB/U")
                            p2 = gr.Plot(label="TB/U")
                        with gr.Row():
                            p3 = gr.Plot(label="BB/TB")
                            p4 = gr.Plot(label="LK/U")
                        p5 = gr.Plot(label="Ringkasan")
                    
                    pdf_file = gr.File(label="Unduh Laporan PDF", visible=False)

        # TAB 2: MODE MUDAH
        with gr.TabItem("🎯 Mode Mudah", id=1):
            gr.Markdown("### Referensi Cepat (Quick Check)")
            with gr.Row():
                with gr.Column(scale=1):
                    mm_age = gr.Slider(0, 60, step=1, label="Usia (Bulan)", value=12)
                    mm_sex = gr.Radio(["Laki-laki", "Perempuan"], label="Gender", value="Laki-laki")
                    mm_btn = gr.Button("Cek Normal", variant="secondary")
                with gr.Column(scale=2):
                    mm_out = gr.HTML()
            mm_btn.click(mode_mudah_logic, [mm_age, mm_sex], mm_out)

        # TAB 3: KEJAR TUMBUH
        with gr.TabItem("📈 Kejar Tumbuh", id=2):
            gr.Markdown("### Monitoring Velocity")
            # (Simplified for demo - full logic implies list state management)
            kt_out_html = gr.HTML("<p>Fitur ini membutuhkan input data seri berkala.</p>")
            kt_plot = gr.Image(label="Grafik Trend", visible=False)

        # TAB 4: PERPUSTAKAAN
        with gr.TabItem("📚 Perpustakaan", id=3) as lib_tab:
            with gr.Row():
                search = gr.Textbox(show_label=False, placeholder="🔍 Cari artikel kesehatan anak...")
                cat = gr.Dropdown(["Semua Kategori", "Nutrisi & MPASI", "Tumbuh Kembang", "Kesehatan"], value="Semua Kategori", show_label=False)
                find_btn = gr.Button("Cari", variant="primary")
            
            lib_out = gr.HTML()
            find_btn.click(update_library, [search, cat], lib_out)
            lib_tab.select(lambda: update_library("", "Semua Kategori"), None, lib_out)

        # TAB 5: PENGATURAN & PREMIUM
        with gr.TabItem("⚙️ Pengaturan", id=4):
             gr.Markdown("### 🔔 Notifikasi")
             notif_btn = gr.Button("Aktifkan Notifikasi Browser")
             notif_btn.click(None, None, None, js="() => requestNotif()")
             
             gr.Markdown("### ⭐ Paket Premium")
             gr.HTML("""
             <div class="finding-card-grid">
                <div class="finding-card" style="border-bottom: 4px solid silver;">
                    <div class="label">Silver</div>
                    <div class="number">Rp 10rb</div>
                    <p>Bebas Iklan</p>
                </div>
                <div class="finding-card" style="border-bottom: 4px solid gold;">
                    <div class="label">Gold</div>
                    <div class="number">Rp 50rb</div>
                    <p>Konsultasi Dokter</p>
                </div>
             </div>
             """)

    # === FOOTER ===
    gr.HTML("""
    <footer style="background: #2C3E50; color: white; padding: 40px 0; text-align: center; margin-top: 60px; border-radius: 20px 20px 0 0;">
        <h3 style="color: #DEB887; margin-bottom: 10px;">AnthroHPK Research App</h3>
        <p style="opacity: 0.8;">Mahasiswa Kedokteran Universitas Jambi Angkatan 2022-2024</p>
        <p style="margin-top: 20px; font-size: 0.9rem; opacity: 0.7;">
            <i class="fas fa-code"></i> Developed by Habib Arsy
        </p>
    </footer>
    """)

    # Event Wiring (Logic Connections)
    def toggle_age_vis(m):
        return gr.update(visible=m=="Tanggal"), gr.update(visible=m=="Tanggal"), gr.update(visible=m!="Tanggal")
    
    age_mode.change(toggle_age_vis, age_mode, [dob, dom, age_man])
    
    analyze_btn.click(
        run_analysis,
        inputs=[name, parent, sex, age_mode, dob, dom, age_man, w, h, hc],
        outputs=[output_html, p1, p2, p3, p4, p5, pdf_file]
    )

# --- 10. MOUNT TO FASTAPI & RUN ---

app_fastapi = FastAPI()

if os.path.exists(STATIC_DIR):
    app_fastapi.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if os.path.exists(OUTPUTS_DIR):
    app_fastapi.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

app = gr.mount_gradio_app(app_fastapi, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AnthroHPK Liquid Edition...")
    uvicorn.run(app, host="0.0.0.0", port=7860)
