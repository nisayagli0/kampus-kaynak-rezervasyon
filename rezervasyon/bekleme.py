"""Bekleme listesi (K9).

ac: dolu bir aralık için bekleme kaydı açar.
tara: boşalan kaynağın kayıtlarını sırayla dener, geçen kaydı rezervasyona çevirir.
gecmisleri_sil: başlangıcı simüle saatten önceye düşen kayıtları siler.
Zamanlar datetime'dır; "o anki saat" durum.saat'tir.
"""

from rezervasyon import talep, zaman
from rezervasyon.dogrulama import dogrula
from rezervasyon.modeller import BeklemeKaydi

# K9: yalnızca başka bir rezervasyon nedeniyle reddedilen talep için kayıt açılır
BEKLEMEYE_UYGUN_KODLAR = ("KESISME", "HAZIRLIK_IHLALI")


def _sirali(durum, kaynak_id):
    """K9: kaynağın bekleme kayıtları, tarama sırasıyla.

    Güvenilirliği yüksek olan önce gelir; eşitse önce kaydolan; o da eşitse
    numarası sayısal olarak küçük olan (b2 önce, b10 sonra).
    """
    kayitlar = [k for k in durum.beklemeler.values() if k.kaynak == kaynak_id]
    return sorted(
        kayitlar,
        key=lambda k: (
            -durum.kullanicilar[k.kullanici].guvenilirlik,
            k.kayit_saati,
            int(k.id[1:]),
        ),
    )


def ac(durum, kullanici_id, kaynak_id, baslangic, bitis):
    """K9: bekleme kaydı açar. Bakiye kontrol edilmez.

    Talep başka bir nedenle geçersizse o hata kodu, zaten geçerliyse
    BEKLEME_GEREKSIZ döner. Numara yalnızca kayıt açılınca tüketilir.
    """
    kod = dogrula(
        durum, kullanici_id, kaynak_id, baslangic, bitis, bakiye_kontrolu=False
    )
    if kod is None:
        return {"durum": "RED", "kod": "BEKLEME_GEREKSIZ"}
    if kod not in BEKLEMEYE_UYGUN_KODLAR:
        return {"durum": "RED", "kod": kod}

    no = durum.yeni_bekleme_no()
    kayit = BeklemeKaydi(no, kullanici_id, kaynak_id, baslangic, bitis, durum.saat)
    durum.beklemeler[no] = kayit
    sira = (
        _sirali(durum, kaynak_id).index(kayit) + 1
    )  # tarama sırasındaki yeri, 1'den başlar
    return {"durum": "TAMAM", "bekleme_id": no, "sira": sira}


def tara(durum, kaynak_id):
    """K9: boşalan kaynağın kayıtlarını sırayla dener, OTOMATIK_ATAMA olaylarını döndürür.

    Her kayıt o anki saat ve bakiyeyle K10'daki tüm kontrollerden geçer. Geçen
    kayıt rezervasyona dönüşür ve listeden çıkar; geçemeyen listede kalır. Tarama
    listenin sonuna kadar sürer.
    """
    olaylar = []
    for kayit in _sirali(durum, kaynak_id):
        if dogrula(durum, kayit.kullanici, kayit.kaynak, kayit.baslangic, kayit.bitis):
            continue

        rezervasyon = talep.rezervasyon_olustur(
            durum, kayit.kullanici, kayit.kaynak, kayit.baslangic, kayit.bitis
        )
        del durum.beklemeler[kayit.id]
        olaylar.append(
            {
                "zaman": zaman.bicimle(durum.saat),
                "tur": "OTOMATIK_ATAMA",
                "bekleme": kayit.id,
                "rezervasyon": rezervasyon.id,
                "kullanici": kayit.kullanici,
                "ucret": rezervasyon.ucret,
                "bakiye": durum.kullanicilar[kayit.kullanici].bakiye,
            }
        )
    return olaylar


def gecmisleri_sil(durum):
    """K9: başlangıcı simüle saatten önceye düşen bekleme kayıtlarını siler."""
    silinecek = [no for no, k in durum.beklemeler.items() if k.baslangic < durum.saat]
    for no in silinecek:
        del durum.beklemeler[no]
