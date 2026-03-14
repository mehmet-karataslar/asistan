# Asistan (Python)

Bu uygulama, mikrofonla el cirpma veya Turkce sesli komut algilar ve belirlenen kosullarda Windows bilgisayari uyku moduna alir, kapatir veya kullanicinin girdigi ozel komutu calistirir.

## Ozellikler

- Renkli arayuz ve coklu tema secimi
- Moduler dosya yapisi
- `Devreye Al` / `Dinlemeyi Durdur` / `Secili Eylemi Test Et` butonlari
- Turkce sesli komut modu ve kullanicinin girdigi anahtar kelime algilama
- Hassasiyet, clap sayisi, clap penceresi, minimum clap araligi, ses seviyesi ve cooldown ayarlari
- `sleep`, `shutdown` ve `custom` eylem secenekleri
- Durum ve log ekrani

## Dosya Yapisi

```text
asistan.py
asistan/
	__init__.py
	actions.py
	audio.py
	settings.py
	theme.py
	ui.py
```

## Gereksinimler

- Windows
- Python 3.10+
- Mikrofon

## Kurulum

```bash
pip install -r requirements.txt
```

## Windows EXE Build

Uretim ortami icin ek araclar:

```bash
pip install Pillow pyinstaller
```

Icon uret ve EXE klasorunu olustur:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_windows.ps1
```

Bu komut sonunda cikti klasoru:

```text
dist/Asistan/
```

Ana uygulama dosyasi:

```text
dist/Asistan/Asistan.exe
```

## Installer (Kurulum Paketi)

1. Inno Setup 6 kur.
2. Asagidaki komutu calistir:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_installer.ps1
```

Alternatif olarak `installer/asistan.iss` dosyasini Inno Setup ile acip Compile yapabilirsiniz.

Uretilen kurulum dosyasi:

```text
dist_installer/Asistan-Setup.exe
```

Bu setup dosyasi, son kullanici bilgisayarina gerekli Python runtime ve uygulama dosyalarini birlikte kurar.

## Veri ve Eklenti Konumu

Kurulumdan sonra uygulama yazilabilir dosyalari su klasorde tutar:

```text
%LOCALAPPDATA%/Asistan/
```

- `asistan_data.db`: ayarlar, komutlar, gecmis
- `plugins/`: kullanici plugin dosyalari

## Calistirma

```bash
python asistan.py
```

## Kullanim

1. Uygulamayi acin.
2. `Algilama Ayarlari` alanindan hassasiyet ve clap ayarlarini ortaminiza gore ayarlayin.
3. `Tetikleme Ayarlari` alanindan `voice` veya `clap` secin.
4. `voice` seciliyse Turkce anahtar kelimeyi girin.
5. `Eylem Ayarlari` alanindan `sleep`, `shutdown` veya `custom` secin.
6. `custom` seciliyse calistirilacak komutu girin.
7. `Devreye Al` ile mikrofon dinlemesini baslatin.
8. `voice` modunda anahtar kelimeyi soyleyin, `clap` modunda ayarladiginiz clap sayisi kadar el cirpin.

## Notlar

- Uyku komutu bazi sistemlerde guc politikasi nedeniyle engellenebilir.
- Yanlis tetikleme olursa hassasiyet esigini yukseltin, minimum clap araligini arttirin veya clap sayisini 3 yapin.
- `shutdown` secenegi bilgisayari hemen kapatir. Test ederken dikkatli olun.
- Turkce ses tanima icin internet baglantisi gerekir.

# asistan
