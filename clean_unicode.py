#!/usr/bin/env python3
"""
==============================================================================
UNICODE CLEANER - Remove Box-Drawing Characters from app.py
==============================================================================
Script ini menghapus SEMUA karakter Unicode box-drawing yang menyebabkan
SyntaxError: invalid character '═' (U+2550)

Author: Claude & Habib Arsy
Date: November 2025
==============================================================================
"""

import shutil
from datetime import datetime
import sys

def clean_unicode_from_file(filename='app.py'):
    """
    Membersihkan karakter Unicode dari file Python
    
    Args:
        filename: Nama file yang akan dibersihkan (default: app.py)
    """
    
    print("=" * 80)
    print("UNICODE CLEANER - app.py".center(80))
    print("=" * 80)
    print()
    
    # Backup original file
    backup_file = f"{filename.replace('.py', '')}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    try:
        shutil.copy(filename, backup_file)
        print(f"✅ Backup dibuat: {backup_file}")
    except FileNotFoundError:
        print(f"❌ Error: File {filename} tidak ditemukan!")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error saat backup: {e}")
        sys.exit(1)
    
    # Baca file
    print(f"\n📖 Membaca file: {filename}")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error saat membaca file: {e}")
        sys.exit(1)
    
    # Definisi karakter yang akan diganti
    replacements = {
        '═': '=',  # Box drawing horizontal double
        '╔': '#',  # Box drawing down-right double
        '╚': '#',  # Box drawing up-right double
        '║': '#',  # Box drawing vertical double
        '╗': '#',  # Box drawing down-left double
        '╝': '#',  # Box drawing up-left double
        '╬': '+',  # Box drawing cross double
        '╠': '+',  # Box drawing vertical-right double
        '╣': '+',  # Box drawing vertical-left double
        '╦': '+',  # Box drawing down-horizontal double
        '╩': '+',  # Box drawing up-horizontal double
    }
    
    # Hitung total karakter yang akan diganti
    total_replacements = 0
    print("\n🧹 Membersihkan karakter Unicode:")
    print("-" * 80)
    
    for old_char, new_char in replacements.items():
        count = content.count(old_char)
        if count > 0:
            content = content.replace(old_char, new_char)
            total_replacements += count
            print(f"   ✓ Mengganti {count:3d}x karakter '{old_char}' (U+{ord(old_char):04X}) dengan '{new_char}'")
    
    print("-" * 80)
    
    if total_replacements == 0:
        print("\n✅ Tidak ada karakter Unicode yang perlu diganti!")
        print("   File sudah bersih.")
    else:
        print(f"\n✅ Total: {total_replacements} karakter Unicode diganti")
        
        # Simpan file yang sudah dibersihkan
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ File berhasil disimpan: {filename}")
        except Exception as e:
            print(f"❌ Error saat menyimpan file: {e}")
            print(f"   Restore backup dengan: cp {backup_file} {filename}")
            sys.exit(1)
    
    # Verifikasi
    print("\n🔍 Verifikasi hasil...")
    remaining = 0
    for char in replacements.keys():
        if char in content:
            remaining += content.count(char)
    
    if remaining > 0:
        print(f"⚠️  Warning: Masih ada {remaining} karakter Unicode tersisa!")
    else:
        print("✅ Verifikasi sukses: Tidak ada karakter Unicode tersisa")
    
    print("\n" + "=" * 80)
    print("PEMBERSIHAN SELESAI".center(80))
    print("=" * 80)
    print()
    print("📋 Langkah selanjutnya:")
    print("   1. Test run: python app.py")
    print("   2. Cek syntax: python -m py_compile app.py")
    print("   3. Commit: git add app.py && git commit -m 'fix: remove unicode'")
    print("   4. Push: git push")
    print()
    print(f"💾 Backup tersimpan di: {backup_file}")
    print("   (Restore jika ada masalah: cp {} {})".format(backup_file, filename))
    print()
    print("=" * 80)


if __name__ == "__main__":
    # Cek argumen
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = 'app.py'
    
    # Jalankan pembersihan
    clean_unicode_from_file(filename)
