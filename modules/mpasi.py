#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#==============================================================================
#                    AnthroHPK v4.0 - MPASI MODULE
#           Fitur Panduan MPASI Lengkap dengan Rekomendasi
#==============================================================================
"""

from typing import Dict, List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.mpasi_guide import (
    MPASI_GUIDE, 
    MPASI_PRINCIPLES, 
    COMMON_FOOD_ALLERGIES,
    get_mpasi_guide_for_month,
    get_texture_for_month,
    get_frequency_for_month,
    generate_mpasi_html
)
from config import MPASI_YOUTUBE_VIDEOS

# ==============================================================================
# MPASI TAB CONTENT GENERATORS
# ==============================================================================

def generate_mpasi_overview_html() -> str:
    """Generate MPASI overview/introduction HTML"""
    
    principles = MPASI_PRINCIPLES
    
    html = """
    <div style='background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%);
                padding: 25px; border-radius: 20px; margin-bottom: 20px;'>
        <h2 style='color: #2e7d32; margin: 0 0 10px 0;'>🍽️ Panduan MPASI Lengkap</h2>
        <p style='color: #1b5e20; margin: 0; font-size: 1.1em;'>
            Makanan Pendamping ASI sesuai standar WHO & IDAI
        </p>
    </div>
    
    <!-- 4 Bintang Principle -->
    <div style='background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
        <h3 style='color: #ff6f00; margin: 0 0 15px 0;'>
            ⭐ {principles['4_bintang']['name']}
        </h3>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;'>
    """
    
    for comp in principles['4_bintang']['components']:
        html += f"""
        <div style='background: #fff8e1; padding: 15px; border-radius: 10px; text-align: center;'>
            <div style='font-size: 2em;'>{comp['icon']}</div>
            <div style='font-weight: bold; color: #e65100; margin: 5px 0;'>{comp['name']}</div>
            <div style='font-size: 0.85em; color: #666;'>{comp['examples']}</div>
        </div>
        """
    
    # Plus lemak
    plus = principles['4_bintang']['plus']
    html += f"""
        <div style='background: #ffecb3; padding: 15px; border-radius: 10px; text-align: center;
                    border: 2px dashed #ffa000;'>
            <div style='font-size: 2em;'>{plus['icon']}</div>
            <div style='font-weight: bold; color: #ff6f00; margin: 5px 0;'>+ {plus['name']}</div>
            <div style='font-size: 0.85em; color: #666;'>{plus['examples']}</div>
        </div>
    </div></div>
    """
    
    # Feeding Rules
    html += f"""
    <div style='background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
        <h3 style='color: #1565c0; margin: 0 0 15px 0;'>
            📋 {principles['feeding_rules']['name']}
        </h3>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px;'>
    """
    
    for rule in principles['feeding_rules']['rules']:
        html += f"""
        <div style='background: #e3f2fd; padding: 12px; border-radius: 8px;'>
            {rule}
        </div>
        """
    
    html += "</div></div>"
    
    # Texture Progression
    html += f"""
    <div style='background: white; padding: 20px; border-radius: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
        <h3 style='color: #6a1b9a; margin: 0 0 15px 0;'>
            📈 {principles['texture_progression']['name']}
        </h3>
        <div style='display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;'>
    """
    
    for stage in principles['texture_progression']['stages']:
        html += f"""
        <div style='background: #f3e5f5; padding: 15px; border-radius: 10px; text-align: center;
                    min-width: 120px;'>
            <div style='font-size: 1.5em;'>{stage['icon']}</div>
            <div style='font-weight: bold; color: #7b1fa2; margin: 5px 0;'>{stage['age']}</div>
            <div style='font-size: 0.85em; color: #666;'>{stage['texture']}</div>
        </div>
        """
    
    html += "</div></div>"
    
    return html


def generate_mpasi_by_month_html(month: int) -> str:
    """
    Generate MPASI guide HTML for specific month
    
    Args:
        month: Age in months
        
    Returns:
        HTML string with MPASI guide
    """
    return generate_mpasi_html(month)


def generate_allergy_guide_html() -> str:
    """Generate food allergy guide HTML"""
    
    html = """
    <div style='background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
                padding: 20px; border-radius: 15px; margin-bottom: 20px;'>
        <h2 style='color: #c62828; margin: 0;'>⚠️ Panduan Alergi Makanan pada Bayi</h2>
    </div>
    """
    
    for allergen, data in COMMON_FOOD_ALLERGIES.items():
        allergen_name = allergen.replace("_", " ").title()
        
        html += f"""
        <div style='background: white; padding: 20px; border-radius: 15px; margin-bottom: 15px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <h3 style='color: #d32f2f; margin: 0 0 15px 0;'>🥜 Alergi {allergen_name}</h3>
            
            <div style='margin-bottom: 15px;'>
                <h4 style='color: #e65100; margin: 0 0 8px 0;'>Tanda-tanda:</h4>
                <ul style='margin: 0; padding-left: 25px;'>
        """
        
        for tanda in data['tanda']:
            html += f"<li style='margin: 4px 0;'>{tanda}</li>"
        
        html += f"""
                </ul>
            </div>
            
            <div style='margin-bottom: 15px;'>
                <h4 style='color: #1565c0; margin: 0 0 8px 0;'>Penanganan:</h4>
                <p style='margin: 0; color: #333;'>{data['penanganan']}</p>
            </div>
            
            <div style='background: #e8f5e9; padding: 10px; border-radius: 8px;'>
                <strong style='color: #2e7d32;'>📅 Kapan coba lagi?</strong>
                <p style='margin: 5px 0 0 0; color: #333;'>{data['kapan_coba_lagi']}</p>
            </div>
        </div>
        """
    
    # Emergency warning
    html += """
    <div style='background: #b71c1c; padding: 20px; border-radius: 15px; color: white;'>
        <h3 style='margin: 0 0 10px 0;'>🚨 DARURAT - Tanda Anafilaksis</h3>
        <p style='margin: 0 0 10px 0;'>Segera ke IGD jika muncul:</p>
        <ul style='margin: 0; padding-left: 25px;'>
            <li>Sesak napas / napas berbunyi</li>
            <li>Bengkak di wajah/tenggorokan</li>
            <li>Pucat dan lemas</li>
            <li>Tidak sadar</li>
        </ul>
        <p style='margin: 15px 0 0 0; font-weight: bold;'>📞 Hubungi 118/119 SEGERA!</p>
    </div>
    """
    
    return html


def generate_mpasi_videos_html(month: int) -> str:
    """Generate MPASI videos HTML for specific month"""
    
    # Find nearest age with videos
    video_ages = sorted(MPASI_YOUTUBE_VIDEOS.keys())
    nearest_age = 6
    
    for age in video_ages:
        if month >= age:
            nearest_age = age
    
    videos = MPASI_YOUTUBE_VIDEOS.get(nearest_age, [])
    
    if not videos:
        return """
        <div style='padding: 20px; background: #f5f5f5; border-radius: 10px; text-align: center;'>
            <p style='color: #666;'>Tidak ada video untuk usia ini.</p>
        </div>
        """
    
    html = f"""
    <div style='background: #e8f5e9; padding: 15px; border-radius: 10px; margin-bottom: 15px;'>
        <h3 style='color: #2e7d32; margin: 0;'>🎥 Video MPASI untuk Usia {nearest_age} Bulan</h3>
    </div>
    <div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px;'>
    """
    
    for video in videos:
        html += f"""
        <div style='background: white; border-radius: 12px; padding: 15px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <h4 style='color: #333; margin: 0 0 10px 0;'>{video['title']}</h4>
            <p style='color: #666; font-size: 0.9em; margin: 0 0 10px 0;'>
                {video['description']}
            </p>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='color: #888; font-size: 0.85em;'>⏱️ {video['duration']}</span>
                <a href='{video['url']}' target='_blank'
                   style='background: linear-gradient(135deg, #ff6b9d, #ff9a9e);
                          color: white; padding: 8px 16px; border-radius: 6px;
                          text-decoration: none; font-weight: 600; font-size: 0.9em;'>
                    ▶️ Tonton
                </a>
            </div>
        </div>
        """
    
    html += "</div>"
    
    return html


# ==============================================================================
# RESEP MPASI SEDERHANA
# ==============================================================================

MPASI_RECIPES = {
    6: [
        {
            "nama": "Bubur Beras Hati Ayam",
            "bahan": ["2 sdm beras", "1 potong hati ayam", "1 batang wortel kecil", "1 sdt EVOO"],
            "cara": [
                "Cuci beras, masak dengan air hingga menjadi bubur lembek",
                "Kukus hati ayam dan wortel hingga matang",
                "Blender halus hati dan wortel dengan sedikit air",
                "Campur dengan bubur, tambahkan EVOO",
                "Saring jika perlu agar tekstur sangat halus"
            ],
            "nutrisi": "Protein + Zat Besi + Vitamin A + Lemak"
        },
        {
            "nama": "Puree Alpukat Pisang",
            "bahan": ["1/4 buah alpukat matang", "1/2 buah pisang", "ASI/sufor secukupnya"],
            "cara": [
                "Kupas dan potong alpukat dan pisang",
                "Lumatkan dengan garpu atau blender",
                "Tambahkan ASI/sufor untuk mengatur kekentalan"
            ],
            "nutrisi": "Lemak Sehat + Kalium + Energi"
        }
    ],
    8: [
        {
            "nama": "Tim Daging Sapi Brokoli",
            "bahan": ["2 sdm nasi", "30g daging sapi giling", "2 kuntum brokoli", "1/2 sdt mentega"],
            "cara": [
                "Tim nasi dengan air hingga lunak",
                "Tumis daging sapi giling hingga matang",
                "Kukus brokoli hingga empuk",
                "Campur semua bahan, cincang kasar",
                "Tambahkan mentega, aduk rata"
            ],
            "nutrisi": "Protein + Zat Besi + Vitamin C + Serat"
        }
    ],
    10: [
        {
            "nama": "Nasi Tim Salmon Sayur",
            "bahan": ["3 sdm nasi", "30g salmon tanpa tulang", "Wortel, buncis, tomat", "Keju parut", "Minyak"],
            "cara": [
                "Tim nasi dengan sayuran potong kecil",
                "Kukus salmon, suwir halus",
                "Campur nasi tim dengan salmon",
                "Taburi keju parut, aduk rata"
            ],
            "nutrisi": "Protein + Omega-3 + Kalsium + Vitamin"
        }
    ],
    12: [
        {
            "nama": "Nasi Goreng Balita",
            "bahan": ["4 sdm nasi", "1 butir telur", "Sayuran cincang", "Kecap manis sedikit", "Minyak"],
            "cara": [
                "Kocok telur, orak-arik di wajan",
                "Masukkan sayuran, tumis sebentar",
                "Tambahkan nasi, aduk rata",
                "Beri sedikit kecap manis (opsional)",
                "Potong kecil-kecil untuk balita"
            ],
            "nutrisi": "Karbohidrat + Protein + Sayuran"
        }
    ]
}


def generate_recipes_html(month: int) -> str:
    """Generate MPASI recipes HTML"""
    
    # Find appropriate recipes
    recipe_ages = sorted(MPASI_RECIPES.keys())
    target_age = 6
    
    for age in recipe_ages:
        if month >= age:
            target_age = age
    
    recipes = MPASI_RECIPES.get(target_age, MPASI_RECIPES[6])
    
    html = f"""
    <div style='background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
                padding: 20px; border-radius: 15px; margin-bottom: 20px;'>
        <h2 style='color: #e65100; margin: 0;'>👨‍🍳 Resep MPASI untuk Usia {target_age}+ Bulan</h2>
    </div>
    """
    
    for recipe in recipes:
        html += f"""
        <div style='background: white; padding: 20px; border-radius: 15px; margin-bottom: 15px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <h3 style='color: #bf360c; margin: 0 0 15px 0;'>🍲 {recipe['nama']}</h3>
            
            <div style='display: grid; grid-template-columns: 1fr 2fr; gap: 20px;'>
                <div>
                    <h4 style='color: #e65100; margin: 0 0 10px 0;'>📝 Bahan:</h4>
                    <ul style='margin: 0; padding-left: 20px;'>
        """
        
        for bahan in recipe['bahan']:
            html += f"<li style='margin: 5px 0;'>{bahan}</li>"
        
        html += """
                    </ul>
                </div>
                <div>
                    <h4 style='color: #2e7d32; margin: 0 0 10px 0;'>👩‍🍳 Cara Membuat:</h4>
                    <ol style='margin: 0; padding-left: 20px;'>
        """
        
        for step in recipe['cara']:
            html += f"<li style='margin: 5px 0;'>{step}</li>"
        
        html += f"""
                    </ol>
                </div>
            </div>
            
            <div style='background: #e8f5e9; padding: 10px; border-radius: 8px; margin-top: 15px;'>
                <strong style='color: #2e7d32;'>✨ Kandungan:</strong> {recipe['nutrisi']}
            </div>
        </div>
        """
    
    return html


print("✅ MPASI module loaded")
