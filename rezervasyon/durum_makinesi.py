"""Durum makinesi (K8): giriş, çıkış, iptal, gelmedi işlemleri.

Her işlev (durum, ...) alır, Durum nesnesini değiştirir ve bir sözlük döndürür:
{"durum": "TAMAM", ...} veya {"durum": "RED", "kod": "..."}.
"""

from rezervasyon import zaman
from rezervasyon.modeller import ONAYLI, KULLANIMDA

# K8: giriş penceresi, başlangıca göre dakika (ikisi dahil)
GIRIS_ONCE_DK = 10
GIRIS_SONRA_DK = 15


def giris(durum, rezervasyon_id):
    """K8, K10: ONAYLI -> KULLANIMDA.

    Hata sırası: BULUNAMADI, DURUM_HATASI, GIRIS_PENCERESI_DISI.
    """
    rezervasyon = durum.rezervasyonlar.get(rezervasyon_id)
    if rezervasyon is None:
        return {"durum": "RED", "kod": "BULUNAMADI"}

    if rezervasyon.durum != ONAYLI:
        return {"durum": "RED", "kod": "DURUM_HATASI"}

    # Pozitif: başlangıçtan sonra, negatif: başlangıçtan önce
    fark = zaman.dakika_farki(rezervasyon.baslangic, durum.saat)
    if fark < -GIRIS_ONCE_DK or fark > GIRIS_SONRA_DK:
        return {"durum": "RED", "kod": "GIRIS_PENCERESI_DISI"}

    rezervasyon.durum = KULLANIMDA
    return {"durum": "TAMAM", "yeni_durum": KULLANIMDA}
