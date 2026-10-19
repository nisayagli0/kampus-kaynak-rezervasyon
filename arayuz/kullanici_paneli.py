"""Kullanıcı paneli (doküman Bölüm 7): seçili kullanıcının bakiyesi, güvenilirliği,
rezervasyonları ve bekleme kayıtları. Her komuttan sonra kendiliğinden yenilenir.

Tablodaki satır seçilince aynı rezervasyon takvimde de seçilir; Giriş / Çıkış / İptal
düğmeleri buradan da kullanılabilir.
"""

from PySide6.QtGui import QBrush
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFormLayout, QHeaderView, QLabel,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from arayuz import bicim, stil
from arayuz.eylemler import EylemSeridi
from rezervasyon import okuma

SUTUNLAR = ["Kaynak", "Başlangıç", "Bitiş", "Durum", "Ücret"]


def _tablo(sutunlar, yukseklik):
    tablo = QTableWidget(0, len(sutunlar))
    tablo.setHorizontalHeaderLabels(sutunlar)
    tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
    tablo.setSelectionMode(QAbstractItemView.SingleSelection)
    tablo.verticalHeader().hide()
    tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tablo.setMinimumHeight(yukseklik)
    return tablo


class KullaniciPaneli(QWidget):
    def __init__(self, oturum, parent=None):
        super().__init__(parent)
        self.oturum = oturum
        self._rezervasyonlar = []  # tablo satırlarına karşılık gelen kimlikler

        yerlesim = QVBoxLayout(self)
        yerlesim.setContentsMargins(8, 8, 8, 8)
        self.secici = QComboBox()
        yerlesim.addWidget(self.secici)

        ozet = QFormLayout()
        self.etiket_rol = QLabel("")
        self.etiket_bakiye = QLabel("")
        self.etiket_guvenilirlik = QLabel("")
        self.etiket_sertifika = QLabel("")
        self.etiket_sertifika.setWordWrap(True)
        ozet.addRow("Rol", self.etiket_rol)
        ozet.addRow("Bakiye", self.etiket_bakiye)
        ozet.addRow("Güvenilirlik", self.etiket_guvenilirlik)
        ozet.addRow("Sertifikalar", self.etiket_sertifika)
        yerlesim.addLayout(ozet)

        yerlesim.addWidget(QLabel("Rezervasyonlar"))
        self.tablo = _tablo(SUTUNLAR, 150)
        yerlesim.addWidget(self.tablo, 1)
        self.eylemler = EylemSeridi(oturum)
        yerlesim.addWidget(self.eylemler)

        yerlesim.addWidget(QLabel("Bekleme kayıtları"))
        self.bekleme = _tablo(["Kaynak", "Başlangıç", "Bitiş", "Kayıt saati"], 80)
        yerlesim.addWidget(self.bekleme)

        self.secici.currentIndexChanged.connect(self._kullanici_secildi)
        self.tablo.itemSelectionChanged.connect(self._satir_secildi)
        oturum.veri_degisti.connect(self.yenile)
        oturum.secim_degisti.connect(self.yenile)
        self.yenile()

    def _kullanici_secildi(self):
        kimlik = self.secici.currentData()
        if kimlik:
            self.oturum.kullanici_sec(kimlik)

    def _satir_secildi(self):
        satirlar = self.tablo.selectionModel().selectedRows()
        if satirlar and satirlar[0].row() < len(self._rezervasyonlar):
            self.oturum.rezervasyon_sec(self._rezervasyonlar[satirlar[0].row()])

    def yenile(self):
        durum = self.oturum.durum
        self.secici.blockSignals(True)
        self.secici.clear()
        kullanicilar = okuma.kullanicilar(durum) if durum else []
        for k in kullanicilar:
            self.secici.addItem(f"{k.ad} ({k.id})", k.id)
        kimlikler = [k.id for k in kullanicilar]
        if self.oturum.secili_kullanici in kimlikler:
            self.secici.setCurrentIndex(kimlikler.index(self.oturum.secili_kullanici))
        self.secici.blockSignals(False)

        ozet = okuma.kullanici_ozeti(durum, self.oturum.secili_kullanici) if durum else None
        if ozet is None:
            for etiket in (self.etiket_rol, self.etiket_bakiye, self.etiket_guvenilirlik,
                           self.etiket_sertifika):
                etiket.setText("—")
            self._tablolari_bosalt()
            self.eylemler.ayarla(None)
            return
        self.etiket_rol.setText(ozet["rol"])
        self.etiket_bakiye.setText(f"{ozet['bakiye']} / {ozet['haftalik_kota']} KP")
        self.etiket_guvenilirlik.setText(f"{ozet['guvenilirlik']} / 100")
        self.etiket_sertifika.setText(", ".join(ozet["sertifikalar"]) or "yok")
        self._rezervasyon_tablosu(durum, ozet["id"])
        self._bekleme_tablosu(durum, ozet["id"])
        self.eylemler.ayarla(self.oturum.secili_rezervasyon
                             if self.oturum.secili_rezervasyon in self._rezervasyonlar else None)

    def _tablolari_bosalt(self):
        self._rezervasyonlar = []
        self.tablo.setRowCount(0)
        self.bekleme.setRowCount(0)

    def _rezervasyon_tablosu(self, durum, kullanici_id):
        kayitlar = okuma.kullanici_rezervasyonlari(durum, kullanici_id)
        self._rezervasyonlar = [r.id for r in kayitlar]
        self.tablo.blockSignals(True)
        self.tablo.setRowCount(len(kayitlar))
        for i, r in enumerate(kayitlar):
            dolgu = stil.DURUM_STIL[r.durum][0].lighter(160)
            degerler = [r.kaynak, bicim.kisa(r.baslangic), bicim.kisa(r.bitis),
                        stil.durum_etiketi(r.durum), f"{r.ucret} KP"]
            for j, deger in enumerate(degerler):
                oge = QTableWidgetItem(deger)
                oge.setBackground(QBrush(dolgu))
                oge.setForeground(QBrush(stil.YAZI_RENGI))
                self.tablo.setItem(i, j, oge)
            if r.id == self.oturum.secili_rezervasyon:
                self.tablo.selectRow(i)
        self.tablo.blockSignals(False)

    def _bekleme_tablosu(self, durum, kullanici_id):
        kayitlar = okuma.bekleme_kayitlari(durum, kullanici_id)
        self.bekleme.setRowCount(len(kayitlar))
        for i, k in enumerate(kayitlar):
            for j, deger in enumerate([k.kaynak, bicim.kisa(k.baslangic), bicim.kisa(k.bitis),
                                       bicim.kisa(k.kayit_saati)]):
                self.bekleme.setItem(i, j, QTableWidgetItem(deger))
