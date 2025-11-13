"""
GiziSiKecil (simplified stable version)
--------------------------------------
FastAPI + Gradio app for child growth monitoring (WHO + Permenkes)
"""

import os
import math
from datetime import datetime, date
from typing import Optional, Dict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pygrowup import Calculator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import gradio as gr

# -------------------------------------------------
# Global config & folders
# -------------------------------------------------
APP_VERSION = "2.1.0"
APP_TITLE = "GiziSiKecil - Monitor Pertumbuhan Anak (Stable)"

BASE_URL = os.getenv("BASE_URL", "https://anthrohpk-app.onrender.com")
STATIC_DIR = "static"
OUTPUTS_DIR = "outputs"
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# -------------------------------------------------
# WHO Calculator
# -------------------------------------------------
try:
    calc = Calculator(
        adjust_height_data=False,
        adjust_weight_scores=False,
        include_cdc=False,
        logger_name="pygrowup",
        log_level="ERROR",
    )
    print("✅ WHO Calculator (pygrowup) loaded")
except Exception as e:
    print("❌ ERROR init Calculator:", e)
    calc = None

# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def as_float(x) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).replace(",", ".").strip())
    except Exception:
        return None


def parse_date(s: str) -> Optional[date]:
    """Terima format: YYYY-MM-DD atau DD/MM/YYYY."""
    if not s:
        return None
    s = s.strip()
    # Format 1: YYYY-MM-DD
    try:
        y, m, d = [int(p) for p in s.split("-")]
        return date(y, m, d)
    except Exception:
        pass
    # Format 2: DD/MM/YYYY
    try:
        d, m, y = [int(p) for p in s.split("/")]
        return date(y, m, d)
    except Exception:
        return None


def age_months_from_dates(dob: date, dom: date) -> Optional[float]:
    if not dob or not dom or dom < dob:
        return None
    days = (dom - dob).days
    if days < 0:
        return None
    return days / 30.4375  # rata-rata hari per bulan


def z_to_percentile(z: Optional[float]) -> Optional[float]:
    if z is None or math.isnan(z):
        return None
    p = 0.5 * (1 + math.erf(z / math.sqrt(2))) * 100
    return round(p, 1)


# -------------------------------------------------
# WHO + Permenkes Z-score computation & labels
# -------------------------------------------------
def compute_zscores(
    sex_label: str,
    age_months: Optional[float],
    w_kg: Optional[float],
    h_cm: Optional[float],
    hc_cm: Optional[float],
) -> Dict[str, Optional[float]]:
    out = {k: None for k in ("waz", "haz", "whz", "baz", "hcz")}
    if calc is None or age_months is None:
        return out

    sex = "M" if sex_label.lower().startswith("l") else "F"

    if w_kg is not None:
        out["waz"] = calc.wfa(w_kg, age_months, sex)
    if h_cm is not None:
        out["haz"] = calc.lhfa(h_cm, age_months, sex)
    if w_kg is not None and h_cm is not None:
        out["whz"] = calc.wfl(w_kg, age_months, sex, h_cm)
        try:
            bmi = w_kg / ((h_cm / 100) ** 2)
            out["baz"] = calc.bmifa(bmi, age_months, sex)
        except Exception:
            out["baz"] = None
    if hc_cm is not None:
        out["hcz"] = calc.hcfa(hc_cm, age_months, sex)

    # sanitasi
    for k, v in list(out.items()):
        try:
            if v is not None:
                v = float(v)
                if math.isinf(v) or math.isnan(v):
                    out[k] = None
                else:
                    out[k] = round(v, 2)
        except Exception:
            out[k] = None
    return out


def classify_permenkes_waz(z: Optional[float]) -> str:
    if z is None:
        return "Tidak diketahui"
    if z < -3:
        return "Gizi buruk (BB sangat kurang)"
    if z < -2:
        return "Gizi kurang"
    if z <= 1:
        return "BB normal"
    return "Risiko BB lebih"


def classify_permenkes_haz(z: Optional[float]) -> str:
    if z is None:
        return "Tidak diketahui"
    if z < -3:
        return "Sangat pendek (stunting berat)"
    if z < -2:
        return "Pendek (stunting)"
    if z <= 3:
        return "Normal"
    return "Tinggi"


def classify_permenkes_whz(z: Optional[float]) -> str:
    if z is None:
        return "Tidak diketahui"
    if z < -3:
        return "Gizi buruk (sangat kurus)"
    if z < -2:
        return "Gizi kurang (kurus)"
    if z <= 1:
        return "Gizi baik (normal)"
    if z <= 2:
        return "Risiko gizi lebih"
    if z <= 3:
        return "Gizi lebih"
    return "Obesitas"


def classify_hcz(z: Optional[float]) -> str:
    if z is None:
        return "Tidak diketahui"
    if z < -3:
        return "Lingkar kepala sangat kecil (mikrosefali berat)"
    if z < -2:
        return "Lingkar kepala di bawah normal (mikrosefali)"
    if z > 3:
        return "Lingkar kepala sangat besar (makrosefali berat)"
    if z > 2:
        return "Lingkar kepala di atas normal (makrosefali)"
    return "Normal"


def build_interpretation(
    name_child: str,
    age_mo: Optional[float],
    w_kg: Optional[float],
    h_cm: Optional[float],
    hc_cm: Optional[float],
    z: Dict[str, Optional[float]],
) -> str:
    title = f"## Hasil Analisis Gizi {'untuk ' + name_child if name_child else ''}\n"
    if age_mo is None:
        return title + "❌ Usia tidak valid. Pastikan tanggal lahir & tanggal ukur benar."

    lines = [
        f"- **Usia:** {age_mo:.1f} bulan",
        f"- **Berat badan:** {w_kg:.1f} kg" if w_kg is not None else "- **Berat badan:** (tidak diisi)",
        f"- **Tinggi/Panjang:** {h_cm:.1f} cm" if h_cm is not None else "- **Tinggi/Panjang:** (tidak diisi)",
        f"- **Lingkar kepala:** {hc_cm:.1f} cm" if hc_cm is not None else "- **Lingkar kepala:** (tidak diisi)",
        "",
        "### Ringkasan Z-score (WHO) & Klasifikasi Permenkes",
    ]

    def row(label, key, permenkes_fn):
        zv = z.get(key)
        if zv is None:
            return f"- **{label}:** Z = —  |  klasifikasi: (data tidak cukup)"
        per = z_to_percentile(zv)
        perm = permenkes_fn(zv)
        per_txt = f"{per} persentil" if per is not None else "—"
        return f"- **{label}:** Z = {zv:.2f}  (≈ {per_txt})  →  **{perm}**"

    lines.append(row("Berat menurut umur (WAZ)", "waz", classify_permenkes_waz))
    lines.append(row("Tinggi/Panjang menurut umur (HAZ)", "haz", classify_permenkes_haz))
    lines.append(row("Berat menurut panjang/tinggi (WHZ)", "whz", classify_permenkes_whz))

    hcz = z.get("hcz")
    if hcz is not None:
        lines.append(
            f"- **Lingkar kepala menurut umur (HCZ):** Z = {hcz:.2f} → {classify_hcz(hcz)}"
        )

    lines.append("")
    lines.append(
        "💡 **Catatan:** Interpretasi ini mengikuti standar WHO & Permenkes RI No. 2 Tahun 2020. "
        "Gunakan sebagai alat bantu edukasi; keputusan klinis tetap oleh tenaga kesehatan."
    )
    return title + "\n".join(lines)


# -------------------------------------------------
# Checklist bulanan sederhana (imunisasi + KPSP)
# -------------------------------------------------
IMMUNIZATION_SCHEDULE = {
    0: ["HB 0", "BCG", "Polio 0"],
    1: ["HB 1", "Polio 1", "DPT-HB-Hib 1"],
    2: ["Polio 2", "DPT-HB-Hib 2"],
    3: ["Polio 3", "DPT-HB-Hib 3"],
    4: ["Polio 4", "DPT-HB-Hib 4"],
    9: ["Campak/MR 1"],
    12: ["Campak Booster"],
    18: ["DPT-HB-Hib Booster", "Polio Booster"],
    24: ["Campak Rubella (MR) 2"],
}

KPSP_QUESTIONS = {
    3: [
        "Mengangkat kepala 45° saat tengkurap?",
        "Tersenyum saat diajak bicara?",
        "Mengoceh (suara vokal)?",
        "Menatap dan mengikuti wajah ibu?",
        "Meraih benda/mainan?",
    ],
    6: [
        "Duduk dengan bantuan (bersandar)?",
        "Memindahkan mainan dari tangan ke tangan?",
        "Mengeluarkan suara 'a-u-o'?",
        "Tertawa keras saat bermain?",
        "Mengenal orang asing (malu/marah)?",
    ],
    9: [
        "Duduk sendiri tanpa bantuan?",
        "Merangkak maju?",
        "Mengucap 'mama/papa' (belum tentu tepat)?",
        "Meraih benda kecil dengan dua jari?",
        "Menirukan gerakan tepuk tangan?",
    ],
    12: [
        "Berdiri sendiri minimal beberapa detik?",
        "Berjalan berpegangan furnitur?",
        "Mengucap 2–3 kata bermakna?",
        "Minum dari cangkir sendiri (sedikit tumpah)?",
        "Menunjuk benda yang diinginkan?",
    ],
    18: [
        "Berjalan sendiri dengan stabil?",
        "Makan sendiri dengan sendok (masih berantakan)?",
        "Mengucap ≥10 kata?",
        "Menumpuk 2–4 kubus?",
        "Menunjuk 3 bagian tubuh?",
    ],
    24: [
        "Berlari beberapa langkah?",
        "Melompat dengan kedua kaki?",
        "Menyusun kalimat 2–3 kata?",
        "Meniru garis vertikal saat menggambar?",
        "Mengikuti perintah 2 langkah?",
    ],
}


def nearest_kpsp_month(age_mo: float) -> int:
    keys = sorted(KPSP_QUESTIONS.keys())
    return min(keys, key=lambda k: abs(k - age_mo))


def build_checklist(age_mo: float) -> str:
    m = int(round(age_mo))
    m = max(0, min(60, m))
    title = f"## Checklist Bulanan & KPSP (Usia ~{m} bulan)\n"

    # Imunisasi bulan ini (tepat atau ±1 bulan)
    imm = [
        (bulan, v)
        for bulan, v in IMMUNIZATION_SCHEDULE.items()
        if abs(bulan - m) <= 1
    ]
    if imm:
        lines = ["### 💉 Imunisasi yang perlu dicek bulan ini:"]
        for bulan, vaks in imm:
            lines.append(f"- Usia {bulan} bulan: " + ", ".join(vaks))
    else:
        lines = ["### 💉 Imunisasi:", "- Tidak ada jadwal khusus bulan ini, cek buku KIA."]

    # KPSP
    ref = nearest_kpsp_month(m)
    lines.append("")
    lines.append(f"### 🧠 Skrining perkembangan (KPSP) sekitar usia {ref} bulan:")
    for q in KPSP_QUESTIONS[ref]:
        lines.append(f"- [ ] {q}")

    lines.append("")
    lines.append(
        "👉 Jika banyak jawaban **TIDAK**, konsultasikan dengan tenaga kesehatan "
        "untuk skrining perkembangan lanjutan."
    )

    return title + "\n".join(lines)


# -------------------------------------------------
# Plot: simple bar chart of Z-scores
# -------------------------------------------------
def make_zscore_bar_chart(z: Dict[str, Optional[float]]) -> plt.Figure:
    labels = ["WAZ", "HAZ", "WHZ", "BAZ", "HCZ"]
    keys = ["waz", "haz", "whz", "baz", "hcz"]
    values = [z.get(k) if z.get(k) is not None else 0 for k in keys]

    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(labels, values)
    ax.axhline(0, color="black", linewidth=1)
    ax.axhline(-2, color="red", linestyle="--", linewidth=1)
    ax.axhline(2, color="red", linestyle="--", linewidth=1)
    ax.set_ylabel("Z-score")
    ax.set_title("Ringkasan Z-score WHO")
    ax.set_ylim(-4, 4)
    fig.tight_layout()
    return fig


# -------------------------------------------------
# Gradio callbacks
# -------------------------------------------------
def analyze_callback(
    name_child,
    sex_label,
    age_mode,
    dob_str,
    dom_str,
    age_months_manual,
    w_kg,
    h_cm,
    hc_cm,
):
    try:
        w = as_float(w_kg)
        h = as_float(h_cm)
        hc = as_float(hc_cm)

        # usia
        if age_mode == "Tanggal":
            dob = parse_date(dob_str) if dob_str else None
            dom = parse_date(dom_str) if dom_str else date.today()
            age_mo = age_months_from_dates(dob, dom) if (dob and dom) else None
        else:
            age_mo = as_float(age_months_manual)

        if age_mo is not None and age_mo < 0:
            age_mo = None

        z = compute_zscores(sex_label, age_mo, w, h, hc)
        md = build_interpretation(name_child or "", age_mo, w, h, hc, z)
        fig = make_zscore_bar_chart(z) if any(v is not None for v in z.values()) else None
        return md, fig
    except Exception as e:
        return f"❌ Terjadi error saat analisis: {e}", None


def checklist_callback(age_months):
    try:
        age = as_float(age_months)
        if age is None:
            return "❌ Masukkan usia yang valid."
        return build_checklist(age)
    except Exception as e:
        return f"❌ Terjadi error saat membuat checklist: {e}"


def toggle_age_inputs(mode):
    if mode == "Tanggal":
        return gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
    else:
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)


# -------------------------------------------------
# Build Gradio UI
# -------------------------------------------------
def build_demo() -> gr.Blocks:
    with gr.Blocks(
        title=APP_TITLE,
        theme=gr.themes.Soft(primary_hue="pink", secondary_hue="teal", neutral_hue="slate"),
    ) as demo:
        gr.Markdown(
            f"# 🏥 GiziSiKecil\n"
            f"Monitor pertumbuhan anak berbasis **WHO Child Growth Standards**\n\n"
            f"_Versi stabil untuk penggunaan sehari-hari & deployment Render (v{APP_VERSION})_"
        )

        with gr.Tab("📊 Kalkulator Gizi"):
            with gr.Row():
                with gr.Column(scale=1):
                    name_child = gr.Textbox(label="Nama anak (opsional)")
                    sex = gr.Radio(
                        ["Laki-laki", "Perempuan"],
                        value="Laki-laki",
                        label="Jenis kelamin",
                    )
                    age_mode = gr.Radio(
                        ["Tanggal", "Usia (bulan)"],
                        value="Tanggal",
                        label="Mode input usia",
                    )
                    dob = gr.Textbox(
                        label="Tanggal lahir (DD/MM/YYYY)",
                        placeholder="12/05/2023",
                    )
                    dom = gr.Textbox(
                        label="Tanggal ukur (DD/MM/YYYY)",
                        value=date.today().strftime("%d/%m/%Y"),
                    )
                    age_months_manual = gr.Number(
                        label="Usia (bulan)",
                        visible=False,
                        precision=1,
                    )

                    w_kg = gr.Number(label="Berat badan (kg)")
                    h_cm = gr.Number(label="Tinggi/panjang (cm)")
                    hc_cm = gr.Number(label="Lingkar kepala (cm)", value=None)

                    btn = gr.Button("🔍 Analisis sekarang", variant="primary")

                with gr.Column(scale=1):
                    result_md = gr.Markdown("Hasil analisis akan muncul di sini.")
                    plot = gr.Plot()

            age_mode.change(
                toggle_age_inputs,
                inputs=age_mode,
                outputs=[dob, dom, age_months_manual],
            )

            btn.click(
                analyze_callback,
                inputs=[
                    name_child,
                    sex,
                    age_mode,
                    dob,
                    dom,
                    age_months_manual,
                    w_kg,
                    h_cm,
                    hc_cm,
                ],
                outputs=[result_md, plot],
            )

        with gr.Tab("📅 Checklist bulanan & KPSP"):
            gr.Markdown(
                "Checklist ini membantu orang tua mengingat imunisasi dan memantau perkembangan "
                "anak berdasarkan usia."
            )
            age_for_check = gr.Slider(0, 60, value=6, step=1, label="Usia anak (bulan)")
            checklist_md = gr.Markdown()
            age_for_check.change(checklist_callback, inputs=age_for_check, outputs=checklist_md)

        gr.Markdown(
            "Made with ❤️ oleh mahasiswa FKIK UNJA. "
            "Untuk edukasi, bukan pengganti konsultasi langsung dengan tenaga kesehatan."
        )

    return demo


# -------------------------------------------------
# FastAPI + mounting Gradio
# -------------------------------------------------
app_fastapi = FastAPI(
    title="GiziSiKecil API",
    description="WHO Child Growth Standards + simple checklist",
    version=APP_VERSION,
)

app_fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(STATIC_DIR):
    app_fastapi.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if os.path.exists(OUTPUTS_DIR):
    app_fastapi.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")


@app_fastapi.get("/health", response_model=dict)
async def health_check():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "calculator": bool(calc),
        "time": datetime.now().isoformat(),
    }


@app_fastapi.get("/premium", response_class=HTMLResponse)
async def premium_page():
    html = f"""
    <html><head><title>GiziSiKecil Premium</title></head>
    <body style="font-family: sans-serif; padding: 2rem;">
      <h1>GiziSiKecil Premium</h1>
      <p>Halaman ini placeholder untuk materi premium (PDF lengkap, template laporan, dsb.).</p>
      <p>Silakan hubungi admin (+62 {os.getenv('CONTACT_WA', '---')}) jika ingin mengembangkan versi premium.</p>
    </body></html>
    """
    return HTMLResponse(content=html)


demo = build_demo()
app = gr.mount_gradio_app(app_fastapi, demo, path="/")
