# 🚀 ANTARES KAPSÜL 3D STUDIO - Kurulum ve Kullanım Kılavuzu

## 📋 İçindekiler
- [Sistem Gereksinimleri](#sistem-gereksinimleri)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Sorun Giderme](#sorun-giderme)
- [İpuçları](#ipuçları)

---

## 🖥️ Sistem Gereksinimleri

### Minimum:
- **Python:** 3.8 veya üzeri
- **RAM:** 4GB
- **İşlemci:** Dual-core
- **Disk:** 2GB boş alan

### Önerilen:
- **Python:** 3.10+
- **RAM:** 8GB veya üzeri
- **İşlemci:** Quad-core veya üzeri
- **GPU:** CUDA destekli (Open3D hızlandırma için)
- **Disk:** 5GB+ boş alan

---

## 🔧 Kurulum

### 1. Python Kurulumu
```bash
# Python 3.10 önerilir
# https://www.python.org/downloads/ adresinden indirin
```

### 2. Sanal Ortam Oluşturma (Önerilen)
```bash
# Windows
python -m venv antares_env
antares_env\Scripts\activate

# Linux/Mac
python3 -m venv antares_env
source antares_env/bin/activate
```

### 3. Gerekli Kütüphaneleri Yükleme

#### Temel Kurulum (Zorunlu):
```bash
pip install PyQt6 opencv-python opencv-contrib-python numpy Pillow requests
```

#### Tam Kurulum (Önerilen):
```bash
pip install -r requirements.txt
```

#### Manuel Kurulum:
```bash
# GUI
pip install PyQt6

# Görüntü işleme
pip install opencv-python opencv-contrib-python numpy Pillow

# 3D işleme (ÖNERİLİR)
pip install open3d

# AI arkaplan temizleme (OPSİYONEL)
pip install rembg

# Network
pip install requests
```

### 4. Kurulum Doğrulama
```bash
python antares_main_improved.py
```

---

## 🎯 Kullanım

### Adım 1: ESP32-CAM Bağlantısı
1. ESP32-CAM'i çalıştırın
2. WiFi ağına bağlanın: **ANTARES_KAPSUL_V8** (Şifre: 12345678)
3. Python programını açın
4. IP adresini girin: **192.168.4.1**
5. "Bağlantıyı Test Et" butonuna tıklayın

### Adım 2: 360° Tarama
1. Arduino üzerinden "Oto Çekim" menüsünden 360° tarama başlatın
2. Python programında "Listeyi Yenile" butonuna tıklayın
3. Listeden taramayı seçin
4. "Seçili Taramayı İndir" butonuna tıklayın

### Adım 3: 3D Model Oluşturma
1. **3D MODEL OLUŞTUR** sekmesine geçin
2. Ayarları yapın:
   - **Kalite:** Orta (önerilir)
   - **AI Temizleme:** Açık (bitki izolasyonu için)
   - **Feature Sayısı:** 2000 (varsayılan)
3. "🚀 3D MODEL OLUŞTUR" butonuna tıklayın
4. İşlemin tamamlanmasını bekleyin (5-15 dakika)

### Adım 4: Görüntüleme
1. **3D GÖRÜNTÜLEYİCİ** sekmesine geçin
2. "👁️ 3D Modeli Aç" ile varsayılan programda açın
3. Veya "📂 Çıktı Klasörünü Aç" ile manuel olarak açın

---

## 🛠️ Sorun Giderme

### Problem: ESP32'ye bağlanılamıyor
**Çözüm:**
- WiFi bağlantısını kontrol edin
- IP adresinin doğru olduğundan emin olun
- ESP32'yi yeniden başlatın
- Firewall ayarlarını kontrol edin

### Problem: "rembg bulunamadı" hatası
**Çözüm:**
```bash
pip install rembg
```
Veya AI temizleme seçeneğini kapatın (GrabCut fallback kullanılır)

### Problem: "Open3D bulunamadı" hatası
**Çözüm:**
```bash
pip install open3d
```
Open3D olmadan mesh oluşturulamaz, sadece point cloud oluşturulur.

### Problem: Feature detection başarısız
**Çözümler:**
- Görüntü kalitesini artırın
- Daha iyi aydınlatma kullanın
- Minimum feature sayısını azaltın (1000'e kadar)
- Nesneyi daha belirgin hale getirin

### Problem: Yavaş çalışma
**Çözümler:**
- Kaliteyi "Düşük" seçin
- Feature sayısını azaltın (1000-1500)
- AI temizlemeyi kapatın
- Daha az görüntü kullanın (8-12 görüntü yeterli)
- RAM'i artırın

### Problem: 3D model bozuk
**Çözümler:**
- Daha fazla görüntü kullanın (12-24)
- Görüntüleri daha dikkatli çekin
- Sabit aydınlatma kullanın
- Nesneyi merkeze yerleştirin
- Minimum 8 görüntü kullanın

---

## 💡 İpuçları ve Püf Noktaları

### En İyi Sonuçlar İçin:

#### Fotoğraf Çekimi:
✅ 360° döner tabla kullanın (Arduino motor sistemi)
✅ Sabit ve yeterli aydınlatma
✅ Düz, kontrast arkaplan (beyaz/siyah)
✅ Nesneyi merkeze yerleştirin
✅ En az 12-24 görüntü (45° veya 30° aralıklar)
✅ Nesne sabit kalmalı

❌ Titreşimli çekim
❌ Değişken aydınlatma
❌ Parlak yansımalar
❌ Çok az görüntü (<8)

#### Ayarlar:
- **İlk denemeler:** Kalite=Düşük, AI=Kapalı, Feature=1000
- **Normal kullanım:** Kalite=Orta, AI=Açık, Feature=2000
- **En iyi kalite:** Kalite=Yüksek, AI=Açık, Feature=5000 (yavaş)

#### Hardware:
- **Open3D:** Mesh generation için zorunlu
- **rembg:** Bitki izolasyonu için şiddetle önerilir
- **CUDA GPU:** Büyük hızlanma sağlar

---

## 📊 Teknik Detaylar

### Desteklenen Formatlar

**Point Cloud:**
- PLY (ASCII/Binary)

**Mesh:**
- PLY (ASCII/Binary)
- OBJ (Wavefront)
- STL (3D printing)

### Photogrammetry Pipeline

1. **Image Loading:** Görüntü doğrulama ve yükleme
2. **Feature Detection:** SIFT/ORB ile keypoint bulma
3. **Feature Matching:** FLANN/BFMatcher ile eşleştirme
4. **Pose Estimation:** Essential matrix ve camera poses
5. **Triangulation:** 3D point generation
6. **Dense Reconstruction:** Point cloud oluşturma
7. **Mesh Generation:** Poisson surface reconstruction
8. **Export:** Multi-format export

### Kalite Ayarları

| Kalite | Features | Matches | RANSAC | Süre |
|--------|----------|---------|--------|------|
| Düşük  | 1000     | 50      | 3.0    | Hızlı |
| Orta   | 2000     | 100     | 2.0    | Normal |
| Yüksek | 5000     | 200     | 1.0    | Yavaş |

---

## 🎨 Harici Program Önerileri

### MeshLab (Ücretsiz)
- **Kullanım:** Mesh görselleştirme ve düzenleme
- **İndirme:** https://www.meshlab.net/
- **Özellikler:** Mesh temizleme, decimation, smoothing

### CloudCompare (Ücretsiz)
- **Kullanım:** Point cloud işleme
- **İndirme:** https://www.cloudcompare.org/
- **Özellikler:** Point cloud alignment, filtering, meshing

### Blender (Ücretsiz)
- **Kullanım:** 3D modelleme, rendering, animasyon
- **İndirme:** https://www.blender.org/
- **Özellikler:** Professional 3D suite

---

## 📞 Destek ve İletişim

### Sık Sorulan Sorular
1. **Minimum kaç görüntü gerekir?** → 8 (12-24 önerilir)
2. **En iyi kalite ayarı nedir?** → Orta (hız/kalite dengesi)
3. **Open3D şart mı?** → Hayır, ama şiddetle önerilir
4. **rembg olmadan çalışır mı?** → Evet, GrabCut fallback kullanır
5. **GPU gerekli mi?** → Hayır, ama hızlandırır

### Hata Raporlama
Lütfen şunları ekleyin:
- Python versiyonu
- Hata mesajı (full traceback)
- Kullanılan ayarlar
- Görüntü sayısı ve kalitesi

---

## 📝 Versiyon Notları

### v2.0 (2025) - Major Update
✨ **Yenilikler:**
- Gelişmiş photogrammetry engine
- Open3D entegrasyonu
- İyileştirilmiş feature matching
- Poisson mesh reconstruction
- Multi-format export (PLY, OBJ, STL)
- Detaylı logging ve progress tracking
- Hata yönetimi iyileştirmeleri

🔧 **İyileştirmeler:**
- Daha hızlı işleme
- Daha iyi mesh kalitesi
- Robust feature detection
- Gelişmiş UI/UX

🐛 **Düzeltmeler:**
- Memory leak düzeltmeleri
- Thread safety iyileştirmeleri
- Edge case handling

### v1.0 (2024)
- İlk sürüm
- Temel photogrammetry
- ESP32 entegrasyonu
- Basic UI

---

## 🚀 Gelecek Güncellemeler

**Planlanıyor:**
- [ ] COLMAP entegrasyonu (daha iyi SfM)
- [ ] GPU hızlandırma (CUDA)
- [ ] Real-time preview
- [ ] Batch processing
- [ ] Advanced mesh editing
- [ ] Texture mapping
- [ ] Multi-view stereo
- [ ] Auto-calibration
- [ ] Cloud processing

---

## 📄 Lisans

Bu proje ANTARES Kapsül projesi kapsamında geliştirilmiştir.

---

## 🙏 Teşekkürler

**Kullanılan Kütüphaneler:**
- OpenCV - Computer Vision
- Open3D - 3D Data Processing
- PyQt6 - GUI Framework
- rembg - Background Removal
- NumPy - Scientific Computing

---

**ANTARES KAPSÜL 3D STUDIO v2.0**  
*Improved Photogrammetry Engine*  
© 2025
