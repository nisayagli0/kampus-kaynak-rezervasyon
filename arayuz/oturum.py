"""Arayüzün tek kapısı: modüle giden her komut buradan geçer.

Oturum, rezervasyon modülünü (RezervasyonSistemi) sarar. Her komutu çalıştırır,
sonucu olay günlüğüne yazar ve ekranlara haber verir. İş kuralı burada da yoktur;
kurallar modülün içindedir (doküman Bölüm 7).
"""

from PySide6.QtCore import QObject, Signal

from rezervasyon import okuma, zaman
from rezervasyon.sistem import RezervasyonSistemi


class Oturum(QObject):
    yuklendi = Signal()       # yeni başlangıç dosyası yüklendi: her şey sıfırlandı
    veri_degisti = Signal()   # bir komut çalıştı: ekranlar kendini yeniler
    saat_degisti = Signal()   # simüle saat ilerledi
    secim_degisti = Signal()  # seçili kullanıcı, gün veya rezervasyon değişti

    def __init__(self):
        super().__init__()
        self._sifirla(None)

    def _sifirla(self, sistem):
        self.sistem = sistem
        self.gunluk = []  # her öğe: {no, saat, komut, girdi, sonuc}
        self.secili_kullanici = None
        self.secili_gun = None
        self.secili_rezervasyon = None

    @property
    def durum(self):
        return self.sistem.durum if self.sistem else None

    # --- Dosya ---
    def yukle(self, yol):
        """Dosyadan sistemi kurar. Hata fırlatırsa eski durum olduğu gibi kalır."""
        yeni = RezervasyonSistemi.dosyadan(yol)
        self._sifirla(yeni)
        kullanicilar = okuma.kullanicilar(yeni.durum)
        self.secili_kullanici = kullanicilar[0].id if kullanicilar else None
        self.secili_gun = okuma.simule_saat(yeni.durum).date()
        self.yuklendi.emit()
        self.veri_degisti.emit()
        self.secim_degisti.emit()

    # --- Seçimler ---
    def kullanici_sec(self, kullanici_id):
        if kullanici_id != self.secili_kullanici:
            self.secili_kullanici = kullanici_id
            self.secim_degisti.emit()

    def gun_sec(self, gun):
        if gun != self.secili_gun:
            self.secili_gun = gun
            self.secim_degisti.emit()

    def rezervasyon_sec(self, rezervasyon_id):
        if rezervasyon_id != self.secili_rezervasyon:
            self.secili_rezervasyon = rezervasyon_id
            self.secim_degisti.emit()

    # --- Komutlar ---
    def komut(self, komut_adi, /, **alanlar):
        """Modülde `komut_adi` komutunu çalıştırır. Dönen sözlük Bölüm 5 biçimindedir.

        komut_adi yalnızca konumla verilir: kullanici_ekle gibi komutların `ad` alanı
        parametre adıyla çakışmasın diye.
        """
        ad = komut_adi
        onceki_saat = self.durum.saat
        try:
            sonuc = getattr(self.sistem, ad)(**alanlar)
        except Exception as hata:  # arayüz çökmesin; hata günlükte görünür
            sonuc = {"durum": "RED", "kod": "BEKLENMEYEN_HATA",
                     "mesaj": f"{type(hata).__name__}: {hata}"}

        komut_adi = "sorgu" if ad.startswith("sorgu_") else ad
        no = len(self.gunluk) + 1
        satir = {"no": no, "komut": komut_adi, **sonuc}
        self.gunluk.append({"no": no, "saat": onceki_saat, "komut": komut_adi,
                            "girdi": dict(alanlar), "sonuc": satir})

        secim_degisti = self._sonucu_isle(ad, alanlar, sonuc)
        if self.durum.saat != onceki_saat:
            self.saat_degisti.emit()
        self.veri_degisti.emit()
        if secim_degisti:
            self.secim_degisti.emit()
        return satir

    def _sonucu_isle(self, ad, alanlar, sonuc):
        """Başarılı komutun ardından seçimi uygun yere taşır; seçim değiştiyse True."""
        if sonuc.get("durum") != "TAMAM":
            return False
        onceki = (self.secili_kullanici, self.secili_gun, self.secili_rezervasyon)
        if ad == "saat":
            self.secili_gun = self.durum.saat.date()
        elif ad == "rezervasyon":
            self.secili_rezervasyon = sonuc["rezervasyon_id"]
            self.secili_gun = zaman.ayristir(alanlar["baslangic"]).date()
        elif ad == "paket":
            self.secili_rezervasyon = sonuc["rezervasyonlar"][0]
        elif ad == "kullanici_ekle":
            self.secili_kullanici = alanlar["id"]
        return onceki != (self.secili_kullanici, self.secili_gun, self.secili_rezervasyon)
