"""Okuma işlevleri: arayüzün Durum nesnesinden okuduğu değerler.

Bu işlevler durumu değiştirmez. Hiçbir rol, tür, sertifika veya sayı kodda
sabit değildir; hepsi başlangıç dosyasından kurulan Durum'dan gelir.
"""

from datetime import datetime, timedelta

from rezervasyon.modeller import ONAYLI, KULLANIMDA, TAMAMLANDI

# Hazırlık süresi yalnızca bu durumlardaki rezervasyonların ardından sayılır (K3)
HAZIRLIGI_OLAN_DURUMLAR = (ONAYLI, KULLANIMDA, TAMAMLANDI)


def simule_saat(durum):
    """Simüle saat (datetime)."""
    return durum.saat


def roller(durum):
    """Başlangıç dosyasındaki rol adları, dosyadaki sırayla."""
    return list(durum.roller)


def rol(durum, ad):
    """Tek rol (haftalik_kota, ileri_gun, azami_sure_dk alanlarıyla)."""
    return durum.roller[ad]


def turler(durum):
    """Başlangıç dosyasındaki kaynak türü adları, dosyadaki sırayla."""
    return list(durum.turler)


def sertifikalar(durum):
    """Türlerin gerektirdiği ve kullanıcıların sahip olduğu sertifikaların birleşimi."""
    bulunanlar = set()
    for tur in durum.turler.values():
        if tur.sertifika:  # None (JSON'daki null) atlanır
            bulunanlar.add(tur.sertifika)
    for kullanici in durum.kullanicilar.values():
        bulunanlar.update(kullanici.sertifikalar)
    return sorted(bulunanlar)


def kullanicilar(durum):
    """Kullanıcı listesi (ekleme sırasıyla)."""
    return list(durum.kullanicilar.values())


def kaynaklar(durum):
    """Kaynak listesi (ekleme sırasıyla)."""
    return list(durum.kaynaklar.values())


# --- Takvim ve paneller için ---

def _numara(kayit):
    """'r10' -> 10: numaraya göre sıralamada r2, r10'dan önce gelir."""
    return int(kayit.id[1:])


def _gun_araligi(gun):
    """date -> (gün başı, ertesi gün başı) datetime çifti."""
    bas = datetime(gun.year, gun.month, gun.day)
    return bas, bas + timedelta(days=1)


def rezervasyon(durum, rezervasyon_id):
    """Tek rezervasyon (her durumda) veya yoksa None."""
    return durum.rezervasyonlar.get(rezervasyon_id)


def rezervasyonlar_gun(durum, gun):
    """Verilen günle kesişen tüm rezervasyonlar (IPTAL ve GELMEDI dahil), başlangıca göre sıralı.

    Takvim iptal ve gelmeyen kutularını da gösterir; hangilerinin doluluğa
    sayıldığını okuma değil modül belirler.
    """
    bas, son = _gun_araligi(gun)
    secilen = [r for r in durum.rezervasyonlar.values() if r.baslangic < son and r.bitis > bas]
    return sorted(secilen, key=lambda r: (r.baslangic, _numara(r)))


def bakimlar_gun(durum, gun):
    """Verilen günle kesişen bakım pencereleri, başlangıca göre sıralı."""
    bas, son = _gun_araligi(gun)
    secilen = [b for b in durum.bakimlar if b.baslangic < son and b.bitis > bas]
    return sorted(secilen, key=lambda b: (b.baslangic, b.kaynak))


def hazirlik_araliklari_gun(durum, gun):
    """Hazırlık süreleri: [(kaynak_id, rezervasyon_id, baslangic, bitis)].

    Süre, rezervasyonun bitişinden başlar ve türün hazirlik_dk değeri kadar sürer.
    Yalnızca ONAYLI, KULLANIMDA ve TAMAMLANDI rezervasyonlar için hesaplanır.
    """
    bas, son = _gun_araligi(gun)
    sonuc = []
    for r in durum.rezervasyonlar.values():
        if r.durum not in HAZIRLIGI_OLAN_DURUMLAR:
            continue
        hazirlik = durum.turler[durum.kaynaklar[r.kaynak].tur].hazirlik_dk
        if hazirlik <= 0:
            continue
        h_bitis = r.bitis + timedelta(minutes=hazirlik)
        if r.bitis < son and h_bitis > bas:
            sonuc.append((r.kaynak, r.id, r.bitis, h_bitis))
    return sorted(sonuc, key=lambda h: (h[2], h[1]))


def bekleme_kayitlari(durum, kullanici=None):
    """Bekleme kayıtları (kayıt numarasına göre); kullanici verilirse yalnız onunkiler."""
    kayitlar = [k for k in durum.beklemeler.values() if kullanici is None or k.kullanici == kullanici]
    return sorted(kayitlar, key=_numara)


def kullanici_rezervasyonlari(durum, kullanici_id):
    """Kullanıcının tüm rezervasyonları, başlangıca göre, eşitlikte numaraya göre."""
    kendi = [r for r in durum.rezervasyonlar.values() if r.kullanici == kullanici_id]
    return sorted(kendi, key=lambda r: (r.baslangic, _numara(r)))


def kullanici_ozeti(durum, kullanici_id):
    """Kullanıcı paneli için özet sözlüğü veya kullanıcı yoksa None."""
    k = durum.kullanicilar.get(kullanici_id)
    if k is None:
        return None
    return {
        "id": k.id,
        "ad": k.ad,
        "rol": k.rol,
        "sertifikalar": list(k.sertifikalar),
        "bakiye": k.bakiye,
        "guvenilirlik": k.guvenilirlik,
        "haftalik_kota": durum.roller[k.rol].haftalik_kota,
    }
