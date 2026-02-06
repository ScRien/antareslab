#!/usr/bin/env python3
"""
ANTARES KAPSÜL - rembg GPU Sorun Giderme ve Düzeltme
Bu script rembg'nin GPU ile çalışmaması sorununu tespit edip çözer
"""

import sys
import subprocess
import importlib.util

def print_header(text):
    """Başlık yazdır"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def run_command(cmd, description):
    """Komut çalıştır ve sonucu göster"""
    print(f"\n🔧 {description}")
    print(f"   Komut: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Başarılı")
            if result.stdout.strip():
                print(f"   Çıktı: {result.stdout.strip()[:200]}")
            return True
        else:
            print("   ❌ Hata!")
            if result.stderr.strip():
                print(f"   Hata: {result.stderr.strip()[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Hata: {e}")
        return False

def check_cuda():
    """CUDA kurulumunu kontrol et"""
    print_header("1. CUDA KONTROLÜ")
    
    # nvidia-smi kontrolü
    print("\n📊 NVIDIA GPU Kontrolü:")
    has_nvidia = run_command("nvidia-smi", "nvidia-smi komutu")
    
    if not has_nvidia:
        print("\n⚠️  UYARI: NVIDIA sürücüsü bulunamadı!")
        print("   → NVIDIA GPU sürücülerini yükleyin")
        return False
    
    # CUDA version
    try:
        result = subprocess.run("nvcc --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ CUDA Toolkit kurulu")
            print(f"   {result.stdout.strip()}")
        else:
            print("   ⚠️  CUDA Toolkit bulunamadı (PyTorch kendi CUDA'sını kullanabilir)")
    except:
        print("   ℹ️  nvcc bulunamadı (PyTorch kendi CUDA'sını kullanabilir)")
    
    return has_nvidia

def check_pytorch():
    """PyTorch CUDA desteğini kontrol et"""
    print_header("2. PYTORCH CUDA KONTROLÜ")
    
    try:
        import torch
        print(f"\n✅ PyTorch versiyonu: {torch.__version__}")
        
        # CUDA availability
        cuda_available = torch.cuda.is_available()
        print(f"   CUDA Kullanılabilir: {'✅ EVET' if cuda_available else '❌ HAYIR'}")
        
        if cuda_available:
            print(f"   CUDA Versiyonu: {torch.version.cuda}")
            print(f"   GPU Sayısı: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
                print(f"         Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB")
        else:
            print("\n⚠️  PyTorch CUDA desteği YOK!")
            print("   → CPU versiyonu yüklü olabilir")
            print("   → PyTorch'u CUDA desteğiyle yeniden yükleyin")
        
        return cuda_available
    except ImportError:
        print("\n❌ PyTorch kurulu değil!")
        print("   → pip install torch torchvision torchaudio")
        return False
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        return False

def check_rembg():
    """rembg kurulumunu kontrol et"""
    print_header("3. REMBG KONTROLÜ")
    
    try:
        import rembg
        print(f"\n✅ rembg versiyonu: {rembg.__version__}")
        
        # GPU backend kontrolü
        try:
            from rembg.session_factory import new_session
            from rembg.bg import remove
            print("   ✅ rembg modülleri yüklendi")
            
            # Session oluşturmayı dene
            try:
                session = new_session()
                print("   ✅ Session oluşturuldu")
                
                # Device kontrolü
                if hasattr(session, 'device'):
                    print(f"   Device: {session.device}")
                
                return True
            except Exception as e:
                print(f"   ⚠️  Session oluşturulamadı: {e}")
                return False
                
        except Exception as e:
            print(f"   ⚠️  rembg import hatası: {e}")
            return False
            
    except ImportError:
        print("\n❌ rembg kurulu değil!")
        return False

def get_installed_packages():
    """Yüklü paketleri listele"""
    print_header("4. YÜKLÜ PAKETLER")
    
    packages = ['torch', 'torchvision', 'rembg', 'onnxruntime', 'onnxruntime-gpu']
    
    for package in packages:
        spec = importlib.util.find_spec(package)
        if spec is not None:
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'N/A')
                print(f"   ✅ {package}: v{version}")
            except:
                print(f"   ⚠️  {package}: Yüklü ama import edilemiyor")
        else:
            print(f"   ❌ {package}: Kurulu değil")

def suggest_fixes(has_cuda, pytorch_cuda, rembg_ok):
    """Çözüm önerileri"""
    print_header("5. ÇÖZÜM ÖNERİLERİ")
    
    if not has_cuda:
        print("\n❌ SORUN 1: NVIDIA Sürücüsü Yok")
        print("   📥 Çözüm:")
        print("   1. https://www.nvidia.com/Download/index.aspx adresinden")
        print("      GPU'nuza uygun sürücüyü indirin")
        print("   2. Sürücüyü kurun ve bilgisayarı yeniden başlatın")
        print()
    
    if has_cuda and not pytorch_cuda:
        print("\n❌ SORUN 2: PyTorch CPU Versiyonu Kurulu")
        print("   📥 Çözüm:")
        print("   1. Önce mevcut PyTorch'u kaldırın:")
        print("      pip uninstall torch torchvision torchaudio -y")
        print()
        print("   2. CUDA versiyonunu yükleyin:")
        print("      # CUDA 11.8 için:")
        print("      pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        print()
        print("      # CUDA 12.1 için:")
        print("      pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        print()
        print("   3. Hangisini kuracağınızı öğrenmek için:")
        print("      nvidia-smi komutunu çalıştırın ve CUDA Version'a bakın")
        print()
    
    if pytorch_cuda and not rembg_ok:
        print("\n❌ SORUN 3: rembg GPU Desteği Aktif Değil")
        print("   📥 Çözüm:")
        print("   1. rembg'yi GPU desteğiyle yeniden yükleyin:")
        print('      pip uninstall rembg -y')
        print('      pip install "rembg[gpu]"')
        print()
        print("   2. VEYA onnxruntime-gpu'yu manuel yükleyin:")
        print("      pip uninstall onnxruntime onnxruntime-gpu -y")
        print("      pip install onnxruntime-gpu")
        print('      pip install rembg')
        print()
    
    if has_cuda and pytorch_cuda and rembg_ok:
        print("\n✅ TÜM SİSTEMLER ÇALIŞIYOR!")
        print("   rembg GPU desteğiyle kullanılabilir durumda")
        print()
    
    # Ek öneriler
    print("\n💡 EK İPUÇLARI:")
    print()
    print("1. CMD/PowerShell'i YÖNETİCİ olarak çalıştırın")
    print()
    print("2. pip'i güncelleyin:")
    print("   python -m pip install --upgrade pip")
    print()
    print("3. Sanal ortam kullanın:")
    print("   python -m venv antares_env")
    print("   antares_env\\Scripts\\activate  # Windows")
    print("   source antares_env/bin/activate  # Linux/Mac")
    print()
    print('4. Eğer "rembg[gpu]" hatası alıyorsanız:')
    print('   • PowerShell kullanıyorsanız: pip install "rembg[gpu]"')
    print("   • CMD kullanıyorsanız: pip install rembg[gpu]")
    print('   • Veya: pip install rembg onnxruntime-gpu')
    print()
    print("5. Başında uyarı alıyorsanız:")
    print("   • Python'u PATH'e ekleyin")
    print("   • pip install --user kullanmayın")
    print("   • Sanal ortam içinde yükleyin")

def test_rembg_gpu():
    """rembg GPU kullanımını test et"""
    print_header("6. REMBG GPU TESTİ")
    
    try:
        import torch
        from rembg import remove
        from PIL import Image
        import numpy as np
        
        print("\n🧪 Test görüntüsü oluşturuluyor...")
        
        # Test görüntüsü oluştur
        test_img = Image.new('RGB', (100, 100), color='red')
        
        print("🔄 rembg ile işleniyor...")
        
        # Device bilgisini göster
        if torch.cuda.is_available():
            print(f"   PyTorch Device: cuda (GPU)")
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
        else:
            print(f"   PyTorch Device: cpu")
        
        # İşle
        import time
        start = time.time()
        output = remove(test_img)
        elapsed = time.time() - start
        
        print(f"   ✅ İşlem tamamlandı ({elapsed:.2f}s)")
        print(f"   Sonuç boyutu: {output.size}")
        
        # GPU kullanımını kontrol et
        if torch.cuda.is_available():
            memory_allocated = torch.cuda.memory_allocated(0) / 1024**2
            print(f"   GPU Memory: {memory_allocated:.1f} MB kullanılıyor")
            
            if memory_allocated > 0:
                print("\n   ✅ GPU BAŞARIYLA KULLANIMDA!")
            else:
                print("\n   ⚠️  GPU memory kullanımı tespit edilemedi")
                print("   → Model CPU'da çalışıyor olabilir")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 70)
    print("  ANTARES KAPSÜL - rembg GPU Sorun Giderme")
    print("=" * 70)
    print("\n🔍 Sisteminiz analiz ediliyor...\n")
    
    # Kontroller
    has_cuda = check_cuda()
    pytorch_cuda = check_pytorch()
    rembg_ok = check_rembg()
    get_installed_packages()
    
    # Öneriler
    suggest_fixes(has_cuda, pytorch_cuda, rembg_ok)
    
    # Test
    if has_cuda and pytorch_cuda and rembg_ok:
        test_rembg_gpu()
    
    # Özet
    print_header("ÖZET")
    print("\n📊 Durum:")
    print(f"   CUDA/GPU: {'✅' if has_cuda else '❌'}")
    print(f"   PyTorch CUDA: {'✅' if pytorch_cuda else '❌'}")
    print(f"   rembg: {'✅' if rembg_ok else '❌'}")
    
    if has_cuda and pytorch_cuda and rembg_ok:
        print("\n🎉 Sistem hazır! rembg GPU ile çalışabilir.")
    else:
        print("\n⚠️  Yukarıdaki çözüm önerilerini takip edin.")
    
    print("\n" + "=" * 70)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nİptal edildi.")
        sys.exit(1)
