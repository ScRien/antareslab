# 📁 ANTARES KAPSÜL 3D STUDIO - Dosya Yapısı

## 📦 İndirdiğiniz Paket İçeriği

```
antares_3d_studio/
│
├── 🚀 antares_main_improved.py     # ANA PROGRAM (Bu dosyayı çalıştırın!)
│
├── 📋 requirements.txt              # Gerekli Python kütüphaneleri
│
├── 📖 README.md                     # Detaylı kullanım kılavuzu (İLK ÖNCELİK!)
├── ⚡ QUICKSTART.md                 # 5 dakikada başlangıç
├── 📝 CHANGELOG.md                  # Versiyon notları
│
├── 🧪 test_system.py                # Sistem test scripti
├── ⚙️ config.ini                    # Konfigürasyon ayarları
│
├── 🪟 start_antares.bat             # Windows başlatıcı
├── 🐧 start_antares.sh              # Linux/Mac başlatıcı
│
└── 📂 original_files/               # Orijinal kaynak dosyalarınız
    ├── main.py                      # Eski Python dosyası
    ├── arduino.ino                  # Arduino kodu
    └── esp32.ino                    # ESP32 kodu
```

---

## 🎯 Nereden Başlamalıyım?

### 1. İLK ADIM: Sistem Testini Çalıştır
```bash
python test_system.py
```
Bu komut kurulumunuzun eksiklerini gösterir.

### 2. İKİNCİ ADIM: Gerekli Kütüphaneleri Yükle
```bash
pip install -r requirements.txt
```

### 3. ÜÇÜNCÜ ADIM: Programı Başlat
```bash
# Windows
python antares_main_improved.py
# veya çift tıkla: start_antares.bat

# Linux/Mac
python3 antares_main_improved.py
# veya terminal'de: ./start_antares.sh
```

---

## 📚 Hangi Dosyayı Okumalıyım?

### 🆕 Yeni kullanıcıysanız:
1. **QUICKSTART.md** → 5 dakikada başla
2. **README.md** → Detaylı bilgi
3. **test_system.py** → Kurulum kontrolü

### 🔧 Sorun yaşıyorsanız:
1. **README.md** → "Sorun Giderme" bölümü
2. **test_system.py** → Hangi paket eksik?
3. **config.ini** → Gelişmiş ayarlar

### 💻 Geliştiriciyseniz:
1. **CHANGELOG.md** → Neler değişti?
2. **antares_main_improved.py** → Kaynak kodu
3. **config.ini** → Ayar seçenekleri

---

## 🔄 Eski Dosyalarım Ne Oldu?

Orijinal dosyalarınız **original_files/** klasöründe saklandı:
- `main.py` - Eski Python kodunuz
- `arduino.ino` - Arduino kodunuz  
- `esp32.ino` - ESP32 kodunuz

**Yeni versiyon (v2.0) şunları içeriyor:**
✅ Gelişmiş photogrammetry engine
✅ Open3D entegrasyonu
✅ Daha iyi hata yönetimi
✅ Poisson mesh reconstruction
✅ Multi-format export (PLY, OBJ, STL)
✅ AI background removal
✅ Detaylı logging

---

## ⚡ Hızlı Kurulum Özeti

### Windows Kullanıcıları:
```cmd
1. start_antares.bat dosyasına çift tıklayın
2. Eksik kütüphane varsa, terminalde şunu yazın:
   pip install -r requirements.txt
3. Tekrar start_antares.bat'a çift tıklayın
```

### Linux/Mac Kullanıcıları:
```bash
1. Terminal açın
2. chmod +x start_antares.sh
3. ./start_antares.sh
4. Eksik kütüphane varsa:
   pip3 install -r requirements.txt
5. ./start_antares.sh
```

---

## 🆘 Yardım

### Hata Alıyorum!
```bash
python test_system.py
```
Bu komut neyin eksik olduğunu gösterir.

### Python Bulunamadı!
https://www.python.org/downloads/ → Python 3.10+ indirin

### Kütüphane Yükleyemiyorum!
```bash
# Windows
python -m pip install --upgrade pip
pip install -r requirements.txt

# Linux/Mac
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
```

---

## 📞 Destek ve Dokümantasyon

**Tam Kılavuz:** README.md (7,000+ kelime)  
**Hızlı Başlangıç:** QUICKSTART.md  
**Sistem Testi:** `python test_system.py`  
**Versiyon Notları:** CHANGELOG.md  

---

## ✅ Başarılı Kurulum Kontrol Listesi

- [ ] Python 3.8+ kurulu
- [ ] test_system.py başarıyla çalıştı
- [ ] Tüm zorunlu kütüphaneler yüklü
- [ ] Program açıldı ve arayüz göründü
- [ ] ESP32'ye bağlanıldı
- [ ] Görüntüler indirildi
- [ ] 3D model oluşturuldu

**Hepsi tamamsa: Hazırsınız! 🎉**

---

## 🎨 Örnek İş Akışı

1. Arduino → 360° tarama başlat (8-24 fotoğraf)
2. Python → ESP32'ye bağlan
3. Python → Görüntüleri indir
4. Python → 3D model oluştur
5. MeshLab/Blender → Modeli aç ve düzenle

**Toplam Süre:** ~10-15 dakika

---

**ANTARES KAPSÜL 3D STUDIO v2.0**  
Improved Photogrammetry Engine  
© 2025

**İyi çalışmalar! 🚀**
