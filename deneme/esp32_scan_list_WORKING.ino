// =============================================================================
// ESP32.INO İÇİN DÜZELTİLMİŞ scan_list_handler FONKSIYONU
// =============================================================================
// Bu fonksiyonu mevcut esp32.ino dosyanızda SATIR 750 civarındaki 
// scan_list_handler fonksiyonunun YERİNE kopyalayın
// =============================================================================

static esp_err_t scan_list_handler(httpd_req_t *req) {
  Serial.println("📋 Tarama listesi istendi");
  
  // JSON başlat
  String json = "{";
  bool first = true;
  
  // SD kartı kontrol et
  if (!SD_MMC.begin()) {
    Serial.println("❌ SD kart erişim hatası");
    httpd_resp_sendstr(req, "{}");
    return ESP_OK;
  }
  
  // Kök dizini aç
  File root = SD_MMC.open("/");
  if (!root || !root.isDirectory()) {
    Serial.println("❌ Kök dizin açılamadı");
    httpd_resp_sendstr(req, "{}");
    return ESP_OK;
  }
  
  // Bulunan sessionları sakla (aynı session'ı tekrar eklememek için)
  String foundSessions[20];  // Maksimum 20 session
  int foundCount = 0;
  
  // Tüm dosyaları tara
  File file = root.openNextFile();
  while (file && foundCount < 20) {
    String filename = String(file.name());
    
    // Slash ile başlıyorsa kaldır
    if (filename.startsWith("/")) {
      filename = filename.substring(1);
    }
    
    Serial.println("  Dosya: " + filename);
    
    // 360_ ile başlayan dosyaları bul
    if (filename.startsWith("360_")) {
      // Format: 360_SESSIONID_COUNT.jpg
      // Örnek: 360_1738774123_0.jpg
      
      int firstUnderscore = filename.indexOf('_');
      int secondUnderscore = filename.indexOf('_', firstUnderscore + 1);
      
      if (firstUnderscore >= 0 && secondUnderscore > firstUnderscore) {
        String sessionID = filename.substring(firstUnderscore + 1, secondUnderscore);
        
        Serial.println("    → Session ID bulundu: " + sessionID);
        
        // Bu session daha önce eklendi mi kontrol et
        bool alreadyAdded = false;
        for (int i = 0; i < foundCount; i++) {
          if (foundSessions[i] == sessionID) {
            alreadyAdded = true;
            break;
          }
        }
        
        if (!alreadyAdded) {
          // Yeni session, listeye ekle
          foundSessions[foundCount++] = sessionID;
          
          // Bu session'a ait dosya sayısını hesapla
          int photoCount = 0;
          
          // Dizini baştan tara
          File root2 = SD_MMC.open("/");
          File file2 = root2.openNextFile();
          
          while (file2) {
            String fname2 = String(file2.name());
            if (fname2.startsWith("/")) fname2 = fname2.substring(1);
            
            // Bu session'a ait mi?
            if (fname2.startsWith("360_" + sessionID + "_")) {
              photoCount++;
            }
            
            file2 = root2.openNextFile();
          }
          root2.close();
          
          Serial.println("    → Fotoğraf sayısı: " + String(photoCount));
          
          // JSON'a ekle
          if (!first) {
            json += ",";
          }
          json += "\"" + sessionID + "\":" + String(photoCount);
          first = false;
        }
      }
    }
    
    file = root.openNextFile();
  }
  
  root.close();
  json += "}";
  
  Serial.println("📤 Gönderilen JSON: " + json);
  
  // HTTP yanıtını gönder
  httpd_resp_set_type(req, "application/json");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  httpd_resp_sendstr(req, json.c_str());
  
  return ESP_OK;
}

// =============================================================================
// KURULUM TALİMATLARI:
// =============================================================================
// 1. Arduino IDE'de esp32.ino dosyasını açın
// 2. CTRL+F → "scan_list_handler" ara
// 3. Mevcut fonksiyonun TAMAMINI sil (static esp_err_t'den } 'ye kadar)
// 4. Yukarıdaki kodu yapıştır
// 5. Upload → ESP32'ye yükle
// 6. ESP32'yi restart et
// 7. Python programında "Listeyi Yenile" butonuna bas
// =============================================================================
