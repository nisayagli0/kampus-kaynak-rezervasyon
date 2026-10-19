"""Rezervasyon modülünün tek giriş noktası.

Komut satırı (komutlar.jsonl) ve masaüstü arayüzü aynı fonksiyonları çağırır.
Parametre adları, komut dosyasındaki JSON alan adlarıyla birebir aynıdır.
Her fonksiyon bir sözlük döndürür:
    {"durum": "TAMAM", ...ek alanlar}  veya  {"durum": "RED", "kod": "..."}
"no" ve "komut" alanlarını komut satırı işleyicisi ekler.
Zamanlar "YYYY-AA-GGTSS:DD" metni olarak gelir.
"""

from rezervasyon import bekleme, durum_makinesi, paket, sorgu, talep, yukleyici, zaman
from rezervasyon import saat as saat_modulu
from rezervasyon.modeller import Durum


class RezervasyonSistemi:
    """Tüm komutları sunan sınıf. Bellek verisi self.durum içinde durur."""

    def __init__(self, durum: Durum):
        self.durum = durum

    @classmethod
    def dosyadan(cls, yol):
        """Başlangıç dosyasını okuyup sistemi kurar."""
        return cls(yukleyici.yukle(yol))

    # --- Saat (K6, K11) ---
    def saat(self, zaman):
        from rezervasyon.zaman import ayristir

        return saat_modulu.ilerlet(self.durum, ayristir(zaman))

    # --- Talepler (K1-K5, K7, K10) ---
    def rezervasyon(self, kullanici, kaynak, baslangic, bitis):
        return talep.rezervasyon(
            self.durum,
            kullanici,
            kaynak,
            zaman.ayristir(baslangic),
            zaman.ayristir(bitis),
        )

    def paket(self, kullanici, kalemler):
        """kalemler: [{"kaynak": ..., "baslangic": ..., "bitis": ...}, ...]"""
        cevrilmis = [
            {
                "kaynak": k["kaynak"],
                "baslangic": zaman.ayristir(k["baslangic"]),
                "bitis": zaman.ayristir(k["bitis"]),
            }
            for k in kalemler
        ]
        return paket.paket(self.durum, kullanici, cevrilmis)

    def fiyat(self, kullanici, kaynak, baslangic, bitis):
        return talep.fiyat(
            self.durum,
            kullanici,
            kaynak,
            zaman.ayristir(baslangic),
            zaman.ayristir(bitis),
        )

    # --- Durum makinesi (K8) ---
    def iptal(self, rezervasyon):
        return durum_makinesi.iptal(self.durum, rezervasyon)

    def giris(self, rezervasyon):
        return durum_makinesi.giris(self.durum, rezervasyon)

    def cikis(self, rezervasyon):
        return durum_makinesi.cikis(self.durum, rezervasyon)

    # --- Bekleme listesi (K9) ---
    def bekleme(self, kullanici, kaynak, baslangic, bitis):
        return bekleme.ac(
            self.durum,
            kullanici,
            kaynak,
            zaman.ayristir(baslangic),
            zaman.ayristir(bitis),
        )

    # --- Sorgular ---
    def sorgu_kullanici(self, id):
        return sorgu.kullanici(self.durum, id)

    def sorgu_kaynak(self, id, gun):
        return sorgu.kaynak(self.durum, id, gun)

    # --- Ekleme (K10 ekleme sırası) ---
    def kullanici_ekle(self, id, ad, rol, sertifikalar, bakiye, guvenilirlik):
        return yukleyici.kullanici_ekle(
            self.durum, id, ad, rol, sertifikalar, bakiye, guvenilirlik
        )

    def kaynak_ekle(self, id, ad, tur, izinli_roller):
        return yukleyici.kaynak_ekle(self.durum, id, ad, tur, izinli_roller)
