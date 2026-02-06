@echo off
REM ANTARES KAPSÜL - rembg GPU Hızlı Düzeltme (Windows)
echo.
echo ================================================
echo  REMBG GPU SORUNU - HIZLI DUZELTME
echo ================================================
echo.

REM Yönetici kontrolü
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] UYARI: Bu script'i YONETİCİ olarak calistirin!
    echo [!] Sag tikla > "Yonetici olarak calistir"
    pause
    exit /b 1
)

echo [1/6] Python versiyonu kontrol ediliyor...
python --version
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi!
    pause
    exit /b 1
)
echo.

echo [2/6] NVIDIA GPU kontrol ediliyor...
nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo [UYARI] NVIDIA GPU bulunamadi veya surucu yuklu degil!
    echo [!] https://www.nvidia.com/Download/index.aspx adresinden surucu yukleyin
    pause
    exit /b 1
)
nvidia-smi
echo.

echo [3/6] Mevcut paketler kaldiriliyor...
pip uninstall torch torchvision torchaudio onnxruntime onnxruntime-gpu rembg -y
echo.

echo [4/6] PyTorch CUDA versiyonu yukleniyor...
echo [!] NVIDIA-SMI'daki CUDA Version'a bakin (ornek: 12.1)
echo.
set /p cuda_version="CUDA versiyonunuz (11.8 veya 12.1): "

if "%cuda_version%"=="11.8" (
    echo [*] CUDA 11.8 icin PyTorch yukleniyor...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
) else if "%cuda_version%"=="12.1" (
    echo [*] CUDA 12.1 icin PyTorch yukleniyor...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    echo [!] Gecersiz secim! 11.8 veya 12.1 giriniz.
    pause
    exit /b 1
)
echo.

echo [5/6] onnxruntime-gpu yukleniyor...
pip install onnxruntime-gpu
echo.

echo [6/6] rembg yukleniyor...
pip install rembg
echo.

echo ================================================
echo  KURULUM TAMAMLANDI!
echo ================================================
echo.
echo [*] Test icin calistirin:
echo     python fix_rembg_gpu.py
echo.
pause
