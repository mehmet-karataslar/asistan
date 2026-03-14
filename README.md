# Asistan (Python)

Bu proje, Windows ortaminda sesli komut ve el cirpma ile bilgisayar eylemleri tetikleyen bir masaustu asistandir.
Asagidaki rehber, sifirdan kurulum yapan bir kullaniciya gore hazirlandi.

## Neler Yapar?

- Sesli komut veya el cirpma ile tetikleme
- Sistem eylemleri (uyku, kapatma, ozel komut)
- Uygulama ac/kapat komut esleme
- Senaryolar, pencere yonetimi ve temel akilli ozellikler
- SQLite ile yerel ayar/senaryo kaydi

## Proje Yapisi

- `asistan.py`: uygulama giris noktasi
- `asistan/`: ana uygulama kodlari
- `plugins/`: ozel eklentiler
- `assets/icons/`: uygulama ikonlari
- `tools/build_windows.ps1`: EXE derleme scripti
- `tools/build_installer.ps1`: kurulum paketi derleme scripti
- `installer/asistan.iss`: Inno Setup installer tanimi

## 1) Sistem Gereksinimleri

- Isletim sistemi: Windows 10/11
- Python: 3.10 veya ustu (onerilen: 3.11+)
- Mikrofon
- Internet: cevrimici ses tanima icin onerilir

## 2) Python Kurulu Mu? (Kontrol)

PowerShell acip sunlari calistir:

```powershell
python --version
py --version
```

Bu komutlardan biri surum dondurmelidir.

## 3) Python Kurulu Degilse Kurulum

### Yontem A - winget ile (onerilen)

```powershell
winget install --id Python.Python.3.11 -e
```

Kurulumdan sonra terminali kapatip yeniden ac ve tekrar kontrol et:

```powershell
python --version
```

### Yontem B - python.org

- [Python indirme sayfasi](https://www.python.org/downloads/) adresinden indir.
- Kurulumda mutlaka `Add Python to PATH` secenegini isaretle.

## 4) SQLite Destegi Var Mi? (Python icinden kontrol)

Bu proje ayarlari SQLite ile tutar. Python'un sqlite3 modulu aktif olmali.

```powershell
python -m sqlite3 --version
```

Alternatif kontrol:

```powershell
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

Hata alirsan Python'u resmi dagitimdan yeniden kur (genelde sqlite3 dahil gelir).

## 5) Projeyi Klonla

```powershell
git clone git@github.com:mehmet-karataslar/asistan.git
cd asistan
```

HTTPS kullanmak istersen:

```powershell
git clone https://github.com/mehmet-karataslar/asistan.git
cd asistan
```

## 6) Sanal Ortam Olustur

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Eger PowerShell script engeli olursa:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 7) Bagimliliklari Kur

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 8) Uygulamayi Gelistirme Modunda Calistir

```powershell
python asistan.py
```

## 9) EXE Build Alma (Gelistirici Icin)

EXE build icin gerekli ek paketler:

```powershell
pip install Pillow pyinstaller
```

Build komutu:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_windows.ps1
```

Olusan cikti:

- `dist/Asistan/Asistan.exe`

Not: Bu EXE, Python runtime dahil paketlenir. Son kullanicida Python kurulu olmasi gerekmez.

## 10) Kurulum Dosyasi (Setup.exe) Uretme

### 10.1 Inno Setup kur

```powershell
winget install --id JRSoftware.InnoSetup -e
```

### 10.2 Installer derle

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_installer.ps1
```

Olusan kurulum dosyasi:

- `dist_installer/Asistan-Setup.exe`

Bu dosya son kullaniciya verilecek asil kurulum dosyasidir.

## 11) Son Kullanici Tarafinda Kurulum Akisi

1. `Asistan-Setup.exe` dosyasini cift tiklayip kurulumu baslat.
2. Kurulum sihirbazinda varsayilan adimlari onayla.
3. Kurulum bitince masaustu kisayolundan uygulamayi ac.

Son kullanicinin ayrica Python, pip veya baska paket kurmasina gerek yoktur.

## 12) Veri Kayit Konumu (Kalici ve Yazilabilir)

Uygulama calisirken veriyi su klasore yazar:

```text
%LOCALAPPDATA%/Asistan/
```

Icerik:

- `asistan_data.db`: ayarlar, komutlar, gecmis, profiller
- `plugins/`: kullanici eklentileri

## 13) Sik Karsilasilan Sorunlar ve Cozumler

### Python komutu bulunamiyor

- Python kurulumunu tekrar yap.
- `Add Python to PATH` seceneginin acik oldugunu dogrula.

### Mikrofon acilmiyor

- Windows mikrofon izinlerini kontrol et.
- Baska bir uygulama mikrofona kilit koyuyor olabilir.

### Build sirasinda PyInstaller hatasi

- Sanal ortam aktif mi kontrol et.
- Paketleri yeniden kur:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
pip install Pillow pyinstaller
```

### Installer scripti Inno Setup bulamiyor

- Inno Setup kurulumunu tamamla.
- Tekrar calistir:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_installer.ps1
```

## 14) Hizli Komut Ozeti

```powershell
# 1) Sanal ortam
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) Bagimlilik
pip install -r requirements.txt

# 3) Uygulama
python asistan.py

# 4) EXE
powershell -ExecutionPolicy Bypass -File .\tools\build_windows.ps1

# 5) Installer
winget install --id JRSoftware.InnoSetup -e
powershell -ExecutionPolicy Bypass -File .\tools\build_installer.ps1
```

## Uygulama Goruntuleri ve Kurulum Videosu

### Ana Pencere

![Ana Pencere](assets/screenshots/main-window.bmp)

### Ayarlar Sekmesi

![Ayarlar Sekmesi](assets/screenshots/settings-tab.bmp)

### Komut Esleme Sekmesi

![Komut Esleme Sekmesi](assets/screenshots/bindings-tab.bmp)

### Kurulum Videosu

[Kurulum videosunu oynat](assets/screenshots/installer-wizard-Kurulum%20Videosu.mp4)
