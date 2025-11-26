#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#==============================================================================
#                    AnthroHPK v4.0 - FIRST 1000 DAYS MODULE
#              1000 Hari Pertama Kehidupan - Fitur Inovatif Baru
#==============================================================================
"""

from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
import math

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FIRST_1000_DAYS_PHASES

# ==============================================================================
# DATA 1000 HPK (HARI PERTAMA KEHIDUPAN)
# ==============================================================================

# Fokus nutrisi per fase
NUTRITION_FOCUS = {
    "kehamilan_trimester1": {
        "title": "Trimester 1 (Minggu 1-12)",
        "focus": "Pembentukan Organ",
        "nutrients": [
            {"name": "Asam Folat", "amount": "600 mcg/hari", "source": "Sayuran hijau, kacang-kacangan, suplemen", "benefit": "Mencegah cacat tabung saraf"},
            {"name": "Zat Besi", "amount": "27 mg/hari", "source": "Daging merah, hati, bayam", "benefit": "Mencegah anemia"},
            {"name": "Vitamin B12", "amount": "2.6 mcg/hari", "source": "Daging, telur, susu", "benefit": "Pembentukan sel darah"}
        ],
        "tips": ["Atasi mual dengan makan sedikit-sedikit", "Hindari makanan mentah", "Istirahat cukup"]
    },
    "kehamilan_trimester2": {
        "title": "Trimester 2 (Minggu 13-26)",
        "focus": "Pertumbuhan Janin",
        "nutrients": [
            {"name": "Protein", "amount": "+25 gram/hari", "source": "Daging, ikan, telur, tahu", "benefit": "Pertumbuhan jaringan"},
            {"name": "Kalsium", "amount": "1000 mg/hari", "source": "Susu, keju, teri", "benefit": "Pembentukan tulang"},
            {"name": "DHA", "amount": "200 mg/hari", "source": "Ikan laut, suplemen", "benefit": "Perkembangan otak"}
        ],
        "tips": ["Kalori tambahan 340 kkal/hari", "Olahraga ringan teratur", "Pemeriksaan USG rutin"]
    },
    "kehamilan_trimester3": {
        "title": "Trimester 3 (Minggu 27-40)",
        "focus": "Pematangan Organ",
        "nutrients": [
            {"name": "Protein", "amount": "+25 gram/hari", "source": "Beragam sumber protein", "benefit": "Persiapan ASI"},
            {"name": "Zat Besi", "amount": "27 mg/hari", "source": "Hati, daging, suplemen", "benefit": "Cadangan besi bayi"},
            {"name": "Vitamin D", "amount": "600 IU/hari", "source": "Sinar matahari, ikan, suplemen", "benefit": "Mineralisasi tulang"}
        ],
        "tips": ["Kalori tambahan 450 kkal/hari", "Persiapan menyusui", "Persiapan persalinan"]
    },
    "0_6_bulan": {
        "title": "Bayi 0-6 Bulan",
        "focus": "ASI Eksklusif",
        "nutrients": [
            {"name": "ASI", "amount": "On demand (8-12x/hari)", "source": "Ibu menyusui", "benefit": "Nutrisi lengkap + antibodi"}
        ],
        "tips": ["IMD segera setelah lahir", "Tidak perlu air/makanan lain", "Skin-to-skin contact"]
    },
    "6_9_bulan": {
        "title": "Bayi 6-9 Bulan",
        "focus": "Pengenalan MPASI",
        "nutrients": [
            {"name": "Protein Hewani", "amount": "Di setiap makan", "source": "Telur, hati, ikan", "benefit": "Cegah anemia & stunting"},
            {"name": "Zat Besi", "amount": "11 mg/hari", "source": "Hati, daging merah", "benefit": "Perkembangan otak"},
            {"name": "Zinc", "amount": "3 mg/hari", "source": "Daging, kerang", "benefit": "Pertumbuhan & imunitas"}
        ],
        "tips": ["MPASI 2-3x sehari + ASI", "Tekstur halus ke kasar", "1 makanan baru per 3 hari"]
    },
    "9_12_bulan": {
        "title": "Bayi 9-12 Bulan",
        "focus": "Variasi & Tekstur",
        "nutrients": [
            {"name": "Protein", "amount": "11 gram/hari", "source": "Beragam sumber", "benefit": "Pertumbuhan optimal"},
            {"name": "Kalsium", "amount": "270 mg/hari", "source": "Susu, keju, sayuran hijau", "benefit": "Tulang & gigi"},
            {"name": "Lemak", "amount": "30-40% kalori", "source": "EVOO, santan, mentega", "benefit": "Perkembangan otak"}
        ],
        "tips": ["3x makan + 2x snack + ASI", "Finger food untuk self-feeding", "Variasi menu harian"]
    },
    "12_24_bulan": {
        "title": "Balita 12-24 Bulan",
        "focus": "Menu Keluarga",
        "nutrients": [
            {"name": "Protein", "amount": "13 gram/hari", "source": "Menu keluarga", "benefit": "Pertumbuhan berkelanjutan"},
            {"name": "Energi", "amount": "1000-1200 kkal/hari", "source": "Makanan seimbang", "benefit": "Aktivitas & pertumbuhan"}
        ],
        "tips": ["Menu keluarga dengan modifikasi", "Prinsip gizi seimbang", "Hindari junk food"]
    }
}

# Stimulasi per fase
STIMULATION_GUIDE = {
    "kehamilan": [
        {"activity": "Bicara dengan janin", "benefit": "Stimulasi pendengaran", "frequency": "Setiap hari"},
        {"activity": "Dengarkan musik klasik", "benefit": "Perkembangan otak", "frequency": "15-30 menit/hari"},
        {"activity": "Baca buku keras", "benefit": "Bonding & stimulasi", "frequency": "Setiap malam"},
        {"activity": "Usap perut lembut", "benefit": "Stimulasi sentuhan", "frequency": "Saat bonding time"}
    ],
    "0_3_bulan": [
        {"activity": "Tummy time", "benefit": "Kekuatan leher & punggung", "frequency": "3-5 menit, beberapa kali/hari"},
        {"activity": "Bicara & bernyanyi", "benefit": "Perkembangan bahasa", "frequency": "Sesering mungkin"},
        {"activity": "Mainan kontras (hitam-putih)", "benefit": "Stimulasi penglihatan", "frequency": "Saat bermain"},
        {"activity": "Skin-to-skin", "benefit": "Bonding & regulasi suhu", "frequency": "Setiap hari"}
    ],
    "4_6_bulan": [
        {"activity": "Bermain cilukba", "benefit": "Permanensi objek", "frequency": "Beberapa kali/hari"},
        {"activity": "Mainan kerincingan", "benefit": "Koordinasi tangan-mata", "frequency": "Saat bermain"},
        {"activity": "Cermin", "benefit": "Pengenalan diri", "frequency": "Saat bermain"},
        {"activity": "Bacakan buku bergambar", "benefit": "Perkembangan bahasa", "frequency": "Setiap hari"}
    ],
    "7_9_bulan": [
        {"activity": "Bermain bola", "benefit": "Motorik kasar", "frequency": "Setiap hari"},
        {"activity": "Mainan susun/sortir", "benefit": "Problem solving", "frequency": "Saat bermain"},
        {"activity": "Tepuk tangan & musik", "benefit": "Koordinasi & ritme", "frequency": "Beberapa kali/hari"},
        {"activity": "Eksplorasi aman", "benefit": "Curiosity & motorik", "frequency": "Saat aktif"}
    ],
    "10_12_bulan": [
        {"activity": "Jalan berpegangan", "benefit": "Persiapan berjalan", "frequency": "Setiap hari"},
        {"activity": "Bermain petak umpet sederhana", "benefit": "Kognitif & sosial", "frequency": "Saat bermain"},
        {"activity": "Menumpuk balok", "benefit": "Motorik halus", "frequency": "Saat bermain"},
        {"activity": "Menunjuk & menyebut nama benda", "benefit": "Bahasa", "frequency": "Sepanjang hari"}
    ],
    "13_18_bulan": [
        {"activity": "Bermain pura-pura", "benefit": "Imajinasi & sosial", "frequency": "Setiap hari"},
        {"activity": "Menggambar/mewarnai", "benefit": "Motorik halus & kreativitas", "frequency": "Beberapa kali/minggu"},
        {"activity": "Bermain air/pasir", "benefit": "Sensori & eksplorasi", "frequency": "Dengan pengawasan"},
        {"activity": "Baca buku interaktif", "benefit": "Bahasa & kognitif", "frequency": "Setiap hari"}
    ],
    "19_24_bulan": [
        {"activity": "Bermain dengan teman sebaya", "benefit": "Sosial-emosional", "frequency": "Beberapa kali/minggu"},
        {"activity": "Puzzle sederhana", "benefit": "Problem solving", "frequency": "Saat bermain"},
        {"activity": "Bernyanyi & gerak", "benefit": "Bahasa & motorik", "frequency": "Setiap hari"},
        {"activity": "Membantu pekerjaan rumah sederhana", "benefit": "Kemandirian", "frequency": "Setiap hari"}
    ]
}

# Red flags per fase
RED_FLAGS = {
    "0_3_bulan": [
        "Tidak merespon suara keras",
        "Tidak menatap wajah",
        "Tidak tersenyum sama sekali",
        "Sangat lemas atau sangat kaku"
    ],
    "4_6_bulan": [
        "Tidak bisa mengangkat kepala saat tengkurap",
        "Tidak meraih benda",
        "Tidak mengeluarkan suara",
        "Tidak tertawa"
    ],
    "7_9_bulan": [
        "Tidak bisa duduk dengan bantuan",
        "Tidak babbling",
        "Tidak merespon nama",
        "Tidak menunjukkan emosi"
    ],
    "10_12_bulan": [
        "Tidak bisa berdiri berpegangan",
        "Tidak mengucapkan satu kata pun",
        "Tidak menunjuk",
        "Kehilangan kemampuan yang sudah dikuasai"
    ],
    "13_18_bulan": [
        "Tidak bisa berjalan di usia 18 bulan",
        "Kosakata < 6 kata di usia 18 bulan",
        "Tidak meniru orang lain",
        "Tidak merespon instruksi sederhana"
    ],
    "19_24_bulan": [
        "Kosakata < 50 kata di usia 24 bulan",
        "Tidak bisa membuat kalimat 2 kata",
        "Tidak bermain pura-pura",
        "Tidak menunjukkan minat pada anak lain"
    ]
}


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def calculate_1000_days_progress(dob: date, measurement_date: date = None) -> Dict:
    """
    Calculate progress in 1000 first days
    
    Args:
        dob: Date of birth
        measurement_date: Reference date (default: today)
        
    Returns:
        Progress information dictionary
    """
    if measurement_date is None:
        measurement_date = date.today()
    
    days_lived = (measurement_date - dob).days
    total_days = 730  # 2 years from birth
    
    percentage = min(100, max(0, (days_lived / total_days) * 100))
    
    # Determine current phase
    if days_lived < 0:
        phase = "pre_birth"
        phase_name = "Sebelum Lahir"
        phase_icon = "🤰"
        phase_color = "#FFB6C1"
    elif days_lived <= 90:  # 0-3 bulan
        phase = "0_3_bulan"
        phase_name = "Bayi Baru Lahir (0-3 bulan)"
        phase_icon = "👶"
        phase_color = "#87CEEB"
    elif days_lived <= 180:  # 3-6 bulan
        phase = "3_6_bulan"
        phase_name = "Bayi (3-6 bulan)"
        phase_icon = "👶"
        phase_color = "#98FB98"
    elif days_lived <= 270:  # 6-9 bulan
        phase = "6_9_bulan"
        phase_name = "Bayi (6-9 bulan)"
        phase_icon = "🍼"
        phase_color = "#DDA0DD"
    elif days_lived <= 365:  # 9-12 bulan
        phase = "9_12_bulan"
        phase_name = "Bayi (9-12 bulan)"
        phase_icon = "🍼"
        phase_color = "#F0E68C"
    elif days_lived <= 545:  # 12-18 bulan
        phase = "12_18_bulan"
        phase_name = "Balita (12-18 bulan)"
        phase_icon = "🚶"
        phase_color = "#FFB347"
    elif days_lived <= 730:  # 18-24 bulan
        phase = "18_24_bulan"
        phase_name = "Balita (18-24 bulan)"
        phase_icon = "🏃"
        phase_color = "#77DD77"
    else:
        phase = "completed"
        phase_name = "1000 Hari Selesai! 🎉"
        phase_icon = "🎓"
        phase_color = "#FFD700"
    
    months_lived = days_lived / 30.4375
    
    return {
        "days_lived": days_lived,
        "months_lived": round(months_lived, 1),
        "total_days": total_days,
        "percentage": round(percentage, 1),
        "remaining_days": max(0, total_days - days_lived),
        "phase": phase,
        "phase_name": phase_name,
        "phase_icon": phase_icon,
        "phase_color": phase_color,
        "is_completed": days_lived >= total_days
    }


def get_nutrition_for_phase(days_lived: int) -> Dict:
    """Get nutrition focus for current phase"""
    if days_lived < 0:
        return NUTRITION_FOCUS.get("kehamilan_trimester3", {})
    elif days_lived <= 180:
        return NUTRITION_FOCUS.get("0_6_bulan", {})
    elif days_lived <= 270:
        return NUTRITION_FOCUS.get("6_9_bulan", {})
    elif days_lived <= 365:
        return NUTRITION_FOCUS.get("9_12_bulan", {})
    else:
        return NUTRITION_FOCUS.get("12_24_bulan", {})


def get_stimulation_for_month(month: int) -> List[Dict]:
    """Get stimulation activities for age in months"""
    if month < 0:
        return STIMULATION_GUIDE.get("kehamilan", [])
    elif month <= 3:
        return STIMULATION_GUIDE.get("0_3_bulan", [])
    elif month <= 6:
        return STIMULATION_GUIDE.get("4_6_bulan", [])
    elif month <= 9:
        return STIMULATION_GUIDE.get("7_9_bulan", [])
    elif month <= 12:
        return STIMULATION_GUIDE.get("10_12_bulan", [])
    elif month <= 18:
        return STIMULATION_GUIDE.get("13_18_bulan", [])
    else:
        return STIMULATION_GUIDE.get("19_24_bulan", [])


def get_red_flags_for_month(month: int) -> List[str]:
    """Get developmental red flags for age"""
    if month <= 3:
        return RED_FLAGS.get("0_3_bulan", [])
    elif month <= 6:
        return RED_FLAGS.get("4_6_bulan", [])
    elif month <= 9:
        return RED_FLAGS.get("7_9_bulan", [])
    elif month <= 12:
        return RED_FLAGS.get("10_12_bulan", [])
    elif month <= 18:
        return RED_FLAGS.get("13_18_bulan", [])
    else:
        return RED_FLAGS.get("19_24_bulan", [])


# ==============================================================================
# HTML GENERATORS
# ==============================================================================

def generate_1000_days_dashboard(dob: date) -> str:
    """
    Generate comprehensive 1000 days dashboard HTML
    
    Args:
        dob: Date of birth
        
    Returns:
        HTML string for dashboard
    """
    progress = calculate_1000_days_progress(dob)
    nutrition = get_nutrition_for_phase(progress['days_lived'])
    month = int(progress['months_lived'])
    stimulation = get_stimulation_for_month(month)
    red_flags = get_red_flags_for_month(month)
    
    html = f"""
    <!-- Progress Header -->
    <div style='background: linear-gradient(135deg, {progress['phase_color']}88 0%, {progress['phase_color']} 100%);
                padding: 25px; border-radius: 20px; margin-bottom: 20px; text-align: center;'>
        <div style='font-size: 4em; margin-bottom: 10px;'>{progress['phase_icon']}</div>
        <h2 style='color: #333; margin: 0 0 10px 0;'>1000 Hari Pertama Kehidupan</h2>
        <h3 style='color: #555; margin: 0 0 15px 0;'>{progress['phase_name']}</h3>
        
        <!-- Progress Bar -->
        <div style='background: rgba(255,255,255,0.5); border-radius: 25px; height: 30px; 
                    overflow: hidden; margin: 15px auto; max-width: 500px;'>
            <div style='background: linear-gradient(90deg, #4CAF50, #8BC34A); height: 100%;
                        width: {progress['percentage']}%; border-radius: 25px;
                        display: flex; align-items: center; justify-content: center;
                        color: white; font-weight: bold; font-size: 0.9em;
                        transition: width 0.5s ease;'>
                {progress['percentage']}%
            </div>
        </div>
        
        <div style='display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; margin-top: 15px;'>
            <div style='background: white; padding: 10px 20px; border-radius: 10px;'>
                <div style='font-size: 1.5em; font-weight: bold; color: #2196F3;'>{progress['days_lived']}</div>
                <div style='font-size: 0.9em; color: #666;'>Hari Dilalui</div>
            </div>
            <div style='background: white; padding: 10px 20px; border-radius: 10px;'>
                <div style='font-size: 1.5em; font-weight: bold; color: #4CAF50;'>{progress['months_lived']}</div>
                <div style='font-size: 0.9em; color: #666;'>Bulan</div>
            </div>
            <div style='background: white; padding: 10px 20px; border-radius: 10px;'>
                <div style='font-size: 1.5em; font-weight: bold; color: #FF9800;'>{progress['remaining_days']}</div>
                <div style='font-size: 0.9em; color: #666;'>Hari Tersisa</div>
            </div>
        </div>
    </div>
    
    <!-- Nutrition Section -->
    <div style='background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
        <h3 style='color: #e65100; margin: 0 0 15px 0;'>
            🍽️ {nutrition.get('title', 'Fokus Nutrisi')}
        </h3>
        <p style='color: #bf360c; font-weight: bold; margin-bottom: 15px;'>
            Fokus: {nutrition.get('focus', '')}
        </p>
    """
    
    # Nutrients table
    if 'nutrients' in nutrition:
        html += """
        <div style='overflow-x: auto;'>
            <table style='width: 100%; border-collapse: collapse; margin-bottom: 15px;'>
                <tr style='background: #fff3e0;'>
                    <th style='padding: 10px; text-align: left; border-bottom: 2px solid #ffcc80;'>Nutrisi</th>
                    <th style='padding: 10px; text-align: left; border-bottom: 2px solid #ffcc80;'>Kebutuhan</th>
                    <th style='padding: 10px; text-align: left; border-bottom: 2px solid #ffcc80;'>Sumber</th>
                    <th style='padding: 10px; text-align: left; border-bottom: 2px solid #ffcc80;'>Manfaat</th>
                </tr>
        """
        
        for nutrient in nutrition['nutrients']:
            html += f"""
                <tr style='border-bottom: 1px solid #eee;'>
                    <td style='padding: 10px; font-weight: bold;'>{nutrient['name']}</td>
                    <td style='padding: 10px;'>{nutrient['amount']}</td>
                    <td style='padding: 10px;'>{nutrient['source']}</td>
                    <td style='padding: 10px; color: #666;'>{nutrient['benefit']}</td>
                </tr>
            """
        
        html += "</table></div>"
    
    # Tips
    if 'tips' in nutrition:
        html += "<div style='background: #e8f5e9; padding: 15px; border-radius: 10px;'>"
        html += "<strong style='color: #2e7d32;'>💡 Tips:</strong><ul style='margin: 10px 0 0 20px;'>"
        for tip in nutrition['tips']:
            html += f"<li style='margin: 5px 0;'>{tip}</li>"
        html += "</ul></div>"
    
    html += "</div>"
    
    # Stimulation Section
    html += """
    <div style='background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
        <h3 style='color: #7b1fa2; margin: 0 0 15px 0;'>🧸 Stimulasi Tumbuh Kembang</h3>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;'>
    """
    
    for activity in stimulation:
        html += f"""
        <div style='background: #f3e5f5; padding: 15px; border-radius: 10px;'>
            <div style='font-weight: bold; color: #6a1b9a; margin-bottom: 5px;'>
                {activity['activity']}
            </div>
            <div style='color: #666; font-size: 0.9em; margin-bottom: 5px;'>
                ✨ {activity['benefit']}
            </div>
            <div style='color: #888; font-size: 0.85em;'>
                ⏱️ {activity['frequency']}
            </div>
        </div>
        """
    
    html += "</div></div>"
    
    # Red Flags Section
    html += """
    <div style='background: #ffebee; padding: 20px; border-radius: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
        <h3 style='color: #c62828; margin: 0 0 15px 0;'>⚠️ Tanda Bahaya (Red Flags)</h3>
        <p style='color: #b71c1c; margin-bottom: 15px;'>
            Segera konsultasi ke dokter jika muncul tanda-tanda berikut:
        </p>
        <ul style='margin: 0; padding-left: 25px;'>
    """
    
    for flag in red_flags:
        html += f"<li style='margin: 8px 0; color: #c62828;'>{flag}</li>"
    
    html += """
        </ul>
        <p style='margin: 15px 0 0 0; font-size: 0.9em; color: #666;'>
            📞 Hotline Kesehatan: 119 ext 8
        </p>
    </div>
    """
    
    return html


def generate_1000_days_timeline() -> str:
    """Generate visual timeline of 1000 days"""
    
    phases = [
        {"day": -270, "name": "Konsepsi", "icon": "🌱", "desc": "Perjalanan dimulai"},
        {"day": 0, "name": "Kelahiran", "icon": "👶", "desc": "Hari pertama kehidupan"},
        {"day": 180, "name": "6 Bulan", "icon": "🍼", "desc": "Mulai MPASI"},
        {"day": 365, "name": "1 Tahun", "icon": "🎂", "desc": "Milestone besar pertama"},
        {"day": 545, "name": "18 Bulan", "icon": "🚶", "desc": "Berjalan & berbicara"},
        {"day": 730, "name": "2 Tahun", "icon": "🎓", "desc": "1000 HPK selesai!"}
    ]
    
    html = """
    <div style='background: white; padding: 20px; border-radius: 15px;'>
        <h3 style='color: #1565c0; margin: 0 0 20px 0; text-align: center;'>
            📅 Timeline 1000 Hari Pertama
        </h3>
        <div style='position: relative; padding: 20px 0;'>
    """
    
    # Timeline line
    html += """
        <div style='position: absolute; top: 50%; left: 5%; right: 5%; 
                    height: 4px; background: linear-gradient(90deg, #e3f2fd, #1565c0, #e3f2fd);
                    border-radius: 2px;'></div>
    """
    
    # Timeline points
    for i, phase in enumerate(phases):
        left_percent = 5 + (i * 18)  # Distribute points
        html += f"""
        <div style='position: relative; display: inline-block; width: 16%; 
                    text-align: center; vertical-align: top;'>
            <div style='font-size: 2em; margin-bottom: 5px;'>{phase['icon']}</div>
            <div style='font-weight: bold; color: #1565c0; font-size: 0.9em;'>{phase['name']}</div>
            <div style='color: #666; font-size: 0.75em;'>{phase['desc']}</div>
        </div>
        """
    
    html += "</div></div>"
    
    return html


print("✅ First 1000 Days module loaded")
