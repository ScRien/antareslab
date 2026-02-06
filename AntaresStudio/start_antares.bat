@echo off
REM ANTARES KAPSÜL 3D STUDIO - Windows Başlatıcı
echo.
echo ================================================
echo  ANTARES KAPSUL 3D STUDIO v2.0
echo ================================================
echo.

REM Sanal ortamı aktifleştir (varsa)
if exist "antares_env\Scripts\activate.bat" (
    echo [*] Sanal ortam aktif ediliyor...
    call antares_env\Scripts\activate.bat
)

REM Python versiyonunu kontrol et
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi!
    echo Lutfen Python 3.8+ yukleyin: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Programı başlat
echo [*] Program baslatiliyor...
echo.
python antares_main_improved.py

REM Hata durumunda bekle
if %errorlevel% neq 0 (
    echo.
    echo [HATA] Program kapandi! Hata kodu: %errorlevel%
    pause
)
