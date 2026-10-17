"""Komut satırı işleyicisi.

Kullanım: python -m komut_satiri.isleyici baslangic.json komutlar.jsonl

Komut dosyasını satır satır okur, her komutu RezervasyonSistemi'ne verir ve
her komut için bir sonuç satırını stdout'a yazar. Hata mesajları stderr'e gider;
stdout'a yalnızca sonuç satırları yazılır.
"""

import json
import sys

from rezervasyon.sistem import RezervasyonSistemi

# Komut adı -> RezervasyonSistemi metodu (sorgu ayrıca ele alınır)
KOMUTLAR = {
    "saat", "rezervasyon", "paket", "fiyat", "iptal", "giris", "cikis",
    "bekleme", "kullanici_ekle", "kaynak_ekle",
}


def komut_isle(sistem, komut):
    """Tek bir komutu çalıştırır, sonuç sözlüğünü döndürür ("no" hariç)."""
    alanlar = dict(komut)
    ad = alanlar.pop("komut")

    if ad == "sorgu":
        tur = alanlar.pop("tur")
        sonuc = getattr(sistem, "sorgu_" + tur)(**alanlar)  # sorgu_kullanici / sorgu_kaynak
    elif ad in KOMUTLAR:
        sonuc = getattr(sistem, ad)(**alanlar)
    else:
        raise ValueError(f"bilinmeyen komut: {ad}")

    return {"komut": ad, **sonuc}


def main(argv):
    if len(argv) != 3:
        print("Kullanım: calistir baslangic.json komutlar.jsonl", file=sys.stderr)
        return 2

    sys.stdout.reconfigure(encoding="utf-8")
    sistem = RezervasyonSistemi.dosyadan(argv[1])

    no = 0
    with open(argv[2], encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if not satir:  # boş satırlar atlanır
                continue
            no += 1
            try:
                sonuc = komut_isle(sistem, json.loads(satir))
            except Exception as hata:  # program çökmez, satır stderr'e raporlanır
                print(f"{no}. komut işlenemedi: {hata!r}", file=sys.stderr)
                continue
            print(json.dumps({"no": no, **sonuc}, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
