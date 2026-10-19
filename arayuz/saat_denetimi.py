"""Saat denetimi (doküman Bölüm 7): hızlı düğmeler, özel tarih-saat seçici ve
oluşan olayların listesi aynı yerde. Simüle saat üst çubukta her zaman görünür.

Saat ilerletme `saat` komutuyla modüle gönderilir; olayları modül üretir.
"""

from datetime import datetime, timedelta

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (QDateTimeEdit, QGridLayout, QLabel, QListWidget, QPushButton,
                               QVBoxLayout, QWidget)

from arayuz import mesajlar, stil
from rezervasyon import zaman


def sonraki_gun_sabahi(an):
    """Ertesi günün 08:00'ı."""
    return datetime(an.year, an.month, an.day, 8) + timedelta(days=1)


def sonraki_pazartesi(an):
    """Bugünden sonraki ilk Pazartesi 08:00 (bugün Pazartesi ise 7 gün sonrası)."""
    kalan = (7 - an.weekday()) % 7 or 7
    return datetime(an.year, an.month, an.day, 8) + timedelta(days=kalan)


class SaatDenetimi(QWidget):
    def __init__(self, oturum, parent=None):
        super().__init__(parent)
        self.oturum = oturum

        yerlesim = QVBoxLayout(self)
        yerlesim.setContentsMargins(8, 8, 8, 8)
        yerlesim.addWidget(QLabel("Simüle saati ilerlet"))

        izgara = QGridLayout()
        self.dugmeler = []
        hizli = [("+15 dk", lambda an: an + timedelta(minutes=15)),
                 ("+1 saat", lambda an: an + timedelta(hours=1)),
                 ("Ertesi gün 08:00", sonraki_gun_sabahi),
                 ("Sonraki Pazartesi 08:00", sonraki_pazartesi)]
        for i, (etiket, hesap) in enumerate(hizli):
            dugme = QPushButton(etiket)
            dugme.clicked.connect(lambda _=False, h=hesap: self._git(h(self.oturum.durum.saat)))
            self.dugmeler.append(dugme)
            izgara.addWidget(dugme, i // 2, i % 2)
        yerlesim.addLayout(izgara)

        yerlesim.addWidget(QLabel("Belirli bir ana git"))
        self.secici = QDateTimeEdit()
        self.secici.setCalendarPopup(True)
        self.secici.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.dugme_git = QPushButton("Bu ana ilerlet")
        self.dugme_git.clicked.connect(self._secilene_git)
        yerlesim.addWidget(self.secici)
        yerlesim.addWidget(self.dugme_git)

        self.mesaj = QLabel("")
        self.mesaj.setWordWrap(True)
        yerlesim.addWidget(self.mesaj)
        yerlesim.addWidget(QLabel("Oluşan olaylar"))
        self.olaylar = QListWidget()
        yerlesim.addWidget(self.olaylar, 1)

        oturum.yuklendi.connect(self._sifirla)
        oturum.saat_degisti.connect(self._seciciyi_guncelle)
        self._sifirla()

    def _sifirla(self):
        self.olaylar.clear()
        self.mesaj.setText("")
        var = self.oturum.durum is not None
        for parca in (*self.dugmeler, self.secici, self.dugme_git):
            parca.setEnabled(var)
        if var:
            self._seciciyi_guncelle()

    def _seciciyi_guncelle(self):
        an = self.oturum.durum.saat
        self.secici.setDateTime(QDateTime(an.year, an.month, an.day, an.hour, an.minute, 0))

    def _secilene_git(self):
        self._git(self.secici.dateTime().toPython().replace(second=0, microsecond=0))

    def _git(self, an):
        sonuc = self.oturum.komut("saat", zaman=zaman.bicimle(an))
        self.olaylar.clear()
        if sonuc["durum"] != "TAMAM":
            self.mesaj.setStyleSheet(f"color: {stil.HATA_YAZI.name()};")
            self.mesaj.setText(mesajlar.red_metni(sonuc))
            return
        self.mesaj.setStyleSheet(f"color: {stil.BASARI_YAZI.name()};")
        olaylar = sonuc["olaylar"]
        self.mesaj.setText(f"Saat ilerletildi. {len(olaylar)} olay oluştu." if olaylar
                           else "Saat ilerletildi; yeni olay yok.")
        for olay in olaylar:
            self.olaylar.addItem(mesajlar.olay_metni(olay))
