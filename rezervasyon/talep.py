"""Tek rezervasyon talebi ve fiyat sorgusu (K5, K6, K10).

Zamanlar datetime'dır. Metinden çevirme sistem.py'de yapılır.
"""

from rezervasyon import ucret
from rezervasyon.dogrulama import dogrula
from rezervasyon.modeller import Rezervasyon


def rezervasyon_olustur(
    durum, kullanici_id, kaynak_id, baslangic, bitis, paket_id=None, ucret_degeri=None
):
    """Ücreti hesaplar, bakiyeden düşer, rezervasyonu kaydeder.

    Doğrulamanın önceden yapıldığını varsayar. Numara burada, yani yalnızca
    başarılı talepte tüketilir. Paket, ücretleri paket öncesi durumdan
    hesaplayıp ucret_degeri ile verir (kalemler birbirinin doluluğuna katılmaz).
    """
    if ucret_degeri is None:
        fiyat_ = ucret.hesapla(durum, kaynak_id, baslangic, bitis)
    else:
        fiyat_ = ucret_degeri
    durum.kullanicilar[kullanici_id].bakiye -= fiyat_

    no = durum.yeni_rezervasyon_no()
    rez = Rezervasyon(
        id=no,
        kullanici=kullanici_id,
        kaynak=kaynak_id,
        baslangic=baslangic,
        bitis=bitis,
        ucret=fiyat_,
        paket=paket_id,
    )
    durum.rezervasyonlar[no] = rez
    return rez


def rezervasyon(durum, kullanici_id, kaynak_id, baslangic, bitis):
    """rezervasyon komutu: doğrula -> ücret -> bakiyeden düş -> kaydet."""
    kod = dogrula(durum, kullanici_id, kaynak_id, baslangic, bitis)
    if kod:
        return {"durum": "RED", "kod": kod}

    rez = rezervasyon_olustur(durum, kullanici_id, kaynak_id, baslangic, bitis)
    return {
        "durum": "TAMAM",
        "rezervasyon_id": rez.id,
        "ucret": rez.ucret,
        "bakiye": durum.kullanicilar[kullanici_id].bakiye,
    }


def fiyat(durum, kullanici_id, kaynak_id, baslangic, bitis):
    """fiyat komutu: bakiye dışındaki tüm kontroller; durumu değiştirmez."""
    kod = dogrula(durum, kullanici_id, kaynak_id, baslangic, bitis, bakiye_kontrolu=False)
    if kod:
        return {"durum": "RED", "kod": kod}
    return {"durum": "TAMAM", "ucret": ucret.hesapla(durum, kaynak_id, baslangic, bitis)}
