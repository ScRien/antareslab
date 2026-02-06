@echo off
title ANTARES KAPSUL 3D STUDIO v2.0
echo ========================================
echo  ANTARES KAPSUL 3D STUDIO v2.0
echo  Arkeolojik Eser Koruma Kapsulu
echo ========================================
echo.

:: Python kontrolu
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi!
    echo Lutfen Python 3.10+ yukleyin: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Sanal ortam kontrolu
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Sanal ortam aktif ediliyor...
    call venv\Scripts\activate.bat
) else (
    echo [INFO] Sanal ortam bulunamadi. Sistem Python kullanilacak.
)

:: Bagimliliklari kontrol et
echo.
echo [INFO] Bagimliliklar kontrol ediliyor...
python -c "import PyQt6" 2>nul
if %errorlevel% neq 0 (
    echo [UYARI] Bagimliliklar eksik! Yuklemek ister misiniz? [E/H]
    set /p install=
    if /i "%install%"=="E" (
        echo.
        echo [INFO] Bagimliliklar yukleniyor...
        pip install -r requirements.txt
    )
)

:: Uygulamayi baslat
echo.
echo [INFO] Uygulama baslatiliyor...
echo.
python main.py

:: Hata durumunda bekle
if %errorlevel% neq 0 (
    echo.
    echo [HATA] Uygulama bir hata ile kapandi.
    echo Hata kodu: %errorlevel%
    pause
)
