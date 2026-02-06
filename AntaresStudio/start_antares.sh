#!/bin/bash
# ANTARES KAPSÜL 3D STUDIO - Linux/Mac Başlatıcı

echo ""
echo "================================================"
echo "  ANTARES KAPSUL 3D STUDIO v2.0"
echo "================================================"
echo ""

# Sanal ortamı aktifleştir (varsa)
if [ -f "antares_env/bin/activate" ]; then
    echo "[*] Sanal ortam aktif ediliyor..."
    source antares_env/bin/activate
fi

# Python versiyonunu kontrol et
if ! command -v python3 &> /dev/null; then
    echo "[HATA] Python bulunamadi!"
    echo "Lutfen Python 3.8+ yukleyin"
    exit 1
fi

# Programı başlat
echo "[*] Program baslatiliyor..."
echo ""
python3 antares_main_improved.py

# Hata durumunda bekle
if [ $? -ne 0 ]; then
    echo ""
    echo "[HATA] Program kapandi! Hata kodu: $?"
    read -p "Devam etmek icin Enter'a basin..."
fi
