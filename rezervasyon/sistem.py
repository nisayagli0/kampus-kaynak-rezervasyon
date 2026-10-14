"""Rezervasyon modülünün tek giriş noktası.

Komut satırı (komutlar.jsonl) ve masaüstü arayüzü aynı fonksiyonları çağırır.
Parametre adları, komut dosyasındaki JSON alan adlarıyla birebir aynıdır.
Her fonksiyon bir sözlük döndürür:
    {"durum": "TAMAM", ...ek alanlar}  veya  {"durum": "RED", "kod": "..."}
"no" ve "komut" alanlarını komut satırı işleyicisi ekler.
Zamanlar "YYYY-AA-GGTSS:DD" metni olarak gelir.
"""

from rezervasyon.modeller import Durum


class RezervasyonSistemi:
    """Tüm komutları sunan sınıf. Bellek verisi self.durum içinde durur."""

    def __init__(self, durum: Durum):
        self.durum = durum

    @classmethod
    def dosyadan(cls, yol):
        """Başlangıç dosyasını okuyup sistemi kurar (yukleyici.py, Erva)."""
        from rezervasyon import yukleyici  # Erva yazınca çalışacak

        return cls(yukleyici.yukle(yol))

    # --- Saat (K6, K11) ---
    def saat(self, zaman):
        raise NotImplementedError

    # --- Talepler (K1-K5, K7, K10) ---
    def rezervasyon(self, kullanici, kaynak, baslangic, bitis):
        raise NotImplementedError

    def paket(self, kullanici, kalemler):
        """kalemler: [{"kaynak": ..., "baslangic": ..., "bitis": ...}, ...]"""
        raise NotImplementedError

    def fiyat(self, kullanici, kaynak, baslangic, bitis):
        raise NotImplementedError

    # --- Durum makinesi (K8) ---
    def iptal(self, rezervasyon):
        raise NotImplementedError

    def giris(self, rezervasyon):
        raise NotImplementedError

    def cikis(self, rezervasyon):
        raise NotImplementedError

    # --- Bekleme listesi (K9) ---
    def bekleme(self, kullanici, kaynak, baslangic, bitis):
        raise NotImplementedError

    # --- Sorgular ---
    def sorgu_kullanici(self, id):
        raise NotImplementedError

    def sorgu_kaynak(self, id, gun):
        raise NotImplementedError

    # --- Ekleme (K10 ekleme sırası) ---
    def kullanici_ekle(self, id, ad, rol, sertifikalar, bakiye, guvenilirlik):
        raise NotImplementedError

    def kaynak_ekle(self, id, ad, tur, izinli_roller):
        raise NotImplementedError
