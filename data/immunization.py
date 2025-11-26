#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#==============================================================================
#                    AnthroHPK v4.0 - IMMUNIZATION DATA
#              Indonesian Immunization Schedule (Permenkes RI)
#==============================================================================
"""

from typing import List, Optional

# ==============================================================================
# JADWAL IMUNISASI INDONESIA (Permenkes RI)
# ==============================================================================

IMMUNIZATION_SCHEDULE = {
    0: {
        "vaccines": ["HB-0 (< 24 jam)", "BCG", "Polio 0 (OPV)"],
        "notes": "Diberikan segera setelah lahir di fasilitas kesehatan",
        "critical": True
    },
    1: {
        "vaccines": ["HB-1", "Polio 1", "DPT-HB-Hib 1", "PCV 1", "Rotavirus 1"],
        "notes": "Kunjungan pertama ke Posyandu/Puskesmas",
        "critical": True
    },
    2: {
        "vaccines": ["Polio 2", "DPT-HB-Hib 2", "PCV 2", "Rotavirus 2"],
        "notes": "Lanjutan imunisasi dasar",
        "critical": True
    },
    3: {
        "vaccines": ["Polio 3", "DPT-HB-Hib 3", "PCV 3", "Rotavirus 3"],
        "notes": "Melengkapi seri imunisasi primer",
        "critical": True
    },
    4: {
        "vaccines": ["Polio 4", "DPT-HB-Hib 4"],
        "notes": "Imunisasi lanjutan",
        "critical": False
    },
    9: {
        "vaccines": ["Campak/MR 1"],
        "notes": "Imunisasi Campak/Measles-Rubella pertama",
        "critical": True
    },
    12: {
        "vaccines": ["Campak Booster", "PCV Booster"],
        "notes": "Booster untuk memperkuat kekebalan",
        "critical": False
    },
    15: {
        "vaccines": ["Influenza (opsional)"],
        "notes": "Imunisasi tambahan yang direkomendasikan",
        "critical": False
    },
    18: {
        "vaccines": ["DPT-HB-Hib Booster", "Polio Booster"],
        "notes": "Booster penting untuk perlindungan jangka panjang",
        "critical": True
    },
    24: {
        "vaccines": ["Campak Rubella (MR) 2", "Japanese Encephalitis (daerah endemis)"],
        "notes": "Melengkapi imunisasi dasar lengkap",
        "critical": True
    }
}

# ==============================================================================
# DETAIL VAKSIN
# ==============================================================================

VACCINE_DETAILS = {
    "HB-0": {
        "full_name": "Hepatitis B Dosis 0",
        "description": "Mencegah Hepatitis B yang ditularkan dari ibu ke bayi",
        "side_effects": "Bengkak/nyeri di tempat suntikan (ringan)",
        "contraindication": "Demam tinggi, alergi komponen vaksin"
    },
    "BCG": {
        "full_name": "Bacillus Calmette-Guérin",
        "description": "Mencegah Tuberkulosis (TB) berat pada anak",
        "side_effects": "Benjolan kecil yang akan membentuk parut",
        "contraindication": "Bayi dengan HIV positif, kondisi imunosupresi"
    },
    "Polio": {
        "full_name": "Vaksin Polio (OPV/IPV)",
        "description": "Mencegah Poliomyelitis (lumpuh layu)",
        "side_effects": "Sangat jarang efek samping",
        "contraindication": "Demam tinggi akut"
    },
    "DPT-HB-Hib": {
        "full_name": "Difteri-Pertusis-Tetanus + Hepatitis B + Haemophilus influenzae type b",
        "description": "Vaksin kombinasi 5-in-1 untuk 5 penyakit berbahaya",
        "side_effects": "Demam, rewel, bengkak di tempat suntikan (1-2 hari)",
        "contraindication": "Riwayat kejang setelah vaksinasi sebelumnya"
    },
    "PCV": {
        "full_name": "Pneumococcal Conjugate Vaccine",
        "description": "Mencegah infeksi pneumokokus (radang paru, meningitis)",
        "side_effects": "Demam ringan, nyeri tempat suntikan",
        "contraindication": "Alergi berat terhadap vaksin sebelumnya"
    },
    "Rotavirus": {
        "full_name": "Vaksin Rotavirus",
        "description": "Mencegah diare berat akibat rotavirus",
        "side_effects": "Diare ringan, muntah sementara",
        "contraindication": "Riwayat intususepsi, gangguan saluran cerna berat"
    },
    "MR": {
        "full_name": "Measles-Rubella",
        "description": "Mencegah Campak dan Rubella (campak Jerman)",
        "side_effects": "Demam ringan 5-12 hari setelah vaksinasi",
        "contraindication": "Alergi telur berat, hamil, kondisi imunosupresi"
    },
    "Influenza": {
        "full_name": "Vaksin Influenza",
        "description": "Mencegah flu musiman (perlu diulang tiap tahun)",
        "side_effects": "Nyeri tempat suntikan, demam ringan",
        "contraindication": "Alergi telur, riwayat Guillain-Barré Syndrome"
    },
    "JE": {
        "full_name": "Japanese Encephalitis",
        "description": "Mencegah radang otak Jepang (daerah endemis)",
        "side_effects": "Demam, sakit kepala ringan",
        "contraindication": "Alergi komponen vaksin"
    }
}


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_immunization_for_month(month: int) -> List[str]:
    """
    Get immunization schedule for specific month
    
    Args:
        month: Age in months (0-60)
        
    Returns:
        List of vaccines due at this age, empty list if none
    """
    schedule = IMMUNIZATION_SCHEDULE.get(month, {})
    return schedule.get("vaccines", [])


def get_immunization_details(month: int) -> dict:
    """
    Get detailed immunization information for specific month
    
    Args:
        month: Age in months
        
    Returns:
        Dictionary with vaccines, notes, and critical flag
    """
    return IMMUNIZATION_SCHEDULE.get(month, {
        "vaccines": [],
        "notes": "Tidak ada imunisasi terjadwal",
        "critical": False
    })


def get_vaccine_info(vaccine_name: str) -> Optional[dict]:
    """
    Get detailed information about a specific vaccine
    
    Args:
        vaccine_name: Name of the vaccine
        
    Returns:
        Dictionary with vaccine details or None
    """
    # Try exact match first
    if vaccine_name in VACCINE_DETAILS:
        return VACCINE_DETAILS[vaccine_name]
    
    # Try partial match
    for key, value in VACCINE_DETAILS.items():
        if key.lower() in vaccine_name.lower():
            return value
    
    return None


def get_upcoming_immunizations(current_month: int, lookahead_months: int = 6) -> List[dict]:
    """
    Get list of upcoming immunizations within lookahead period
    
    Args:
        current_month: Current age in months
        lookahead_months: How many months ahead to look
        
    Returns:
        List of upcoming immunization schedules
    """
    upcoming = []
    
    for month in range(current_month, current_month + lookahead_months + 1):
        if month in IMMUNIZATION_SCHEDULE:
            schedule = IMMUNIZATION_SCHEDULE[month]
            upcoming.append({
                "month": month,
                "vaccines": schedule["vaccines"],
                "notes": schedule.get("notes", ""),
                "critical": schedule.get("critical", False),
                "months_away": month - current_month
            })
    
    return upcoming


def get_missed_immunizations(current_month: int, given_vaccines: List[str] = None) -> List[dict]:
    """
    Check for missed immunizations
    
    Args:
        current_month: Current age in months
        given_vaccines: List of vaccines already given (optional)
        
    Returns:
        List of potentially missed immunizations
    """
    if given_vaccines is None:
        given_vaccines = []
    
    given_vaccines_lower = [v.lower() for v in given_vaccines]
    missed = []
    
    for month, schedule in IMMUNIZATION_SCHEDULE.items():
        if month <= current_month:
            for vaccine in schedule["vaccines"]:
                # Check if vaccine was given
                vaccine_given = any(
                    vac in vaccine.lower() or vaccine.lower() in vac 
                    for vac in given_vaccines_lower
                )
                
                if not vaccine_given:
                    missed.append({
                        "month": month,
                        "vaccine": vaccine,
                        "critical": schedule.get("critical", False),
                        "months_overdue": current_month - month
                    })
    
    return missed


def generate_immunization_html(month: int, include_details: bool = True) -> str:
    """
    Generate HTML for immunization display
    
    Args:
        month: Age in months
        include_details: Whether to include vaccine details
        
    Returns:
        HTML string for display
    """
    schedule = get_immunization_details(month)
    vaccines = schedule["vaccines"]
    
    if not vaccines:
        return f"""
        <div style="padding: 15px; background: #f8f9fa; border-radius: 10px; margin: 10px 0;">
            <h4 style="color: #28a745; margin: 0;">✅ Tidak Ada Imunisasi Terjadwal</h4>
            <p style="margin: 5px 0 0 0; color: #666;">
                Untuk bulan ke-{month}, tidak ada imunisasi rutin yang dijadwalkan.
            </p>
        </div>
        """
    
    html = f"""
    <div style="padding: 15px; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                border-radius: 10px; margin: 10px 0; border-left: 4px solid #2196f3;">
        <h4 style="color: #1565c0; margin: 0 0 10px 0;">
            💉 Jadwal Imunisasi Bulan ke-{month}
            {'<span style="color: #d32f2f; font-size: 0.8em;">(PENTING)</span>' if schedule.get("critical") else ''}
        </h4>
        <ul style="margin: 0; padding-left: 20px;">
    """
    
    for vaccine in vaccines:
        details = get_vaccine_info(vaccine) if include_details else None
        
        html += f'<li style="margin: 5px 0;"><strong>{vaccine}</strong>'
        
        if details:
            html += f'<br><small style="color: #666;">{details["description"]}</small>'
        
        html += '</li>'
    
    html += f"""
        </ul>
        <p style="margin: 10px 0 0 0; font-size: 0.9em; color: #555;">
            📝 {schedule.get("notes", "")}
        </p>
    </div>
    """
    
    return html


print("✅ Immunization data loaded")
