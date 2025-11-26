#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#==============================================================================
#                    AnthroHPK v4.0 - ARTICLES DATABASE
#           Perpustakaan Ibu Balita - 40+ Artikel Edukasi
#==============================================================================
"""

from typing import List, Dict, Optional
import re

# ==============================================================================
# KATEGORI ARTIKEL
# ==============================================================================

ARTICLE_CATEGORIES = [
    "Gizi & Stunting",
    "Nutrisi & MPASI",
    "Tumbuh Kembang",
    "Kesehatan Ibu",
    "Imunisasi",
    "ASI & Menyusui",
    "Perkembangan Anak",
    "Tips Parenting"
]

# ==============================================================================
# DATABASE ARTIKEL
# ==============================================================================

ARTIKEL_DATABASE = [
    # =========================================================================
    # KATEGORI: GIZI & STUNTING
    # =========================================================================
    {
        "id": 1,
        "kategori": "Gizi & Stunting",
        "title": "Mengenal Stunting dan Cara Pencegahannya",
        "summary": "Panduan lengkap memahami stunting, penyebab, dan langkah pencegahan efektif.",
        "source": "Kemenkes RI | UNICEF",
        "image_url": "https://images.pexels.com/photos/3845126/pexels-photo-3845126.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# Mengenal Stunting dan Cara Pencegahannya

Stunting adalah kondisi gagal tumbuh pada anak akibat kekurangan gizi kronis, terutama dalam 1000 Hari Pertama Kehidupan (HPK).

## Apa itu Stunting?

Stunting ditandai dengan tinggi badan anak yang lebih pendek dari standar usianya (Z-score TB/U < -2 SD menurut WHO). Ini bukan sekadar "pendek", tapi mencerminkan gangguan pertumbuhan yang berdampak jangka panjang.

## Dampak Stunting

* **Jangka Pendek:** Rentan sakit, perkembangan otak terganggu, kemampuan belajar menurun
* **Jangka Panjang:** Produktivitas rendah saat dewasa, risiko penyakit degeneratif meningkat, siklus kemiskinan

## Penyebab Utama

1. **Gizi Buruk pada Ibu Hamil:** Kurang asupan protein, zat besi, asam folat
2. **ASI Tidak Optimal:** Tidak ASI eksklusif 6 bulan, penyapihan terlalu dini
3. **MPASI Tidak Adekuat:** Kurang protein hewani, porsi tidak cukup
4. **Infeksi Berulang:** Diare kronis, ISPA berulang
5. **Sanitasi Buruk:** Air tidak bersih, tidak cuci tangan

## Pencegahan Stunting

### 1000 HPK (Hari Pertama Kehidupan)
* Gizi ibu hamil optimal
* IMD dan ASI eksklusif 6 bulan
* MPASI kaya protein hewani mulai 6 bulan
* Imunisasi lengkap
* Sanitasi & air bersih

---

**Sumber:** Kemenkes RI, UNICEF Indonesia
        """
    },
    {
        "id": 2,
        "kategori": "Gizi & Stunting",
        "title": "Protein Hewani: Kunci Cegah Stunting",
        "summary": "Mengapa protein hewani sangat penting untuk pertumbuhan anak dan mencegah stunting.",
        "source": "IDAI | WHO",
        "image_url": "https://images.pexels.com/photos/616354/pexels-photo-616354.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# Protein Hewani: Kunci Cegah Stunting

Protein hewani mengandung asam amino esensial lengkap yang sangat dibutuhkan untuk pertumbuhan optimal anak.

## Mengapa Protein Hewani?

* **Asam amino lengkap:** Semua 9 asam amino esensial tersedia
* **Bioavailabilitas tinggi:** Mudah diserap tubuh (90%+)
* **Kaya zat besi heme:** Mencegah anemia
* **Zinc tinggi:** Penting untuk imunitas dan pertumbuhan

## Sumber Protein Hewani Terbaik

1. **Telur** - Murah, mudah didapat, protein lengkap
2. **Ikan** - Omega-3 untuk otak, protein tinggi
3. **Hati ayam/sapi** - Zat besi dan vitamin A tertinggi
4. **Daging ayam/sapi** - Protein dan zinc
5. **Susu dan produk olahan** - Kalsium untuk tulang

## Kebutuhan Protein Anak

| Usia | Kebutuhan/hari |
|------|----------------|
| 6-11 bulan | 11 gram |
| 1-3 tahun | 13 gram |
| 4-6 tahun | 19 gram |

## Tips Pemberian

* Berikan protein hewani di SETIAP waktu makan
* Variasi jenis protein setiap hari
* Kombinasi dengan sayuran untuk gizi seimbang

---

**Sumber:** IDAI, WHO
        """
    },
    {
        "id": 3,
        "kategori": "Gizi & Stunting",
        "title": "Wasting vs Stunting: Apa Bedanya?",
        "summary": "Memahami perbedaan antara wasting (kurus) dan stunting (pendek) pada anak.",
        "source": "WHO | Kemenkes RI",
        "image_url": "https://images.pexels.com/photos/3807517/pexels-photo-3807517.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# Wasting vs Stunting: Apa Bedanya?

Keduanya adalah bentuk malnutrisi, tapi dengan karakteristik dan penanganan berbeda.

## Wasting (Kurus)

* **Definisi:** BB/TB < -2 SD (berat badan rendah untuk tinggi badan)
* **Penyebab:** Kekurangan gizi AKUT (jangka pendek)
* **Ciri:** Anak tampak kurus, tulang terlihat
* **Reversibilitas:** Bisa diperbaiki dalam hitungan minggu/bulan
* **Penanganan:** PMT (Pemberian Makanan Tambahan), F75/F100 untuk gizi buruk

## Stunting (Pendek)

* **Definisi:** TB/U < -2 SD (tinggi badan rendah untuk usia)
* **Penyebab:** Kekurangan gizi KRONIS (jangka panjang, sejak dalam kandungan)
* **Ciri:** Anak pendek dari teman sebayanya
* **Reversibilitas:** Sulit diperbaiki setelah usia 2 tahun
* **Penanganan:** Pencegahan sejak 1000 HPK

## Kombinasi Wasting + Stunting

Anak bisa mengalami keduanya sekaligus (concurrent wasting-stunting), yang merupakan kondisi paling berisiko tinggi.

---

**Sumber:** WHO, Kemenkes RI
        """
    },
    
    # =========================================================================
    # KATEGORI: NUTRISI & MPASI
    # =========================================================================
    {
        "id": 4,
        "kategori": "Nutrisi & MPASI",
        "title": "Panduan Memulai MPASI 6 Bulan",
        "summary": "Langkah demi langkah memulai MPASI yang benar sesuai rekomendasi WHO.",
        "source": "WHO | IDAI",
        "image_url": "https://images.pexels.com/photos/3662630/pexels-photo-3662630.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# Panduan Memulai MPASI 6 Bulan

MPASI (Makanan Pendamping ASI) dimulai saat bayi genap 6 bulan (180 hari).

## Tanda Bayi Siap MPASI

* Bisa duduk dengan bantuan minimal
* Kontrol kepala baik
* Tertarik melihat makanan
* Refleks menjulurkan lidah berkurang
* Membuka mulut saat ditawari makanan

## Prinsip MPASI WHO

1. **Tepat Waktu:** Mulai genap 6 bulan
2. **Adekuat:** Memenuhi kebutuhan gizi
3. **Aman:** Higienis dalam penyiapan
4. **Diberikan dengan Benar:** Responsif feeding

## Menu MPASI Pertama

* Tekstur: Puree halus (disaring)
* Frekuensi: 1-2x sehari
* Porsi: 2-3 sendok makan
* Jenis: Karbohidrat + protein hewani + sayur + lemak

## Contoh Menu Hari Pertama

**Bubur Beras Hati Ayam:**
- 2 sdm beras, masak jadi bubur
- 1 potong hati ayam, kukus, blender halus
- 1 sdt minyak zaitun
- Saring hingga sangat halus

---

**Sumber:** WHO, IDAI
        """
    },
    {
        "id": 5,
        "kategori": "Nutrisi & MPASI",
        "title": "Mengatasi GTM (Gerakan Tutup Mulut)",
        "summary": "Strategi menghadapi anak yang menolak makan atau menjadi picky eater.",
        "source": "IDAI",
        "image_url": "https://images.pexels.com/photos/3771129/pexels-photo-3771129.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# Mengatasi GTM (Gerakan Tutup Mulut)

GTM adalah fase normal yang dialami banyak balita, biasanya mulai usia 1-2 tahun.

## Penyebab GTM

* **Bosan:** Menu monoton
* **Trauma:** Dipaksa makan, dimarahi
* **Kenyang:** Jadwal makan terlalu dekat
* **Tidak nyaman:** Tumbuh gigi, sariawan
* **Neofobia:** Takut makanan baru (normal!)

## Feeding Rules (IDAI)

1. **Jadwal teratur:** 3x makan + 2x snack
2. **Durasi max 30 menit:** Selesai atau tidak, akhiri
3. **Tanpa distraksi:** No TV, gadget, mainan
4. **Tidak memaksa:** Suasana menyenangkan
5. **Biarkan lapar:** Hanya air putih di antara jadwal

## Yang TIDAK Boleh Dilakukan

* Memaksa dengan kekerasan
* Menyuap sambil bermain/nonton TV
* Memberi camilan terus-menerus
* Mengganti makanan dengan susu formula

## Kapan Khawatir?

* BB tidak naik 2 bulan berturut-turut
* Menolak SEMUA jenis makanan
* Tampak lemas dan pucat

---

**Sumber:** IDAI
        """
    },
    {
        "id": 6,
        "kategori": "Nutrisi & MPASI",
        "title": "Pentingnya Lemak dalam MPASI",
        "summary": "Mengapa lemak sangat penting untuk bayi dan cara menambahkannya dalam MPASI.",
        "source": "WHO | IDAI",
        "image_url": "https://images.pexels.com/photos/557659/pexels-photo-557659.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# Pentingnya Lemak dalam MPASI

Lemak sering dilupakan, padahal KRUSIAL untuk perkembangan bayi!

## Mengapa Bayi Butuh Lemak?

* **60% otak = lemak:** Penting untuk perkembangan kognitif
* **Penyerap vitamin:** Vitamin A, D, E, K larut dalam lemak
* **Kalori padat:** 9 kkal/gram (vs protein/karbo 4 kkal/gram)
* **Perut bayi kecil:** Butuh makanan padat energi

## Kebutuhan Lemak

WHO: 30-45% kalori MPASI harus dari lemak

## Sumber Lemak Sehat

### Lemak Nabati:
* Minyak zaitun (EVOO)
* Minyak kelapa
* Alpukat
* Santan

### Lemak Hewani:
* Kuning telur
* Mentega (unsalted)
* Keju
* Ikan berlemak (salmon)

## Cara Menambahkan

Tambahkan 1/2 - 1 sendok teh lemak di SETIAP porsi MPASI!

---

**Sumber:** WHO, IDAI
        """
    },
    
    # =========================================================================
    # KATEGORI: ASI & MENYUSUI
    # =========================================================================
    {
        "id": 7,
        "kategori": "ASI & Menyusui",
        "title": "Panduan ASI Eksklusif 6 Bulan",
        "summary": "Kunci sukses menyusui eksklusif dan cara mengatasi masalah umum laktasi.",
        "source": "Kemenkes RI | IDAI",
        "image_url": "https://images.pexels.com/photos/3845459/pexels-photo-3845459.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# Panduan ASI Eksklusif 6 Bulan

ASI eksklusif = HANYA ASI selama 6 bulan pertama, tanpa tambahan apapun.

## Manfaat ASI

* **Untuk Bayi:** Antibodi, nutrisi sempurna, bonding
* **Untuk Ibu:** Kontrasepsi alami, cepat pulih, risiko kanker menurun

## Kunci Sukses Menyusui

### 1. IMD (Inisiasi Menyusu Dini)
Bayi langsung disusui dalam 1 jam pertama kelahiran.

### 2. Pelekatan Benar
* Mulut bayi terbuka lebar
* Areola masuk ke mulut (bukan hanya puting)
* Dagu menempel payudara
* Tidak terdengar bunyi "kecap"

### 3. On Demand
Susui kapanpun bayi menunjukkan tanda lapar.

## Masalah Umum & Solusi

### Puting Lecet
* Penyebab: Pelekatan salah
* Solusi: Perbaiki posisi, oleskan ASI ke puting

### ASI Kurang
* Penyebab: Frekuensi kurang, stres
* Solusi: Susui lebih sering, rileks, cukup minum

### Payudara Bengkak
* Penyebab: Produksi melimpah, tidak lancar
* Solusi: Kompres hangat sebelum menyusui, susui sering

---

**Sumber:** Kemenkes RI, IDAI
        """
    },
    {
        "id": 8,
        "kategori": "ASI & Menyusui",
        "title": "ASI Perah: Cara Menyimpan yang Benar",
        "summary": "Panduan lengkap memerah, menyimpan, dan menghangatkan ASI perah.",
        "source": "IDAI | CDC",
        "image_url": "https://images.pexels.com/photos/3845457/pexels-photo-3845457.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# ASI Perah: Cara Menyimpan yang Benar

Untuk ibu bekerja atau yang perlu menyimpan stok ASI.

## Cara Memerah ASI

* **Manual:** Teknik Marmet, gratis tapi perlu latihan
* **Pompa Manual:** Lebih cepat, harga terjangkau
* **Pompa Elektrik:** Paling efisien, bisa double pumping

## Aturan Penyimpanan (Aturan 4-4-4)

| Lokasi | Suhu | Durasi |
|--------|------|--------|
| Suhu ruang | 25°C | 4 jam |
| Kulkas | 4°C | 4 hari |
| Freezer | -18°C | 4-6 bulan |

## Tips Penyimpanan

* Gunakan wadah khusus ASI atau kantong ASI
* Beri label tanggal dan jam perah
* Simpan di bagian dalam kulkas (bukan pintu)
* Gunakan prinsip FIFO (First In First Out)

## Cara Menghangatkan

1. Pindahkan dari freezer ke kulkas (overnight)
2. Rendam wadah di air hangat (bukan panas!)
3. Goyangkan perlahan untuk mencampur lemak
4. JANGAN gunakan microwave!

## ASI yang Sudah Dihangatkan

* Habiskan dalam 2 jam
* TIDAK boleh dibekukan ulang
* Sisa minum HARUS dibuang

---

**Sumber:** IDAI, CDC
        """
    },
    
    # =========================================================================
    # KATEGORI: TUMBUH KEMBANG
    # =========================================================================
    {
        "id": 9,
        "kategori": "Tumbuh Kembang",
        "title": "Milestone Perkembangan Bayi 0-12 Bulan",
        "summary": "Tahapan perkembangan normal bayi dari lahir hingga 1 tahun.",
        "source": "IDAI | CDC",
        "image_url": "https://images.pexels.com/photos/3875089/pexels-photo-3875089.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# Milestone Perkembangan Bayi 0-12 Bulan

Setiap bayi berkembang dengan kecepatan berbeda, tapi ada patokan umum.

## 0-3 Bulan

### Motorik
* Mengangkat kepala saat tengkurap
* Tangan mulai terbuka (tidak selalu mengepal)

### Bahasa
* Menangis untuk komunikasi
* Mulai cooing (suara "aaaa")

### Sosial
* Tersenyum sosial (respon saat diajak bicara)
* Menatap wajah

## 4-6 Bulan

### Motorik
* Berguling (telentang ↔ tengkurap)
* Duduk dengan bantuan
* Meraih dan menggenggam mainan

### Bahasa
* Babbling (ba-ba, ma-ma tanpa makna)
* Tertawa keras

### Sosial
* Mengenal orang asing (stranger anxiety mulai)

## 7-9 Bulan

### Motorik
* Duduk sendiri tanpa bantuan
* Merangkak
* Berdiri berpegangan

### Bahasa
* Mama/papa dengan makna
* Mengerti "tidak"

## 10-12 Bulan

### Motorik
* Berjalan berpegangan (cruising)
* Berdiri sendiri sebentar
* Beberapa mulai berjalan

### Bahasa
* 1-3 kata bermakna
* Menunjuk untuk berkomunikasi

---

**Sumber:** IDAI, CDC
        """
    },
    {
        "id": 10,
        "kategori": "Tumbuh Kembang",
        "title": "Stimulasi Tumbuh Kembang Anak",
        "summary": "Cara menstimulasi perkembangan motorik, bahasa, dan kognitif anak.",
        "source": "IDAI | Kemenkes RI",
        "image_url": "https://images.pexels.com/photos/3661452/pexels-photo-3661452.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# Stimulasi Tumbuh Kembang Anak

Stimulasi adalah rangsangan yang diberikan untuk mengoptimalkan perkembangan.

## Prinsip Stimulasi

* **Bertahap:** Sesuai usia dan kemampuan
* **Berulang:** Konsisten setiap hari
* **Bervariasi:** Gunakan berbagai cara dan alat
* **Menyenangkan:** Dalam suasana bermain

## Stimulasi per Aspek

### Motorik Kasar
* Tummy time (tengkurap)
* Merangkak di matras
* Bermain bola
* Naik turun tangga (dengan pengawasan)

### Motorik Halus
* Meraih mainan
* Memindahkan benda antar tangan
* Menyusun balok
* Mencoret-coret

### Bahasa
* Ajak bicara sesering mungkin
* Bacakan buku
* Nyanyikan lagu
* Sebutkan nama benda

### Kognitif
* Cilukba (permanensi objek)
* Puzzle sederhana
* Sortir warna/bentuk
* Bermain peran

### Sosial-Emosional
* Peluk dan cium
* Bermain bersama
* Kenalkan teman sebaya
* Ajarkan berbagi

---

**Sumber:** IDAI, Kemenkes RI
        """
    },
    
    # =========================================================================
    # KATEGORI: KESEHATAN IBU
    # =========================================================================
    {
        "id": 11,
        "kategori": "Kesehatan Ibu",
        "title": "Gizi Ibu Hamil untuk Cegah Stunting",
        "summary": "Nutrisi penting selama kehamilan untuk mendukung pertumbuhan janin optimal.",
        "source": "Kemenkes RI | WHO",
        "image_url": "https://images.pexels.com/photos/3622614/pexels-photo-3622614.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# Gizi Ibu Hamil untuk Cegah Stunting

Pencegahan stunting dimulai sejak dalam kandungan!

## Kebutuhan Nutrisi Meningkat

### Trimester 1
* Asam folat: 600 mcg/hari (cegah neural tube defect)
* Kalori: +0 (belum perlu tambahan)
* Fokus: Atasi mual dengan makan sedikit-sedikit

### Trimester 2
* Kalori: +340 kkal/hari
* Protein: +25 gram/hari
* Zat besi: 27 mg/hari
* Kalsium: 1000 mg/hari

### Trimester 3
* Kalori: +450 kkal/hari
* Protein: +25 gram/hari
* DHA: 200-300 mg/hari (perkembangan otak)

## Makanan yang Direkomendasikan

* **Protein:** Telur, ikan, daging, tempe, tahu
* **Zat besi:** Hati, daging merah, bayam
* **Kalsium:** Susu, keju, ikan teri
* **Asam folat:** Sayuran hijau, kacang-kacangan
* **DHA:** Ikan laut (salmon, kembung, sarden)

## Suplemen Wajib

* Tablet Tambah Darah (Fe + asam folat): 1x sehari
* Kalsium: sesuai anjuran dokter

## Yang Harus Dihindari

* Alkohol
* Kafein berlebihan (max 200mg/hari)
* Ikan tinggi merkuri (hiu, king mackerel)
* Makanan mentah/setengah matang

---

**Sumber:** Kemenkes RI, WHO
        """
    },
    {
        "id": 12,
        "kategori": "Kesehatan Ibu",
        "title": "Baby Blues vs Postpartum Depression",
        "summary": "Mengenali perbedaan baby blues dan depresi pasca melahirkan.",
        "source": "IDAI | WHO",
        "image_url": "https://images.pexels.com/photos/3763585/pexels-photo-3763585.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# Baby Blues vs Postpartum Depression

Perubahan mood setelah melahirkan adalah hal yang umum, tapi perlu dibedakan.

## Baby Blues (Normal)

### Karakteristik
* Muncul hari ke-3 sampai ke-10 pasca persalinan
* Berlangsung 2-3 minggu
* Dialami 50-80% ibu baru

### Gejala
* Mudah menangis
* Mood swing
* Cemas ringan
* Sulit tidur
* Sensitif

### Penanganan
* Dukungan keluarga
* Istirahat cukup
* Biasanya membaik sendiri

## Postpartum Depression (Perlu Penanganan)

### Karakteristik
* Muncul dalam 4 minggu - 1 tahun pasca persalinan
* Berlangsung berminggu-minggu/berbulan-bulan
* Dialami 10-15% ibu

### Gejala
* Sedih berkepanjangan
* Tidak tertarik pada bayi
* Merasa tidak mampu merawat bayi
* Pikiran menyakiti diri/bayi
* Gangguan tidur dan nafsu makan berat

### Penanganan
* HARUS konsultasi profesional (psikolog/psikiater)
* Mungkin perlu obat dan terapi
* Dukungan keluarga sangat penting

## Kapan Cari Bantuan?

* Gejala > 2 minggu tidak membaik
* Pikiran menyakiti diri/bayi
* Tidak mampu merawat bayi

**Hotline:** 119 ext 8

---

**Sumber:** IDAI, WHO
        """
    },
    
    # =========================================================================
    # KATEGORI: IMUNISASI
    # =========================================================================
    {
        "id": 13,
        "kategori": "Imunisasi",
        "title": "Jadwal Imunisasi Dasar Lengkap",
        "summary": "Panduan jadwal imunisasi wajib untuk anak usia 0-24 bulan.",
        "source": "Kemenkes RI | IDAI",
        "image_url": "https://images.pexels.com/photos/3985166/pexels-photo-3985166.jpeg?auto=compress&cs=tinysrgb&w=400",
        "full_content": """
# Jadwal Imunisasi Dasar Lengkap

Imunisasi melindungi anak dari penyakit berbahaya yang dapat dicegah.

## Jadwal Imunisasi Indonesia

### Lahir (0 bulan)
* **HB-0:** Hepatitis B dosis 0 (dalam 24 jam)
* **BCG:** Tuberkulosis
* **Polio 0:** OPV

### 1 Bulan
* Polio 1
* DPT-HB-Hib 1
* PCV 1
* Rotavirus 1

### 2 Bulan
* Polio 2
* DPT-HB-Hib 2
* PCV 2
* Rotavirus 2

### 3 Bulan
* Polio 3
* DPT-HB-Hib 3
* PCV 3
* Rotavirus 3

### 4 Bulan
* Polio 4
* DPT-HB-Hib 4

### 9 Bulan
* **Campak/MR 1:** Measles-Rubella

### 18 Bulan
* DPT-HB-Hib Booster
* Polio Booster

### 24 Bulan
* MR 2

## KIPI (Kejadian Ikutan Pasca Imunisasi)

### Normal
* Demam ringan
* Nyeri di tempat suntikan
* Rewel

### Perlu ke Dokter
* Demam >39°C
* Kejang
* Bengkak luas
* Sesak napas

---

**Sumber:** Kemenkes RI, IDAI
        """
    },
]

# Tambahkan lebih banyak artikel untuk melengkapi 40 artikel...
# (Artikel 14-40 akan ditambahkan di bagian selanjutnya)

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_categories() -> List[str]:
    """Get list of all article categories"""
    return ARTICLE_CATEGORIES


def get_article_by_id(article_id: int) -> Optional[Dict]:
    """Get article by ID"""
    for article in ARTIKEL_DATABASE:
        if article.get("id") == article_id:
            return article
    return None


def search_articles(query: str = "", category: str = "") -> List[Dict]:
    """
    Search articles by query and/or category
    
    Args:
        query: Search term (searches title, summary, content)
        category: Filter by category (exact match)
        
    Returns:
        List of matching articles
    """
    results = []
    query_lower = query.lower().strip()
    
    for article in ARTIKEL_DATABASE:
        # Category filter
        if category and category != "Semua Kategori":
            if article.get("kategori") != category:
                continue
        
        # Query filter
        if query_lower:
            title = article.get("title", "").lower()
            summary = article.get("summary", "").lower()
            content = article.get("full_content", "").lower()
            
            if not (query_lower in title or query_lower in summary or query_lower in content):
                continue
        
        results.append(article)
    
    return results


def get_articles_by_category(category: str) -> List[Dict]:
    """Get all articles in a category"""
    return [a for a in ARTIKEL_DATABASE if a.get("kategori") == category]


def format_article_content(content: str) -> str:
    """
    Convert markdown-like content to HTML
    
    Args:
        content: Raw article content with markdown
        
    Returns:
        HTML formatted content
    """
    html = content
    
    # Convert headers
    html = re.sub(r'^# (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    
    # Convert bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # Convert lists
    html = re.sub(r'^\* (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    
    # Convert line breaks
    html = html.replace('\n\n', '</p><p>')
    html = html.replace('\n', '<br>')
    
    # Wrap in paragraph
    html = f'<p>{html}</p>'
    
    # Clean up
    html = html.replace('<p></p>', '')
    html = html.replace('---', '<hr>')
    
    return html


print(f"✅ Articles database loaded: {len(ARTIKEL_DATABASE)} articles")
