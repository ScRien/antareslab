# 🚀 ANTARES KAPSÜL 3D STUDIO - Hızlı Başlangıç

## ⚡ 5 Dakikada Kurulum

### 1️⃣ Python Kurulumu (Yüklüyse atla)
```bash
# https://www.python.org/downloads/ adresinden Python 3.10+ indirin
```

### 2️⃣ Kütüphaneleri Yükle
```bash
# Temel (Zorunlu) - 2 dakika
pip install PyQt6 opencv-python opencv-contrib-python numpy Pillow requests

# Tam Paket (Önerilen) - 5 dakika
pip install -r requirements.txt
```

### 3️⃣ Programı Başlat
```bash
# Windows
python antares_main_improved.py

# veya
start_antares.bat

# Linux/Mac
python3 antares_main_improved.py

# veya
./start_antares.sh
```

---

## 🎯 İlk Kullanım (3 Adım)

### ADIM 1: ESP32'ye Bağlan
1. ESP32-CAM WiFi: **ANTARES_KAPSUL_V8** (şifre: 12345678)
2. IP: **192.168.4.1** (varsayılan)
3. "Bağlantıyı Test Et" ✅

### ADIM 2: Görüntüleri İndir
1. Arduino'dan 360° tarama başlat
2. "Listeyi Yenile" tıkla
3. Taramayı seç → "İndir" ✅

### ADIM 3: 3D Model Oluştur
1. "3D MODEL OLUŞTUR" sekmesi
2. Ayarlar:
   - Kalite: **Orta** ⭐
   - AI Temizleme: **Açık** ✅
3. "🚀 3D MODEL OLUŞTUR" ✅

**Süre:** ~5-10 dakika (bilgisayara göre)

---

## 💡 Minimum Gereksinimler

✅ Python 3.8+  
✅ 4GB RAM  
✅ En az 8 görüntü  

---

## 🆘 Hızlı Sorun Giderme

**Problem:** Bağlantı yok  
**Çözüm:** WiFi kontrol, IP doğrula, ESP32 restart

**Problem:** rembg hatası  
**Çözüm:** `pip install rembg` veya AI'yı kapat

**Problem:** open3d hatası  
**Çözüm:** `pip install open3d` (ÖNERİLİR)

**Problem:** Yavaş  
**Çözüm:** Kalite=Düşük, Feature=1000

---

## 📖 Detaylı Bilgi

- **README.md** - Tam kılavuz
- **test_system.py** - Sistem testi
- **CHANGELOG.md** - Versiyon notları

---

## 🎨 Önerilen Harici Programlar

**MeshLab** → Mesh görüntüleme  
**CloudCompare** → Point cloud  
**Blender** → Professional editing  

---

## 📞 Destek

Sorun mu var?
1. `python test_system.py` çalıştır
2. README.md oku
3. Log dosyalarını kontrol et

---

**ANTARES KAPSÜL 3D STUDIO v2.0**  
© 2025 - Ready to use! 🚀
