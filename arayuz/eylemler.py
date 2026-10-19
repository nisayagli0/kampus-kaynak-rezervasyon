"""Giriş, Çıkış, İptal düğmeleri ve sonuç alanı (doküman Bölüm 7).

Aynı şerit takvimin detay kartında ve kullanıcı panelinde kullanılır.
Sonuç, işlemin yapıldığı şeridin altında görünür. Numara yazılmaz; şerit
seçili rezervasyon üzerinde çalışır.
"""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from arayuz import mesajlar, stil
from rezervasyon import okuma
from rezervasyon.modeller import KULLANIMDA, ONAYLI


class EylemSeridi(QWidget):
    def __init__(self, oturum, parent=None):
        super().__init__(parent)
        self.oturum = oturum
        self._rezervasyon = None

        yerlesim = QVBoxLayout(self)
        yerlesim.setContentsMargins(0, 0, 0, 0)
        yerlesim.setSpacing(4)
        dugmeler = QHBoxLayout()
        self.dugme_giris = QPushButton("Giriş")
        self.dugme_cikis = QPushButton("Çıkış")
        self.dugme_iptal = QPushButton("İptal et")
        for komut, dugme in (("giris", self.dugme_giris), ("cikis", self.dugme_cikis),
                             ("iptal", self.dugme_iptal)):
            dugme.clicked.connect(lambda _=False, k=komut: self._calistir(k))
            dugmeler.addWidget(dugme)
        dugmeler.addStretch(1)
        yerlesim.addLayout(dugmeler)

        self.sonuc = QLabel("")
        self.sonuc.setWordWrap(True)
        yerlesim.addWidget(self.sonuc)
        self.ayarla(None)

    def ayarla(self, rezervasyon_id):
        """Şeridi bir rezervasyona bağlar. Başka rezervasyona geçilince eski sonuç silinir."""
        if rezervasyon_id != self._rezervasyon:
            self.sonuc.setText("")
        self._rezervasyon = rezervasyon_id
        r = okuma.rezervasyon(self.oturum.durum, rezervasyon_id) if (
            self.oturum.durum and rezervasyon_id) else None
        # Düğme etkinliği yalnızca gösterim kolaylığıdır; asıl denetimi modül yapar.
        self.dugme_giris.setEnabled(r is not None and r.durum == ONAYLI)
        self.dugme_cikis.setEnabled(r is not None and r.durum == KULLANIMDA)
        self.dugme_iptal.setEnabled(r is not None and r.durum == ONAYLI)

    def _calistir(self, komut):
        if not self._rezervasyon:
            return
        sonuc = self.oturum.komut(komut, rezervasyon=self._rezervasyon)
        renk = stil.BASARI_YAZI if sonuc["durum"] == "TAMAM" else stil.HATA_YAZI
        self.sonuc.setStyleSheet(f"color: {renk.name()};")
        self.sonuc.setText(mesajlar.eylem_ozeti(komut, sonuc))
