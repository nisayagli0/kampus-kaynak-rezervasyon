"""İki sonuç dosyasını (JSONL) satır satır, alan alan karşılaştırır.

Kullanım: python testler/karsilastir.py beklenen.jsonl cikti.jsonl

Beklenen satırdaki her alan çıktıda aynı değerle bulunmalıdır. Eksik veya
farklı alan hatadır; çıktıdaki fazladan alan hata sayılmaz (doküman Bölüm 5).
"""

import json
import sys


def oku(yol):
    with open(yol, encoding="utf-8") as f:
        return [json.loads(satir) for satir in f if satir.strip()]


def karsilastir(beklenen, cikti):
    """Fark mesajlarının listesini döndürür (fark yoksa boş liste)."""
    farklar = []
    for i, b in enumerate(beklenen, 1):
        if i > len(cikti):
            farklar.append(f"Satır {i}: çıktıda yok (beklenen {b})")
            continue
        c = cikti[i - 1]
        for alan, deger in b.items():
            if alan not in c:
                farklar.append(f"Satır {i}: '{alan}' alanı eksik (beklenen {deger!r})")
            elif c[alan] != deger:
                farklar.append(f"Satır {i}: '{alan}' beklenen {deger!r}, çıktı {c[alan]!r}")

    if len(cikti) > len(beklenen):
        farklar.append(f"Çıktıda fazladan {len(cikti) - len(beklenen)} satır var")
    return farklar


def main(argv):
    if len(argv) != 3:
        print("Kullanım: python testler/karsilastir.py beklenen.jsonl cikti.jsonl")
        return 2

    sys.stdout.reconfigure(encoding="utf-8")
    beklenen, cikti = oku(argv[1]), oku(argv[2])
    farklar = karsilastir(beklenen, cikti)

    for fark in farklar:
        print(fark)
    if farklar:
        print(f"{len(farklar)} fark bulundu.")
        return 1
    print(f"Tüm satırlar eşleşti ({len(beklenen)} satır).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
