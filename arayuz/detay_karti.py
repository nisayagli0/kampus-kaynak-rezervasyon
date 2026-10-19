"""Takvimde seçilen rezervasyonun detay kartı (doküman Bölüm 7).

Kartta rezervasyonun bilgileri ve Giriş / Çıkış / İptal düğmeleri durur.
İşlemin sonucu (iade, bakiye, güvenilirlik, otomatik atamalar) aynı kartta görünür.
"""

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from arayuz import bicim, stil
from arayuz.eylemler import EylemSeridi
from rezervasyon import okuma


class DetayKarti(QFrame):
    def __init__(self, oturum, parent=None):
        super().__init__(parent)
        self.oturum = oturum
        self.setFrameShape(QFrame.StyledPanel)
        yerlesim = QVBoxLayout(self)
        yerlesim.setContentsMargins(10, 8, 10, 8)
        yerlesim.setSpacing(4)
        self.baslik = QLabel("")
        self.baslik.setStyleSheet("font-weight: bold;")
        self.bilgi = QLabel("")
        self.bilgi.setWordWrap(True)
        self.eylemler = EylemSeridi(oturum)
        yerlesim.addWidget(self.baslik)
        yerlesim.addWidget(self.bilgi)
        yerlesim.addWidget(self.eylemler)
        oturum.veri_degisti.connect(self.yenile)
        oturum.secim_degisti.connect(self.yenile)
        self.yenile()

    def yenile(self):
        durum, rid = self.oturum.durum, self.oturum.secili_rezervasyon
        r = okuma.rezervasyon(durum, rid) if (durum and rid) else None
        self.eylemler.ayarla(r.id if r else None)
        if r is None:
            self.baslik.setText("Rezervasyon ayrıntısı")
            self.bilgi.setStyleSheet(f"color: {stil.SOLUK_YAZI.name()};")
            self.bilgi.setText("Takvimde bir rezervasyon kutusuna tıklayın.")
            return
        kullanici = durum.kullanicilar[r.kullanici]
        kaynak = durum.kaynaklar[r.kaynak]
        self.baslik.setText(f"{kaynak.ad} · {stil.durum_etiketi(r.durum)}")
        self.bilgi.setStyleSheet("")
        paket = f" · Paket: {r.paket}" if getattr(r, "paket", None) else ""
        self.bilgi.setText(
            f"{kullanici.ad} ({kullanici.id}) · {bicim.aralik(r.baslangic, r.bitis)} · "
            f"Ücret: {r.ucret} KP{paket} · Kayıt: {r.id}")
