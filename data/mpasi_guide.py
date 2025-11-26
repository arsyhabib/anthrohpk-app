#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#==============================================================================
#                    AnthroHPK v4.0 - MPASI GUIDE DATA
#           Panduan Makanan Pendamping ASI Lengkap Per Bulan
#                    (FITUR BARU - Sesuai WHO & IDAI)
#==============================================================================
"""

from typing import List, Dict, Optional

# ==============================================================================
# PANDUAN MPASI LENGKAP PER BULAN
# ==============================================================================

MPASI_GUIDE = {
    # =========================================================================
    # 6 BULAN - AWAL MPASI
    # =========================================================================
    6: {
        "title": "🍼 MPASI 6 Bulan - Perkenalan Pertama",
        "subtitle": "Milestone: Memulai Makanan Padat",
        "readiness_signs": [
            "Bisa duduk dengan sedikit bantuan",
            "Kontrol kepala sudah baik",
            "Refleks menjulurkan lidah (tongue thrust) sudah berkurang",
            "Tertarik melihat orang lain makan",
            "Membuka mulut saat ditawari makanan"
        ],
        "texture": "Sangat halus (puree/saring halus)",
        "consistency": "Seperti yogurt encer, tidak ada gumpalan",
        "frequency": "1-2x sehari",
        "portion": "1-2 sendok makan, tingkatkan bertahap",
        "breastfeeding": "ASI tetap utama, minimal 8x sehari",
        
        "food_groups": {
            "karbohidrat": {
                "examples": ["Bubur beras merah", "Bubur beras putih", "Kentang tumbuk halus"],
                "tips": "Mulai dengan bubur 1 jenis bahan, konsistensi sangat encer"
            },
            "protein_hewani": {
                "examples": ["Hati ayam halus", "Kuning telur", "Ikan kukus halus"],
                "tips": "Protein hewani SANGAT PENTING sejak awal MPASI untuk cegah anemia"
            },
            "protein_nabati": {
                "examples": ["Tahu halus", "Tempe kukus halus"],
                "tips": "Bisa dikenalkan sebagai variasi"
            },
            "sayuran": {
                "examples": ["Wortel kukus halus", "Labu kuning", "Brokoli puree"],
                "tips": "Pilih sayuran manis terlebih dahulu"
            },
            "lemak_tambahan": {
                "examples": ["Minyak zaitun (EVOO)", "Santan", "Mentega unsalted"],
                "tips": "WAJIB tambahkan 1/2-1 sdt lemak di setiap porsi!"
            }
        },
        
        "menu_contoh": [
            {
                "nama": "Bubur Hati Ayam Wortel",
                "bahan": "Beras, hati ayam, wortel, minyak zaitun",
                "cara": "Blender sangat halus, tambahkan EVOO"
            },
            {
                "nama": "Puree Kentang Kuning Telur",
                "bahan": "Kentang, kuning telur, mentega",
                "cara": "Kukus, haluskan, tambahkan kuning telur matang dan mentega"
            }
        ],
        
        "pantangan": [
            "❌ Madu (risiko botulisme hingga 1 tahun)",
            "❌ Garam dan gula tambahan",
            "❌ Putih telur (risiko alergi tinggi, tunggu 9-12 bulan)",
            "❌ Makanan keras/bulat kecil (risiko tersedak)"
        ],
        
        "tips_sukses": [
            "💡 Satu makanan baru, tunggu 3 hari untuk pantau alergi",
            "💡 Berikan saat bayi tidak terlalu lapar atau kenyang",
            "💡 Suasana makan yang tenang dan menyenangkan",
            "💡 Jangan paksa jika menolak, coba lagi besok"
        ],
        
        "warning_signs": [
            "⚠️ Ruam kulit setelah makan (kemungkinan alergi)",
            "⚠️ Muntah terus-menerus",
            "⚠️ Diare atau sembelit berat",
            "⚠️ Menolak makan total lebih dari 1 minggu"
        ]
    },
    
    # =========================================================================
    # 7 BULAN
    # =========================================================================
    7: {
        "title": "🥄 MPASI 7 Bulan - Eksplorasi Rasa",
        "subtitle": "Milestone: Variasi Bahan Makanan",
        "texture": "Halus dengan sedikit tekstur (puree kasar)",
        "consistency": "Seperti yogurt kental, boleh ada sedikit butiran halus",
        "frequency": "2-3x sehari",
        "portion": "2-4 sendok makan",
        "breastfeeding": "ASI tetap 6-8x sehari",
        
        "food_groups": {
            "karbohidrat": {
                "examples": ["Nasi tim halus", "Oatmeal", "Ubi jalar", "Singkong"],
                "tips": "Mulai kombinasi 2 bahan"
            },
            "protein_hewani": {
                "examples": ["Daging sapi halus", "Ayam cincang halus", "Ikan salmon/kembung"],
                "tips": "Variasi protein hewani setiap hari"
            },
            "protein_nabati": {
                "examples": ["Kacang merah halus", "Kacang hijau", "Edamame"],
                "tips": "Kombinasi dengan hewani untuk protein lengkap"
            },
            "sayuran": {
                "examples": ["Bayam", "Kangkung", "Buncis", "Zucchini"],
                "tips": "Kenalkan sayuran hijau"
            },
            "buah": {
                "examples": ["Pisang", "Alpukat", "Pepaya", "Mangga matang"],
                "tips": "Buah sebagai snack atau pencuci mulut"
            },
            "lemak_tambahan": {
                "examples": ["Minyak kelapa", "Keju parut", "Santan kental"],
                "tips": "Variasi sumber lemak"
            }
        },
        
        "menu_contoh": [
            {
                "nama": "Tim Daging Sapi Brokoli",
                "bahan": "Nasi, daging sapi giling, brokoli, bawang putih, EVOO",
                "cara": "Tim bersama, haluskan sesuai tekstur"
            },
            {
                "nama": "Salmon Kentang Bayam",
                "bahan": "Salmon tanpa tulang, kentang, bayam, mentega",
                "cara": "Kukus, haluskan dengan sedikit tekstur"
            }
        ],
        
        "tips_sukses": [
            "💡 Mulai kenalkan finger food lunak (pisang potong)",
            "💡 Biarkan bayi memegang sendok (belajar makan mandiri)",
            "💡 Porsi makan boleh bervariasi setiap hari"
        ]
    },
    
    # =========================================================================
    # 8 BULAN
    # =========================================================================
    8: {
        "title": "🍗 MPASI 8 Bulan - Protein Power",
        "subtitle": "Milestone: Fokus Protein Hewani",
        "texture": "Cincang halus / mashed kasar",
        "consistency": "Seperti bubur kacang hijau, ada butiran",
        "frequency": "3x sehari + 1-2x snack",
        "portion": "3-4 sendok makan per makan",
        "breastfeeding": "ASI 5-6x sehari",
        
        "food_groups": {
            "protein_hewani": {
                "examples": ["Daging kambing", "Bebek", "Udang (jika tidak alergi)", "Kerang"],
                "tips": "PRIORITASKAN protein hewani untuk cegah stunting!"
            },
            "karbohidrat": {
                "examples": ["Nasi merah", "Pasta kecil", "Roti tawar tanpa kulit"],
                "tips": "Variasi sumber karbohidrat"
            }
        },
        
        "menu_contoh": [
            {
                "nama": "Nasi Tim Ayam Komplit",
                "bahan": "Nasi, ayam suwir, wortel, buncis, kaldu ayam, minyak",
                "cara": "Tim sampai lunak, tekstur cincang kasar"
            }
        ],
        
        "tips_sukses": [
            "💡 Protein hewani di SETIAP waktu makan",
            "💡 Finger food: wortel kukus, brokoli kecil",
            "💡 Mulai latih minum dari gelas/sippy cup"
        ]
    },
    
    # =========================================================================
    # 9 BULAN
    # =========================================================================
    9: {
        "title": "🥕 MPASI 9 Bulan - Tekstur Beragam",
        "subtitle": "Milestone: Transisi ke Makanan Kasar",
        "texture": "Cincang kasar / dicacah",
        "consistency": "Makanan lunak yang bisa dikunyah dengan gusi",
        "frequency": "3x makan + 2x snack",
        "portion": "4-6 sendok makan",
        "breastfeeding": "ASI 4-5x sehari",
        
        "food_groups": {
            "protein_hewani": {
                "examples": ["Semua jenis daging", "Telur utuh (jika tidak alergi)", "Ikan laut"],
                "tips": "Boleh coba putih telur dengan pemantauan"
            },
            "finger_food": {
                "examples": ["Roti panggang", "Keju potong", "Buah potong", "Sayur kukus"],
                "tips": "Latih kemampuan self-feeding"
            }
        },
        
        "menu_contoh": [
            {
                "nama": "Nasi Tim Telur Tomat",
                "bahan": "Nasi, telur orak-arik, tomat, keju parut",
                "cara": "Orak-arik telur, campur nasi tim dan tomat"
            }
        ],
        
        "tips_sukses": [
            "💡 Tekstur lebih kasar untuk latih mengunyah",
            "💡 Berikan finger food di setiap makan",
            "💡 Makan bersama keluarga (role model)"
        ]
    },
    
    # =========================================================================
    # 10-11 BULAN
    # =========================================================================
    10: {
        "title": "🍽️ MPASI 10-11 Bulan - Menu Keluarga",
        "subtitle": "Milestone: Transisi ke Makanan Keluarga",
        "texture": "Dicacah / potongan kecil",
        "consistency": "Hampir seperti makanan dewasa, potongan kecil",
        "frequency": "3x makan + 2x snack",
        "portion": "6-8 sendok makan",
        "breastfeeding": "ASI 3-4x sehari",
        
        "food_groups": {
            "makanan_keluarga": {
                "examples": ["Menu keluarga yang dihaluskan/dipotong kecil"],
                "tips": "Pisahkan porsi anak sebelum diberi garam/bumbu"
            }
        },
        
        "menu_contoh": [
            {
                "nama": "Nasi Ayam Kecap (modifikasi)",
                "bahan": "Nasi, ayam suwir, buncis, wortel, kecap sedikit",
                "cara": "Masak menu keluarga, potong kecil untuk anak"
            }
        ],
        
        "tips_sukses": [
            "💡 Anak mulai makan menu yang sama dengan keluarga",
            "💡 Latih makan dengan sendok dan garpu",
            "💡 Minum dari gelas biasa (dengan bantuan)"
        ]
    },
    
    # =========================================================================
    # 12 BULAN KE ATAS
    # =========================================================================
    12: {
        "title": "🎂 MPASI 12+ Bulan - Makan Mandiri",
        "subtitle": "Milestone: Makanan Keluarga Penuh",
        "texture": "Potongan kecil, makanan keluarga",
        "consistency": "Seperti makanan dewasa",
        "frequency": "3x makan + 2x snack",
        "portion": "Sesuai nafsu makan (1/2 - 3/4 porsi dewasa)",
        "breastfeeding": "ASI dilanjutkan sebagai pelengkap hingga 2 tahun",
        
        "food_groups": {
            "prinsip_4_bintang": {
                "examples": ["Karbohidrat + Protein Hewani + Sayur + Buah + Lemak"],
                "tips": "Setiap makan harus mengandung 4 komponen"
            }
        },
        
        "menu_contoh": [
            {
                "nama": "Piring Seimbang Anak",
                "bahan": "1/4 nasi, 1/4 lauk hewani, 1/4 sayur, 1/4 buah",
                "cara": "Ikuti prinsip isi piringku"
            }
        ],
        
        "tips_sukses": [
            "💡 Anak sudah bisa makan sendiri dengan supervisi",
            "💡 Variasi menu setiap hari",
            "💡 Hindari junk food dan minuman manis",
            "💡 Jadwal makan teratur (tidak grazing sepanjang hari)"
        ]
    }
}

# ==============================================================================
# DATA TAMBAHAN MPASI
# ==============================================================================

MPASI_PRINCIPLES = {
    "4_bintang": {
        "name": "Prinsip Menu 4 Bintang",
        "components": [
            {"name": "Makanan Pokok", "icon": "🍚", "examples": "Nasi, kentang, ubi, singkong, roti"},
            {"name": "Lauk Hewani", "icon": "🍗", "examples": "Daging, ayam, ikan, telur, hati"},
            {"name": "Lauk Nabati", "icon": "🫘", "examples": "Tempe, tahu, kacang-kacangan"},
            {"name": "Sayur & Buah", "icon": "🥬", "examples": "Sayuran hijau, wortel, buah segar"},
        ],
        "plus": {"name": "Lemak Tambahan", "icon": "🧈", "examples": "Minyak, mentega, santan"}
    },
    
    "feeding_rules": {
        "name": "Feeding Rules (Aturan Makan)",
        "rules": [
            "⏰ Jadwal teratur: 3x makan + 2x snack",
            "⏱️ Durasi makan maksimal 30 menit",
            "🚫 Tanpa distraksi (TV, gadget, mainan)",
            "😊 Suasana menyenangkan, tidak memaksa",
            "🪑 Duduk di kursi makan (bukan digendong)",
            "👶 Biarkan anak makan sendiri (messy eating OK!)",
            "💧 Air putih di antara waktu makan"
        ]
    },
    
    "texture_progression": {
        "name": "Progresi Tekstur MPASI",
        "stages": [
            {"age": "6 bulan", "texture": "Puree halus (disaring)", "icon": "🥣"},
            {"age": "7-8 bulan", "texture": "Puree kasar (tidak disaring)", "icon": "🍲"},
            {"age": "9-10 bulan", "texture": "Cincang halus", "icon": "🍛"},
            {"age": "11-12 bulan", "texture": "Cincang kasar / finger food", "icon": "🍽️"},
            {"age": "12+ bulan", "texture": "Makanan keluarga", "icon": "👨‍👩‍👧"}
        ]
    }
}

# Alergi makanan umum pada bayi
COMMON_FOOD_ALLERGIES = {
    "telur": {
        "tanda": ["Ruam kulit", "Bengkak bibir/mata", "Muntah", "Diare"],
        "penanganan": "Stop konsumsi, konsultasi dokter",
        "kapan_coba_lagi": "Bisa dicoba lagi setelah 3-6 bulan dengan pengawasan dokter"
    },
    "susu_sapi": {
        "tanda": ["Kolik", "Diare berdarah", "Ruam eksim", "Muntah"],
        "penanganan": "Hindari produk susu sapi, gunakan formula khusus",
        "kapan_coba_lagi": "Evaluasi berkala oleh dokter"
    },
    "kacang": {
        "tanda": ["Ruam gatal", "Sesak napas", "Bengkak", "Anafilaksis (darurat)"],
        "penanganan": "Hindari total, siap EpiPen jika alergi berat",
        "kapan_coba_lagi": "Harus dengan pengawasan dokter spesialis"
    },
    "seafood": {
        "tanda": ["Gatal-gatal", "Bengkak", "Mual muntah", "Sesak napas"],
        "penanganan": "Stop konsumsi, ke IGD jika sesak",
        "kapan_coba_lagi": "Konsultasi alergi dokter anak"
    }
}


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_mpasi_guide_for_month(month: int) -> Optional[Dict]:
    """
    Get MPASI guide for specific month
    
    Args:
        month: Age in months
        
    Returns:
        Dictionary with MPASI guide or None
    """
    if month < 6:
        return {
            "title": "🤱 ASI Eksklusif",
            "subtitle": "Belum saatnya MPASI",
            "message": "Bayi di bawah 6 bulan hanya membutuhkan ASI eksklusif. "
                       "MPASI dimulai saat usia genap 6 bulan (180 hari).",
            "is_pre_mpasi": True
        }
    
    # Find the appropriate guide
    guide_ages = sorted(MPASI_GUIDE.keys())
    
    selected_age = 6
    for age in guide_ages:
        if month >= age:
            selected_age = age
    
    return MPASI_GUIDE.get(selected_age)


def get_texture_for_month(month: int) -> str:
    """Get recommended texture for specific month"""
    if month < 6:
        return "ASI Eksklusif"
    elif month == 6:
        return "Puree sangat halus (disaring)"
    elif month <= 7:
        return "Puree halus"
    elif month <= 8:
        return "Puree kasar / mashed"
    elif month <= 9:
        return "Cincang halus"
    elif month <= 11:
        return "Cincang kasar / finger food"
    else:
        return "Makanan keluarga"


def get_frequency_for_month(month: int) -> Dict:
    """Get recommended feeding frequency for specific month"""
    if month < 6:
        return {"meals": 0, "snacks": 0, "breastfeeding": "8-12x atau on demand"}
    elif month == 6:
        return {"meals": 2, "snacks": 0, "breastfeeding": "6-8x"}
    elif month <= 8:
        return {"meals": 3, "snacks": 1, "breastfeeding": "5-6x"}
    elif month <= 11:
        return {"meals": 3, "snacks": 2, "breastfeeding": "4-5x"}
    else:
        return {"meals": 3, "snacks": 2, "breastfeeding": "3-4x (pelengkap)"}


def generate_mpasi_html(month: int) -> str:
    """
    Generate comprehensive HTML for MPASI guide display
    
    Args:
        month: Age in months
        
    Returns:
        HTML string for display
    """
    guide = get_mpasi_guide_for_month(month)
    
    if guide is None:
        return "<p>Data tidak tersedia</p>"
    
    if guide.get("is_pre_mpasi"):
        return f"""
        <div style="padding: 20px; background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); 
                    border-radius: 15px; text-align: center;">
            <h3 style="color: #e65100; margin: 0;">{guide['title']}</h3>
            <p style="color: #bf360c; margin: 10px 0 0 0; font-size: 1.1em;">
                {guide['message']}
            </p>
        </div>
        """
    
    # Build comprehensive guide HTML
    html = f"""
    <div style="padding: 20px; background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
                border-radius: 15px; margin-bottom: 20px;">
        <h2 style="color: #2e7d32; margin: 0;">{guide['title']}</h2>
        <p style="color: #388e3c; margin: 5px 0 0 0; font-style: italic;">{guide['subtitle']}</p>
    </div>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
        <div style="background: #e3f2fd; padding: 15px; border-radius: 10px;">
            <strong>🍽️ Tekstur</strong><br>{guide.get('texture', '-')}
        </div>
        <div style="background: #fce4ec; padding: 15px; border-radius: 10px;">
            <strong>⏰ Frekuensi</strong><br>{guide.get('frequency', '-')}
        </div>
        <div style="background: #fff3e0; padding: 15px; border-radius: 10px;">
            <strong>🥄 Porsi</strong><br>{guide.get('portion', '-')}
        </div>
        <div style="background: #f3e5f5; padding: 15px; border-radius: 10px;">
            <strong>🤱 ASI</strong><br>{guide.get('breastfeeding', '-')}
        </div>
    </div>
    """
    
    # Food groups
    if 'food_groups' in guide:
        html += """
        <div style="background: white; padding: 15px; border-radius: 10px; margin-bottom: 15px; 
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="color: #1565c0; margin: 0 0 15px 0;">🥗 Kelompok Makanan</h4>
        """
        
        for group_name, group_data in guide['food_groups'].items():
            examples = ", ".join(group_data.get('examples', []))
            tips = group_data.get('tips', '')
            
            html += f"""
            <div style="margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 8px;">
                <strong style="color: #333;">{group_name.replace('_', ' ').title()}</strong><br>
                <span style="color: #666;">{examples}</span><br>
                <small style="color: #888;">💡 {tips}</small>
            </div>
            """
        
        html += "</div>"
    
    # Menu examples
    if 'menu_contoh' in guide:
        html += """
        <div style="background: white; padding: 15px; border-radius: 10px; margin-bottom: 15px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <h4 style="color: #7b1fa2; margin: 0 0 15px 0;">👨‍🍳 Contoh Menu</h4>
        """
        
        for menu in guide['menu_contoh']:
            html += f"""
            <div style="margin: 10px 0; padding: 10px; background: #fafafa; border-radius: 8px; 
                        border-left: 3px solid #7b1fa2;">
                <strong>{menu['nama']}</strong><br>
                <small style="color: #666;">📝 Bahan: {menu['bahan']}</small><br>
                <small style="color: #888;">🍳 Cara: {menu['cara']}</small>
            </div>
            """
        
        html += "</div>"
    
    # Tips
    if 'tips_sukses' in guide:
        html += """
        <div style="background: #e8f5e9; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
            <h4 style="color: #2e7d32; margin: 0 0 10px 0;">💡 Tips Sukses</h4>
            <ul style="margin: 0; padding-left: 20px;">
        """
        for tip in guide['tips_sukses']:
            html += f"<li style='margin: 5px 0;'>{tip}</li>"
        html += "</ul></div>"
    
    # Warnings
    if 'pantangan' in guide:
        html += """
        <div style="background: #ffebee; padding: 15px; border-radius: 10px;">
            <h4 style="color: #c62828; margin: 0 0 10px 0;">⛔ Pantangan</h4>
            <ul style="margin: 0; padding-left: 20px;">
        """
        for item in guide['pantangan']:
            html += f"<li style='margin: 5px 0; color: #b71c1c;'>{item}</li>"
        html += "</ul></div>"
    
    return html


print("✅ MPASI Guide data loaded")
