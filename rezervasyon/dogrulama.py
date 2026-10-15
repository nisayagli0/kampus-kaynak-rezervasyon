"""Rezervasyon talebinin doğrulanması (K1, K10).

dogrula, K10 sırasıyla ilk başarısız adımın kodunu, talep geçerliyse None döndürür.
Zamanlar datetime'dır; simüle saat durum.saat'ten okunur.
"""

from datetime import timedelta

from rezervasyon import ucret, zaman
from rezervasyon.modeller import ONAYLI, KULLANIMDA, TAMAMLANDI

# GELMEDI ve IPTAL hiçbir kontrolde sayılmaz (K3)
KESISME_DURUMLARI = (ONAYLI, KULLANIMDA)
HAZIRLIK_DURUMLARI = (ONAYLI, KULLANIMDA, TAMAMLANDI)  # K4 için de aynı
ARDISIK_BOSLUK_DK = 60


def dogrula(durum, kullanici_id, kaynak_id, baslangic, bitis, bakiye_kontrolu=True):
    # 1. Kullanıcı veya kaynak yok
    kullanici = durum.kullanicilar.get(kullanici_id)
    kaynak = durum.kaynaklar.get(kaynak_id)
    if kullanici is None or kaynak is None:
        return "BULUNAMADI"

    rol = durum.roller[kullanici.rol]
    tur = durum.turler[kaynak.tur]

    # 2. 15 dk adımı; bitiş başlangıçtan sonra olmalı (eşitlik de hata, varsayım 3)
    if not zaman.adima_uygun_mu(baslangic) or not zaman.adima_uygun_mu(bitis):
        return "ZAMAN_ADIMI_HATASI"
    if bitis <= baslangic:
        return "ZAMAN_ADIMI_HATASI"

    # 3. Başlangıç simüle saatten önce olamaz
    if baslangic < durum.saat:
        return "GECMIS_ZAMAN"

    # 4. Aynı gün içinde 08:00-22:00
    acilis = baslangic.replace(hour=8, minute=0)
    kapanis = baslangic.replace(hour=22, minute=0)
    if baslangic < acilis or bitis > kapanis:
        return "CALISMA_SAATI_DISI"

    # 5. En az 30 dk, en fazla rolün azami süresi
    sure = zaman.dakika_farki(baslangic, bitis)
    if sure < 30 or sure > rol.azami_sure_dk:
        return "SURE_SINIRI"

    # 6. İleri tarih sınırı (güvenilirlik 50'nin altındaysa 1 gün), sınır dahil
    ileri_gun = rol.ileri_gun if kullanici.guvenilirlik >= 50 else 1
    if baslangic > durum.saat + timedelta(days=ileri_gun):
        return "ILERI_TARIH_SINIRI"

    # 7. Rol izni
    if kullanici.rol not in kaynak.izinli_roller:
        return "ROL_IZNI_YOK"

    # 8. Sertifika
    if tur.sertifika is not None and tur.sertifika not in kullanici.sertifikalar:
        return "SERTIFIKA_YOK"

    # 9. Bakım penceresiyle kesişme (bakımdan sonra hazırlık uygulanmaz, K2)
    for bakim in durum.bakimlar:
        if bakim.kaynak == kaynak_id and baslangic < bakim.bitis and bitis > bakim.baslangic:
            return "BAKIM"

    ayni_kaynak = [r for r in durum.rezervasyonlar.values() if r.kaynak == kaynak_id]

    # 10. Rezervasyonla kesişme: b < e' ve e > b'
    for r in ayni_kaynak:
        if r.durum in KESISME_DURUMLARI and baslangic < r.bitis and bitis > r.baslangic:
            return "KESISME"

    # 11. Hazırlık süresi: b < e' + h ve e + h > b'
    h = timedelta(minutes=tur.hazirlik_dk)
    for r in ayni_kaynak:
        if r.durum in HAZIRLIK_DURUMLARI and baslangic < r.bitis + h and bitis + h > r.baslangic:
            return "HAZIRLIK_IHLALI"

    # 12. Aynı kullanıcı, aynı kaynak: en az 60 dk boşluk (K4)
    bosluk = timedelta(minutes=ARDISIK_BOSLUK_DK)
    for r in ayni_kaynak:
        if (
            r.kullanici == kullanici_id
            and r.durum in HAZIRLIK_DURUMLARI
            and baslangic < r.bitis + bosluk
            and bitis + bosluk > r.baslangic
        ):
            return "ARDISIK_KULLANIM"

    # 13. Ücret > bakiye (fiyat ve paket kalemleri için atlanır)
    if bakiye_kontrolu:
        if ucret.hesapla(durum, kaynak_id, baslangic, bitis) > kullanici.bakiye:
            return "BAKIYE_YETERSIZ"

    return None
