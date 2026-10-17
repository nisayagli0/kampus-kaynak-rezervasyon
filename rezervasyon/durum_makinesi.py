"""Durum makinesi (K6, K8): rezervasyonun durum geçişleri.

Her işlev (durum, ...) alır ve Durum nesnesini değiştirir. Komut işlevleri
(giris, cikis, iptal) {"durum": "TAMAM", ...} veya {"durum": "RED", "kod": ...}
döndürür. Zamana bağlı geçişleri (gelmedi, tamamlandi) saat.py çağırır.
"""

from rezervasyon import bekleme, zaman
from rezervasyon.modeller import ONAYLI, KULLANIMDA, TAMAMLANDI, IPTAL, GELMEDI

# K8: giriş penceresi, başlangıca göre dakika (ikisi dahil)
GIRIS_ONCE_DK = 10
GIRIS_SONRA_DK = 15

# K8: iptalde iade eşikleri, başlangıca kalan dakika
TAM_IADE_DK = 24 * 60
YARIM_IADE_DK = 2 * 60

# K8: güvenilirlik değişimleri ve sınırları
GELMEDI_CEZASI = 15
GEC_IPTAL_CEZASI = 5
TAMAMLANMA_ODULU = 2
GUVENILIRLIK_ENAZ = 0
GUVENILIRLIK_ENCOK = 100


def _bul(durum, rezervasyon_id, beklenen_durum):
    """K10 sırası: BULUNAMADI, sonra DURUM_HATASI.

    (rezervasyon, None) veya (None, red_sozlugu) döndürür.
    """
    rezervasyon = durum.rezervasyonlar.get(rezervasyon_id)
    if rezervasyon is None:
        return None, {"durum": "RED", "kod": "BULUNAMADI"}
    if rezervasyon.durum != beklenen_durum:
        return None, {"durum": "RED", "kod": "DURUM_HATASI"}
    return rezervasyon, None


def guvenilirlik_degistir(durum, kullanici_id, fark):
    """K8: güvenilirliği değiştirir, 0-100 arasında tutar, yeni değeri döndürür."""
    kullanici = durum.kullanicilar[kullanici_id]
    yeni = kullanici.guvenilirlik + fark
    kullanici.guvenilirlik = max(GUVENILIRLIK_ENAZ, min(GUVENILIRLIK_ENCOK, yeni))
    return kullanici.guvenilirlik


def iade_et(durum, kullanici_id, miktar):
    """K6: bakiyeye iade ekler; bakiye haftalık kotayı aşmaz.

    Bakiyeye gerçekte eklenen miktarı döndürür (kotayı aşan kısım iade edilmez).
    """
    kullanici = durum.kullanicilar[kullanici_id]
    kota = durum.roller[kullanici.rol].haftalik_kota
    eklenen = max(0, min(miktar, kota - kullanici.bakiye))
    kullanici.bakiye += eklenen
    return eklenen


def giris(durum, rezervasyon_id):
    """K8, K10: ONAYLI -> KULLANIMDA.

    Hata sırası: BULUNAMADI, DURUM_HATASI, GIRIS_PENCERESI_DISI.
    """
    rezervasyon, red = _bul(durum, rezervasyon_id, ONAYLI)
    if red:
        return red

    # Pozitif: başlangıçtan sonra, negatif: başlangıçtan önce
    fark = zaman.dakika_farki(rezervasyon.baslangic, durum.saat)
    if fark < -GIRIS_ONCE_DK or fark > GIRIS_SONRA_DK:
        return {"durum": "RED", "kod": "GIRIS_PENCERESI_DISI"}

    rezervasyon.durum = KULLANIMDA
    return {"durum": "TAMAM", "yeni_durum": KULLANIMDA}


def cikis(durum, rezervasyon_id):
    """K8: KULLANIMDA -> TAMAMLANDI (erken çıkış).

    Bitiş çıkış saati olur, kalan süre serbest kalır. İade yok, güvenilirlik değişmez.
    """
    rezervasyon, red = _bul(durum, rezervasyon_id, KULLANIMDA)
    if red:
        return red

    rezervasyon.durum = TAMAMLANDI
    rezervasyon.bitis = durum.saat
    kullanici = durum.kullanicilar[rezervasyon.kullanici]
    return {
        "durum": "TAMAM",
        "yeni_durum": TAMAMLANDI,
        "guvenilirlik": kullanici.guvenilirlik,
        "olaylar": bekleme.tara(durum, rezervasyon.kaynak),
    }


def iptal(durum, rezervasyon_id):
    """K8: ONAYLI -> IPTAL. İade, iptal anından başlangıca kalan süreye göre.

    24 saat ve üzeri %100; 2 saat ve üzeri, 24 saatten az %50 (aşağı yuvarlanır);
    2 saatten az (başlangıç geçmiş dahil) %0 ve güvenilirlik -5.
    """
    rezervasyon, red = _bul(durum, rezervasyon_id, ONAYLI)
    if red:
        return red

    kalan = zaman.dakika_farki(durum.saat, rezervasyon.baslangic)
    if kalan >= TAM_IADE_DK:
        iade = rezervasyon.ucret
    elif kalan >= YARIM_IADE_DK:
        iade = rezervasyon.ucret // 2
    else:
        iade = 0
        guvenilirlik_degistir(durum, rezervasyon.kullanici, -GEC_IPTAL_CEZASI)

    rezervasyon.durum = IPTAL
    eklenen = iade_et(durum, rezervasyon.kullanici, iade)
    kullanici = durum.kullanicilar[rezervasyon.kullanici]
    return {
        "durum": "TAMAM",
        "iade": eklenen,
        "bakiye": kullanici.bakiye,
        "guvenilirlik": kullanici.guvenilirlik,
        "olaylar": bekleme.tara(durum, rezervasyon.kaynak),
    }


def gelmedi(durum, rezervasyon_id):
    """K8: ONAYLI -> GELMEDI (saat.py çağırır). İade yok, güvenilirlik -15.

    Kullanıcının yeni güvenilirliğini döndürür.
    """
    rezervasyon = durum.rezervasyonlar[rezervasyon_id]
    rezervasyon.durum = GELMEDI
    return guvenilirlik_degistir(durum, rezervasyon.kullanici, -GELMEDI_CEZASI)


def tamamlandi(durum, rezervasyon_id):
    """K8: KULLANIMDA -> TAMAMLANDI, bitiş saatinde (saat.py çağırır). Güvenilirlik +2.

    Kullanıcının yeni güvenilirliğini döndürür.
    """
    rezervasyon = durum.rezervasyonlar[rezervasyon_id]
    rezervasyon.durum = TAMAMLANDI
    return guvenilirlik_degistir(durum, rezervasyon.kullanici, TAMAMLANMA_ODULU)
