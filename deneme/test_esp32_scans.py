#!/usr/bin/env python3
"""
ESP32 360° Tarama Listesi Test Aracı
Bu script ESP32'nizdeki taramaları kontrol eder
"""

import requests
import json
import sys

def test_esp32_connection(ip="192.168.4.1"):
    """ESP32 bağlantısını test et"""
    print("=" * 60)
    print("🔌 ESP32 BAĞLANTI TESTİ")
    print("=" * 60)
    
    # 1. Ana sayfa testi
    print(f"\n1️⃣ Ana sayfa testi: http://{ip}/")
    try:
        response = requests.get(f"http://{ip}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ ESP32'ye bağlantı başarılı!")
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Bağlantı hatası: {e}")
        return False
    
    # 2. Tarama listesi testi
    print(f"\n2️⃣ Tarama listesi testi: http://{ip}/360_list")
    try:
        response = requests.get(f"http://{ip}/360_list", timeout=10)
        
        print(f"   HTTP Durum Kodu: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            print(f"   Ham Yanıt: {response.text}")
            
            try:
                data = response.json()
                print(f"\n   ✅ JSON Parse Başarılı!")
                print(f"   📊 Bulunan Tarama Sayısı: {len(data)}")
                
                if len(data) == 0:
                    print("\n   ⚠️ HİÇ TARAMA BULUNAMADI!")
                    print("\n   Olası Sebepler:")
                    print("   • Arduino'dan henüz tarama yapılmamış")
                    print("   • ESP32 SD kartı okuyamıyor")
                    print("   • scan_list_handler fonksiyonu güncel değil")
                    print("\n   Çözüm:")
                    print("   1. Arduino → Oto Çekim → Başlat")
                    print("   2. Arduino Seri Monitör → 'DURUM' komutu")
                    print("   3. ESP32'yi restart et")
                else:
                    print("\n   📸 Bulunan Taramalar:")
                    for session_id, count in data.items():
                        from datetime import datetime
                        ts = int(session_id) / 1000
                        date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                        print(f"      • {date_str} | {count} fotoğraf | Session: {session_id}")
                        
                        # Örnek URL
                        print(f"        → İlk fotoğraf: http://{ip}/360_{session_id}_0.jpg")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON Parse Hatası: {e}")
                print(f"   Ham Yanıt: {response.text}")
                return False
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ İstek hatası: {e}")
        return False
    
    return True

def test_photo_download(ip, session_id, photo_index=0):
    """Tek bir fotoğrafı indirmeyi test et"""
    print(f"\n3️⃣ Fotoğraf indirme testi")
    url = f"http://{ip}/360_{session_id}_{photo_index}.jpg"
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Fotoğraf indirildi! ({len(response.content)} bytes)")
            
            # Kaydet
            filename = f"test_download_{session_id}_{photo_index}.jpg"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"   💾 Kaydedildi: {filename}")
            return True
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Hata: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("🚀 ANTARES ESP32 TARAMA LİSTESİ TEST ARACI")
    print("=" * 60)
    
    # IP adresini al
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = input("\nESP32 IP Adresi (Enter = 192.168.4.1): ").strip()
        if not ip:
            ip = "192.168.4.1"
    
    print(f"\n📍 Test edilen IP: {ip}")
    
    # Bağlantı testi
    success = test_esp32_connection(ip)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ TÜM TESTLER BAŞARILI!")
        print("=" * 60)
        print("\n💡 Python programında 'Listeyi Yenile' butonu çalışmalı!")
    else:
        print("\n" + "=" * 60)
        print("❌ TEST BAŞARISIZ")
        print("=" * 60)
        print("\n🔧 Kontrol Listesi:")
        print("   1. ESP32 WiFi'ye bağlı mısınız?")
        print("      → WiFi: ANTARES_KAPSUL_V8")
        print("      → Şifre: 12345678")
        print("\n   2. Arduino'dan tarama yaptınız mı?")
        print("      → Arduino → Oto Çekim → Başlat")
        print("\n   3. ESP32 SD kartı okuyor mu?")
        print("      → Arduino Seri Monitör → 'DURUM' komutu")
        print("\n   4. scan_list_handler güncel mi?")
        print("      → esp32_scan_list_WORKING.ino dosyasını kullanın")
        print("\n   5. ESP32'yi restart ettiniz mi?")
        print("      → ESP32'yi kapat/aç")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
