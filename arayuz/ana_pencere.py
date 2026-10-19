"""Ana pencere: dosya seçimi, simüle saat, takvim, sağ paneller ve olay günlüğü.

Arayüzde iş kuralı yoktur. Her komut Oturum üzerinden rezervasyon modülüne gider
(doküman Bölüm 7). Çalıştırma (proje kökünden): python -m arayuz.ana_pencere [baslangic.json]
"""

import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame, QGroupBox, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QSplitter, QTabWidget, QVBoxLayout,
                               QWidget)

from arayuz import bicim, stil
from arayuz.detay_karti import DetayKarti
from arayuz.ekleme_diyaloglari import KaynakEkleDiyalogu, KullaniciEkleDiyalogu
from arayuz.kullanici_paneli import KullaniciPaneli
from arayuz.olay_gunlugu import OlayGunlugu
from arayuz.oturum import Oturum
from arayuz.saat_denetimi import SaatDenetimi
from arayuz.takvim import Takvim
from arayuz.talep_formu import TalepFormu


class AnaPencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kampüs Kaynak Rezervasyon")
        self.resize(1360, 820)
        self.oturum = Oturum()
        self._arayuzu_kur()
        self.oturum.yuklendi.connect(self._saati_goster)
        self.oturum.veri_degisti.connect(self._saati_goster)
        self._saati_goster()

    # --- Yerleşim ---
    def _arayuzu_kur(self):
        merkez = QWidget()
        ana = QVBoxLayout(merkez)
        ana.setContentsMargins(0, 0, 0, 0)
        ana.setSpacing(0)
        ana.addWidget(self._ust_cubuk())

        self.takvim = Takvim(self.oturum)
        self.detay = DetayKarti(self.oturum)
        sol = QWidget()
        sol_yerlesim = QVBoxLayout(sol)
        sol_yerlesim.setContentsMargins(0, 0, 0, 0)
        sol_yerlesim.addWidget(self.takvim, 1)
        sol_yerlesim.addWidget(self.detay)

        self.talep_formu = TalepFormu(self.oturum)
        self.takvim.cizim.bos_secildi.connect(self._bos_secildi)
        sag = QTabWidget()
        self.sag = sag
        sag.addTab(self.talep_formu, "Talep")
        sag.addTab(KullaniciPaneli(self.oturum), "Kullanıcı")
        sag.addTab(SaatDenetimi(self.oturum), "Saat")

        bolucu = QSplitter(Qt.Horizontal)
        bolucu.addWidget(sol)
        bolucu.addWidget(sag)
        bolucu.setStretchFactor(0, 3)
        bolucu.setStretchFactor(1, 1)
        bolucu.setSizes([930, 400])
        ana.addWidget(bolucu, 1)
        ana.addWidget(self._alt_gunluk())
        self.setCentralWidget(merkez)

    def _ust_cubuk(self):
        cubuk = QFrame()
        cubuk.setStyleSheet(
            f"QFrame {{ background: {stil.SATIR_ZEMIN_ALT.name()};"
            f" border-bottom: 1px solid {stil.SAAT_CIZGISI.name()}; }}"
        )
        yerlesim = QHBoxLayout(cubuk)
        yerlesim.setContentsMargins(12, 8, 12, 8)

        self.dugme_dosya = QPushButton("Başlangıç dosyası seç…")
        self.dugme_dosya.clicked.connect(self.dosya_sec)
        yerlesim.addWidget(self.dugme_dosya)

        self.etiket_dosya = QLabel("Dosya seçilmedi")
        self.etiket_dosya.setStyleSheet("border: none;")
        yerlesim.addWidget(self.etiket_dosya, 1)

        self.dugme_kullanici = QPushButton("Yeni kullanıcı…")
        self.dugme_kaynak = QPushButton("Yeni kaynak…")
        self.dugme_kullanici.clicked.connect(lambda: self._diyalog(KullaniciEkleDiyalogu))
        self.dugme_kaynak.clicked.connect(lambda: self._diyalog(KaynakEkleDiyalogu))
        yerlesim.addWidget(self.dugme_kullanici)
        yerlesim.addWidget(self.dugme_kaynak)

        baslik = QLabel("Simüle saat")
        baslik.setStyleSheet(f"color: {stil.SOLUK_YAZI.name()}; border: none;")
        self.etiket_saat = QLabel("--")
        yazi = QFont(stil.YAZI_AILESI, stil.YAZI_BOYUTU_BASLIK)
        yazi.setBold(True)
        self.etiket_saat.setFont(yazi)
        self.etiket_saat.setStyleSheet(f"color: {stil.SAAT_IMLECI.name()}; border: none;")
        yerlesim.addWidget(baslik)
        yerlesim.addWidget(self.etiket_saat)
        return cubuk

    def _alt_gunluk(self):
        kutu = QGroupBox("Olay günlüğü")
        kutu.setCheckable(True)  # işaret kaldırılınca katlanır
        kutu.setChecked(True)
        self.gunluk = OlayGunlugu(self.oturum)
        self.gunluk.setMinimumHeight(110)
        self.gunluk.setMaximumHeight(170)
        yerlesim = QVBoxLayout(kutu)
        yerlesim.addWidget(self.gunluk)
        kutu.toggled.connect(self.gunluk.setVisible)
        return kutu

    # --- Dosya ---
    def dosya_sec(self):
        yol, _ = QFileDialog.getOpenFileName(
            self, "Başlangıç dosyasını seç", "", "JSON dosyaları (*.json);;Tüm dosyalar (*)")
        if yol:
            self.dosya_yukle(yol)

    def dosya_yukle(self, yol):
        """Sistemi baştan kurar. Başarısızsa eski durum korunur, hata üst çubukta görünür."""
        try:
            self.oturum.yukle(yol)
        except Exception as hata:
            mesaj = f"Yüklenemedi: {type(hata).__name__}: {hata}"
            self.etiket_dosya.setText(mesaj)
            self.etiket_dosya.setToolTip(mesaj)
            self.etiket_dosya.setStyleSheet(f"color: {stil.HATA_YAZI.name()}; border: none;")
            return
        self.etiket_dosya.setText(os.path.basename(yol))
        self.etiket_dosya.setToolTip(yol)
        self.etiket_dosya.setStyleSheet("border: none;")

    # --- Diğer ---
    def _diyalog(self, sinif):
        if self.oturum.durum is not None:
            sinif(self.oturum, self).exec()

    def _bos_secildi(self, kaynak_id, baslangic):
        self.sag.setCurrentWidget(self.talep_formu)
        self.talep_formu.bos_aralik_onerisi(kaynak_id, baslangic)

    def _saati_goster(self):
        var = self.oturum.durum is not None
        self.dugme_kullanici.setEnabled(var)
        self.dugme_kaynak.setEnabled(var)
        self.etiket_saat.setText(bicim.saat_metni(self.oturum.durum.saat) if var else "--")


def main():
    uygulama = QApplication(sys.argv)
    uygulama.setFont(QFont(stil.YAZI_AILESI, stil.YAZI_BOYUTU))
    pencere = AnaPencere()
    pencere.show()
    if len(sys.argv) > 1:
        pencere.dosya_yukle(sys.argv[1])
    sys.exit(uygulama.exec())


if __name__ == "__main__":
    main()
