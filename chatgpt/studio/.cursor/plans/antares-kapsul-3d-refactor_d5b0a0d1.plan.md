---
name: Antares-Kapsul-3D-Refactor
overview: Antares Kapsül 3D Studio projesini üretim seviyesinde, modüler, performanslı ve test edilebilir bir yapıya taşımak; UI/UX, photogrammetry pipeline ve donanım entegrasyonunu kurumsal standartlara yaklaştırmak.
todos:
  - id: ui-theme-refactor
    content: Dark Industrial tema için merkezi stylesheet tasarlayıp `antares_main_improved.py` ve widget’lara uygulamak
    status: completed
  - id: background-task-system
    content: QThreadPool/QRunnable tabanlı `TaskManager` ile ağır işlemleri UI’dan ayırmak
    status: in_progress
  - id: mode-based-processing
    content: Fast Mode (ORB+BFMatcher+GrabCut) ve High Quality Mode (SIFT+FLANN+rembg) pipeline’larını `image_processor.py` içinde soyutlamak
    status: pending
  - id: modular-architecture
    content: HardwareConnector, ImageProcessor, ModelGenerator ve ErrorHandler modüllerini oluşturup ana dosyayı sadeleştirmek
    status: pending
  - id: memory-and-errors
    content: Bellek yönetimi ve spesifik hata yönetimi iyileştirmelerini uygulamak
    status: pending
  - id: tests-and-mocks
    content: "`test_system.py` için hardware mock modu, uçtan uca 3D pipeline testi ve export doğrulama script’i eklemek"
    status: pending
  - id: requirements-cleanup
    content: "`requirements.txt` dosyasını yeni modlara göre sadeleştirip uyumlu sürümlerle güncellemek"
    status: pending
  - id: perf-docs
    content: Performans gözlemlerini ve yeni mimariyi kısaca dokümante etmek
    status: pending
  - id: todo-1770376693599-u6wlsyf5p
    content: ""
    status: pending
isProject: false
---

## Genel Yaklaşım

- **Hedef**: `antares_main_improved.py` dosyasını sadeleştirip modüler bir mimariye taşımak, modern bir PyQt6 arayüzü ve optimize edilmiş bir 3D rekonstrüksiyon pipeline’ı ile birlikte kararlı, test edilebilir bir sistem oluşturmak.
- **Kısıtlar ve Tercihler**:
  - Yeni modüller/paketler oluşturmak ve ana dosyayı bunlara bölmek serbest.
  - Open3D için öncelik: kararlı, odak yönetimi düzgün harici pencere; embed denemesi yapılırsa opsiyonel.
  - Hedef platformlar: Windows 10/11 ve Linux, modern Python (3.9+ varsayılacak).

## 1. UI/UX Refaktörü (PyQt6)

- **1.1. Tasarım Envanterini Çıkarma**
  - `antares_main_improved.py` içindeki mevcut stylesheet tanımlarını ve kullanılan ana widget hiyerarşisini incele (ana `QMainWindow`, tab’ler, düğmeler, listeler, progress bar’lar).
  - `widgets/` altındaki özel widget’ların (özellikle `viewer_3d.py`, `project_browser.py`, `wizard_widget.py`) stil ihtiyaçlarını not et.
- **1.2. “Dark Industrial” Tema Tasarımı**
  - Yeni bir merkezi stil dosyası oluştur: örneğin `[ui/styles.py]` veya `resources/styles/dark_industrial.qss`.
    - Temel renk paleti: koyu gri arkaplanlar, vurgu için turkuaz/amber, düşük doygunluklu ikon ve border renkleri.
    - Ortak widget stilleri: `QPushButton`, `QToolButton`, `QTabBar`, `QTreeView`, `QTableView`, `QLineEdit`, `QComboBox`, `QProgressBar`, `QScrollBar` için 
      - **Yuvarlatılmış köşeler**, 
      - **İyileştirilmiş padding/margin**, 
      - Hover/pressed durumları,
      - Focus highlight.
  - `antares_main_improved.py` üzerinde uygulanan eski stylesheet bloklarını kaldırıp, merkezi stil dosyasını uygulayan bir fonksiyon ekle: örn. `apply_dark_industrial_theme(app)`.
- **1.3. İkonografi ve Kullanılabilirlik İyileştirmeleri**
  - Mevcut buton ve menüler için bir ikon haritası tanımla (örneğin `[ui/icons.py]`); `QAction` ve `QToolButton`’lara tutarlı ikon seti uygula.
  - Kritik aksiyonlar (yeni tarama, rekonstrüksiyon başlat, dışa aktar, donanım testi) için daha belirgin ikon ve kısa açıklayıcı tooltip’ler ekle.
- **1.4. Non-Blocking UI ve 60fps Hissi**
  - Mevcut QThread kullanımlarını envanterle: 
    - `antares_main_improved.py` ve `core/safe_operation.py` içindeki uzun süren işlemleri (görüntü indirme, feature extraction, eşleştirme, 3D rekonstrüksiyon, rembg çağrıları).
  - Yeni bir **iş yükü yürütme katmanı** tasarla: örn. `core/task_executor.py`:
    - `QThreadPool` + `QRunnable` tabanlı generic `BackgroundTask` sınıfı.
    - İş tamamlama, hata ve progress sinyallerini PyQt sinyalleri üzerinden UI’ya bağlayan bir `TaskManager`.
  - Ana UI tarafında:
    - Ağır fonksiyon çağrılarını doğrudan çalıştırmak yerine `TaskManager.run_in_background(...)` kullan.
    - UI thread içinde sadece sinyal işleme, progress güncelleme ve sonucun görselleştirilmesini bırak.
  - Event-loop’u kilitleyen beklemeleri (`time.sleep`, bloklayıcı I/O) tespit edip QRunnable içine taşı.
- **1.5. Open3D Görselleştirme Entegrasyonu**
  - Öncelik: **kararlı harici pencere** yönetimi.
    - Mevcut Open3D kullanımını `viewer_3d.py` veya ayrı bir servis modülüne (ör. `visualization/open3d_viewer.py`) soyutla.
    - Bir `Open3DViewerService` sınıfı tanımla:
      - Mesh/point cloud yükleme ve gösterme fonksiyonları.
      - `show_in_external_window(mesh)` gibi metotlarla PyQt sinyallerinden tetikleme.
      - Pencere odak/ön plana getirme için uygun Open3D + OS seviyesinde (mümkün olduğu kadar) çağrılar.
  - İkinci aşama (opsiyonel, zaman ve uygunluk durumuna göre): PyQt içine gömülebilir Open3D widget denemesi (ör. `QWidget` içerisine Open3D’s `VisualizerWithKeyCallback` veya `Open3D WebVisualizer` embed yaklaşımı) ve mevcut mimariyi bozmadan prototipleme.

## 2. Bağımlılık ve Kütüphane Optimizasyonu

- **2.1. Mevcut `requirements.txt` Analizi**
  - `[requirements.txt]` içindeki tüm paketleri sınıflandır:
    - UI (PyQt6, pyvista vs.)
    - Görüntü İşleme (opencv-python, numpy, Pillow)
    - 3D (open3d, pyvista, trimesh vs.)
    - Arka plan temizleme (rembg, onnxruntime vs.)
    - Yardımcılar (requests, tqdm vs.).
  - Kullanılmayan veya proje kodunda referansı olmayan bağımlılıkları `grep/semantic search` ile tespit et.
- **2.2. Windows + Linux Uyumluluğu İçin Versiyon Stratejisi**
  - OpenCV, Open3D, rembg, PyQt6 için **geniş uyumlu, ama nispeten güncel** sürüm aralıkları belirle (örn. `opencv-python>=4.8,<5`, `open3d>=0.18,<0.20`, `PyQt6>=6.5,<7`).
  - GPU bağımlı paketler veya platforma çok bağlı kütüphaneler varsa (ör. belirli rembg engine’leri), bunları opsiyonel hale getirmek veya yoruma almak için not düş.
- **2.3. Fast Mode ve High Quality Mode İçin Bağımlılık Gereksinimleri**
  - **Fast Mode**:
    - ORB, BFMatcher, GrabCut: `opencv-python` + `numpy` yeterli.
  - **High Quality Mode**:
    - SIFT, FLANN: yine OpenCV içinde (non-free modüller için kullanılabilirliğe dikkat).
    - `rembg` + uygun backend (örn. `onnxruntime`); CPU tabanlı kullanım varsayılarak listeye ekle.
  - Tüm bu modlara göre minimal ama yeterli bir `requirements.txt` hazırlayıp, yorum satırlarıyla hangi modun neyi kullandığını kısaca belirt.

## 3. Kod Refaktörü ve Mantık İyileştirmeleri

- **3.1. Mimari Ayırma ve Yeni Modüller**
  - Yeni modüller/paketler oluştur:
    - `[hardware/hardware_connector.py]`: ESP32-CAM ve dönme platformu/Arduino ile haberleşme (HTTP, seri vs.)
    - `[processing/image_processor.py]`: 
      - Feature extraction (ORB/SIFT), eşleştirme (BFMatcher/FLANN), arka plan temizleme (GrabCut/rembg), ön-işleme.
      - Fast/High Quality mod seçim mantığı.
    - `[processing/model_generator.py]`: 
      - Structure-from-Motion veya mevcut pipeline’a göre 3D point cloud/mesh üretimi (Open3D entegrasyonu).
    - `[core/error_handler.py]`: 
      - Ortak exception sınıfları (örn. `CameraTimeoutError`, `Esp32ConnectionError`, `ReconstructionError` vs.).
      - Kullanıcıya gösterilecek mesajların şablonları.
    - `[core/settings.py]`: `config.ini` ile entegre merkezi ayar yönetimi.
  - `antares_main_improved.py` içinde GUI katmanını bu modüllerin yüksek seviye API’lerini çağıracak hale getir (iş mantığı UI’dan ayrılmış olacak).
- **3.2. Fast Mode vs High Quality Mode Akışları**
  - `image_processor.py` içinde bir strateji pattern’i benzeri yapı kur:
    - `BaseReconstructionMode`, `FastModeProcessor`, `HighQualityModeProcessor` sınıfları.
    - Parametre: kalite modu seçimi (`fast` / `high_quality`) UI’dan gelir ve uygun sınıf enjekte edilir.
  - **Fast Mode** pipeline’ı:
    - ORB ile feature extraction.
    - BFMatcher ile hızlı eşleştirme.
    - GrabCut ile hızlı/heuristik arka plan temizleme.
  - **High Quality Mode** pipeline’ı:
    - SIFT ile daha güçlü feature extraction.
    - FLANN tabanlı eşleştirme + outlier rejection.
    - `rembg` ile AI tabanlı foreground extraction.
- **3.3. Bellek Yönetimi İyileştirmeleri**
  - Büyük `numpy` dizileri ve OpenCV/Open3D objelerinin yaşam süresini belirgin hale getir:
    - Uzun süreli objeleri (örneğin final point cloud/mesh) ile geçici ara çıktıları ayır.
  - Her aşamanın sonunda geçici objeleri temizleyen yardımcı fonksiyonlar ekle:
    - Örneğin `processing/memory_utils.py` içinde `safe_clear_array(arr)`, `release_cv_image(img)` gibi fonksiyonlar.
    - Kritik yerlerde `del obj` ve `gc.collect()` çağrılarını (özellikle büyük dataset’ler sonrası) kontrollü ve sınırlı şekilde kullan.
- **3.4. Hata Yönetimi ve Kullanıcı Uyarıları**
  - Geniş `try-except` bloklarını gözden geçir ve mümkün olduğunca spesifik exception’lara parçala:
    - Ağ/haberleşme: `requests.Timeout`, `requests.ConnectionError`.
    - Dosya sistemi: `FileNotFoundError`, `PermissionError`.
    - OpenCV/Open3D: ilgili kütüphane hataları.
  - `core/error_handler.py` içinde hata -> kullanıcı mesajı haritalaması tanımla:
    - Örn. `CameraTimeoutError` → "Kamera zaman aşımına uğradı. ESP32 güç bağlantısını ve Wi-Fi erişimini kontrol edin." gibi lokalize/metin tabanlı mesajlar.
  - UI katmanında tüm kritik işlemler bu hata katmanını kullanarak `QMessageBox` veya custom notification sistemi üzerinden anlamlı uyarılar gösterir.

## 4. Otomatik Testler (Birim ve Entegrasyon)

- **4.1. Hardware Mock Modu Tasarımı**
  - `[tests/test_system.py]` içinde veya ayrı bir modülde `[tests/mocks/hardware_mock.py]` oluştur:
    - ESP32-CAM için simüle edilmiş HTTP endpoint’ler veya dosya tabanlı görüntü sağlayıcı.
    - Döner platform için step/position simülasyonu (gerçekte seri port yok, sadece çağrıların kayıt edilmesi yeterli).
  - `hardware_connector.py` tasarımını **bağımlılık enjeksiyonu**na uygun hale getir:
    - Gerçek implementasyon ve mock implementasyon aynı arayüzü uygulasın (örn. `BaseHardwareInterface`).
  - `test_system.py` içine bir "hardware mock mode" flag’i ekle (örn. komut satırı argümanı veya ortam değişkeni):
    - Mock modda gerçek donanım yerine mock sınıflar enjekte edilir.
- **4.2. Uçtan Uca 3D Pipeline Testi**
  - Test verisi olarak küçük bir örnek görüntü seti ekle (veya mevcut dataset’ten küçük bir alt küme kullan):
    - Fast mode ve high quality mode için iki ayrı test senaryosu yaz:
      - Görüntülerin başarıyla okunması.
      - En azından küçük bir point cloud/mesh üretilmesi (tam fotogrametrik doğruluk gerekmiyor).
    - Test sonunda:
      - Üretilen `.ply` veya `.obj` dosyasının varlığını ve temel bütünlüğünü doğrula (bkz. 4.3).
- **4.3. Çıktı Dosyası Bütünlük Doğrulama Script’i**
  - Yeni bir script ekle: örn. `[tools/validate_export.py]`:
    - Girdi: `.obj` veya `.ply` dosya yolu.
    - Open3D veya basit parser ile dosyayı yükle.
    - Doğrulamalar:
      - Dosya açılabiliyor mu?
      - Vertex sayısı > 0 mı?
      - (Varsa) face sayısı makul aralıkta mı?
    - Başarılı/başarısız durum için komut satırına anlamlı mesajlar yazdır.
  - `test_system.py` içinde bu script’i/ fonksiyonunu çağıran ek bir test ekle.

## 5. Performans İyileştirmeleri ve Dokümantasyon

- **5.1. Basit Benchmark’lar**
  - Tipik bir görüntü seti için aşağıdakilerin yaklaşık süre ve bellek tüketimini ölç (kabaca, manuel loglama yeterli):
    - Eski pipeline vs yeni pipeline (Fast Mode ve High Quality Mode ayrı ayrı).
  - Özellikle şu aşamaları logla:
    - Görüntü indirme/senkronizasyon.
    - Feature extraction + matching.
    - 3D rekonstrüksiyon (point cloud/mesh).
- **5.2. Performans Notlarının Toplanması**
  - Önemli gözlemleri not et:
    - Fast Mode’da beklenen hız kazanımları (ör. x% daha hızlı, daha az bellek).
    - High Quality Mode’da kalite artışı (daha yoğun/temiz point cloud, daha az gürültü), ama daha uzun süre.
- **5.3. Kısa Dokümantasyon**
  - Özet bir doküman hazırla: örn. `[docs/performance_and_architecture.md]`:
    - Yeni mimari özet (modüller arası ilişkiler, data flow).
    - Fast Mode vs High Quality Mode karşılaştırması.
    - Bellek ve performans iyileştirmelerine dair kısa bulgular.

## 6. Entegrasyon ve Geriye Dönük Uyum

- **6.1. Giriş Noktası Düzenleme**
  - `antares_main_improved.py` dosyasını, yeni modüler yapıyı kullanan hafif bir **UI bootstrap** dosyası haline getir:
    - Uygulama başlatma (`QApplication`), tema uygulama, ana pencere oluşturma ve yeni modüllerin wiring işlemi.
- **6.2. Eski Yol ve Ayarlar**
  - Eski proje klasör yapıları (`antares_3d_data/`, `ANTARES_Projects` vs.) ile yeni yapı arasında uyum katmanı ekle veya en azından backward compatible okuma desteği bırak.
- **6.3. Hata Durumunda Geri Dönüş**
  - Kritik yerlerde (özellikle donanım bağlantısı ve Open3D görselleştirme) için loglama ekle; böylece sorun olduğunda eski davranışı anlamak ve debug etmek daha kolay olur.

