#!/usr/bin/env python3
"""
ANTARES KAPSÜL 3D STUDIO - Sistem Test ve Doğrulama
Bu script kurulumunuzun doğru çalıştığını test eder
"""

import sys
import importlib.util

def check_python_version():
    """Python versiyonunu kontrol et"""
    print("🔍 Python Versiyonu Kontrolü...")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Yetersiz!")
        print(f"   → Python 3.8 veya üzeri gerekli")
        return False

def check_package(package_name, is_required=True):
    """Paket kurulumunu kontrol et"""
    spec = importlib.util.find_spec(package_name)
    
    if spec is not None:
        try:
            module = importlib.import_module(package_name)
            version = getattr(module, '__version__', 'N/A')
            status = "✅ KURULU"
            print(f"   {status} {package_name} (v{version})")
            return True
        except Exception as e:
            print(f"   ⚠️ HATA {package_name}: {e}")
            return False
    else:
        if is_required:
            print(f"   ❌ EKSİK {package_name} - ZORUNLU")
        else:
            print(f"   ⚠️ EKSİK {package_name} - Opsiyonel (Kurulması önerilir)")
        return False

def check_opencv_features():
    """OpenCV özelliklerini kontrol et"""
    try:
        import cv2
        print("\n🔬 OpenCV Özellikleri:")
        
        # SIFT kontrolü
        try:
            detector = cv2.SIFT_create()
            print("   ✅ SIFT - Mevcut")
        except:
            print("   ⚠️ SIFT - Mevcut değil (ORB fallback kullanılacak)")
        
        # FLANN kontrolü
        try:
            from cv2 import FlannBasedMatcher
            print("   ✅ FLANN - Mevcut")
        except:
            print("   ⚠️ FLANN - Mevcut değil (BFMatcher fallback kullanılacak)")
        
        return True
    except:
        return False

def check_gpu():
    """GPU desteğini kontrol et"""
    print("\n🎮 GPU Kontrolü:")
    
    # Open3D CUDA kontrolü
    try:
        import open3d as o3d
        if hasattr(o3d.core, 'cuda'):
            print("   ✅ Open3D CUDA desteği - Mevcut")
        else:
            print("   ℹ️ Open3D CUDA desteği - Mevcut değil (CPU kullanılacak)")
    except:
        print("   ⚠️ Open3D kurulu değil")
    
    # PyTorch CUDA kontrolü (rembg için)
    try:
        import torch
        if torch.cuda.is_available():
            print(f"   ✅ PyTorch CUDA - Mevcut (GPU: {torch.cuda.get_device_name(0)})")
        else:
            print("   ℹ️ PyTorch CUDA - Mevcut değil (CPU kullanılacak)")
    except:
        print("   ℹ️ PyTorch kurulu değil")

def print_summary(required_ok, optional_ok):
    """Özet rapor"""
    print("\n" + "=" * 60)
    print("📊 KURULUM DURUMU ÖZET")
    print("=" * 60)
    
    if required_ok:
        print("✅ TEMEL KURULUM TAMAM - Program çalıştırılabilir")
    else:
        print("❌ TEMEL KURULUM EKSİK - Lütfen gerekli paketleri yükleyin")
        print("\n📥 Kurulum komutu:")
        print("   pip install PyQt6 opencv-python opencv-contrib-python numpy Pillow requests")
    
    if not optional_ok:
        print("\n⚠️ OPSİYONEL PAKETLER EKSİK")
        print("   Daha iyi sonuçlar için şunları yükleyin:")
        print("   pip install open3d rembg")
    
    print("\n" + "=" * 60)
    
    if required_ok:
        print("\n🚀 Programı başlatmak için:")
        print("   python antares_main_improved.py")
    
    print("\n📖 Detaylı bilgi için README.md dosyasını okuyun")
    print("=" * 60)

def main():
    """Ana test fonksiyonu"""
    print("=" * 60)
    print("🚀 ANTARES KAPSÜL 3D STUDIO - Sistem Testi")
    print("=" * 60)
    print()
    
    # Python versiyonu
    python_ok = check_python_version()
    print()
    
    # Zorunlu paketler
    print("📦 ZORUNLU Paketler Kontrolü:")
    required_packages = {
        'PyQt6': True,
        'cv2': True,  # opencv-python
        'numpy': True,
        'PIL': True,  # Pillow
        'requests': True
    }
    
    required_ok = python_ok
    for package, _ in required_packages.items():
        result = check_package(package, is_required=True)
        required_ok = required_ok and result
    
    print()
    
    # Opsiyonel paketler
    print("📦 OPSİYONEL Paketler Kontrolü:")
    optional_packages = {
        'open3d': '3D mesh generation için ÖNERİLİR',
        'rembg': 'AI arkaplan temizleme için ÖNERİLİR'
    }
    
    optional_ok = True
    for package, desc in optional_packages.items():
        result = check_package(package, is_required=False)
        optional_ok = optional_ok and result
    
    # OpenCV özellikleri
    if required_ok:
        check_opencv_features()
    
    # GPU kontrolü
    if optional_ok:
        check_gpu()
    
    # Özet
    print_summary(required_ok, optional_ok)
    
    return 0 if required_ok else 1

if __name__ == "__main__":
    sys.exit(main())
