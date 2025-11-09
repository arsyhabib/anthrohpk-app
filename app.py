"""
AnthroHPK Web Application
=========================

This module adapts the AnthroHPK notebook into a web application
powered by FastAPI and Gradio.  It preserves the core
computation, plotting and reporting logic while removing the Colab‑
specific pieces.  The application exposes a Gradio interface at the
root path and serves static files to support a Progressive Web App
(PWA) and Trusted Web Activity (TWA) deployment.

Usage::

    uvicorn app:app --host 0.0.0.0 --port 8000

"""
import io
import os
import csv
import math
import datetime
import traceback
from functools import lru_cache

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pygrowup import Calculator
import gradio as gr
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import qrcode
from PIL import Image
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import warnings
warnings.filterwarnings('ignore')

# Initialise growth calculator
try:
    calc = Calculator(adjust_height_data=False, adjust_weight_scores=False, include_cdc=False)
except Exception as e:
    print(f"Calculator init error: {e}")
    calc = None

# Helpers
@lru_cache(maxsize=1000)
def z_to_percentile(z):
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return None
    return round((0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))) * 100.0, 1)

def fmtz(z, nd=2):
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "—"
    return f"{z:.{nd}f}"

def parse_date(s):
    if not s or str(s).strip() == "":
        return None
    s = str(s).strip()
    try:
        parts = [int(p) for p in s.split("-")]
        if len(parts) == 3:
            return datetime.date(parts[0], parts[1], parts[2])
    except Exception:
        pass
    try:
        parts = [int(p) for p in s.split("/")]
        if len(parts) == 3:
            return datetime.date(parts[2], parts[1], parts[0])
    except Exception:
        pass
    return None

def age_months_from_dates(dob, dom):
    try:
        delta = dom - dob
        days = delta.days
        if days < 0:
            return None, None
        months = days / 30.4375
        return months, days
    except Exception:
        return None, None

def safe_float(x):
    if x is None or x == "" or str(x).strip() == "":
        return None
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return None

# Age grid and bounds
AGE_GRID = np.arange(0.0, 60.0 + 1e-9, 0.25)
BOUNDS = {
    'wfa': (1.0, 30.0),
    'hfa': (45.0, 125.0),
    'hcfa': (30.0, 55.0),
    'wfl_w': (1.0, 30.0),
    'wfl_l': (45.0, 110.0)
}

def _safe_z(fn, *args):
    try:
        z = fn(*args)
        if z is None or math.isnan(z) or math.isinf(z):
            return None
        return float(z)
    except Exception:
        return None

def invert_z_with_scan(z_of_m, target_z, lo, hi, samples=120):
    xs = np.linspace(lo, hi, samples)
    zs = []
    for x in xs:
        z = z_of_m(x)
        zs.append(None if z is None else (z - target_z))
    last_x, last_f = None, None
    best_x, best_abs = None, float('inf')
    for x, f in zip(xs, zs):
        if f is not None:
            af = abs(f)
            if af < best_abs:
                best_x, best_abs = x, af
            if last_f is not None and f * last_f < 0:
                try:
                    root = brentq(lambda t: (z_of_m(t) or 0.0) - target_z, last_x, x, xtol=1e-6, rtol=1e-6, maxiter=100)
                    return float(root)
                except Exception:
                    pass
            last_x, last_f = x, f
    return float(best_x if best_x is not None else (lo + hi) / 2.0)

def wfa_curve_smooth(sex, z):
    lo, hi = BOUNDS['wfa']
    vals = []
    for a in AGE_GRID:
        z_of_m = lambda m: _safe_z(calc.wfa, m, a, sex)
        vals.append(invert_z_with_scan(z_of_m, z, lo, hi))
    return AGE_GRID.copy(), np.asarray(vals)

def hfa_curve_smooth(sex, z):
    lo, hi = BOUNDS['hfa']
    vals = []
    for a in AGE_GRID:
        z_of_m = lambda m: _safe_z(calc.lhfa, m, a, sex)
        vals.append(invert_z_with_scan(z_of_m, z, lo, hi))
    return AGE_GRID.copy(), np.asarray(vals)

def hcfa_curve_smooth(sex, z):
    lo, hi = BOUNDS['hcfa']
    vals = []
    for a in AGE_GRID:
        z_of_m = lambda m: _safe_z(calc.hcfa, m, a, sex)
        vals.append(invert_z_with_scan(z_of_m, z, lo, hi))
    return AGE_GRID.copy(), np.asarray(vals)

def wfl_curve_smooth(sex, age_mo, z, lengths=None):
    if lengths is None:
        lengths = np.arange(BOUNDS['wfl_l'][0], BOUNDS['wfl_l'][1] + 1e-9, 0.5)
    lo_w, hi_w = BOUNDS['wfl_w']
    weights = []
    for L in lengths:
        z_of_w = lambda w: _safe_z(calc.wfl, w, age_mo, sex, L)
        weights.append(invert_z_with_scan(z_of_w, z, lo_w, hi_w))
    return np.asarray(lengths), np.asarray(weights)

# Classifications

def permenkes_waz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Tidak diketahui"
    if z < -3: return "Gizi buruk (BB sangat kurang)"
    if z < -2: return "Gizi kurang"
    if z <= 1: return "BB normal"
    return "Risiko BB lebih"

def who_waz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Unknown"
    if z < -3: return "Severely underweight"
    if z < -2: return "Underweight"
    if z > 2:  return "Possible risk of overweight"
    return "Normal"

def permenkes_haz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Tidak diketahui"
    if z < -3: return "Sangat pendek (stunting berat)"
    if z < -2: return "Pendek (stunting)"
    if z <= 3: return "Normal"
    return "Tinggi"

def who_haz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Unknown"
    if z < -3: return "Severely stunted"
    if z < -2: return "Stunted"
    if z > 3:  return "Tall"
    return "Normal"

def permenkes_whz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Tidak diketahui"
    if z < -3: return "Gizi buruk (sangat kurus)"
    if z < -2: return "Gizi kurang (kurus)"
    if z <= 1: return "Gizi baik (normal)"
    if z <= 2: return "Risiko gizi lebih"
    if z <= 3: return "Gizi lebih"
    return "Obesitas"

def who_whz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Unknown"
    if z < -3: return "Severe wasting"
    if z < -2: return "Wasting"
    if z <= 2: return "Normal"
    if z <= 3: return "Overweight"
    return "Obesity"

def permenkes_baz(z):
    return permenkes_whz(z)

def who_baz(z):
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return "Unknown"
    if z < -3: return "Severe thinness"
    if z < -2: return "Thinness"
    if z <= 2: return "Normal"
    if z <= 3: return "Overweight"
    return "Obesity"

def hcz_text(z):
    if z is None or (isinstance(z, float) and math.isnan(z)):
        return ("Tidak diketahui", "Unknown")
    if z < -3: return ("Lingkar kepala sangat kecil", "Severe microcephaly")
    if z < -2: return ("Lingkar kepala di bawah normal", "Below normal")
    if z > 3:  return ("Lingkar kepala sangat besar", "Severe macrocephaly")
    if z > 2:  return ("Lingkar kepala di atas normal", "Above normal")
    return ("Normal", "Normal")

def biv_warnings(age_mo, sex, w, h, hc, z_waz, z_haz, z_whz, z_baz, z_hcz):
    warns, errors = [], []
    for name, z, critical, warn in [
        ("WAZ", z_waz, 6, 5),
        ("HAZ", z_haz, 6, 5),
        ("WHZ", z_whz, 5, 4),
        ("BAZ", z_baz, 5, 4),
        ("HCZ", z_hcz, 5, 4)
    ]:
        try:
            if z is not None and not math.isnan(z):
                if abs(z) > critical:
                    errors.append(f"❌ {name} = {fmtz(z)} sangat tidak wajar (|Z| > {critical}). Periksa ulang pengukuran dan satuan.")
                elif abs(z) > warn:
                    warns.append(f"⚠️ {name} = {fmtz(z)} mendekati batas ekstrem. Verifikasi pengukuran direkomendasikan.")
        except Exception:
            pass
    if w is not None:
        if w < 1.0 or w > 30:
            errors.append(f"❌ Berat {w} kg di luar rentang normal balita (1-30 kg). Periksa satuan.")
        elif w < 2.0 or w > 25:
            warns.append(f"⚠️ Berat {w} kg tidak lazim untuk balita. Verifikasi ulang.")
    if h is not None:
        if h < 35 or h > 130:
            errors.append(f"❌ Panjang/tinggi {h} cm di luar rentang normal (35-130 cm). Periksa satuan.")
        elif h < 40 or h > 120:
            warns.append(f"⚠️ Panjang/tinggi {h} cm tidak lazim. Verifikasi ulang.")
    if hc is not None:
        if hc < 20 or hc > 60:
            errors.append(f"❌ Lingkar kepala {hc} cm di luar rentang normal (20-60 cm).")
        elif hc < 25 or hc > 55:
            warns.append(f"⚠️ Lingkar kepala {hc} cm tidak lazim. Verifikasi ulang.")
    if age_mo is not None:
        if age_mo < 0:
            errors.append("❌ Usia tidak boleh negatif.")
        elif age_mo > 60:
            warns.append("ℹ️ Aplikasi ini dioptimalkan untuk usia 0-60 bulan.")
        if h is not None:
            if age_mo < 24 and h > 100:
                warns.append("⚠️ Usia <24 bulan tapi panjang > 100 cm. Pastikan metode pengukuran benar.")
            elif age_mo >= 24 and h < 60:
                warns.append("⚠️ Usia ≥24 bulan tapi tinggi < 60 cm. Pastikan metode pengukuran benar.")
    try:
        if all(x is not None for x in [w, h, z_whz, z_waz]):
            if z_waz < -2 and z_whz > -1:
                warns.append("ℹ️ Pola menunjukkan kemungkinan malnutrisi kronis (BB/U rendah namun BB/TB normal).")
    except Exception:
        pass
    return errors, warns

# Themes
THEMES = {
    "pastel": {"primary":"#f6a5c0","secondary":"#9ee0c8","accent":"#ffd4a3","neutral":"#ffffff","text":"#2c3e50","grid":"#e0e0e0"},
    "dark":   {"primary":"#ff6b9d","secondary":"#4ecdc4","accent":"#ffe66d","neutral":"#1a1a2e","text":"#eaeaea","grid":"#444444"},
    "colorblind": {"primary":"#0173b2","secondary":"#de8f05","accent":"#029e73","neutral":"#ffffff","text":"#333333","grid":"#cccccc"}
}

def apply_matplotlib_theme(theme_name="pastel"):
    plt.style.use('default')
    plt.rcParams.update({
        "axes.facecolor": "#FFFFFF",
        "figure.facecolor": "#FFFFFF",
        "savefig.facecolor": "#FFFFFF",
        "text.color": "#000000",
        "axes.labelcolor": "#000000",
        "axes.edgecolor": "#000000",
        "xtick.color": "#000000",
        "ytick.color": "#000000",
        "grid.color": "#CCCCCC",
        "grid.alpha": 0.5,
        "grid.linestyle": "--",
        "grid.linewidth": 0.5,
        "legend.framealpha": 1.0,
        "legend.fancybox": False,
        "legend.edgecolor": "#000000",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 7,
        "axes.linewidth": 1.2,
    })
    return THEMES.get(theme_name, THEMES["pastel"])

# Core computation

def compute_all(sex_text, age_mode, dob_str, dom_str, age_months_input,
                weight_kg, height_cm, headcirc_cm, name_child, name_parent,
                lang_mode, theme_name):
    try:
        w = safe_float(weight_kg)
        h = safe_float(height_cm)
        if w is None or h is None:
            return ("❌ **Error:** Berat & Tinggi wajib diisi (angka valid).\n\nContoh: Berat=8.5 kg, Tinggi=72.0 cm", None)
        if w <= 0:
            return ("❌ **Error:** Berat badan harus > 0 kg.", None)
        if h <= 0:
            return ("❌ **Error:** Panjang/Tinggi badan harus > 0 cm.", None)
        sex = 'M' if sex_text.lower().startswith('l') else 'F'
        if age_mode == "Tanggal":
            dob = parse_date(dob_str)
            dom = parse_date(dom_str)
            if not dob:
                return ("❌ **Error:** Tanggal lahir tidak valid (YYYY-MM-DD atau DD/MM/YYYY).", None)
            if not dom:
                return ("❌ **Error:** Tanggal ukur tidak valid (YYYY-MM-DD atau DD/MM/YYYY).", None)
            if dom < dob:
                return (f"❌ **Error:** Tanggal ukur < tanggal lahir (lahir={dob}, ukur={dom}).", None)
            age_result = age_months_from_dates(dob, dom)
            if age_result[0] is None:
                return ("❌ **Error:** Gagal menghitung usia dari tanggal.", None)
            age_mo, age_days = age_result
        else:
            age_mo = safe_float(age_months_input)
            if age_mo is None:
                return ("❌ **Error:** Usia (bulan) harus berupa angka.", None)
            age_days = int(age_mo * 30.4375)
        age_mo = max(0.0, min(age_mo, 60.0))
        hc = safe_float(headcirc_cm)
        z_scores = {}
        try:
            z_scores['waz'] = calc.wfa(w, age_mo, sex)
        except Exception:
            z_scores['waz'] = float('nan')
        try:
            z_scores['haz'] = calc.lhfa(h, age_mo, sex)
        except Exception:
            z_scores['haz'] = float('nan')
        try:
            z_scores['whz'] = calc.wfl(w, age_mo, sex, h)
        except Exception:
            z_scores['whz'] = float('nan')
        try:
            bmi = w / ((h / 100.0) ** 2)
            z_scores['baz'] = calc.bmifa(bmi, age_mo, sex)
        except Exception:
            z_scores['baz'] = float('nan')
        try:
            z_scores['hcz'] = calc.hcfa(hc, age_mo, sex) if hc is not None else float('nan')
        except Exception:
            z_scores['hcz'] = float('nan')
        percentiles = {k: z_to_percentile(v) for k, v in z_scores.items()}
        classifications = {
            'permenkes': {
                'waz': permenkes_waz(z_scores['waz']),
                'haz': permenkes_haz(z_scores['haz']),
                'whz': permenkes_whz(z_scores['whz']),
                'baz': permenkes_baz(z_scores['baz']),
                'hcz': hcz_text(z_scores['hcz'])[0]
            },
            'who': {
                'waz': who_waz(z_scores['waz']),
                'haz': who_haz(z_scores['haz']),
                'whz': who_whz(z_scores['whz']),
                'baz': who_baz(z_scores['baz']),
                'hcz': hcz_text(z_scores['hcz'])[1]
            }
        }
        errors, warns = biv_warnings(
            age_mo, sex, w, h, hc,
            z_scores['waz'], z_scores['haz'], z_scores['whz'],
            z_scores['baz'], z_scores['hcz']
        )
        md = build_markdown_report(
            name_child, name_parent, age_mo, age_days, sex_text,
            w, h, hc, z_scores, percentiles, classifications,
            lang_mode, errors, warns
        )
        payload = {
            'sex': sex,
            'sex_text': sex_text,
            'age_mo': age_mo,
            'age_days': age_days,
            'w': w,
            'h': h,
            'hc': hc,
            'name_child': name_child,
            'name_parent': name_parent,
            'z': z_scores,
            'permenkes': classifications['permenkes'],
            'who': classifications['who'],
            'pct': percentiles,
            'lang_mode': lang_mode,
            'theme': theme_name,
            'errors': errors,
            'warns': warns
        }
        return (md, payload)
    except Exception as e:
        error_trace = traceback.format_exc()
        print("Computation error", error_trace)
        return (f"❌ **Error tidak terduga:**\n\n````\n{str(e)}\n````\n\nSilakan periksa input Anda.", None)

def build_markdown_report(name_child, name_parent, age_mo, age_days, sex_text,
                         w, h, hc, z_scores, percentiles, classifications,
                         lang_mode, errors, warns):
    overall_status = "🟢 Normal"
    critical_issues = []
    for k, z in z_scores.items():
        if z is not None and not math.isnan(z):
            if abs(z) > 3:
                overall_status = "🔴 Perlu Perhatian Segera"; critical_issues.append(k.upper())
            elif abs(z) > 2 and overall_status == "🟢 Normal":
                overall_status = "🟡 Perlu Monitoring"
    md = f"# 📊 Laporan Status Gizi Anak\n\n## Status: {overall_status}\n\n"
    if critical_issues:
        md += f"⚠️ **Indeks kritis:** {', '.join(critical_issues)}\n\n"
    if errors:
        md += "## ❌ Peringatan Kritis\n\n" + "\n\n".join(errors) + "\n\n---\n\n"
    md += "### 👤 Informasi Anak\n\n"
    if name_child and str(name_child).strip(): md += f"**Nama:** {name_child}\n\n"
    if name_parent and str(name_parent).strip(): md += f"**Orang Tua/Wali:** {name_parent}\n\n"
    md += f"**Jenis Kelamin:** {sex_text}\n\n"
    md += f"**Usia:** {age_mo:.1f} bulan (~{age_days} hari)\n\n---\n\n"
    md += "### 📏 Data Antropometri\n\n| Pengukuran | Nilai |\n|------------|-------|\n"
    md += f"| Berat Badan | **{w:.1f} kg** |\n"
    md += f"| Panjang/Tinggi | **{h:.1f} cm** |\n"
    if hc is not None:
        md += f"| Lingkar Kepala | **{hc:.1f} cm** |\n"
    md += "\n---\n\n"
    if lang_mode == "Orang tua":
        md += "### 💡 Ringkasan untuk Orang Tua\n\n" + generate_parent_narrative(z_scores, classifications['permenkes']) + "\n\n"
    else:
        md += "### 🏥 Ringkasan Klinis\n\n" + generate_clinical_narrative(z_scores, classifications) + "\n\n"
    md += "---\n\n### 📈 Hasil Lengkap (Z-score & Kategori)\n\n| Indeks | Z-score | Persentil | Status (Permenkes) | Status (WHO) |\n|--------|---------|-----------|-------------------|-------------|\n"
    indices = [('WAZ (BB/U)','waz'),('HAZ (TB/U)','haz'),('WHZ (BB/TB)','whz'),('BAZ (IMT/U)','baz'),('HCZ (LK/U)','hcz')]
    for label, key in indices:
        z_val = fmtz(z_scores[key]); pct_val = f"{percentiles[key]}%" if percentiles[key] is not None else "—"
        perm_cat = classifications['permenkes'][key]; who_cat = classifications['who'][key]
        z_raw = z_scores[key]
        if z_raw is not None and not math.isnan(z_raw):
            status_icon = "🔴" if abs(z_raw) > 3 else ("🟡" if abs(z_raw) > 2 else ("🟢" if abs(z_raw) <= 2 else "⚪"))
        else:
            status_icon = "⚪"
        md += f"| {status_icon} **{label}** | {z_val} | {pct_val} | {perm_cat} | {who_cat} |\n"
    if warns:
        md += "\n### ⚠️ Catatan Validasi\n\n" + "\n\n".join(warns) + "\n"
    md += "\n---\n\n**📌 Catatan Penting:**\n\n- Hasil ini bersifat **skrining edukatif**, bukan diagnosis medis\n- Klasifikasi mengacu pada **Permenkes No. 2/2020** dan **WHO Child Growth Standards**\n- Untuk interpretasi lengkap dan penanganan, konsultasikan dengan tenaga kesehatan\n- Data Anda **tidak disimpan** di server (privasi terjaga)\n\n"
    return md

def generate_parent_narrative(z_scores, perm_class):
    bullets, advice = [], []
    if z_scores['haz'] is not None and not math.isnan(z_scores['haz']):
        if z_scores['haz'] < -3:
            bullets.append("🔴 **Tinggi badan sangat pendek** - Stunting berat"); advice.append("→ **Segera konsultasi**")
        elif z_scores['haz'] < -2:
            bullets.append("🟡 **Tinggi badan pendek** - Indikasi stunting"); advice.append("→ Konsultasi program perbaikan gizi")
    if z_scores['whz'] is not None and not math.isnan(z_scores['whz']):
        if z_scores['whz'] < -3:
            bullets.append("🔴 **Sangat kurus** - Gizi buruk"); advice.append("→ **Butuh penanganan segera**")
        elif z_scores['whz'] < -2:
            bullets.append("🟡 **Kurus** - Perlu perbaikan gizi"); advice.append("→ Tingkatkan asupan & pantau berat")
        elif z_scores['whz'] > 3:
            bullets.append("🔴 **Obesitas**"); advice.append("→ Konsultasi ahli gizi")
        elif z_scores['whz'] > 2:
            bullets.append("🟡 **Berat berlebih**"); advice.append("→ Perhatikan pola makan & aktivitas")
    if z_scores['waz'] is not None and not math.isnan(z_scores['waz']):
        if z_scores['waz'] < -2:
            bullets.append("🟡 **Berat menurut umur rendah**")
    if not bullets:
        bullets.append("🟢 **Pertumbuhan normal** - Sesuai standar WHO"); advice.append("→ Pertahankan gizi seimbang & pantau rutin")
    result = "\n".join(bullets)
    if advice:
        result += "\n\n**🎯 Rekomendasi:**\n\n" + "\n".join(advice)
    return result

def generate_clinical_narrative(z_scores, classifications):
    lines = []
    for key in ['waz','haz','whz','baz','hcz']:
        z = z_scores[key]
        if z is not None and not math.isnan(z):
            perm = classifications['permenkes'][key]
            who = classifications['who'][key]
            lines.append(f"**{key.upper()}:** {fmtz(z)} - {perm} (WHO: {who})")
    return "\n\n".join(lines)

def median_values_for(sex_text, age_mode, dob_str, dom_str, age_months_input):
    try:
        sex = 'M' if sex_text.lower().startswith('l') else 'F'
        if age_mode == "Tanggal":
            dob = parse_date(dob_str); dom = parse_date(dom_str)
            if not dob or not dom or dom < dob: return (None, None, None)
            age_mo, _ = age_months_from_dates(dob, dom)
        else:
            age_mo = safe_float(age_months_input)
            if age_mo is None: return (None, None, None)
        age_mo = max(0.0, min(age_mo, 60.0))
        w0 = invert_z_with_scan(lambda m: _safe_z(calc.wfa, m, age_mo, sex), 0.0, *BOUNDS['wfa'])
        h0 = invert_z_with_scan(lambda m: _safe_z(calc.lhfa, m, age_mo, sex), 0.0, *BOUNDS['hfa'])
        c0 = invert_z_with_scan(lambda m: _safe_z(calc.hcfa, m, age_mo, sex), 0.0, *BOUNDS['hcfa'])
        return (round(w0, 2), round(h0, 1), round(c0, 1))
    except Exception:
        return (None, None, None)

# Plotting helpers

def _zone_fill(ax, x, lower, upper, color, alpha, label):
    try:
        ax.fill_between(x, lower, upper, color=color, alpha=alpha, zorder=1, label=label, linewidth=0)
    except Exception:
        pass

def plot_wfa(payload):
    apply_matplotlib_theme(payload['theme'])
    sex, age, w = payload['sex'], payload['age_mo'], payload['w']
    sd_lines = { -3:('#DC143C','-'), -2:('#FF6347','-'), -1:('#FFA500','--'), 0:('#228B22','-'), 1:('#FFA500','--'), 2:('#FF6347','-'), 3:('#DC143C','-') }
    curves = {}
    for z, (c, ls) in sd_lines.items():
        x, y = wfa_curve_smooth(sex, z)
        curves[z] = (x, y)
    fig, ax = plt.subplots(figsize=(11, 7))
    x = curves[0][0]
    _zone_fill(ax, x, curves[-3][1], curves[-2][1], '#FFE6E6', 0.35, 'Zona Gizi Buruk')
    _zone_fill(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Zona Gizi Kurang')
    _zone_fill(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.40, 'Zona Normal')
    _zone_fill(ax, x, curves[1][1],  curves[2][1],  '#FFF3CD', 0.30, 'Risiko Gizi Lebih')
    _zone_fill(ax, x, curves[2][1],  curves[3][1],  '#F8D7DA', 0.35, 'Gizi Lebih')
    for z, (c, ls) in sd_lines.items():
        ax.plot(curves[z][0], curves[z][1], color=c, linestyle=ls, linewidth=2.0 if abs(z) in (0,2) else 1.6, label=("Median" if z==0 else f"{z:+d} SD"), zorder=5)
    z_waz = payload['z']['waz']
    point_color = '#228B22'
    if z_waz is not None:
        if z_waz < -3 or z_waz > 3: point_color = '#8B0000'
        elif z_waz < -2 or z_waz > 2: point_color = '#DC143C'
        elif z_waz < -1 or z_waz > 1: point_color = '#FF8C00'
    ax.scatter([age], [w], s=300, c=point_color, edgecolors='black', linewidths=2.5, marker='o', zorder=20, label='Data Anak')
    ax.plot([age, age], [0, w], 'k--', linewidth=1, alpha=0.3, zorder=1)
    ax.set_xlabel('Usia (bulan)', fontweight='bold'); ax.set_ylabel('Berat Badan (kg)', fontweight='bold')
    ax.set_title('GRAFIK PERTUMBUHAN WHO: Berat Badan menurut Umur (BB/U)\n' + ("Laki-laki" if sex=='M' else "Perempuan") + ' | 0-60 bulan', fontweight='bold')
    ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.5); ax.minorticks_on()
    ax.set_xlim(0, 60); ax.set_xticks(range(0, 61, 6)); ax.set_xticks(range(0, 61, 3), minor=True)
    y_min = min([curves[z][1].min() for z in (-3,-2,0,2,3)]); y_max = max([curves[z][1].max() for z in (-3,-2,0,2,3)])
    ax.set_ylim(max(0, y_min - 1), y_max + 2)
    ax.legend(loc='upper left', frameon=True, edgecolor='black', fontsize=8, ncol=2)
    fig.text(0.99, 0.01, 'WHO Child Growth Standards 2006', ha='right', va='bottom', fontsize=7, style='italic', alpha=0.6)
    plt.tight_layout(); return fig

def plot_hfa(payload):
    apply_matplotlib_theme(payload['theme'])
    sex, age, h = payload['sex'], payload['age_mo'], payload['h']
    sd_lines = { -3:('#DC143C','-'), -2:('#FF6347','-'), -1:('#FFA500','--'), 0:('#228B22','-'), 1:('#FFA500','--'), 2:('#FF6347','-'), 3:('#DC143C','-') }
    curves = {}
    for z, (c, ls) in sd_lines.items():
        x, y = hfa_curve_smooth(sex, z)
        curves[z] = (x, y)
    fig, ax = plt.subplots(figsize=(11, 7))
    x = curves[0][0]
    _zone_fill(ax, x, curves[-3][1], curves[-2][1], '#FFE6E6', 0.30, 'Severe Stunting')
    _zone_fill(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Stunting')
    _zone_fill(ax, x, curves[-1][1], curves[2][1],  '#E8F5E9', 0.40, 'Normal')
    _zone_fill(ax, x, curves[2][1],  curves[3][1],  '#E3F2FD', 0.30, 'Tall')
    for z, (c, ls) in sd_lines.items():
        ax.plot(curves[z][0], curves[z][1], color=c, linestyle=ls, linewidth=2.0 if abs(z) in (0,2) else 1.6, label=("Median" if z==0 else f"{z:+d} SD"), zorder=5)
    z_haz = payload['z']['haz']
    point_color = '#228B22'
    if z_haz is not None:
        if z_haz < -3 or z_haz > 3: point_color = '#8B0000'
        elif z_haz < -2 or z_haz > 2: point_color = '#DC143C'
        elif z_haz < -1 or z_haz > 1: point_color = '#FF8C00'
    ax.scatter([age], [h], s=300, c=point_color, edgecolors='black', linewidths=2.5, marker='o', zorder=20, label='Data Anak')
    ax.plot([age, age], [40, h], 'k--', linewidth=1, alpha=0.3, zorder=1)
    ax.set_xlabel('Usia (bulan)', fontweight='bold'); ax.set_ylabel('Panjang/Tinggi Badan (cm)', fontweight='bold')
    ax.set_title('GRAFIK PERTUMBUHAN WHO: Panjang/Tinggi menurut Umur (TB/U)\n' + ("Laki-laki" if sex=='M' else "Perempuan") + ' | 0-60 bulan', fontweight='bold')
    ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.5); ax.minorticks_on()
    ax.set_xlim(0, 60); ax.set_xticks(range(0, 61, 6)); ax.set_xticks(range(0, 61, 3), minor=True)
    y_min = min([curves[z][1].min() for z in (-3,-2,0,2,3)]); y_max = max([curves[z][1].max() for z in (-3,-2,0,2,3)])
    ax.set_ylim(max(45, y_min - 1), y_max + 2)
    ax.legend(loc='upper left', frameon=True, edgecolor='black', fontsize=8, ncol=2)
    fig.text(0.99, 0.01, 'WHO Child Growth Standards 2006', ha='right', va='bottom', fontsize=7, style='italic', alpha=0.6)
    plt.tight_layout(); return fig

def plot_hcfa(payload):
    apply_matplotlib_theme(payload['theme'])
    sex, age, hc = payload['sex'], payload['age_mo'], payload.get('hc')
    sd_lines = { -3:('#DC143C','-'), -2:('#FF6347','-'), -1:('#FFA500','--'), 0:('#228B22','-'), 1:('#FFA500','--'), 2:('#FF6347','-'), 3:('#DC143C','-') }
    curves = {}
    for z, (c, ls) in sd_lines.items():
        x, y = hcfa_curve_smooth(sex, z)
        curves[z] = (x, y)
    fig, ax = plt.subplots(figsize=(11, 7))
    x = curves[0][0]
    _zone_fill(ax, x, curves[-3][1], curves[-2][1], '#FFD4D4', 0.40, 'Microcephaly Berat')
    _zone_fill(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Microcephaly')
    _zone_fill(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.40, 'Zona Normal')
    _zone_fill(ax, x, curves[1][1],  curves[2][1],  '#E3F2FD', 0.30, 'Macrocephaly')
    _zone_fill(ax, x, curves[2][1],  curves[3][1],  '#BBDEFB', 0.35, 'Macrocephaly Berat')
    for z, (c, ls) in sd_lines.items():
        ax.plot(curves[z][0], curves[z][1], color=c, linestyle=ls, linewidth=2.0 if abs(z) in (0,2) else 1.6, label=("Median" if z==0 else f"{z:+d} SD"), zorder=5)
    if hc is not None:
        z_hcz = payload['z']['hcz']
        point_color = '#228B22'
        if z_hcz is not None:
            if z_hcz < -3 or z_hcz > 3: point_color = '#8B0000'
            elif z_hcz < -2 or z_hcz > 2: point_color = '#DC143C'
            elif z_hcz < -1 or z_hcz > 1: point_color = '#FF8C00'
        ax.scatter([age], [hc], s=300, c=point_color, edgecolors='black', linewidths=2.5, marker='o', zorder=20, label='Data Anak')
        ax.plot([age, age], [25, hc], 'k--', linewidth=1, alpha=0.3, zorder=1)
    ax.set_xlabel('Usia (bulan)', fontweight='bold'); ax.set_ylabel('Lingkar Kepala (cm)', fontweight='bold')
    ax.set_title('GRAFIK PERTUMBUHAN WHO: Lingkar Kepala menurut Umur (LK/U)\n' + ("Laki-laki" if sex=='M' else "Perempuan") + ' | 0-60 bulan', fontweight='bold')
    ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.5); ax.minorticks_on()
    ax.set_xlim(0, 60); ax.set_xticks(range(0, 61, 6)); ax.set_xticks(range(0, 61, 3), minor=True)
    y_min = min([curves[z][1].min() for z in (-3,-2,0,2,3)]); y_max = max([curves[z][1].max() for z in (-3,-2,0,2,3)])
    ax.set_ylim(max(25, y_min - 1), y_max + 2)
    ax.legend(loc='upper left', frameon=True, edgecolor='black', fontsize=8, ncol=2)
    fig.text(0.99, 0.01, 'WHO Child Growth Standards 2006', ha='right', va='bottom', fontsize=7, style='italic', alpha=0.6)
    plt.tight_layout(); return fig

def plot_wfl(payload):
    apply_matplotlib_theme(payload['theme'])
    sex, age, h, w = payload['sex'], payload['age_mo'], payload['h'], payload['w']
    lengths = np.arange(BOUNDS['wfl_l'][0], BOUNDS['wfl_l'][1] + 1e-9, 0.5)
    sd_lines = { -3:('#DC143C','-'), -2:('#FF6347','-'), -1:('#FFA500','--'), 0:('#228B22','-'), 1:('#FFA500','--'), 2:('#FF6347','-'), 3:('#DC143C','-') }
    curves = {}
    for z, (c, ls) in sd_lines.items():
        x, y = wfl_curve_smooth(sex, age, z, lengths)
        curves[z] = (x, y)
    fig, ax = plt.subplots(figsize=(11, 7))
    x = curves[0][0]
    _zone_fill(ax, x, curves[-3][1], curves[-2][1], '#FFD4D4', 0.40, 'Wasting Berat')
    _zone_fill(ax, x, curves[-2][1], curves[-1][1], '#FFEBCC', 0.30, 'Wasting')
    _zone_fill(ax, x, curves[-1][1], curves[1][1],  '#E8F5E9', 0.40, 'Zona Normal')
    _zone_fill(ax, x, curves[1][1],  curves[2][1],  '#FFF9C4', 0.30, 'Risiko Overweight')
    _zone_fill(ax, x, curves[2][1],  curves[3][1],  '#FFD4D4', 0.40, 'Overweight/Obesitas')
    for z, (c, ls) in sd_lines.items():
        ax.plot(curves[z][0], curves[z][1], color=c, linestyle=ls, linewidth=2.0 if abs(z) in (0,2) else 1.6, label=("Median" if z==0 else f"{z:+d} SD"), zorder=5)
    if h is not None and w is not None:
        z_whz = payload['z']['whz']
        point_color = '#228B22'
        if z_whz is not None:
            if z_whz < -3 or z_whz > 3: point_color = '#8B0000'
            elif z_whz < -2 or z_whz > 2: point_color = '#DC143C'
            elif z_whz < -1 or z_whz > 1: point_color = '#FF8C00'
        ax.scatter([h], [w], s=300, c=point_color, edgecolors='black', linewidths=2.5, marker='o', zorder=20, label='Data Anak')
        ax.plot([h, h], [0, w], 'k--', linewidth=1, alpha=0.3, zorder=1)
    ax.set_xlabel('Panjang/Tinggi Badan (cm)', fontweight='bold'); ax.set_ylabel('Berat Badan (kg)', fontweight='bold')
    ax.set_title('GRAFIK PERTUMBUHAN WHO: Berat menurut Panjang/Tinggi (BB/TB)\n' + ("Laki-laki" if sex=='M' else "Perempuan"), fontweight='bold')
    ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.5); ax.minorticks_on()
    ax.set_xlim(lengths.min(), lengths.max())
    y_min = min([curves[z][1].min() for z in (-3,-2,0,2,3)]); y_max = max([curves[z][1].max() for z in (-3,-2,0,2,3)])
    ax.set_ylim(max(0, y_min - 1), y_max + 2)
    ax.legend(loc='upper left', frameon=True, edgecolor='black', fontsize=8, ncol=2)
    fig.text(0.99, 0.01, 'WHO Child Growth Standards 2006', ha='right', va='bottom', fontsize=7, style='italic', alpha=0.6)
    plt.tight_layout(); return fig

def plot_bars(payload):
    apply_matplotlib_theme(payload['theme'])
    z = payload['z']
    labels = ['WAZ\n(BB/U)', 'HAZ\n(TB/U)', 'WHZ\n(BB/TB)', 'BAZ\n(IMT/U)', 'HCZ\n(LK/U)']
    values = [z['waz'], z['haz'], z['whz'], z['baz'], z['hcz']]
    def get_bar_color(v):
        if v is None or math.isnan(v): return '#CCCCCC'
        if abs(v) > 3: return '#8B0000'
        if abs(v) > 2: return '#DC143C'
        if abs(v) > 1: return '#FF8C00'
        return '#228B22'
    colors_bar = [get_bar_color(v) for v in values]
    plot_values = [0 if (v is None or (isinstance(v,float) and math.isnan(v))) else v for v in values]
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.axhspan(-3, -2, color='#FFD4D4', alpha=0.3, label='Zona Kurang (-3 to -2 SD)')
    ax.axhspan(-2,  2, color='#E8F5E9', alpha=0.3, label='Zona Normal (-2 to +2 SD)')
    ax.axhspan( 2,  3, color='#FFD4D4', alpha=0.3, label='Zona Lebih (+2 to +3 SD)')
    ax.axhline(0, color='#228B22', linewidth=3, linestyle='-', label='Median (0 SD)', zorder=5)
    ax.axhline(-2, color='#DC143C', linewidth=2, linestyle='--', label='-2 SD', alpha=0.7)
    ax.axhline( 2, color='#DC143C', linewidth=2, linestyle='--', label='+2 SD', alpha=0.7)
    ax.axhline(-3, color='#8B0000', linewidth=1.5, linestyle=':',  label='-3 SD', alpha=0.5)
    ax.axhline( 3, color='#8B0000', linewidth=1.5, linestyle=':',  label='+3 SD', alpha=0.5)
    bars = ax.bar(labels, plot_values, color=colors_bar, edgecolor='black', linewidth=2, width=0.6, alpha=0.9, zorder=10)
    for i, (v, bar) in enumerate(zip(values, bars)):
        if v is not None and not (isinstance(v,float) and math.isnan(v)):
            y_pos = bar.get_height(); offset = 0.3 if y_pos >= 0 else -0.5
            status = "Kritis" if abs(v)>3 else ("Perlu Perhatian" if abs(v)>2 else ("Borderline" if abs(v)>1 else "Normal"))
            ax.text(bar.get_x()+bar.get_width()/2, y_pos+offset, f'{fmtz(v,2)}\n({status})', ha='center', va='bottom' if y_pos>=0 else 'top', fontweight='bold', fontsize=10, bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor=colors_bar[i], linewidth=2), zorder=15)
    ax.set_ylabel('Z-score', fontweight='bold', fontsize=12)
    ax.set_title('RINGKASAN STATUS GIZI - Semua Indeks Antropometri\nWHO Child Growth Standards', fontweight='bold', fontsize=13, pad=15)
    ax.set_ylim(-5, 5); ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.5, zorder=1)
    ax.legend(loc='upper right', frameon=True, edgecolor='black', fontsize=8, title='Referensi WHO', title_fontsize=9)
    fig.text(0.99, 0.01, 'WHO Child Growth Standards 2006', ha='right', va='bottom', fontsize=7, style='italic', alpha=0.6)
    plt.tight_layout(); return fig

# Export helpers

def export_png(fig, filename):
    try:
        path = filename
        fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
        return path
    except Exception:
        return None

def export_csv(payload, filename):
    try:
        path = filename
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['=== DATA ANAK ==='])
            writer.writerow(['Nama Anak', payload.get('name_child', '')])
            writer.writerow(['Orang Tua/Wali', payload.get('name_parent', '')])
            writer.writerow(['Jenis Kelamin', payload.get('sex_text', '')])
            writer.writerow(['Usia (bulan)', f"{payload.get('age_mo', 0):.2f}"])
            writer.writerow(['Usia (hari)', payload.get('age_days', 0)])
            writer.writerow([])
            writer.writerow(['=== PENGUKURAN ==='])
            writer.writerow(['Berat Badan (kg)', payload.get('w', '')])
            writer.writerow(['Panjang/Tinggi (cm)', payload.get('h', '')])
            writer.writerow(['Lingkar Kepala (cm)', payload.get('hc', '')])
            writer.writerow([])
            writer.writerow(['=== HASIL ANALISIS ==='])
            writer.writerow(['Indeks', 'Z-score', 'Persentil (%)', 'Kategori Permenkes', 'Kategori WHO'])
            for key, label in [('waz','WAZ (BB/U)'),('haz','HAZ (TB/U)'),('whz','WHZ (BB/TB)'),('baz','BAZ (IMT/U)'),('hcz','HCZ (LK/U)')]:
                writer.writerow([label, fmtz(payload['z'][key]), payload['pct'][key] if payload['pct'][key] is not None else '', payload['permenkes'][key], payload['who'][key]])
            writer.writerow([])
            writer.writerow(['Tanggal Export', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['Sumber', 'AnthroHPK - WHO Child Growth Standards + Permenkes 2020'])
        return path
    except Exception:
        return None

def qr_image_bytes(text="https://github.com/AnthroHPK"):
    try:
        qr = qrcode.QRCode(box_size=3, border=2); qr.add_data(text); qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)
        return buf
    except Exception:
        return None

def export_pdf(payload, md_text, figs, filename):
    try:
        path = filename
        c = canvas.Canvas(path, pagesize=A4)
        W, H = A4
        now = datetime.datetime.now().strftime("%d %B %Y, %H:%M WIB")
        # Header bar
        c.setFillColorRGB(0.965, 0.647, 0.753)
        c.rect(0, H - 50, W, 50, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, H - 32, "AnthroHPK - Laporan Status Gizi Anak")
        c.setFont("Helvetica", 10)
        c.drawRightString(W - 30, H - 32, now)
        y = H - 80
        c.setFont("Helvetica-Bold", 12); c.drawString(30, y, "INFORMASI ANAK"); y -= 20; c.setFont("Helvetica", 10)
        if payload.get('name_child'): c.drawString(40, y, f"Nama: {payload['name_child']}"); y -= 15
        if payload.get('name_parent'): c.drawString(40, y, f"Orang Tua/Wali: {payload['name_parent']}"); y -= 15
        c.drawString(40, y, f"Jenis Kelamin: {payload['sex_text']}"); y -= 15
        c.drawString(40, y, f"Usia: {payload['age_mo']:.1f} bulan (~{payload['age_days']} hari)"); y -= 25
        c.setFont("Helvetica-Bold", 12); c.drawString(30, y, "DATA ANTROPOMETRI"); y -= 20; c.setFont("Helvetica", 10)
        c.drawString(40, y, f"Berat Badan: {payload['w']:.1f} kg"); y -= 15
        c.drawString(40, y, f"Panjang/Tinggi: {payload['h']:.1f} cm"); y -= 15
        if payload.get('hc'): c.drawString(40, y, f"Lingkar Kepala: {payload['hc']:.1f} cm"); y -= 20
        else: y -= 5
        y -= 10; c.setFont("Helvetica-Bold", 12); c.drawString(30, y, "HASIL ANALISIS"); y -= 20
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, y, "Indeks"); c.drawString(120, y, "Z-score"); c.drawString(180, y, "Persentil"); c.drawString(250, y, "Status (Permenkes)"); c.drawString(400, y, "Status (WHO)")
        y -= 3; c.line(35, y, W - 35, y); y -= 12; c.setFont("Helvetica", 9)
        for key, label in [('waz','WAZ (BB/U)'),('haz','HAZ (TB/U)'),('whz','WHZ (BB/TB)'),('baz','BAZ (IMT/U)'),('hcz','HCZ (LK/U)')]:
            c.drawString(40, y, label); c.drawString(120, y, fmtz(payload['z'][key])); pct = payload['pct'][key]
            c.drawString(180, y, f"{pct}%" if pct is not None else "—"); c.drawString(250, y, payload['permenkes'][key][:30]); c.drawString(400, y, payload['who'][key][:25]); y -= 14
        qr_buf = qr_image_bytes()
        if qr_buf: c.drawImage(ImageReader(qr_buf), W - 80, 30, width=50, height=50)
        c.setFont("Helvetica-Oblique", 8); c.drawRightString(W - 30, 15, "Hal. 1"); c.showPage()
        page_num = 2
        titles = [
            "Grafik Berat Badan menurut Umur (BB/U)",
            "Grafik Panjang/Tinggi menurut Umur (TB/U)",
            "Grafik Lingkar Kepala menurut Umur (LK/U)",
            "Grafik Berat menurut Panjang/Tinggi (BB/TB)",
            "Grafik Ringkasan Semua Indeks"
        ]
        for title, fig in zip(titles, figs):
            c.setFillColorRGB(0.965, 0.647, 0.753); c.rect(0, H - 50, W, 50, stroke=0, fill=1)
            c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawString(30, H - 32, title)
            buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white'); buf.seek(0)
            c.drawImage(ImageReader(buf), 30, 100, width=W - 60, preserveAspectRatio=True)
            c.setFont("Helvetica-Oblique", 8); c.drawRightString(W - 30, 15, f"Hal. {page_num}"); c.showPage(); page_num += 1
        c.setFillColorRGB(0.965, 0.647, 0.753); c.rect(0, H - 50, W, 50, stroke=0, fill=1)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawString(30, H - 32, "Catatan Penting & Disclaimer")
        y = H - 80; c.setFont("Helvetica", 10)
        disclaimers = [
            "1. Aplikasi ini bersifat SKRINING EDUKATIF, bukan diagnosis medis.", "",
            "2. Hasil harus diinterpretasikan oleh tenaga kesehatan terlatih.", "",
            "3. Klasifikasi mengacu pada:", "   • WHO Child Growth Standards (2006)", "   • Permenkes RI No. 2 Tahun 2020", "",
            "4. Data Anda TIDAK disimpan di server (privasi terjaga).", "",
            "5. Untuk konsultasi lanjutan, hubungi:", "   • Posyandu / Puskesmas / Dokter anak", "",
            "6. Pastikan pengukuran: alat terkalibrasi, teknik benar, anak tenang."
        ]
        # Use the ``disclaimers`` list defined above for iteration.  Fall back to an empty list if not defined.
        for line in locals().get('disclaimers', []):
            c.drawString(40, y, line)
            y -= 15
        y -= 20; c.setFont("Helvetica-BoldOblique", 10); c.drawString(40, y, "Referensi:"); y -= 15; c.setFont("Helvetica", 9)
        c.drawString(40, y, "WHO: https://www.who.int/tools/child-growth-standards"); y -= 12
        c.drawString(40, y, "Permenkes: https://peraturan.bpk.go.id/Details/135219")
        c.setFont("Helvetica-Oblique", 8); c.drawRightString(W - 30, 15, f"Hal. {page_num}")
        c.save(); return path
    except Exception:
        return None

# UI callback functions

def do_prefill(sex_text, age_mode, dob, dom, age_mo):
    try:
        w, h, hc = median_values_for(sex_text, age_mode, dob, dom, age_mo)
        if w is None:
            return (gr.update(), gr.update(), gr.update(), "❌ Tidak dapat menghitung median. Periksa input usia.")
        return (gr.update(value=w), gr.update(value=h), gr.update(value=hc), f"✅ Prefill berhasil! Nilai median WHO (Z=0) terisi.")
    except Exception as e:
        return (gr.update(), gr.update(), gr.update(), f"❌ Error: {str(e)}")

def do_demo():
    return ("Perempuan","Usia (bulan)","","",18.0,10.2,80.5,46.8,"Siti Aisyah","Ibu Fatimah","Orang tua","pastel","✅ **Mode Demo Aktif!** Klik '🔍 Analisis Sekarang'.")

def update_age_input_visibility(age_mode_selected):
    if age_mode_selected == "Tanggal":
        return (gr.update(visible=True, interactive=True), gr.update(visible=True, interactive=True), gr.update(visible=False, interactive=False))
    else:
        return (gr.update(visible=False, interactive=False), gr.update(visible=False, interactive=False), gr.update(visible=True, interactive=True))

def run_all(sex_text, age_mode, dob, dom, age_mo, w, h, hc, name_child, name_parent, lang_mode, theme):
    try:
        result = compute_all(sex_text, age_mode, dob, dom, age_mo, w, h, hc, name_child, name_parent, lang_mode, theme)
        if result[1] is None:
            return (result[0], None, None, None, None, None, None, None, None, None, None, None, None, "❌ Analisis gagal. Lihat pesan error di atas.")
        md, payload = result
        fig1 = plot_wfa(payload)
        fig2 = plot_hfa(payload)
        fig3 = plot_hcfa(payload)
        fig4 = plot_wfl(payload)
        fig5 = plot_bars(payload)
        figs = [fig1, fig2, fig3, fig4, fig5]
        png1 = export_png(fig1, "chart_wfa.png")
        png2 = export_png(fig2, "chart_hfa.png")
        png3 = export_png(fig3, "chart_hcfa.png")
        png4 = export_png(fig4, "chart_wfl.png")
        png5 = export_png(fig5, "chart_bars.png")
        child_name = (payload.get('name_child') or 'Anak').replace(' ', '_')[:30]
        pdf = export_pdf(payload, md, figs, f"Laporan_Gizi_{child_name}.pdf")
        csvf = export_csv(payload, "hasil_analisis.csv")
        status_msg = "✅ **Analisis selesai!** Lihat hasil di bawah dan unduh laporan jika diperlukan."
        if payload.get('errors'): status_msg = "⚠️ **Analisis selesai dengan peringatan kritis!** Periksa validasi data."
        return (md, fig1, fig2, fig3, fig4, fig5, pdf, csvf, png1, png2, png3, png4, png5, status_msg)
    except Exception as e:
        error_trace = traceback.format_exc(); print("Run all error", error_trace)
        return (f"❌ **Error Sistem:**\n\n````\n{str(e)}\n````\n\nSilakan refresh dan coba lagi.", None, None, None, None, None, None, None, None, None, None, None, None, "❌ Terjadi error sistem.")

# Build Gradio interface
custom_css = """
.gradio-container { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.status-success { color: #28a745; font-weight: bold; }
.status-warning { color: #ffc107; font-weight: bold; }
.status-error   { color: #dc3545; font-weight: bold; }
.big-button     { font-size: 18px !important; font-weight: bold !important; padding: 20px !important; }
"""

with gr.Blocks(
    title="AnthroHPK - Kalkulator Status Gizi Anak (0-5 tahun)",
    theme=gr.themes.Soft(primary_hue="pink", secondary_hue="teal", neutral_hue="slate"),
    css=custom_css
) as demo:
    gr.Markdown("""
    # 🏥 **AnthroHPK** - Kalkulator Status Gizi Anak Profesional
    ### 📊 WHO Child Growth Standards + Permenkes 2020 | Usia 0-60 Bulan

    > 🔒 **Privasi Terjaga**: Data Anda tidak disimpan di server  
    > ⚕️ **Standar Resmi**: WHO & Permenkes RI No. 2/2020  
    > 📱 **Mudah Digunakan**: Mode Orang Tua & Nakes
    """)
    gr.Markdown("---")
    with gr.Row():
        with gr.Column(scale=5):
            gr.Markdown("## 📝 Input Data Anak")
            with gr.Group():
                gr.Markdown("### 👤 Identitas")
                with gr.Row():
                    name_child = gr.Textbox(label="Nama Anak (opsional)", placeholder="Budi Santoso", info="Untuk laporan PDF")
                    name_parent = gr.Textbox(label="Nama Orang Tua/Wali (opsional)", placeholder="Ibu Siti", info="Untuk laporan PDF")
                sex = gr.Radio(["Laki-laki","Perempuan"], label="Jenis Kelamin", value="Laki-laki")
            with gr.Group():
                gr.Markdown("### 📅 Usia")
                age_mode = gr.Radio(["Tanggal","Usia (bulan)"], label="Mode Input Usia", value="Tanggal")
                with gr.Row():
                    dob = gr.Textbox(label="Tanggal Lahir", placeholder="2023-06-15 atau 15/06/2023", info="YYYY-MM-DD atau DD/MM/YYYY", visible=True)
                    dom = gr.Textbox(label="Tanggal Pengukuran", placeholder="2025-11-10 atau 10/11/2025", info="Tanggal ukur", visible=True)
                age_mo = gr.Number(label="Usia (bulan)", value=12.0, precision=1, visible=False)
            with gr.Group():
                gr.Markdown("### 📏 Data Antropometri")
                gr.Markdown("*Gunakan **kg** untuk berat & **cm** untuk panjang/tinggi*")
                with gr.Row():
                    w = gr.Number(label="Berat Badan (kg)", value=10.0, precision=2)
                    h = gr.Number(label="Panjang/Tinggi Badan (cm)", value=75.0, precision=1)
                hc = gr.Number(label="Lingkar Kepala (cm) - Opsional", value=None, precision=1)
            with gr.Group():
                gr.Markdown("### ⚙️ Pengaturan Tampilan")
                with gr.Row():
                    lang_mode = gr.Radio(["Orang tua","Nakes"], label="Mode Bahasa Output", value="Orang tua")
                    theme = gr.Radio(["pastel","dark","colorblind"], label="Tema Grafik", value="pastel")
            gr.Markdown("---")
            with gr.Row():
                prefill_btn = gr.Button("📊 Isi Nilai Median WHO (Z=0)", variant="secondary", size="sm")
                demo_btn   = gr.Button("🎬 Coba Demo", variant="secondary", size="sm")
            status_msg = gr.Markdown("💡 **Tip**: Klik 'Coba Demo' lalu 'Analisis Sekarang'")
            run_btn = gr.Button("🔍 Analisis Sekarang", variant="primary", size="lg", elem_classes="big-button")
        with gr.Column(scale=2):
            gr.Markdown("## 💡 Panduan Cepat")
            with gr.Accordion("📏 Tips Pengukuran", open=True):
                gr.Markdown("**Berat:** tanpa sepatu, pakaian minimal. **Tinggi:** <24 bln terlentang, ≥24 bln berdiri. **LK:** ukur 3x, ambil terbesar.")
            with gr.Accordion("🎯 Interpretasi Z-Score", open=False):
                gr.Markdown("""
                | Z | Status |
                |---|--------|
                | < -3 | 🔴 Sangat kurang |
                | -3 s/d -2 | 🟡 Kurang |
                | -2 s/d +2 | 🟢 Normal |
                | +2 s/d +3 | 🟡 Risiko lebih |
                | > +3 | 🔴 Obesitas |
                """)
            with gr.Accordion("⚠️ Peringatan", open=False):
                gr.Markdown("Skrining edukatif; konsultasi nakes bila ada masalah. Pastikan satuan benar.")
    gr.Markdown("---")
    with gr.Row():
        with gr.Column():
            gr.Markdown("## 📊 Hasil Analisis")
            out_md = gr.Markdown("*Hasil akan tampil setelah klik 'Analisis Sekarang'*")
    gr.Markdown("---")
    gr.Markdown("## 📈 Grafik Pertumbuhan")
    with gr.Tabs():
        with gr.TabItem("📊 BB menurut Umur (WFA)"):
            gr.Markdown("*Apakah berat sesuai usia?*")
            plt1 = gr.Plot(label="Weight-for-Age")
        with gr.TabItem("📏 TB/PB menurut Umur (HFA)"):
            gr.Markdown("*Deteksi stunting*")
            plt2 = gr.Plot(label="Height-for-Age")
        with gr.TabItem("🧠 Lingkar Kepala (HCFA)"):
            gr.Markdown("*Pantau perkembangan kepala*")
            plt3 = gr.Plot(label="Head Circumference-for-Age")
        with gr.TabItem("🎯 BB menurut TB/PB (WFL)"):
            gr.Markdown("*Kurus/normal/overweight*")
            plt4 = gr.Plot(label="Weight-for-Length")
        with gr.TabItem("📊 Ringkasan (Bar)"):
            gr.Markdown("*Semua indeks dalam satu grafik*")
            plt5 = gr.Plot(label="Summary Bar Chart")
    gr.Markdown("---")
    gr.Markdown("## 💾 Unduh Laporan")
    with gr.Row():
        with gr.Column():
            pdf_out = gr.File(label="📄 Laporan PDF (A4)", file_types=[".pdf"])
            gr.Markdown("*Multi-halaman dengan grafik & tabel*")
        with gr.Column():
            csv_out = gr.File(label="📊 Data CSV", file_types=[".csv"])
            gr.Markdown("*Untuk analisis lanjutan*")
    with gr.Row():
        png1 = gr.File(label="🖼️ Grafik WFA (PNG)", file_types=[".png"])
        png2 = gr.File(label="🖼️ Grafik HFA (PNG)", file_types=[".png"])
        png3 = gr.File(label="🖼️ Grafik HCFA (PNG)", file_types=[".png"])
    with gr.Row():
        png4 = gr.File(label="🖼️ Grafik WFL (PNG)", file_types=[".png"])
        png5 = gr.File(label="🖼️ Grafik Bar (PNG)", file_types=[".png"])
    with gr.Accordion("📖 Panduan Lengkap & FAQ", open=False):
        gr.Markdown("Panduan lengkap tersedia di dokumentasi resmi.")

    # Events
    age_mode.change(fn=update_age_input_visibility, inputs=[age_mode], outputs=[dob, dom, age_mo])
    prefill_btn.click(fn=do_prefill, inputs=[sex, age_mode, dob, dom, age_mo], outputs=[w, h, hc, status_msg])
    demo_btn.click(fn=do_demo, outputs=[sex, age_mode, dob, dom, age_mo, w, h, hc, name_child, name_parent, lang_mode, theme, status_msg])
    run_btn.click(fn=run_all, inputs=[sex, age_mode, dob, dom, age_mo, w, h, hc, name_child, name_parent, lang_mode, theme], outputs=[out_md, plt1, plt2, plt3, plt4, plt5, pdf_out, csv_out, png1, png2, png3, png4, png5, status_msg])

# Create FastAPI app and mount Gradio
app = FastAPI()
# Serve static files for assetlinks and manifest
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")
app.mount("/static", StaticFiles(directory="static"), name="static")
demo.queue(max_size=10)
app = gr.mount_gradio_app(app, demo, path="/")

