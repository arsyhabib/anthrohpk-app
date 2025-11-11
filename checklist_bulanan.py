"""
Modul Checklist Sehat Bulanan (0–24 bulan)
Integrasi dengan AnthroHPK - WHO Child Growth Standards
Rujukan: Permenkes RI No. 2/2020, IDAI, WHO/UNICEF
"""

from __future__ import annotations

import datetime
from typing import Dict, List, Tuple, Optional
import io

# --- Opsional: ReportLab untuk PDF ---
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader  # noqa: F401
    _HAS_REPORTLAB = True
except Exception:
    _HAS_REPORTLAB = False

# --- Gradio (untuk membangun tab UI) ---
import gradio as gr


# =========================
# ===== DATA CHECKLIST ====
# =========================

CHECKLIST_DATA: Dict[int, Dict[str, object]] = {
    0: {
        "feeding": "Inisiasi menyusu dini; ASI on demand; tanda kecukupan (pipis ≥6×/hari setelah hari ke-4)",
        "pertumbuhan": "Ukur BB/PB/LK; catat 2× untuk PB/LK; verifikasi usia kronologis/koreksi bila prematur",
        "perkembangan": "Respons suara/visual; bonding kulit-ke-kulit; tidur aman",
        "kpsp_due": False,
        "warnings": ["Demam/hipotermia", "Malas minum", "Kuning menyeluruh", "Muntah hijau", "Napas cepat/tarikan"],
    },
    1: {
        "feeding": "ASI eksklusif; pemantauan kenaikan BB tiap bulan; dukungan pelekatan & pumping bagi ibu bekerja",
        "pertumbuhan": "BB dan PB meningkat stabil; bila WAZ datar 2 kunjungan → evaluasi asupan/infeksi",
        "perkembangan": "Kontak mata; senyum sosial; angkat kepala tengkurap",
        "kpsp_due": False,
        "warnings": ["Demam ≥38°C pada <3 bulan", "Napas cepat/tarikan", "Dehidrasi", "Kejang"],
    },
    2: {
        "feeding": "ASI eksklusif; pemantauan kenaikan BB tiap bulan",
        "pertumbuhan": "BB dan PB meningkat stabil; verifikasi teknik pengukuran",
        "perkembangan": "Tengkurap; menggenggam; mengoceh",
        "kpsp_due": False,
        "warnings": ["Demam ≥38°C pada <3 bulan", "Napas cepat/tarikan", "Dehidrasi", "Kejang"],
    },
    3: {
        "feeding": "ASI eksklusif; pemantauan kenaikan BB tiap bulan",
        "pertumbuhan": "BB dan PB meningkat stabil",
        "perkembangan": "Berguling; memegang mainan; tertawa",
        "kpsp_due": True,
        "kpsp_paket": "3 bulan",
        "warnings": ["Demam tinggi", "Napas cepat", "Tidak mau minum"],
    },
    6: {
        "feeding": "MULAI MPASI; target 2-3×/hari + ASI on demand; utamakan zat besi (hewani)",
        "pertumbuhan": "Verifikasi z-score; bila LAZ <-2 SD → ulang ukur PB (2×) & optimasi MPASI",
        "perkembangan": "Duduk dengan bantuan; meraih benda; babbling",
        "kpsp_due": True,
        "kpsp_paket": "6 bulan",
        "warnings": ["BB tidak naik 2 bulan berturut-turut", "Menolak makan", "Diare persisten"],
    },
    9: {
        "feeding": "Naikkan kualitas menu; mulai finger food sesuai kesiapan",
        "pertumbuhan": "Review tren 3 bulan; bila WAZ stagnan → tingkatkan densitas energi",
        "perkembangan": "Merangkak; pincer grasp; meniru suara",
        "kpsp_due": True,
        "kpsp_paket": "9 bulan",
        "warnings": ["Tidak bisa duduk sendiri", "Tidak merespons nama", "Penurunan BB"],
    },
    12: {
        "feeding": "3-4×/hari + 1-2 selingan; lanjut menyusui",
        "pertumbuhan": "Evaluasi tren kuartal; bila BB tidak naik 2× kunjungan → intervensi lebih intensif",
        "perkembangan": "Berdiri dengan pegangan; kata pertama; menunjuk",
        "kpsp_due": True,
        "kpsp_paket": "12 bulan",
        "warnings": ["Tidak bisa berdiri dengan bantuan", "Tidak ada kata bermakna", "Stunting (LAZ <-2)"],
    },
    15: {
        "feeding": "Kukuhkan rutinitas makan; atasi picky eating (responsive feeding)",
        "pertumbuhan": "Tinjau LAZ; bila <-2 SD → paket intervensi rumah + follow-up 4 minggu",
        "perkembangan": "Berjalan mandiri; 3-6 kata; menunjuk keinginan",
        "kpsp_due": True,
        "kpsp_paket": "15 bulan",
        "warnings": ["Belum bisa berjalan", "Kehilangan kemampuan yang sudah dikuasai", "Wasting (WHZ <-2)"],
    },
    18: {
        "feeding": "Menu keluarga; variasi sumber zat besi; ajak makan bersama keluarga",
        "pertumbuhan": "Review WAZ/LAZ; bila stagnan → konseling intensif",
        "perkembangan": "Naik tangga; susun 2-3 balok; 10-20 kata",
        "kpsp_due": True,
        "kpsp_paket": "18 bulan",
        "warnings": ["Belum bisa naik tangga", "Kurang dari 6 kata", "Obesitas (WHZ >+3)"],
    },
    21: {
        "feeding": "Pertahankan frekuensi; latih kemandirian makan",
        "pertumbuhan": "Rencanakan transisi ke pemantauan 2-3 bulanan setelah 24 bln",
        "perkembangan": "Menendang bola; makan sendiri dengan sendok; kalimat 2 kata",
        "kpsp_due": True,
        "kpsp_paket": "21 bulan",
        "warnings": ["Tidak bisa menendang bola", "Tidak ada kalimat 2 kata", "Infeksi berulang"],
    },
    24: {
        "feeding": "Pola makan keluarga; pertahankan variasi & kepadatan gizi",
        "pertumbuhan": "Rekap 2 tahun pertama; rencana pemantauan lanjutan (3-6 bulanan)",
        "perkembangan": "Berlari; mencuci tangan; kalimat 3 kata",
        "kpsp_due": True,
        "kpsp_paket": "24 bulan",
        "warnings": ["Tidak bisa berlari", "Tidak ada kalimat 3 kata", "Picky eater ekstrem"],
    },
}

DEFAULT_CHECKLIST: Dict[str, object] = {
    "feeding": "Lanjut ASI/MPASI sesuai usia; frekuensi 3-4×/hari + selingan",
    "pertumbuhan": "Pantau BB/PB bulanan; verifikasi z-score",
    "perkembangan": "Stimulasi motorik, bahasa, sosial sesuai usia",
    "kpsp_due": False,
    "warnings": ["Demam tinggi", "Sesak napas", "Diare berdarah", "Dehidrasi", "Kejang"],
}


# ===============================
# ====== LOGIKA / UTILITAS ======
# ===============================

def generate_monthly_checklist(
    age_months: float,
    z_scores: Dict[str, Optional[float]],
    feeding_status: str = "",
    kpsp_result: str = "Belum dilakukan",
) -> Tuple[List[str], List[str], List[str]]:
    """
    Kembalikan tuple (do_now, saran, warnings) untuk usia tertentu.
    z_scores berisi kunci: waz, haz, whz, baz, hcz (boleh None).
    """
    age_mo = int(round(age_months))
    checklist = CHECKLIST_DATA.get(age_mo, DEFAULT_CHECKLIST)

    do_now: List[str] = []
    saran: List[str] = []
    warnings: List[str] = []

    # Prioritas dengan z-score ekstrem
    if any((z is not None and abs(float(z)) > 3) for z in z_scores.values() if z is not None):
        do_now.append("PRIORITAS: Ulang ukur BB/PB/LK dengan teknik benar (2× pengukuran)")

    # MPASI mulai 6 bulan
    if age_mo == 6 and "belum mpasi" in (feeding_status or "").lower():
        do_now.append("MULAI MPASI sekarang: 2-3×/hari; utamakan sumber zat besi (hewani)")

    # KPSP jatuh tempo
    if bool(checklist.get("kpsp_due")) and kpsp_result == "Belum dilakukan":
        paket = str(checklist.get("kpsp_paket", age_mo))
        do_now.append(f"Lakukan KPSP paket {paket} (skrining perkembangan)")

    # Intervensi berdasar z-score
    if (z_scores.get("haz") is not None) and (float(z_scores["haz"]) < -2):
        do_now.append("Stunting: tingkatkan MPASI 3-4×/hari + konsultasi gizi di Puskesmas")

    if (z_scores.get("whz") is not None) and (float(z_scores["whz"]) < -2):
        do_now.append("Wasting/Kurus: naikkan densitas energi MPASI + evaluasi penyakit akut")

    if (z_scores.get("waz") is not None) and (float(z_scores["waz"]) < -2):
        do_now.append("Gizi kurang: perbaiki frekuensi & kualitas makan; follow-up 2 minggu")

    if kpsp_result in ("Meragukan", "Penyimpangan"):
        do_now.append(f"Hasil KPSP: {kpsp_result} → konsultasi tumbuh kembang/dokter anak")

    if not do_now:
        do_now.append("Lanjutkan pemantauan rutin bulanan di Posyandu/Puskesmas")
        do_now.append("Catat hasil ukur di Buku KIA")

    # Saran perbaikan
    saran.append(f"Feeding: {checklist['feeding']}")
    saran.append(f"Perkembangan: {checklist['perkembangan']}")
    if age_mo >= 6:
        saran.append("Variasikan protein hewani (telur, ikan, ayam, daging) untuk cegah anemia")
    if age_mo >= 12:
        saran.append("Ajak makan bersama keluarga; latih kemandirian makan dengan sendok")
    saran.append("Jaga kebersihan alat makan; cuci tangan sebelum makan")
    saran.append("Pastikan tidur cukup (bayi 12–14 jam; batita 11–13 jam per hari)")

    # Warnings
    warnings.extend([f"{w}" for w in checklist.get("warnings", [])])
    if (z_scores.get("haz") is not None) and (float(z_scores["haz"]) < -3):
        warnings.append("STUNTING BERAT: segera konsultasi ke Puskesmas/RS")
    if (z_scores.get("whz") is not None) and (float(z_scores["whz"]) < -3):
        warnings.append("GIZI BURUK AKUT: rujuk segera ke fasilitas kesehatan")
    if (z_scores.get("whz") is not None) and (float(z_scores["whz"]) > 3):
        warnings.append("OBESITAS: konsultasi ahli gizi untuk penyesuaian pola makan")
    warnings.append("Bila ada demam tinggi/kejang/sesak/dehidrasi → RUJUK SEGERA")

    return do_now, saran, warnings


def _wrap_text(text: str, max_len: int = 90) -> List[str]:
    """Word-wrapping sederhana untuk PDF."""
    words = text.split()
    lines: List[str] = []
    cur: List[str] = []
    cur_len = 0
    for w in words:
        add = (1 if cur else 0) + len(w)
        if cur_len + add <= max_len:
            cur.append(w)
            cur_len += add
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines or [""]


def export_checklist_pdf_simple(
    age_months: float,
    child_name: str,
    parent_name: str,
    do_now: List[str],
    saran: List[str],
    warnings: List[str],
    filename: str = "Checklist_Bulanan.pdf",
) -> Optional[str]:
    """Export checklist ke PDF 1 halaman (butuh reportlab)."""
    if not _HAS_REPORTLAB:
        return None
    try:
        W, H = A4
        c = canvas.Canvas(filename, pagesize=A4)
        age_mo = int(round(age_months))
        now = datetime.datetime.now().strftime("%d %B %Y")

        # Header
        c.setFillColorRGB(0.965, 0.647, 0.753)
        c.rect(0, H - 60, W, 60, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, H - 35, f"Checklist Sehat Bulanan - Usia {age_mo} Bulan")
        c.setFont("Helvetica", 10)
        c.drawRightString(W - 30, H - 35, now)

        y = H - 90

        # Info anak
        c.setFont("Helvetica-Bold", 12); c.drawString(30, y, "INFORMASI ANAK"); y -= 18
        c.setFont("Helvetica", 10)
        if child_name: c.drawString(40, y, f"Nama Anak: {child_name}"); y -= 14
        if parent_name: c.drawString(40, y, f"Orang Tua/Wali: {parent_name}"); y -= 14
        c.drawString(40, y, f"Usia: {age_mo} bulan"); y -= 22

        # DO NOW
        c.setFont("Helvetica-Bold", 12); c.setFillColorRGB(0.8, 0.2, 0.2)
        c.drawString(30, y, "DO NOW (Prioritas)"); y -= 18
        c.setFillColor(colors.black); c.setFont("Helvetica", 9)
        for i, item in enumerate(do_now[:3], 1):
            clean = item
            lines = _wrap_text(clean, 95)
            c.drawString(40, y, f"{i}. {lines[0]}"); y -= 12
            for ln in lines[1:]:
                c.drawString(50, y, ln); y -= 12
            y -= 2

        y -= 6

        # SARAN
        c.setFont("Helvetica-Bold", 12); c.setFillColorRGB(0.2, 0.6, 0.8)
        c.drawString(30, y, "SARAN PERBAIKAN"); y -= 18
        c.setFillColor(colors.black); c.setFont("Helvetica", 9)
        for i, item in enumerate(saran[:4], 1):
            lines = _wrap_text(item, 95)
            c.drawString(40, y, f"{i}. {lines[0]}"); y -= 12
            for ln in lines[1:]:
                c.drawString(50, y, ln); y -= 12
            y -= 2

        y -= 6

        # WARNINGS
        if y < 150:
            c.setFont("Helvetica-Bold", 10); c.setFillColorRGB(0.8, 0.1, 0.1)
            c.drawString(30, y, "WARNINGS (lihat aplikasi untuk detail)")
        else:
            c.setFont("Helvetica-Bold", 12); c.setFillColorRGB(0.8, 0.1, 0.1)
            c.drawString(30, y, "WARNINGS / RED FLAGS"); y -= 18
            c.setFillColor(colors.black); c.setFont("Helvetica", 9)
            for item in warnings[:3]:
                lines = _wrap_text(item, 95)
                c.drawString(40, y, f"• {lines[0]}"); y -= 12
                for ln in lines[1:]:
                    c.drawString(50, y, ln); y -= 12

        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(W / 2, 30, "AnthroHPK - Checklist Sehat Bulanan | Permenkes 2/2020 + WHO Standards")
        c.drawCentredString(W / 2, 16, "Bukan diagnosis medis. Konsultasikan dengan tenaga kesehatan.")

        c.save()
        return filename
    except Exception as e:
        print(f"[Checklist PDF] Error: {e}")
        return None


def get_feeding_status_from_age(age_months: float) -> str:
    if age_months < 6:
        return "ASI Eksklusif"
    if age_months < 12:
        return "ASI + MPASI 2-3×/hari"
    if age_months < 24:
        return "ASI + MPASI 3-4×/hari"
    return "Makanan keluarga + ASI"


def validate_checklist_input(age_months: float) -> Tuple[bool, str]:
    if age_months < 0:
        return False, "Usia tidak boleh negatif"
    if age_months > 24:
        return False, "Checklist ini untuk usia 0–24 bulan"
    return True, ""


# ======================================
# ====== KOMPONEN UI UNTUK GRADIO ======
# ======================================

def create_checklist_ui():
    """
    Bangun tab UI Gradio untuk Checklist Bulanan.
    Return sebuah gr.Column() yang siap dipasang di gr.TabItem().
    """
    with gr.Column() as tab:
        gr.Markdown("## 📋 Checklist Sehat Bulanan (0–24 bulan)")
        gr.Markdown("Skrining edukatif berbasis Permenkes/WHO. Hasil bukan diagnosis.")

        with gr.Group():
            with gr.Row():
                age_mo = gr.Number(label="Usia (bulan)", value=9.0, precision=1)
                child_name = gr.Textbox(label="Nama Anak (opsional)", placeholder="Budi Santoso")
                parent_name = gr.Textbox(label="Nama Orang Tua/Wali (opsional)", placeholder="Ibu Siti")

            with gr.Row():
                feeding = gr.Textbox(
                    label="Status Feeding (opsional)",
                    placeholder="Contoh: ASI + MPASI 2×/hari",
                    value=""
                )
                kpsp = gr.Radio(
                    ["Belum dilakukan", "Sesuai", "Meragukan", "Penyimpangan"],
                    label="Status KPSP",
                    value="Belum dilakukan",
                )

        with gr.Accordion("Opsional: Masukkan Z-score (jika ada)", open=False):
            with gr.Row():
                waz = gr.Number(label="WAZ (BB/U)", value=None, precision=2)
                haz = gr.Number(label="HAZ (TB/U)", value=None, precision=2)
                whz = gr.Number(label="WHZ (BB/TB)", value=None, precision=2)
                baz = gr.Number(label="BAZ (IMT/U)", value=None, precision=2)
                hcz = gr.Number(label="HCZ (LK/U)", value=None, precision=2)

        with gr.Row():
            make_btn = gr.Button("🔎 Susun Checklist", variant="primary")
            pdf_btn = gr.Button("📄 Ekspor PDF (1 halaman)", variant="secondary")

        out_md = gr.Markdown("*Checklist akan tampil di sini setelah Anda klik tombol di atas*")
        out_file = gr.File(label="Checklist PDF", file_types=[".pdf"])

        # ==== Callbacks ====

        def _do_generate(age: float, fd: str, kpsp_status: str,
                         _waz, _haz, _whz, _baz, _hcz,
                         child: str):
            ok, msg = validate_checklist_input(age)
            if not ok:
                return f"❌ {msg}"

            # isi default feeding bila kosong
            fd = (fd or "").strip() or get_feeding_status_from_age(age)

            z_dict = {
                "waz": _waz if _waz is not None else None,
                "haz": _haz if _haz is not None else None,
                "whz": _whz if _whz is not None else None,
                "baz": _baz if _baz is not None else None,
                "hcz": _hcz if _hcz is not None else None,
            }

            do_now, saran, warns = generate_monthly_checklist(
                age_months=age, z_scores=z_dict, feeding_status=fd, kpsp_result=kpsp_status
            )

            return format_checklist_markdown(
                age_months=age,
                child_name=child or "",
                do_now=do_now,
                saran=saran,
                warnings=warns,
            )

        def _do_pdf(age: float, fd: str, kpsp_status: str,
                    _waz, _haz, _whz, _baz, _hcz,
                    child: str, parent: str):
            ok, msg = validate_checklist_input(age)
            if not ok:
                return None, f"❌ {msg}"

            fd = (fd or "").strip() or get_feeding_status_from_age(age)
            z_dict = {
                "waz": _waz if _waz is not None else None,
                "haz": _haz if _haz is not None else None,
                "whz": _whz if _whz is not None else None,
                "baz": _baz if _baz is not None else None,
                "hcz": _hcz if _hcz is not None else None,
            }
            do_now, saran, warns = generate_monthly_checklist(age, z_dict, fd, kpsp_status)

            if not _HAS_REPORTLAB:
                return None, "⚠️ Fitur PDF membutuhkan paket reportlab. Tambahkan ke requirements.txt: reportlab"

            fname = f"Checklist_{(child or 'Anak').replace(' ', '_')[:30]}.pdf"
            path = export_checklist_pdf_simple(age, child or "", parent or "", do_now, saran, warns, filename=fname)
            if path is None:
                return None, "❌ Gagal membuat PDF."
            return path, "✅ PDF berhasil dibuat."

        make_btn.click(
            _do_generate,
            inputs=[age_mo, feeding, kpsp, waz, haz, whz, baz, hcz, child_name],
            outputs=[out_md],
        )

        pdf_btn.click(
            _do_pdf,
            inputs=[age_mo, feeding, kpsp, waz, haz, whz, baz, hcz, child_name, parent_name],
            outputs=[out_file, out_md],
        )

    return tab


# =========================
# ====== DEMO LOCAL  ======
# =========================
if __name__ == "__main__":
    # Demo kecil bila file dijalankan langsung
    with gr.Blocks() as demo:
        with gr.Tab("Checklist Bulanan"):
            create_checklist_ui()
    demo.launch()
