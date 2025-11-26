#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#==============================================================================
#                    AnthroHPK v4.0 - MOTHER MODULE
#              Fitur Kesehatan & Edukasi untuk Ibu - FITUR BARU
#==============================================================================
"""

from typing import Dict, List, Optional
from datetime import date, datetime
import math

# ==============================================================================
# DATA KEBUTUHAN GIZI IBU
# ==============================================================================

# Kebutuhan gizi ibu menyusui
IBU_MENYUSUI_NUTRITION = {
    "kalori": {
        "amount": "+500 kkal/hari",
        "note": "Tambahan dari kebutuhan normal (~2000 kkal)",
        "sources": ["Nasi/roti", "Protein hewani", "Lemak sehat", "Buah-buahan"]
    },
    "protein": {
        "amount": "71 gram/hari",
        "note": "Untuk produksi ASI berkualitas",
        "sources": ["Telur", "Ikan", "Daging", "Tempe/tahu", "Kacang-kacangan"]
    },
    "kalsium": {
        "amount": "1000-1300 mg/hari",
        "note": "Untuk tulang ibu dan kualitas ASI",
        "sources": ["Susu", "Keju", "Yogurt", "Teri", "Sayuran hijau"]
    },
    "zat_besi": {
        "amount": "9-10 mg/hari",
        "note": "Pemulihan pasca persalinan",
        "sources": ["Daging merah", "Hati", "Bayam", "Kacang merah"]
    },
    "vitamin_d": {
        "amount": "600-800 IU/hari",
        "note": "Untuk tulang dan transfer ke ASI",
        "sources": ["Sinar matahari pagi", "Ikan berlemak", "Kuning telur", "Suplemen"]
    },
    "asam_folat": {
        "amount": "500 mcg/hari",
        "note": "Regenerasi sel darah",
        "sources": ["Sayuran hijau", "Jeruk", "Kacang-kacangan", "Sereal fortifikasi"]
    },
    "omega_3": {
        "amount": "200-300 mg DHA/hari",
        "note": "Untuk perkembangan otak bayi melalui ASI",
        "sources": ["Ikan salmon", "Ikan kembung", "Ikan sarden", "Suplemen minyak ikan"]
    },
    "cairan": {
        "amount": "3-3.5 liter/hari",
        "note": "Untuk produksi ASI optimal",
        "sources": ["Air putih", "Sup", "Jus buah", "Susu"]
    }
}

# Kebutuhan gizi ibu hamil per trimester
IBU_HAMIL_NUTRITION = {
    "trimester1": {
        "title": "Trimester 1 (Minggu 1-12)",
        "kalori_tambahan": 0,
        "fokus": ["Asam folat", "Vitamin B6 (mual)", "Zat besi"],
        "pantangan": ["Alkohol", "Kafein berlebih", "Makanan mentah", "Ikan tinggi merkuri"],
        "tips": [
            "Makan sedikit tapi sering untuk atasi mual",
            "Pilih makanan kering saat bangun tidur",
            "Hindari bau menyengat",
            "Istirahat cukup"
        ]
    },
    "trimester2": {
        "title": "Trimester 2 (Minggu 13-26)",
        "kalori_tambahan": 340,
        "fokus": ["Kalsium", "Protein", "Zat besi", "DHA"],
        "pantangan": ["Makanan tinggi garam", "Kafein berlebih", "Makanan mentah"],
        "tips": [
            "Tingkatkan asupan protein",
            "Konsumsi susu/produk olahan susu",
            "Makan ikan 2-3x/minggu",
            "Olahraga ringan teratur"
        ]
    },
    "trimester3": {
        "title": "Trimester 3 (Minggu 27-40)",
        "kalori_tambahan": 450,
        "fokus": ["Protein", "Zat besi", "Kalsium", "DHA", "Serat"],
        "pantangan": ["Makanan bergas", "Porsi besar sekaligus", "Makanan pedas berlebih"],
        "tips": [
            "Makan porsi kecil lebih sering",
            "Cukupi kebutuhan zat besi (cadangan untuk bayi)",
            "Persiapan laktasi dengan pijat payudara lembut",
            "Banyak minum air"
        ]
    }
}

# Tips manajemen laktasi
LAKTASI_TIPS = {
    "persiapan": {
        "title": "Persiapan Sebelum Melahirkan",
        "tips": [
            "Ikuti kelas edukasi menyusui",
            "Pijat payudara lembut di trimester 3",
            "Siapkan mental dan dukungan keluarga",
            "Pelajari posisi menyusui yang benar",
            "Siapkan bra menyusui yang nyaman"
        ]
    },
    "awal": {
        "title": "Awal Menyusui (0-2 Minggu)",
        "tips": [
            "IMD segera setelah lahir (dalam 1 jam)",
            "Skin-to-skin sebanyak mungkin",
            "Susui on demand (8-12x/hari)",
            "Pastikan pelekatan benar",
            "Jangan berikan dot/empeng di 2 minggu pertama"
        ]
    },
    "masalah_umum": {
        "title": "Mengatasi Masalah Menyusui",
        "problems": {
            "puting_lecet": {
                "penyebab": "Pelekatan tidak tepat",
                "solusi": ["Perbaiki posisi dan pelekatan", "Oleskan ASI ke puting setelah menyusui", "Biarkan puting kering udara", "Gunakan nipple cream jika perlu"]
            },
            "asi_kurang": {
                "penyebab": "Frekuensi kurang, stres, dehidrasi",
                "solusi": ["Susui lebih sering", "Power pumping", "Cukupi cairan (3L/hari)", "Istirahat dan kurangi stres", "Konsumsi ASI booster (opsional)"]
            },
            "payudara_bengkak": {
                "penyebab": "Produksi berlebih, saluran tersumbat",
                "solusi": ["Kompres hangat sebelum menyusui", "Kompres dingin setelah menyusui", "Susui/pompa sesering mungkin", "Pijat lembut ke arah puting"]
            },
            "mastitis": {
                "penyebab": "Saluran tersumbat + infeksi",
                "solusi": ["TERUS menyusui (tidak kontraindikasi!)", "Kompres hangat", "Istirahat", "Ke dokter jika demam >38°C lebih dari 24 jam"]
            }
        }
    },
    "asi_perah": {
        "title": "Manajemen ASI Perah",
        "aturan": {
            "suhu_ruang": {"durasi": "4 jam", "suhu": "25°C"},
            "kulkas": {"durasi": "4 hari", "suhu": "4°C"},
            "freezer": {"durasi": "6 bulan", "suhu": "-18°C"}
        },
        "tips": [
            "Label dengan tanggal dan jam perah",
            "Simpan di bagian dalam kulkas (bukan pintu)",
            "Gunakan prinsip FIFO (First In First Out)",
            "Hangatkan dengan air hangat (BUKAN microwave)",
            "ASI yang sudah dihangatkan habiskan dalam 2 jam"
        ]
    }
}

# Kesehatan mental ibu
MENTAL_HEALTH = {
    "baby_blues": {
        "title": "Baby Blues (Normal)",
        "durasi": "3-10 hari pasca persalinan",
        "gejala": [
            "Mudah menangis",
            "Mood swing",
            "Cemas ringan",
            "Sulit tidur",
            "Sensitif"
        ],
        "penanganan": [
            "Dukungan keluarga",
            "Istirahat cukup",
            "Biasanya membaik sendiri dalam 2 minggu"
        ]
    },
    "ppd": {
        "title": "Postpartum Depression (Perlu Bantuan)",
        "durasi": "Bisa muncul hingga 1 tahun pasca persalinan",
        "gejala": [
            "Sedih berkepanjangan (>2 minggu)",
            "Tidak tertarik pada bayi",
            "Merasa tidak mampu jadi ibu",
            "Pikiran menyakiti diri/bayi",
            "Gangguan tidur dan nafsu makan berat",
            "Kelelahan ekstrem",
            "Sulit berkonsentrasi"
        ],
        "penanganan": [
            "HARUS konsultasi profesional",
            "Mungkin perlu terapi dan/atau obat",
            "Dukungan keluarga sangat penting",
            "Jangan malu mencari bantuan"
        ],
        "hotline": "119 ext 8"
    },
    "self_care": {
        "title": "Self-Care untuk Ibu Baru",
        "tips": [
            "Tidur saat bayi tidur",
            "Terima bantuan dari orang lain",
            "Jangan tuntut kesempurnaan",
            "Luangkan waktu untuk diri sendiri (15-30 menit)",
            "Tetap terhubung dengan teman/keluarga",
            "Olahraga ringan jika sudah diizinkan dokter",
            "Makan teratur dan bergizi",
            "Ceritakan perasaan pada pasangan/keluarga"
        ]
    }
}

# Pemulihan pasca persalinan
POSTPARTUM_RECOVERY = {
    "normal": {
        "title": "Persalinan Normal",
        "timeline": {
            "hari_1_3": ["Keluar lokia (darah nifas) merah segar", "Nyeri perineum jika ada jahitan", "Mulai menyusui"],
            "minggu_1": ["Lokia berubah kecoklatan", "Rahim mulai mengecil", "Mulai mobilisasi aktif"],
            "minggu_2_6": ["Lokia berkurang, menjadi kekuningan", "Jahitan (jika ada) mulai sembuh", "Boleh berhubungan intim setelah lokia berhenti dan terasa nyaman"],
            "bulan_2_3": ["Pemulihan hampir sempurna", "Bisa mulai olahraga", "Menstruasi bisa kembali (jika tidak full menyusui)"]
        },
        "warning_signs": [
            "Perdarahan banyak (ganti pembalut >1x/jam)",
            "Demam >38°C",
            "Nyeri perut hebat",
            "Keluarnya cairan berbau tidak sedap",
            "Jahitan terbuka"
        ]
    },
    "caesar": {
        "title": "Persalinan Caesar",
        "timeline": {
            "hari_1_3": ["Nyeri luka operasi", "Dibantu mobilisasi bertahap", "Makan bertahap (cairan → lunak → biasa)"],
            "minggu_1_2": ["Jahitan luar biasanya dilepas", "Boleh mandi, jaga luka tetap kering", "Hindari mengangkat beban berat"],
            "minggu_3_6": ["Nyeri berkurang", "Luka mulai menutup sempurna", "Aktivitas normal bertahap"],
            "bulan_2_3": ["Pemulihan luka dalam", "Boleh olahraga ringan", "Konsultasi jika planning kehamilan berikutnya"]
        },
        "warning_signs": [
            "Luka operasi merah, bengkak, keluar nanah",
            "Demam >38°C",
            "Nyeri perut yang memberat",
            "Perdarahan banyak dari vagina"
        ]
    }
}


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_menyusui_nutrition() -> Dict:
    """Get complete nutrition needs for breastfeeding mother"""
    return IBU_MENYUSUI_NUTRITION


def get_hamil_nutrition(trimester: int) -> Dict:
    """Get nutrition needs for specific trimester"""
    trimester_key = f"trimester{trimester}"
    return IBU_HAMIL_NUTRITION.get(trimester_key, IBU_HAMIL_NUTRITION["trimester1"])


def get_laktasi_tips(category: str = None) -> Dict:
    """Get lactation management tips"""
    if category and category in LAKTASI_TIPS:
        return {category: LAKTASI_TIPS[category]}
    return LAKTASI_TIPS


def get_mental_health_info() -> Dict:
    """Get mental health information"""
    return MENTAL_HEALTH


def get_recovery_info(birth_type: str = "normal") -> Dict:
    """Get postpartum recovery information"""
    return POSTPARTUM_RECOVERY.get(birth_type, POSTPARTUM_RECOVERY["normal"])


# ==============================================================================
# HTML GENERATORS
# ==============================================================================

def generate_mother_nutrition_html(phase: str = "menyusui") -> str:
    """
    Generate comprehensive nutrition guide HTML for mother
    
    Args:
        phase: "menyusui" or "hamil1", "hamil2", "hamil3"
        
    Returns:
        HTML string
    """
    html = ""
    
    if phase == "menyusui":
        nutrition = IBU_MENYUSUI_NUTRITION
        
        html = """
        <div style='background: linear-gradient(135deg, #fce4ec 0%, #f8bbd9 100%);
                    padding: 20px; border-radius: 15px; margin-bottom: 20px;'>
            <h2 style='color: #c2185b; margin: 0;'>🤱 Kebutuhan Gizi Ibu Menyusui</h2>
            <p style='color: #880e4f; margin: 5px 0 0 0;'>
                Nutrisi optimal untuk produksi ASI berkualitas
            </p>
        </div>
        """
        
        html += """
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px;'>
        """
        
        colors = ["#e3f2fd", "#e8f5e9", "#fff3e0", "#f3e5f5", "#e0f7fa", "#fbe9e7", "#f1f8e9", "#e8eaf6"]
        
        for i, (nutrient, data) in enumerate(nutrition.items()):
            bg_color = colors[i % len(colors)]
            nutrient_name = nutrient.replace("_", " ").title()
            sources = ", ".join(data['sources'][:3]) + ("..." if len(data['sources']) > 3 else "")
            
            html += f"""
            <div style='background: {bg_color}; padding: 15px; border-radius: 12px;'>
                <h4 style='margin: 0 0 10px 0; color: #333;'>{nutrient_name}</h4>
                <div style='font-size: 1.2em; font-weight: bold; color: #1565c0; margin-bottom: 5px;'>
                    {data['amount']}
                </div>
                <div style='color: #666; font-size: 0.9em; margin-bottom: 8px;'>
                    📝 {data['note']}
                </div>
                <div style='color: #888; font-size: 0.85em;'>
                    🥗 Sumber: {sources}
                </div>
            </div>
            """
        
        html += "</div>"
    
    else:  # hamil
        trimester = int(phase[-1]) if phase.startswith("hamil") else 1
        data = get_hamil_nutrition(trimester)
        
        html = f"""
        <div style='background: linear-gradient(135deg, #e1bee7 0%, #ce93d8 100%);
                    padding: 20px; border-radius: 15px; margin-bottom: 20px;'>
            <h2 style='color: #6a1b9a; margin: 0;'>🤰 {data['title']}</h2>
            <p style='color: #4a148c; margin: 5px 0 0 0;'>
                Kalori tambahan: <strong>+{data['kalori_tambahan']} kkal/hari</strong>
            </p>
        </div>
        
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;'>
            <div style='background: #e8f5e9; padding: 15px; border-radius: 12px;'>
                <h4 style='color: #2e7d32; margin: 0 0 10px 0;'>✅ Fokus Nutrisi</h4>
                <ul style='margin: 0; padding-left: 20px;'>
        """
        
        for fokus in data['fokus']:
            html += f"<li style='margin: 5px 0;'>{fokus}</li>"
        
        html += """
                </ul>
            </div>
            <div style='background: #ffebee; padding: 15px; border-radius: 12px;'>
                <h4 style='color: #c62828; margin: 0 0 10px 0;'>❌ Pantangan</h4>
                <ul style='margin: 0; padding-left: 20px;'>
        """
        
        for pantangan in data['pantangan']:
            html += f"<li style='margin: 5px 0;'>{pantangan}</li>"
        
        html += """
                </ul>
            </div>
        </div>
        
        <div style='background: #fff8e1; padding: 15px; border-radius: 12px; margin-top: 15px;'>
            <h4 style='color: #f57f17; margin: 0 0 10px 0;'>💡 Tips</h4>
            <ul style='margin: 0; padding-left: 20px;'>
        """
        
        for tip in data['tips']:
            html += f"<li style='margin: 5px 0;'>{tip}</li>"
        
        html += "</ul></div>"
    
    return html


def generate_laktasi_guide_html() -> str:
    """Generate comprehensive lactation guide HTML"""
    
    html = """
    <div style='background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                padding: 20px; border-radius: 15px; margin-bottom: 20px;'>
        <h2 style='color: #1565c0; margin: 0;'>🤱 Panduan Manajemen Laktasi</h2>
    </div>
    """
    
    # Persiapan
    html += f"""
    <div style='background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
        <h3 style='color: #7b1fa2; margin: 0 0 15px 0;'>
            📚 {LAKTASI_TIPS['persiapan']['title']}
        </h3>
        <ul style='margin: 0; padding-left: 20px;'>
    """
    for tip in LAKTASI_TIPS['persiapan']['tips']:
        html += f"<li style='margin: 8px 0;'>{tip}</li>"
    html += "</ul></div>"
    
    # Awal menyusui
    html += f"""
    <div style='background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
        <h3 style='color: #00695c; margin: 0 0 15px 0;'>
            👶 {LAKTASI_TIPS['awal']['title']}
        </h3>
        <ul style='margin: 0; padding-left: 20px;'>
    """
    for tip in LAKTASI_TIPS['awal']['tips']:
        html += f"<li style='margin: 8px 0;'>{tip}</li>"
    html += "</ul></div>"
    
    # Masalah umum
    html += """
    <div style='background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
        <h3 style='color: #d84315; margin: 0 0 15px 0;'>
            🩹 Mengatasi Masalah Menyusui
        </h3>
    """
    
    problems = LAKTASI_TIPS['masalah_umum']['problems']
    for problem_key, problem_data in problems.items():
        problem_name = problem_key.replace("_", " ").title()
        html += f"""
        <div style='background: #fff8e1; padding: 15px; border-radius: 10px; margin-bottom: 10px;'>
            <h4 style='color: #f57f17; margin: 0 0 10px 0;'>{problem_name}</h4>
            <p style='margin: 0 0 10px 0; color: #666;'>
                <strong>Penyebab:</strong> {problem_data['penyebab']}
            </p>
            <div style='color: #333;'>
                <strong>Solusi:</strong>
                <ul style='margin: 5px 0 0 20px;'>
        """
        for solusi in problem_data['solusi']:
            html += f"<li style='margin: 3px 0;'>{solusi}</li>"
        html += "</ul></div></div>"
    
    html += "</div>"
    
    # ASI Perah
    html += f"""
    <div style='background: white; padding: 20px; border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
        <h3 style='color: #0277bd; margin: 0 0 15px 0;'>
            🍼 {LAKTASI_TIPS['asi_perah']['title']}
        </h3>
        
        <div style='background: #e3f2fd; padding: 15px; border-radius: 10px; margin-bottom: 15px;'>
            <h4 style='margin: 0 0 10px 0; color: #1565c0;'>⏱️ Aturan Penyimpanan ASI</h4>
            <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; text-align: center;'>
    """
    
    aturan = LAKTASI_TIPS['asi_perah']['aturan']
    for tempat, data in aturan.items():
        html += f"""
        <div style='background: white; padding: 10px; border-radius: 8px;'>
            <div style='font-weight: bold; color: #333;'>{tempat.replace('_', ' ').title()}</div>
            <div style='font-size: 1.2em; color: #1565c0;'>{data['durasi']}</div>
            <div style='font-size: 0.85em; color: #666;'>({data['suhu']})</div>
        </div>
        """
    
    html += """
            </div>
        </div>
        <ul style='margin: 0; padding-left: 20px;'>
    """
    
    for tip in LAKTASI_TIPS['asi_perah']['tips']:
        html += f"<li style='margin: 8px 0;'>{tip}</li>"
    
    html += "</ul></div>"
    
    return html


def generate_mental_health_html() -> str:
    """Generate mental health awareness HTML"""
    
    html = """
    <div style='background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
                padding: 20px; border-radius: 15px; margin-bottom: 20px;'>
        <h2 style='color: #6a1b9a; margin: 0;'>💜 Kesehatan Mental Ibu</h2>
        <p style='color: #4a148c; margin: 5px 0 0 0;'>
            Mengenali dan mengatasi perubahan emosi pasca persalinan
        </p>
    </div>
    """
    
    # Baby Blues vs PPD comparison
    html += """
    <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-bottom: 20px;'>
    """
    
    # Baby Blues
    bb = MENTAL_HEALTH['baby_blues']
    html += f"""
        <div style='background: #e8f5e9; padding: 20px; border-radius: 12px;'>
            <h3 style='color: #2e7d32; margin: 0 0 15px 0;'>😢 {bb['title']}</h3>
            <p style='color: #388e3c; font-weight: bold;'>Durasi: {bb['durasi']}</p>
            <h4 style='color: #1b5e20; margin: 15px 0 10px 0;'>Gejala:</h4>
            <ul style='margin: 0; padding-left: 20px;'>
    """
    for gejala in bb['gejala']:
        html += f"<li style='margin: 5px 0;'>{gejala}</li>"
    html += """
            </ul>
            <h4 style='color: #1b5e20; margin: 15px 0 10px 0;'>Penanganan:</h4>
            <ul style='margin: 0; padding-left: 20px;'>
    """
    for item in bb['penanganan']:
        html += f"<li style='margin: 5px 0;'>{item}</li>"
    html += "</ul></div>"
    
    # PPD
    ppd = MENTAL_HEALTH['ppd']
    html += f"""
        <div style='background: #ffebee; padding: 20px; border-radius: 12px;'>
            <h3 style='color: #c62828; margin: 0 0 15px 0;'>⚠️ {ppd['title']}</h3>
            <p style='color: #d32f2f; font-weight: bold;'>Durasi: {ppd['durasi']}</p>
            <h4 style='color: #b71c1c; margin: 15px 0 10px 0;'>Gejala:</h4>
            <ul style='margin: 0; padding-left: 20px;'>
    """
    for gejala in ppd['gejala']:
        html += f"<li style='margin: 5px 0;'>{gejala}</li>"
    html += """
            </ul>
            <h4 style='color: #b71c1c; margin: 15px 0 10px 0;'>Penanganan:</h4>
            <ul style='margin: 0; padding-left: 20px;'>
    """
    for item in ppd['penanganan']:
        html += f"<li style='margin: 5px 0;'>{item}</li>"
    html += f"""
            </ul>
            <div style='background: #ffcdd2; padding: 10px; border-radius: 8px; margin-top: 15px; text-align: center;'>
                <strong>📞 Hotline Kesehatan: {ppd['hotline']}</strong>
            </div>
        </div>
    </div>
    """
    
    # Self-care tips
    sc = MENTAL_HEALTH['self_care']
    html += f"""
    <div style='background: #e8eaf6; padding: 20px; border-radius: 12px;'>
        <h3 style='color: #303f9f; margin: 0 0 15px 0;'>💆 {sc['title']}</h3>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;'>
    """
    
    for tip in sc['tips']:
        html += f"""
        <div style='background: white; padding: 10px; border-radius: 8px; font-size: 0.95em;'>
            ✨ {tip}
        </div>
        """
    
    html += "</div></div>"
    
    return html


print("✅ Mother module loaded")
