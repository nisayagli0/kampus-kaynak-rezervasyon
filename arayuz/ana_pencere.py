"""Ana pencere iskeleti: başlangıç dosyası seçimi, simüle saat, boş paneller.

Arayüzde iş kuralı yoktur. Her değer rezervasyon modülünden okunur
(doküman Bölüm 7). Çalıştırma (proje kökünden): python -m arayuz.ana_pencere
"""

import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from arayuz import stil
from rezervasyon import okuma
from rezervasyon.sistem import RezervasyonSistemi

HAFTA_GUNLERI = [
    "Pazartesi",
    "Salı",
    "Çarşamba",
    "Perşembe",
    "Cuma",
    "Cumartesi",
    "Pazar",
]


def saat_metni(dt):
    """datetime -> '08.03.2027 Pazartesi 08:00' (yalnızca gösterim)."""
    return f"{dt.strftime('%d.%m.%Y')} {HAFTA_GUNLERI[dt.weekday()]} {dt.strftime('%H:%M')}"


def yer_tutucu(metin):
    """Henüz yazılmamış bir panelin yerinde duran açıklama etiketi."""
    etiket = QLabel(metin)
    etiket.setAlignment(Qt.AlignCenter)
    etiket.setFrameShape(QFrame.StyledPanel)
    etiket.setStyleSheet(
        f"color: {stil.SOLUK_YAZI.name()}; background: {stil.ZEMIN.name()};"
    )
    return etiket


class AnaPencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kampüs Kaynak Rezervasyon")
        self.resize(1280, 760)
        self.sistem = None  # RezervasyonSistemi; dosya yüklenince kurulur
        self._arayuzu_kur()
        self._saati_goster()

    # --- Yerleşim ---
    def _arayuzu_kur(self):
        merkez = QWidget()
        ana = QVBoxLayout(merkez)
        ana.setContentsMargins(0, 0, 0, 0)
        ana.setSpacing(0)
        ana.addWidget(self._ust_cubuk())

        # Orta: takvim (geniş) | sağ panel (sekmeli)
        bolucu = QSplitter(Qt.Horizontal)
        bolucu.addWidget(yer_tutucu("Kaynak takvimi\n(Gün 2'de gelecek)"))
        sag = QTabWidget()
        sag.addTab(yer_tutucu("Kullanıcı seçici ve panel\n(Gün 5)"), "Kullanıcı paneli")
        sag.addTab(yer_tutucu("Talep formu\n(Gün 4)"), "Talep formu")
        bolucu.addWidget(sag)
        bolucu.setStretchFactor(0, 3)
        bolucu.setStretchFactor(1, 1)
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

        # Gün 2: gün seçici, Gün 6: saat ilerletme düğmeleri buraya gelecek.

        baslik = QLabel("Simüle saat")
        baslik.setStyleSheet(f"color: {stil.SOLUK_YAZI.name()}; border: none;")
        self.etiket_saat = QLabel("--")
        yazi = QFont(stil.YAZI_AILESI, stil.YAZI_BOYUTU_BASLIK)
        yazi.setBold(True)
        self.etiket_saat.setFont(yazi)
        self.etiket_saat.setStyleSheet(
            f"color: {stil.SAAT_IMLECI.name()}; border: none;"
        )
        yerlesim.addWidget(baslik)
        yerlesim.addWidget(self.etiket_saat)
        return cubuk

    def _alt_gunluk(self):
        kutu = QGroupBox("Olay günlüğü")
        kutu.setCheckable(True)  # işaret kaldırılınca katlanır
        kutu.setChecked(True)
        icerik = yer_tutucu("Oturumdaki tüm işlemler burada listelenecek (Gün 6)")
        icerik.setMinimumHeight(90)
        yerlesim = QVBoxLayout(kutu)
        yerlesim.addWidget(icerik)
        kutu.toggled.connect(icerik.setVisible)
        return kutu

    # --- Dosya ---
    def dosya_sec(self):
        yol, _ = QFileDialog.getOpenFileName(
            self,
            "Başlangıç dosyasını seç",
            "",
            "JSON dosyaları (*.json);;Tüm dosyalar (*)",
        )
        if yol:
            self.dosya_yukle(yol)

    def dosya_yukle(self, yol):
        """Modülden sistemi kurar. Başarısızsa eski durum korunur, hata üst çubukta görünür."""
        try:
            yeni = RezervasyonSistemi.dosyadan(yol)
        except Exception as hata:
            mesaj = f"Yüklenemedi: {type(hata).__name__}: {hata}"
            self.etiket_dosya.setText(mesaj)
            self.etiket_dosya.setToolTip(mesaj)
            self.etiket_dosya.setStyleSheet(
                f"color: {stil.SAAT_IMLECI.name()}; border: none;"
            )
            return
        self.sistem = yeni
        self.etiket_dosya.setText(os.path.basename(yol))
        self.etiket_dosya.setToolTip(yol)
        self.etiket_dosya.setStyleSheet("border: none;")
        self._saati_goster()

    def _saati_goster(self):
        if self.sistem is None:
            self.etiket_saat.setText("--")
        else:
            self.etiket_saat.setText(saat_metni(okuma.simule_saat(self.sistem.durum)))


def main():
    uygulama = QApplication(sys.argv)
    uygulama.setFont(QFont(stil.YAZI_AILESI, stil.YAZI_BOYUTU))
    pencere = AnaPencere()
    pencere.show()
    sys.exit(uygulama.exec())


if __name__ == "__main__":
    main()
