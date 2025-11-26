#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#==============================================================================
#                    AnthroHPK v4.0 - UTILITIES MODULE
#                    Common Utility Functions
#==============================================================================
"""

import math
import random
from datetime import datetime, date
from typing import Optional, Any, Tuple, List
from functools import lru_cache
from scipy.special import erf

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MOTIVATIONAL_QUOTES, BOUNDS

# ==============================================================================
# TYPE CONVERSION UTILITIES
# ==============================================================================

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


# ==============================================================================
# AGE CALCULATION UTILITIES
# ==============================================================================

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


def calculate_age_text(age_months: float) -> str:
    """
    Convert age in months to human readable text
    
    Args:
        age_months: Age in months
        
    Returns:
        Formatted string like "1 tahun 6 bulan" or "8 bulan"
    """
    if age_months is None:
        return "N/A"
    
    years = int(age_months // 12)
    months = int(age_months % 12)
    
    if years > 0 and months > 0:
        return f"{years} tahun {months} bulan"
    elif years > 0:
        return f"{years} tahun"
    else:
        return f"{months} bulan"


def calculate_1000_days_progress(dob: date, measurement_date: date = None) -> dict:
    """
    Calculate progress in 1000 first days of life
    
    Args:
        dob: Date of birth
        measurement_date: Date to calculate from (default: today)
        
    Returns:
        Dictionary with day number, phase, percentage, etc.
    """
    if measurement_date is None:
        measurement_date = date.today()
    
    days_lived = (measurement_date - dob).days
    
    # 1000 hari = 730 hari setelah lahir (2 tahun) + 270 hari kehamilan
    # Tapi kita hitung dari lahir, jadi 730 hari = 24 bulan
    total_days = 730  # dari lahir sampai 2 tahun
    
    percentage = min(100, (days_lived / total_days) * 100)
    
    # Determine phase
    if days_lived < 0:
        phase = "pre_birth"
        phase_name = "Sebelum Lahir"
    elif days_lived <= 180:  # 0-6 bulan
        phase = "0_6_bulan"
        phase_name = "ASI Eksklusif (0-6 bulan)"
    elif days_lived <= 365:  # 6-12 bulan
        phase = "6_12_bulan"
        phase_name = "MPASI Awal (6-12 bulan)"
    elif days_lived <= 730:  # 12-24 bulan
        phase = "12_24_bulan"
        phase_name = "Balita (12-24 bulan)"
    else:
        phase = "completed"
        phase_name = "1000 Hari Selesai!"
    
    return {
        "days_lived": days_lived,
        "total_days": total_days,
        "percentage": round(percentage, 1),
        "remaining_days": max(0, total_days - days_lived),
        "phase": phase,
        "phase_name": phase_name,
        "is_completed": days_lived >= total_days
    }


# ==============================================================================
# Z-SCORE UTILITIES
# ==============================================================================

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


def get_zscore_color(z: Optional[float]) -> str:
    """
    Get color based on Z-score severity
    
    Args:
        z: Z-score value
        
    Returns:
        Hex color code
    """
    if z is None:
        return "#888888"
    
    abs_z = abs(z)
    
    if abs_z > 3:
        return "#8B0000"  # Dark red - severe
    elif abs_z > 2:
        return "#DC143C"  # Crimson - moderate
    elif abs_z > 1:
        return "#FFA500"  # Orange - mild
    else:
        return "#28a745"  # Green - normal


def get_zscore_status_emoji(z: Optional[float]) -> str:
    """
    Get emoji status based on Z-score
    
    Args:
        z: Z-score value
        
    Returns:
        Status emoji
    """
    if z is None:
        return "❓"
    
    abs_z = abs(z)
    
    if abs_z > 3:
        return "🚨"
    elif abs_z > 2:
        return "⚠️"
    elif abs_z > 1:
        return "📊"
    else:
        return "✅"


# ==============================================================================
# VALIDATION UTILITIES
# ==============================================================================

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


# ==============================================================================
# MISC UTILITIES
# ==============================================================================

def get_random_quote() -> str:
    """Get random motivational quote for parents"""
    return random.choice(MOTIVATIONAL_QUOTES)


def get_sex_code(sex_text: str) -> str:
    """
    Convert sex text to WHO code
    
    Args:
        sex_text: "Laki-laki" or "Perempuan"
        
    Returns:
        "M" or "F"
    """
    return "M" if sex_text.lower().startswith("l") else "F"


def get_sex_text(sex_code: str) -> str:
    """
    Convert WHO sex code to Indonesian text
    
    Args:
        sex_code: "M" or "F"
        
    Returns:
        "Laki-laki" or "Perempuan"
    """
    return "Laki-laki" if sex_code.upper() == "M" else "Perempuan"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division that returns default on division by zero
    """
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value between min and max
    """
    return max(min_val, min(max_val, value))


print("✅ Utilities module loaded")
