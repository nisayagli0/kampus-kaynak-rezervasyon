"""Talep formu (doküman Bölüm 7): tek kaynak ve paket talebi.

Gün, saat ve kaynak listeden seçilir; yazı yazılmaz. Varsayılanlar simüle saatten
ve takvimde seçili günden gelir. Red mesajı Türkçe açıklamayla aynı formda görünür;
KESISME veya HAZIRLIK_IHLALI ise bilgiler yeniden girilmeden "Bekleme kaydı aç" çıkar.
Kurallar modülde işler; form yalnızca komutu gönderir ve sonucu gösterir.
"""

from datetime import date, timedelta

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (QComboBox, QDateEdit, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QTabWidget, QToolButton, QVBoxLayout, QWidget)

from arayuz import mesajlar, stil
from rezervasyon import okuma

ZAMANLAR = [f"{s:02d}:{d:02d}" for s in range(24) for d in (0, 15, 30, 45)]
EN_FAZLA_KALEM = 6  # üst sınırı aşan paketin modülden PAKET_BOYUTU almasını gösterebilmek için
GUN_BASLANGICI = "08:00"


def _ceyrege_yukari(dt):
    """datetime -> sonraki (veya aynı) 15 dakikalık an."""
    dt = dt.replace(second=0, microsecond=0)
    fazla = dt.minute % 15
    return dt if fazla == 0 else dt + timedelta(minutes=15 - fazla)


def varsayilan_aralik(simule_saat, gun):
    """Seçili gün için başlangıç ve bitiş saati metinleri ('HH:MM', 1 saatlik süre)."""
    if gun == simule_saat.date():
        bas = _ceyrege_yukari(simule_saat)
        bas_metin = bas.strftime("%H:%M") if (bas.date() == gun and bas.strftime("%H:%M") >= GUN_BASLANGICI) \
            else GUN_BASLANGICI
    else:
        bas_metin = GUN_BASLANGICI
    saat, dakika = map(int, bas_metin.split(":"))
    bit = min(saat * 60 + dakika + 60, 23 * 60 + 45)
    return bas_metin, f"{bit // 60:02d}:{bit % 60:02d}"


def _zaman_kutusu(secili):
    kutu = QComboBox()
    kutu.addItems(ZAMANLAR)
    kutu.setCurrentText(secili)
    kutu.setMaxVisibleItems(12)
    return kutu


def _tarih_kutusu(gun):
    kutu = QDateEdit()
    kutu.setCalendarPopup(True)
    kutu.setDisplayFormat("dd.MM.yyyy")
    kutu.setDate(QDate(gun.year, gun.month, gun.day))
    return kutu


def _metin(tarih_kutusu, zaman_kutusu):
    """Seçimleri modülün beklediği 'YYYY-AA-GGTSS:DD' metnine çevirir."""
    return f"{tarih_kutusu.date().toString('yyyy-MM-dd')}T{zaman_kutusu.currentText()}"


class KalemSatiri(QFrame):
    """Paketin bir kalemi: kaynak, gün, başlangıç, bitiş."""

    def __init__(self, kaynaklar, gun, bas, bit, silinebilir, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        yerlesim = QGridLayout(self)
        yerlesim.setContentsMargins(6, 4, 6, 4)
        self.kaynak = QComboBox()
        for k in kaynaklar:
            self.kaynak.addItem(f"{k.ad} ({k.id})", k.id)
        self.gun = _tarih_kutusu(gun)
        self.bas = _zaman_kutusu(bas)
        self.bit = _zaman_kutusu(bit)
        self.sil = QToolButton()
        self.sil.setText("✕")
        self.sil.setToolTip("Kalemi kaldır")
        self.sil.setEnabled(silinebilir)
        yerlesim.addWidget(self.kaynak, 0, 0, 1, 3)
        yerlesim.addWidget(self.sil, 0, 3)
        yerlesim.addWidget(self.gun, 1, 0)
        yerlesim.addWidget(self.bas, 1, 1)
        yerlesim.addWidget(self.bit, 1, 2)
        self.sonuc = QLabel("")
        self.sonuc.setWordWrap(True)
        self.sonuc.hide()
        yerlesim.addWidget(self.sonuc, 2, 0, 1, 4)

    def sonucu_yaz(self, metin, basarili):
        """Paket denemesinin bu kalem için sonucunu kalemin kendi satırında gösterir."""
        renk = stil.BASARI_YAZI if basarili else stil.HATA_YAZI
        self.sonuc.setStyleSheet(f"color: {renk.name()};")
        self.sonuc.setText(metin)
        self.sonuc.setVisible(bool(metin))

    def kalem(self):
        return {"kaynak": self.kaynak.currentData(),
                "baslangic": _metin(self.gun, self.bas), "bitis": _metin(self.gun, self.bit)}


class TalepFormu(QWidget):
    def __init__(self, oturum, parent=None):
        super().__init__(parent)
        self.oturum = oturum
        self._son_talep = None  # "Bekleme kaydı aç" için son tekil talebin alanları
        self._kaynak_kimlikleri = []

        self._kullanici_kimlikleri = None

        yerlesim = QVBoxLayout(self)
        yerlesim.setContentsMargins(8, 8, 8, 8)
        ust = QHBoxLayout()
        ust.addWidget(QLabel("Kullanıcı"))
        self.kullanici = QComboBox()
        ust.addWidget(self.kullanici, 1)
        yerlesim.addLayout(ust)
        self.sekmeler = QTabWidget()
        self.sekmeler.addTab(self._tekil_sayfa(), "Tek kaynak")
        self.sekmeler.addTab(self._paket_sayfa(), "Paket")
        yerlesim.addWidget(self.sekmeler, 1)
        self.kullanici.currentIndexChanged.connect(self._kullanici_secildi)

        oturum.yuklendi.connect(self._sifirla)
        oturum.secim_degisti.connect(self._secime_uy)
        oturum.saat_degisti.connect(self._saate_uy)
        oturum.veri_degisti.connect(self._listeleri_tazele)
        self._sifirla()

    # --- Kurulum ---
    def _tekil_sayfa(self):
        sayfa = QWidget()
        yer = QGridLayout(sayfa)
        self.kaynak = QComboBox()
        self.gun = _tarih_kutusu(date(2000, 1, 1))
        self.bas = _zaman_kutusu(GUN_BASLANGICI)
        self.bit = _zaman_kutusu("09:00")
        yer.addWidget(QLabel("Kaynak"), 0, 0)
        yer.addWidget(self.kaynak, 0, 1, 1, 2)
        yer.addWidget(QLabel("Gün"), 1, 0)
        yer.addWidget(self.gun, 1, 1, 1, 2)
        yer.addWidget(QLabel("Saat"), 2, 0)
        yer.addWidget(self.bas, 2, 1)
        yer.addWidget(self.bit, 2, 2)
        dugmeler = QHBoxLayout()
        self.dugme_fiyat = QPushButton("Fiyatı göster")
        self.dugme_talep = QPushButton("Rezervasyon yap")
        self.dugme_talep.setDefault(True)
        dugmeler.addWidget(self.dugme_fiyat)
        dugmeler.addWidget(self.dugme_talep)
        yer.addLayout(dugmeler, 3, 0, 1, 3)
        self.sonuc = QLabel("")
        self.sonuc.setWordWrap(True)
        yer.addWidget(self.sonuc, 4, 0, 1, 3)
        self.dugme_bekleme = QPushButton("Bekleme kaydı aç")
        self.dugme_bekleme.hide()
        yer.addWidget(self.dugme_bekleme, 5, 0, 1, 3)
        yer.setRowStretch(6, 1)

        self.dugme_fiyat.clicked.connect(lambda: self._tekil_gonder("fiyat"))
        self.dugme_talep.clicked.connect(lambda: self._tekil_gonder("rezervasyon"))
        self.dugme_bekleme.clicked.connect(self._bekleme_ac)
        self.gun.dateChanged.connect(self._gun_degisti)
        return sayfa

    def _paket_sayfa(self):
        sayfa = QWidget()
        yer = QVBoxLayout(sayfa)
        self.kalemler = []
        kalem_alani = QWidget()
        self.kalemler_yeri = QVBoxLayout(kalem_alani)
        self.kalemler_yeri.setContentsMargins(0, 0, 0, 0)
        self.kalemler_yeri.addStretch(1)
        kaydirma = QScrollArea()
        kaydirma.setWidgetResizable(True)
        kaydirma.setFrameShape(QFrame.NoFrame)
        kaydirma.setWidget(kalem_alani)
        yer.addWidget(kaydirma, 1)
        dugmeler = QHBoxLayout()
        self.dugme_kalem_ekle = QPushButton("+ Kalem ekle")
        self.dugme_paket = QPushButton("Paketi iste")
        self.dugme_paket.setDefault(True)
        dugmeler.addWidget(self.dugme_kalem_ekle)
        dugmeler.addWidget(self.dugme_paket)
        yer.addLayout(dugmeler)
        self.paket_sonuc = QLabel("")
        self.paket_sonuc.setWordWrap(True)
        yer.addWidget(self.paket_sonuc)
        self.dugme_kalem_ekle.clicked.connect(self._kalem_ekle)
        self.dugme_paket.clicked.connect(self._paket_gonder)
        return sayfa

    # --- Varsayılanlar ve eşitleme ---
    def _kaynaklari_doldur(self):
        durum = self.oturum.durum
        kaynaklar = okuma.kaynaklar(durum) if durum else []
        kimlikler = [k.id for k in kaynaklar]
        if kimlikler == self._kaynak_kimlikleri:
            return
        secili = self.kaynak.currentData()
        self.kaynak.clear()
        for k in kaynaklar:
            self.kaynak.addItem(f"{k.ad} ({k.id})", k.id)
        if secili in kimlikler:
            self.kaynak.setCurrentIndex(kimlikler.index(secili))
        self._kaynak_kimlikleri = kimlikler

    def _sifirla(self):
        """Yeni dosya yüklenince form ve paket kalemleri baştan kurulur."""
        self._kaynak_kimlikleri = None
        self._kaynaklari_doldur()
        self._son_talep = None
        self.sonuc.setText("")
        self.paket_sonuc.setText("")
        self.dugme_bekleme.hide()
        for kalem in self.kalemler:
            kalem.setParent(None)
        self.kalemler = []
        if self.oturum.durum:
            self._saate_uy()
            self._kalem_ekle()
            self._kalem_ekle()
        self._etkinlik()

    def _etkinlik(self):
        var = self.oturum.durum is not None
        for parca in (self.kullanici, self.kaynak, self.gun, self.bas, self.bit, self.dugme_fiyat,
                      self.dugme_talep, self.dugme_kalem_ekle, self.dugme_paket):
            parca.setEnabled(var)
        self._kullanici_yaz()

    def _kullanici_yaz(self):
        """Kullanıcı listesini ve seçimi oturumla eşitler."""
        durum = self.oturum.durum
        kullanicilar = okuma.kullanicilar(durum) if durum else []
        kimlikler = [k.id for k in kullanicilar]
        self.kullanici.blockSignals(True)
        if kimlikler != self._kullanici_kimlikleri:
            self.kullanici.clear()
            for k in kullanicilar:
                self.kullanici.addItem(f"{k.ad} ({k.id})", k.id)
            self._kullanici_kimlikleri = kimlikler
        if self.oturum.secili_kullanici in kimlikler:
            self.kullanici.setCurrentIndex(kimlikler.index(self.oturum.secili_kullanici))
        self.kullanici.blockSignals(False)

    def _kullanici_secildi(self):
        kimlik = self.kullanici.currentData()
        if kimlik:
            self.oturum.kullanici_sec(kimlik)

    def _secime_uy(self):
        """Takvimde gün değişince form günü de değişir; kullanıcı etiketi güncellenir."""
        self._kullanici_yaz()
        gun = self.oturum.secili_gun
        if gun and self.gun.date().toPython() != gun:
            self.gun.blockSignals(True)
            self.gun.setDate(QDate(gun.year, gun.month, gun.day))
            self.gun.blockSignals(False)
            self._varsayilan_saatler()

    def _gun_degisti(self, qdate):
        """Formdaki gün elle değiştirilirse takvim de o güne geçer."""
        if self.oturum.durum:
            self.oturum.gun_sec(qdate.toPython())
            self._varsayilan_saatler()

    def _saate_uy(self):
        self._secime_uy()
        self._varsayilan_saatler()

    def _varsayilan_saatler(self):
        durum = self.oturum.durum
        if not durum:
            return
        bas, bit = varsayilan_aralik(durum.saat, self.gun.date().toPython())
        self.bas.setCurrentText(bas)
        self.bit.setCurrentText(bit)

    def _listeleri_tazele(self):
        self._kaynaklari_doldur()
        self._kullanici_yaz()

    def bos_aralik_onerisi(self, kaynak_id, baslangic):
        """Takvimde boş yere tıklanınca form o kaynak ve saatle dolar (1 saatlik süre)."""
        self.sekmeler.setCurrentIndex(0)
        if kaynak_id in (self._kaynak_kimlikleri or []):
            self.kaynak.setCurrentIndex(self._kaynak_kimlikleri.index(kaynak_id))
        self.bas.setCurrentText(baslangic.strftime("%H:%M"))
        bit = min(baslangic.hour * 60 + baslangic.minute + 60, 23 * 60 + 45)
        self.bit.setCurrentText(f"{bit // 60:02d}:{bit % 60:02d}")

    # --- Tekil talep ---
    def _tekil_alanlar(self):
        return {"kullanici": self.oturum.secili_kullanici, "kaynak": self.kaynak.currentData(),
                "baslangic": _metin(self.gun, self.bas), "bitis": _metin(self.gun, self.bit)}

    def _yaz(self, etiket, metin, basarili):
        renk = stil.BASARI_YAZI if basarili else stil.HATA_YAZI
        etiket.setStyleSheet(f"color: {renk.name()};")
        etiket.setText(metin)

    def _tekil_gonder(self, komut):
        if not self.oturum.secili_kullanici:
            self._yaz(self.sonuc, "Önce bir kullanıcı seçin (Kullanıcı sekmesi).", False)
            return
        alanlar = self._tekil_alanlar()
        sonuc = self.oturum.komut(komut, **alanlar)
        self.dugme_bekleme.hide()
        if sonuc["durum"] == "TAMAM" and komut == "fiyat":
            self._yaz(self.sonuc, f"Talep geçerli. Ücret: {sonuc['ucret']} KP "
                                  "(bakiye değişmedi).", True)
        elif sonuc["durum"] == "TAMAM":
            self._yaz(self.sonuc, f"Rezervasyon alındı. Ücret: {sonuc['ucret']} KP · "
                                  f"Kalan bakiye: {sonuc['bakiye']} KP.", True)
        else:
            self._yaz(self.sonuc, mesajlar.red_metni(sonuc), False)
            if sonuc.get("kod") in mesajlar.BEKLEMEYE_UYGUN_KODLAR:
                self._son_talep = alanlar
                self.dugme_bekleme.show()

    def _bekleme_ac(self):
        if not self._son_talep:
            return
        sonuc = self.oturum.komut("bekleme", **self._son_talep)
        if sonuc["durum"] == "TAMAM":
            self._yaz(self.sonuc, f"Bekleme kaydı açıldı. Listedeki sıranız: {sonuc['sira']}.", True)
            self.dugme_bekleme.hide()
        else:
            self._yaz(self.sonuc, mesajlar.red_metni(sonuc), False)

    # --- Paket ---
    def _kalem_ekle(self):
        if len(self.kalemler) >= EN_FAZLA_KALEM or not self.oturum.durum:
            return
        gun = self.gun.date().toPython()
        bas, bit = varsayilan_aralik(self.oturum.durum.saat, gun)
        kalem = KalemSatiri(okuma.kaynaklar(self.oturum.durum), gun, bas, bit,
                            silinebilir=True)
        kalem.sil.clicked.connect(lambda _=False, k=kalem: self._kalem_sil(k))
        self.kalemler.append(kalem)
        self.kalemler_yeri.insertWidget(len(self.kalemler) - 1, kalem)
        self.dugme_kalem_ekle.setEnabled(len(self.kalemler) < EN_FAZLA_KALEM)

    def _kalem_sil(self, kalem):
        self.kalemler.remove(kalem)
        kalem.setParent(None)
        self.dugme_kalem_ekle.setEnabled(True)

    def _paket_gonder(self):
        if not self.oturum.secili_kullanici:
            self._yaz(self.paket_sonuc, "Önce bir kullanıcı seçin (Kullanıcı sekmesi).", False)
            return
        kalemler = [k.kalem() for k in self.kalemler]
        for satir in self.kalemler:
            satir.sonucu_yaz("", True)
        sonuc = self.oturum.komut("paket", kullanici=self.oturum.secili_kullanici, kalemler=kalemler)
        if sonuc["durum"] == "TAMAM":
            for satir, ucret in zip(self.kalemler, sonuc["ucretler"]):
                satir.sonucu_yaz(f"Alındı · {ucret} KP", True)
            self._yaz(self.paket_sonuc, f"Paket alındı. Toplam: {sonuc['toplam']} KP · "
                                        f"Kalan bakiye: {sonuc['bakiye']} KP.", True)
            return
        for kalem_sonucu in sonuc.get("kalemler", []):
            sira = kalem_sonucu["sira"]
            if sira >= len(self.kalemler):
                continue
            if kalem_sonucu["durum"] == "TAMAM":
                self.kalemler[sira].sonucu_yaz("Geçti", True)
            else:
                kod = kalem_sonucu.get("kod", "?")
                self.kalemler[sira].sonucu_yaz(
                    f"Reddedildi: {mesajlar.aciklama(kod)} ({kod})", False)
        self._yaz(self.paket_sonuc, mesajlar.red_metni(sonuc), False)
