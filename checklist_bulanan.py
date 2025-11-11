"""
Modul Checklist Sehat Bulanan (0-24 bulan)
Integrasi dengan AnthroHPK - WHO Child Growth Standards
Berdasarkan: Kemenkes RI, IDAI, WHO/UNICEF Guidelines
"""

import datetime
from typing import Dict, List, Tuple, Optional
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import io

# ===== DATA CHECKLIST PER BULAN =====

CHECKLIST_DATA = {
    0: {
        "feeding": "Inisiasi menyusu dini; ASI on demand; tanda kecukupan (pipis ≥6×/hari setelah hari ke-4)",
        "pertumbuhan": "Ukur BB/PB/LK; catat 2× untuk PB/LK; verifikasi usia kronologis/koreksi bila prematur",
        "perkembangan": "Respons suara/visual; bonding kulit-ke-kulit; tidur aman",
        "kpsp_due": False,
        "warnings": ["Demam/hipotermia", "Malas minum", "Kuning menyeluruh", "Muntah hijau", "Napas cepat/tarikan"]
    },
    1: {
        "feeding": "ASI eksklusif; pemantauan kenaikan BB tiap bulan; dukungan pelekatan & pumping bagi ibu bekerja",
        "pertumbuhan": "BB dan PB meningkat stabil; bila WAZ datar 2 kunjungan → evaluasi asupan/infeksi",
        "perkembangan": "Kontak mata; senyum sosial; angkat kepala tengkurap",
        "kpsp_due": False,
        "warnings": ["Demam ≥38°C pada <3 bulan", "Napas cepat/tarikan", "Dehidrasi", "Kejang"]
    },
    2: {
        "feeding": "ASI eksklusif; pemantauan kenaikan BB tiap bulan",
        "pertumbuhan": "BB dan PB meningkat stabil; verifikasi teknik pengukuran",
        "perkembangan": "Tengkurap; menggenggam; mengoceh",
        "kpsp_due": False,
        "warnings": ["Demam ≥38°C pada <3 bulan", "Napas cepat/tarikan", "Dehidrasi", "Kejang"]
    },
    3: {
        "feeding": "ASI eksklusif; pemantauan kenaikan BB tiap bulan",
        "pertumbuhan": "BB dan PB meningkat stabil",
        "perkembangan": "Berguling; memegang mainan; tertawa",
        "kpsp_due": True,
        "kpsp_paket": "3 bulan",
        "warnings": ["Demam tinggi", "Napas cepat", "Tidak mau minum"]
    },
    6: {
        "feeding": "**MULAI MPASI**; target 2-3×/hari + ASI on demand; utamakan **zat besi** (hewani)",
        "pertumbuhan": "Verifikasi z-score; bila LAZ <-2 SD → ulang ukur PB (2×) & optimasi MPASI",
        "perkembangan": "Duduk dengan bantuan; meraih benda; babbling",
        "kpsp_due": True,
        "kpsp_paket": "6 bulan",
        "warnings": ["BB tidak naik 2 bulan berturut-turut", "Menolak makan", "Diare persisten"]
    },
    9: {
        "feeding": "Naikkan kualitas menu; mulai finger food sesuai kesiapan",
        "pertumbuhan": "Review tren 3 bulan; bila WAZ stagnan → ↑ densitas energi",
        "perkembangan": "Merangkak; menggenggam dengan ibu jari-telunjuk; meniru suara",
        "kpsp_due": True,
        "kpsp_paket": "9 bulan",
        "warnings": ["Tidak bisa duduk sendiri", "Tidak merespons nama", "Penurunan BB"]
    },
    12: {
        "feeding": "**3-4×/hari** + 1-2 selingan; lanjut menyusui",
        "pertumbuhan": "Evaluasi tren kuartal; bila BB tidak naik 2× kunjungan → intervensi lebih intensif",
        "perkembangan": "Berdiri dengan pegangan; kata pertama; menunjuk",
        "kpsp_due": True,
        "kpsp_paket": "12 bulan",
        "warnings": ["Tidak bisa berdiri dengan bantuan", "Tidak ada kata bermakna", "Stunting (LAZ <-2)"]
    },
    15: {
        "feeding": "Kukuhkan rutinitas makan; atasi pilih-pilih (responsive feeding)",
        "pertumbuhan": "Tinjau LAZ; bila <-2 SD → paket intervensi rumah + follow-up 4 minggu",
        "perkembangan": "Berjalan mandiri; 3-6 kata; menunjuk keinginan",
        "kpsp_due": True,
        "kpsp_paket": "15 bulan",
        "warnings": ["Belum bisa berjalan", "Kehilangan kemampuan yang sudah dikuasai", "Wasting (WHZ <-2)"]
    },
    18: {
        "feeding": "Menu keluarga; variasi sumber zat besi; ajak makan bersama keluarga",
        "pertumbuhan": "Review WAZ/LAZ; bila stagnan → konseling intensif",
        "perkembangan": "Naik tangga; menyusun 2-3 balok; 10-20 kata",
        "kpsp_due": True,
        "kpsp_paket": "18 bulan",
        "warnings": ["Belum bisa naik tangga", "Kurang dari 6 kata", "Obesitas (WHZ >+3)"]
    },
    21: {
        "feeding": "Pertahankan frekuensi; latih kemandirian makan",
        "pertumbuhan": "Rencanakan transisi ke pemantauan 2-3 bulanan setelah 24 bln",
        "perkembangan": "Menendang bola; makan sendiri dengan sendok; kalimat 2 kata",
        "kpsp_due": True,
        "kpsp_paket": "21 bulan",
        "warnings": ["Tidak bisa menendang bola", "Tidak ada kalimat 2 kata", "Infeksi berulang"]
    },
    24: {
        "feeding": "Pola makan keluarga; pertahankan variasi & kepadatan gizi",
        "pertumbuhan": "Rekap 2 tahun pertama; rencana pemantauan lanjutan (3-6 bulanan)",
        "perkembangan": "Berlari; mencuci tangan; kalimat 3 kata",
        "kpsp_due": True,
        "kpsp_paket": "24 bulan",
        "warnings": ["Tidak bisa berlari", "Tidak ada kalimat 3 kata", "Picky eater ekstrem"]
    }
}

# Default untuk bulan yang tidak ada data spesifik
DEFAULT_CHECKLIST = {
    "feeding": "Lanjut ASI/MPASI sesuai usia; frekuensi 3-4×/hari + selingan",
    "pertumbuhan": "Pantau BB/PB bulanan; verifikasi z-score",
    "perkembangan": "Stimulasi motorik, bahasa, sosial sesuai usia",
    "kpsp_due": False,
    "warnings": ["Demam tinggi", "Sesak napas", "Diare berdarah", "Dehidrasi", "Kejang"]
}

# ===== FUNGSI GENERATOR CHECKLIST =====

def generate_monthly_checklist(
    age_months: float,
    z_scores: Dict[str, Optional[float]],
    feeding_status: str = "",
    kpsp_result: str = "Belum dilakukan"
) -> Tuple[List[str], List[str], List[str]]:
    """
    Generate checklist bulanan: Do Now, Saran Perbaikan, Warnings/Red Flags
    
    Args:
        age_months: Usia anak dalam bulan
        z_scores: Dict berisi z-score (waz, haz, whz, baz, hcz)
        feeding_status: Status pemberian makan
        kpsp_result: Hasil KPSP (Sesuai/Meragukan/Penyimpangan)
    
    Returns:
        Tuple[do_now, saran, warnings]
    """
    
    age_mo = int(round(age_months))
    
    # Ambil data checklist untuk bulan ini
    checklist = CHECKLIST_DATA.get(age_mo, DEFAULT_CHECKLIST)
    
    do_now = []
    saran = []
    warnings = []
    
    # ===== 1. DO NOW (Prioritas Tinggi) =====
    
    # Pengukuran antropometri
    if any(z is not None and abs(z) > 3 for z in z_scores.values() if z is not None):
        do_now.append("🔴 **PRIORITAS**: Ulang ukur BB/PB/LK dengan teknik benar (2× pengukuran)")
    
    # MPASI (usia 6 bulan)
    if age_mo == 6 and "belum mpasi" in feeding_status.lower():
        do_now.append("🍽️ **MULAI MPASI SEKARANG**: 2-3×/hari, utamakan sumber zat besi (hati/daging/ikan/telur)")
    
    # KPSP jatuh tempo
    if checklist.get("kpsp_due") and kpsp_result == "Belum dilakukan":
        do_now.append(f"📋 **Lakukan KPSP paket {checklist.get('kpsp_paket', age_mo)} bulan** (skrining perkembangan)")
    
    # Intervensi berdasarkan z-score
    if z_scores.get('haz') is not None and z_scores['haz'] < -2:
        do_now.append("📏 **Stunting terdeteksi**: Tingkatkan MPASI 3-4×/hari + konsultasi gizi ke Puskesmas")
    
    if z_scores.get('whz') is not None and z_scores['whz'] < -2:
        do_now.append("⚖️ **Wasting/Kurus**: Naikkan densitas energi MPASI + evaluasi penyakit akut")
    
    if z_scores.get('waz') is not None and z_scores['waz'] < -2:
        do_now.append("🍴 **Gizi Kurang**: Perbaiki frekuensi & kualitas makan; follow-up 2 minggu")
    
    # KPSP Meragukan/Penyimpangan
    if kpsp_result in ["Meragukan", "Penyimpangan"]:
        do_now.append(f"🧩 **Hasil KPSP: {kpsp_result}** → Konsultasi ke dokter anak/klinik tumbuh kembang")
    
    # Default jika tidak ada prioritas khusus
    if not do_now:
        do_now.append("✅ Lanjutkan pemantauan rutin bulanan di Posyandu/Puskesmas")
        do_now.append(f"📖 Catat hasil ukur di Buku KIA")
    
    # ===== 2. SARAN PERBAIKAN =====
    
    saran.append(f"🍽️ **Feeding**: {checklist['feeding']}")
    saran.append(f"🧒 **Perkembangan**: {checklist['perkembangan']}")
    
    # Saran tambahan berdasarkan kondisi
    if age_mo >= 6:
        saran.append("🥘 Variasikan sumber protein hewani (telur, ikan, ayam, daging) untuk cegah anemia")
    
    if age_mo >= 12:
        saran.append("👨‍👩‍👧 Ajak makan bersama keluarga; latih kemandirian makan dengan sendok")
    
    saran.append("🧼 Jaga kebersihan alat makan; cuci tangan sebelum makan")
    saran.append("💤 Pastikan tidur cukup (12-14 jam/hari untuk bayi, 11-13 jam untuk batita)")
    
    # ===== 3. WARNINGS / RED FLAGS =====
    
    # Red flags umum dari checklist
    for warning in checklist.get("warnings", []):
        warnings.append(f"⚠️ {warning}")
    
    # Red flags antropometri kritis
    if z_scores.get('haz') is not None and z_scores['haz'] < -3:
        warnings.append("🔴 **STUNTING BERAT**: Segera konsultasi ke Puskesmas/RS untuk evaluasi komprehensif")
    
    if z_scores.get('whz') is not None and z_scores['whz'] < -3:
        warnings.append("🔴 **GIZI BURUK AKUT**: RUJUK SEGERA ke fasilitas kesehatan terdekat")
    
    if z_scores.get('whz') is not None and z_scores['whz'] > 3:
        warnings.append("🔴 **OBESITAS**: Konsultasi ahli gizi untuk penyesuaian pola makan")
    
    # General red flag
    warnings.append("⚡ **Bila ada demam tinggi/kejang/sesak/dehidrasi → RUJUK SEGERA**")
    
    return do_now, saran, warnings


def format_checklist_markdown(
    age_months: float,
    child_name: str,
    do_now: List[str],
    saran: List[str],
    warnings: List[str]
) -> str:
    """Format checklist ke Markdown untuk display"""
    
    age_mo = int(round(age_months))
    now = datetime.datetime.now().strftime("%d %B %Y")
    
    md = f"""# 📋 Checklist Sehat Bulanan - Usia {age_mo} Bulan

## 👶 **Anak: {child_name or 'Tidak disebutkan'}**
📅 **Tanggal Checklist**: {now}

---

## 🎯 **DO NOW** (Lakukan Hari Ini/Minggu Ini)

"""
    for i, item in enumerate(do_now, 1):
        md += f"{i}. {item}\n\n"
    
    md += """---

## 💡 **SARAN PERBAIKAN** (Optimasi Harian/Mingguan)

"""
    for i, item in enumerate(saran, 1):
        md += f"{i}. {item}\n\n"
    
    md += """---

## ⚠️ **WARNINGS / RED FLAGS**

"""
    for item in warnings:
        md += f"- {item}\n\n"
    
    md += """---

## 📌 **Catatan Penting**

- ✅ Checklist ini bersifat **skrining edukatif**, bukan diagnosis medis
- ✅ Konsultasikan dengan **tenaga kesehatan** untuk interpretasi lengkap
- ✅ Gunakan **Buku KIA** untuk mencatat hasil pemantauan
- ✅ Rujukan: **Permenkes No. 2/2020**, **IDAI**, **WHO Child Growth Standards**

---

**Aplikasi AnthroHPK** | Data Anda tidak disimpan di server 🔒
"""
    
    return md


def export_checklist_pdf_simple(
    age_months: float,
    child_name: str,
    parent_name: str,
    do_now: List[str],
    saran: List[str],
    warnings: List[str],
    filename: str = "Checklist_Bulanan.pdf"
) -> str:
    """Export checklist ke PDF sederhana (1 halaman)"""
    
    try:
        c = canvas.Canvas(filename, pagesize=A4)
        W, H = A4
        age_mo = int(round(age_months))
        now = datetime.datetime.now().strftime("%d %B %Y")
        
        # Header
        c.setFillColorRGB(0.965, 0.647, 0.753)  # Pink pastel
        c.rect(0, H - 60, W, 60, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, H - 35, f"Checklist Sehat Bulanan - Usia {age_mo} Bulan")
        c.setFont("Helvetica", 10)
        c.drawRightString(W - 30, H - 35, now)
        
        y = H - 90
        
        # Informasi anak
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "INFORMASI ANAK")
        y -= 20
        c.setFont("Helvetica", 10)
        if child_name:
            c.drawString(40, y, f"Nama Anak: {child_name}")
            y -= 15
        if parent_name:
            c.drawString(40, y, f"Orang Tua/Wali: {parent_name}")
            y -= 15
        c.drawString(40, y, f"Usia: {age_mo} bulan")
        y -= 30
        
        # DO NOW
        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(0.8, 0.2, 0.2)  # Red
        c.drawString(30, y, "🎯 DO NOW (Prioritas)")
        c.setFillColor(colors.black)
        y -= 20
        c.setFont("Helvetica", 9)
        for i, item in enumerate(do_now[:3], 1):  # Max 3 items
            clean_item = item.replace("🔴", "").replace("🍽️", "").replace("📋", "").replace("📏", "").replace("⚖️", "").replace("🍴", "").replace("🧩", "").replace("✅", "").replace("📖", "").strip()
            wrapped = _wrap_text(clean_item, 90)
            c.drawString(40, y, f"{i}. {wrapped[0]}")
            y -= 12
            for line in wrapped[1:]:
                c.drawString(50, y, line)
                y -= 12
            y -= 5
        
        y -= 10
        
        # SARAN
        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(0.2, 0.6, 0.8)  # Blue
        c.drawString(30, y, "💡 SARAN PERBAIKAN")
        c.setFillColor(colors.black)
        y -= 20
        c.setFont("Helvetica", 9)
        for i, item in enumerate(saran[:4], 1):  # Max 4 items
            clean_item = item.replace("🍽️", "").replace("🧒", "").replace("🥘", "").replace("👨‍👩‍👧", "").replace("🧼", "").replace("💤", "").strip()
            wrapped = _wrap_text(clean_item, 90)
            c.drawString(40, y, f"{i}. {wrapped[0]}")
            y -= 12
            for line in wrapped[1:]:
                c.drawString(50, y, line)
                y -= 12
            y -= 5
        
        y -= 10
        
        # WARNINGS
        if y < 150:  # Cek ruang tersisa
            c.setFont("Helvetica-Bold", 10)
            c.setFillColorRGB(0.8, 0.1, 0.1)
            c.drawString(30, y, "⚠️ WARNINGS (lihat aplikasi untuk detail)")
        else:
            c.setFont("Helvetica-Bold", 12)
            c.setFillColorRGB(0.8, 0.1, 0.1)
            c.drawString(30, y, "⚠️ WARNINGS / RED FLAGS")
            c.setFillColor(colors.black)
            y -= 20
            c.setFont("Helvetica", 9)
            for item in warnings[:3]:  # Max 3 warnings
                clean_item = item.replace("⚠️", "").replace("🔴", "").replace("⚡", "").strip()
                wrapped = _wrap_text(clean_item, 90)
                c.drawString(40, y, f"• {wrapped[0]}")
                y -= 12
                for line in wrapped[1:]:
                    c.drawString(50, y, line)
                    y -= 12
        
        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(W / 2, 30, "AnthroHPK - Checklist Sehat Bulanan | Permenkes 2/2020 + WHO Standards")
        c.drawCentredString(W / 2, 15, "⚠️ Bukan diagnosis medis. Konsultasikan dengan tenaga kesehatan.")
        
        c.save()
        return filename
    
    except Exception as e:
        print(f"Error export PDF: {e}")
        return None


def _wrap_text(text: str, max_len: int = 80) -> List[str]:
    """Helper untuk wrap text panjang"""
    words = text.split()
    lines = []
    current_line = []
    current_len = 0
    
    for word in words:
        if current_len + len(word) + 1 <= max_len:
            current_line.append(word)
            current_len += len(word) + 1
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_len = len(word)
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines if lines else [""]


# ===== FUNGSI HELPER UNTUK INTEGRASI =====

def get_feeding_status_from_age(age_months: float) -> str:
    """Helper untuk determine feeding status default berdasarkan usia"""
    if age_months < 6:
        return "ASI Eksklusif"
    elif age_months < 12:
        return "ASI + MPASI 2-3×/hari"
    elif age_months < 24:
        return "ASI + MPASI 3-4×/hari"
    else:
        return "Makanan keluarga + ASI"


def validate_checklist_input(age_months: float) -> Tuple[bool, str]:
    """Validasi input untuk checklist"""
    if age_months < 0:
        return False, "Usia tidak boleh negatif"
    if age_months > 24:
        return False, "Checklist ini untuk usia 0-24 bulan. Gunakan pemantauan reguler untuk usia >24 bulan"
    return True, ""


# ===== DEMO STANDALONE (untuk testing) =====

if __name__ == "__main__":
    # Test case
    test_z_scores = {
        'waz': -1.5,
        'haz': -2.2,  # Stunting
        'whz': -0.8,
        'baz': -0.5,
        'hcz': 0.2
    }
    
    do_now, saran, warnings = generate_monthly_checklist(
        age_months=9.0,
        z_scores=test_z_scores,
        feeding_status="ASI + MPASI 2×/hari",
        kpsp_result="Belum dilakukan"
    )
    
    md = format_checklist_markdown(
        age_months=9.0,
        child_name="Budi Santoso",
        do_now=do_now,
        saran=saran,
        warnings=warnings
    )
    
    print(md)
    
    # Export PDF
    pdf_file = export_checklist_pdf_simple(
        age_months=9.0,
        child_name="Budi Santoso",
        parent_name="Ibu Siti",
        do_now=do_now,
        saran=saran,
        warnings=warnings,
        filename="test_checklist.pdf"
    )
    
    if pdf_file:
        print(f"\n✅ PDF berhasil dibuat: {pdf_file}")
