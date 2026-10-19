"""Arayüzün görünüm sabitleri: renkler, desenler, etiketler, yazı tipleri.

Arayüzde renk veya yazı tipi başka dosyada yazılmaz; hepsi buradan okunur.
Her durum renge ek olarak desen ve yazı etiketiyle de ayırt edilir.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from rezervasyon.modeller import ONAYLI, KULLANIMDA, TAMAMLANDI, IPTAL, GELMEDI

# Her durum: (dolgu rengi, çizgi rengi, desen, kısa etiket)
DURUM_STIL = {
    ONAYLI: (QColor("#4a90d9"), QColor("#2c5f99"), Qt.SolidPattern, "Onaylı"),
    KULLANIMDA: (QColor("#4caf6a"), QColor("#2e7d46"), Qt.SolidPattern, "Kullanımda"),
    TAMAMLANDI: (QColor("#b0bec5"), QColor("#78909c"), Qt.SolidPattern, "Tamamlandı"),
    IPTAL: (QColor("#e57373"), QColor("#b71c1c"), Qt.BDiagPattern, "İptal"),
    GELMEDI: (QColor("#ffb74d"), QColor("#e65100"), Qt.FDiagPattern, "Gelmedi"),
}

# Bakım penceresi: koyu gri, çapraz ızgara
BAKIM_DOLGU = QColor("#757575")
BAKIM_CIZGI = QColor("#424242")
BAKIM_DESEN = Qt.DiagCrossPattern
BAKIM_ETIKET = "Bakım"

# Hazırlık süresi: çok soluk, rezervasyonun hemen yanında
HAZIRLIK_DOLGU = QColor("#fff3c4")
HAZIRLIK_CIZGI = QColor("#e0c060")
HAZIRLIK_ETIKET = "Hazırlık"

# Takvim zemini
ZEMIN = QColor("#ffffff")
SATIR_ZEMIN_ALT = QColor("#f6f8fa")  # çift satırlar için hafif ton
SAAT_CIZGISI = QColor("#b0b7c0")  # belirgin saat çizgileri
CEYREK_CIZGISI = QColor("#e4e8ec")  # soluk 15 dakikalık çizgiler
YAZI_RENGI = QColor("#1f2933")
SOLUK_YAZI = QColor("#6b7785")

# Simüle saat çizgisi
SAAT_IMLECI = QColor("#c62828")
SAAT_IMLECI_KALINLIK = 2

# Sonuç mesajları
BASARI_YAZI = QColor("#1b6e3a")
HATA_YAZI = QColor("#b71c1c")

# Yazı tipi
YAZI_AILESI = "Segoe UI"
YAZI_BOYUTU = 10
YAZI_BOYUTU_KUCUK = 8
YAZI_BOYUTU_BASLIK = 12


def durum_etiketi(durum):
    """Durum sabitinin ekranda görünen Türkçe adı."""
    return DURUM_STIL[durum][3]
