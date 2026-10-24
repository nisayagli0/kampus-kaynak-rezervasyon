# Kampüs Kaynak Rezervasyon Sistemi

Yazılım Laboratuvarı I, 2026–2027 Güz, Proje I. Kocaeli Üniversitesi Bilgisayar Mühendisliği.

Proje iki parçadan oluşur:

- **Rezervasyon modülü** (`rezervasyon/`): K1–K11 kurallarını uygular, arayüzden bağımsızdır, yalnızca Python standart kütüphanesini kullanır.
- **Masaüstü uygulaması** (`arayuz/`, PySide6): aynı modülü ekrandan kullanır. İş kuralı içermez.

Modül iki yoldan çalışır: komut satırından (`komut_satiri/`) ve masaüstü uygulamasından. İkisi de `rezervasyon/sistem.py` içindeki `RezervasyonSistemi` sınıfını çağırır.

## Gereksinimler

- Python 3.11 veya üzeri (3.13 ile denendi)
- Komut satırı için ek paket gerekmez.
- Masaüstü uygulaması için PySide6 (`requirements.txt`)

## Kurulum

Windows (PowerShell), proje klasöründe:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux / macOS:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Komut satırından çalıştırma

Girdi bir başlangıç dosyası (JSON) ve bir komut dosyasıdır (JSON Lines). Çıktı, her komut için bir satır olacak şekilde standart çıktıya yazılır.

Windows:

```
calistir.bat baslangic.json komutlar.jsonl > sonuclar.jsonl
```

Linux / macOS:

```
./calistir.sh baslangic.json komutlar.jsonl > sonuclar.jsonl
```

Betikler hangi klasörden çağrılırsa çağrılsın çalışır. Linux'ta `./calistir.sh` çalışmazsa önce `chmod +x calistir.sh` yazın.

Bir komut işlenemezse program çökmez. Hata ayrıntısı standart hataya (stderr) yazılır, standart çıktıya o komutun yerine `{"no":N,"komut":...,"durum":"RED","kod":"BEKLENMEYEN_HATA"}` satırı yazılır. Böylece satır sayısı komut sayısıyla aynı kalır.

Örnek senaryo (19 komut):

```
calistir.bat testler\ornek\baslangic.json testler\ornek\komutlar.jsonl > cikti.jsonl
python testler/karsilastir.py testler/ornek/sonuclar.jsonl cikti.jsonl
```

Beklenen çıktı: `Tüm satırlar eşleşti (19 satır).`

## Masaüstü uygulamasını çalıştırma

```
python -m arayuz.ana_pencere
python -m arayuz.ana_pencere testler/ornek/baslangic.json
```

Dosya adı verilmezse uygulama açıldıktan sonra üst çubuktaki düğmeyle başlangıç dosyası seçilir. Yeni bir dosya seçildiğinde tüm durum o dosyaya göre yeniden kurulur. Veriler yalnızca bellekte tutulur.

## Testler

```
python -m unittest discover -s testler -t .
```

Kendi test senaryolarımız `testler/kendi/` altındadır. Her klasörde `baslangic.json`, `komutlar.jsonl` ve beklenen `sonuclar.jsonl` bulunur:

| Klasör | Neyi sınar |
|---|---|
| `ekleme` | `kullanici_ekle` ve `kaynak_ekle` doğrulama sırası ve hata kodları |
| `guvenilirlik_dusuk` | Güvenilirlik 50'nin altındayken ileri tarih sınırı ve paket reddi |
| `k10_sira` | K10 doğrulama sırası (aynı anda birden fazla kural ihlalinde dönen kod) |
| `parametre` | Başlangıç dosyasındaki parametrelerin değişmesiyle davranışın değişmesi |

Bir senaryoyu çalıştırmak için (Windows):

```
calistir.bat testler\kendi\k10_sira\baslangic.json testler\kendi\k10_sira\komutlar.jsonl > cikti.jsonl
python testler/karsilastir.py testler/kendi/k10_sira/sonuclar.jsonl cikti.jsonl
```

`karsilastir.py` beklenen dosyadaki her alanın çıktıda aynı olmasını ister. Çıktıdaki fazladan alanlar hata sayılmaz.

## Klasör yapısı

```
rezervasyon/     Modül: modeller, kurallar (K1-K11), sistem.py (tek giriş noktası)
komut_satiri/    Komut dosyasını okuyup sonuç satırlarını yazan işleyici
arayuz/          PySide6 masaüstü uygulaması (iş kuralı yok)
testler/         Birim testleri, örnek senaryo, kendi senaryolarımız
docs/            Arayüz tasarım notları
calistir.sh      Linux / macOS çalıştırma betiği
calistir.bat     Windows çalıştırma betiği
```

## Dokümanda açık olmayan noktalar ve varsayımlarımız

Aşağıdaki noktalar proje dokümanında kesin belirtilmediği için aşağıdaki gibi yorumlandı:

- `HAFTALIK_SIFIRLAMA` olayı `zaman` ve `tur` alanlarıyla yazılır.
- Bekleme kaydındaki `sira`, aynı kaynaktaki kayıtların tarama sırasındaki (güvenilirlik, sonra kayıt numarası) yeridir.
- `bitis` değeri `baslangic` değerine eşitse `ZAMAN_ADIMI_HATASI` döner.
- Talep yalnızca bakiye yetersizliği yüzünden geçersizse bekleme kaydı açılmaz, `BEKLEME_GEREKSIZ` döner.
- Başlangıcı geçen bekleme kayıtları, `saat` komutundaki tüm olaylar işlendikten sonra silinir.
- `sorgu` için bulunamayan kimlikte `BULUNAMADI`, geçersiz tarihte `GECERSIZ_DEGER` döner.
- Komut satırında işlenemeyen satır için `BEKLENMEYEN_HATA` kodu kullanılır (dokümanda yoktur).