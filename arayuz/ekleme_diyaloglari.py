"""Yeni kullanıcı ve yeni kaynak ekleme pencereleri (doküman Bölüm 7).

Rol, tür ve sertifikalar başlangıç dosyasından gelen listelerden seçilir. Modül reddederse
kod ve Türkçe açıklama aynı pencerede görünür; başarıda pencere kapanır ve ekranlar yenilenir.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QPushButton, QSpinBox, QVBoxLayout, QHBoxLayout)

from arayuz import mesajlar, stil
from rezervasyon import okuma


def _isaretli_liste(adlar, varsayilan_isaretli):
    liste = QListWidget()
    liste.setMaximumHeight(90)
    for ad in adlar:
        oge = QListWidgetItem(ad)
        oge.setFlags(oge.flags() | Qt.ItemIsUserCheckable)
        oge.setCheckState(Qt.Checked if varsayilan_isaretli else Qt.Unchecked)
        liste.addItem(oge)
    return liste


def _isaretliler(liste):
    return [liste.item(i).text() for i in range(liste.count())
            if liste.item(i).checkState() == Qt.Checked]


def _sonraki_kimlik(mevcut, onek):
    """'u' + ilk kullanılmayan sayı gibi bir öneri üretir (kullanıcı değiştirebilir)."""
    n = 1
    while f"{onek}{n}" in mevcut:
        n += 1
    return f"{onek}{n}"


class _EklemeDiyalogu(QDialog):
    """İki pencerenin ortak iskeleti: form, hata etiketi, Ekle ve Vazgeç düğmeleri."""

    def __init__(self, oturum, baslik, parent=None):
        super().__init__(parent)
        self.oturum = oturum
        self.setWindowTitle(baslik)
        self.setMinimumWidth(380)
        yerlesim = QVBoxLayout(self)
        self.form = QFormLayout()
        yerlesim.addLayout(self.form)
        self.hata = QLabel("")
        self.hata.setWordWrap(True)
        self.hata.setStyleSheet(f"color: {stil.HATA_YAZI.name()};")
        yerlesim.addWidget(self.hata)
        dugmeler = QHBoxLayout()
        dugmeler.addStretch(1)
        self.dugme_ekle = QPushButton("Ekle")
        self.dugme_ekle.setDefault(True)
        vazgec = QPushButton("Vazgeç")
        dugmeler.addWidget(vazgec)
        dugmeler.addWidget(self.dugme_ekle)
        yerlesim.addLayout(dugmeler)
        vazgec.clicked.connect(self.reject)
        self.dugme_ekle.clicked.connect(self._gonder)

    def _gonder(self):
        sonuc = self.oturum.komut(self.komut_adi, **self.alanlar())
        if sonuc["durum"] == "TAMAM":
            self.accept()
        else:
            self.hata.setText(mesajlar.red_metni(sonuc))  # pencere açık kalır, düzeltilebilir


class KullaniciEkleDiyalogu(_EklemeDiyalogu):
    komut_adi = "kullanici_ekle"

    def __init__(self, oturum, parent=None):
        super().__init__(oturum, "Yeni kullanıcı", parent)
        durum = oturum.durum
        self.kimlik = QLineEdit(_sonraki_kimlik(set(durum.kullanicilar), "u"))
        self.ad = QLineEdit()
        self.ad.setPlaceholderText("Ad Soyad")
        self.rol = QComboBox()
        self.rol.addItems(okuma.roller(durum))
        self.sertifikalar = _isaretli_liste(okuma.sertifikalar(durum), False)
        self.bakiye = QSpinBox()
        self.bakiye.setRange(-100000, 100000)
        self.guvenilirlik = QSpinBox()
        self.guvenilirlik.setRange(-1000, 1000)
        self.guvenilirlik.setValue(80)
        for etiket, parca in (("Kimlik", self.kimlik), ("Ad", self.ad), ("Rol", self.rol),
                              ("Sertifikalar", self.sertifikalar), ("Bakiye (KP)", self.bakiye),
                              ("Güvenilirlik", self.guvenilirlik)):
            self.form.addRow(etiket, parca)
        self.rol.currentTextChanged.connect(self._rol_degisti)
        self._rol_degisti(self.rol.currentText())

    def _rol_degisti(self, rol):
        """Varsayılan bakiye rolün haftalık kotasıdır."""
        if rol:
            self.bakiye.setValue(okuma.rol(self.oturum.durum, rol).haftalik_kota)

    def alanlar(self):
        return {"id": self.kimlik.text().strip(), "ad": self.ad.text().strip(),
                "rol": self.rol.currentText(), "sertifikalar": _isaretliler(self.sertifikalar),
                "bakiye": self.bakiye.value(), "guvenilirlik": self.guvenilirlik.value()}


class KaynakEkleDiyalogu(_EklemeDiyalogu):
    komut_adi = "kaynak_ekle"

    def __init__(self, oturum, parent=None):
        super().__init__(oturum, "Yeni kaynak", parent)
        durum = oturum.durum
        self.tur = QComboBox()
        self.tur.addItems(okuma.turler(durum))
        self.kimlik = QLineEdit()
        self.ad = QLineEdit()
        self.roller = _isaretli_liste(okuma.roller(durum), True)
        for etiket, parca in (("Tür", self.tur), ("Kimlik", self.kimlik), ("Ad", self.ad),
                              ("İzinli roller", self.roller)):
            self.form.addRow(etiket, parca)
        self.tur.currentTextChanged.connect(self._tur_degisti)
        self._tur_degisti(self.tur.currentText())

    def _tur_degisti(self, tur):
        """Aynı türdeki kaynakların adlandırmasına uyan kimlik ve ad önerir."""
        mevcut = {k.id for k in okuma.kaynaklar(self.oturum.durum)}
        ayni_tur = [k for k in okuma.kaynaklar(self.oturum.durum) if k.tur == tur]
        onek = ayni_tur[0].id.rsplit("-", 1)[0] if ayni_tur and "-" in ayni_tur[0].id else tur[:3]
        n = 1
        while f"{onek}-{n}" in mevcut:
            n += 1
        self.kimlik.setText(f"{onek}-{n}")
        self.ad.setText(f"{tur.capitalize()} {n}")

    def alanlar(self):
        return {"id": self.kimlik.text().strip(), "ad": self.ad.text().strip(),
                "tur": self.tur.currentText(), "izinli_roller": _isaretliler(self.roller)}
