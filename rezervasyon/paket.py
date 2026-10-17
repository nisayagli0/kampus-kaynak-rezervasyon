"""Paket rezervasyon (K7).

2-4 kalem tek talepte istenir; ya hepsi alınır ya hiçbiri. Doğrulama ve ücret
paket öncesi duruma göre yapılır. Kalemlerde zamanlar datetime'dır.
"""

from datetime import timedelta

from rezervasyon import talep, ucret
from rezervasyon.dogrulama import ARDISIK_BOSLUK_DK, dogrula

EN_AZ_KALEM = 2
EN_FAZLA_KALEM = 4
GUVENILIRLIK_SINIRI = 50


def _red(kod, kalemler):
    return {"durum": "RED", "kod": kod, "kalemler": kalemler}


def _araliklar_cakisir(a, b, bosluk):
    """a ile b arasında 'bosluk'tan az mesafe var mı (kesişme dahil)?"""
    return a["baslangic"] < b["bitis"] + bosluk and a["bitis"] + bosluk > b["baslangic"]


def _paket_ici_kesisme_var_mi(durum, kalemler):
    """Aynı kaynaktaki kalemler kesişiyor, hazırlık veya art arda kullanım ihlali var mı?"""
    for i, a in enumerate(kalemler):
        for b in kalemler[i + 1:]:
            if a["kaynak"] != b["kaynak"]:
                continue
            tur = durum.turler[durum.kaynaklar[a["kaynak"]].tur]
            hazirlik = timedelta(minutes=tur.hazirlik_dk)
            ardisik = timedelta(minutes=ARDISIK_BOSLUK_DK)  # kalemlerin kullanıcısı aynı
            if (
                _araliklar_cakisir(a, b, timedelta(0))
                or _araliklar_cakisir(a, b, hazirlik)
                or _araliklar_cakisir(a, b, ardisik)
            ):
                return True
    return False


def paket(durum, kullanici_id, kalemler):
    """kalemler: [{"kaynak": id, "baslangic": datetime, "bitis": datetime}, ...]"""
    # 1. Kullanıcı yok
    kullanici = durum.kullanicilar.get(kullanici_id)
    if kullanici is None:
        return _red("BULUNAMADI", [])

    # 2. Kalem sayısı
    if not EN_AZ_KALEM <= len(kalemler) <= EN_FAZLA_KALEM:
        return _red("PAKET_BOYUTU", [])

    # 3. Güvenilirlik
    if kullanici.guvenilirlik < GUVENILIRLIK_SINIRI:
        return _red("GUVENILIRLIK_DUSUK", [])

    # 4. Her kalem bakiye hariç ayrı ayrı doğrulanır (paket öncesi duruma göre)
    sonuclar = []
    for sira, k in enumerate(kalemler):
        kod = dogrula(durum, kullanici_id, k["kaynak"], k["baslangic"], k["bitis"],
                      bakiye_kontrolu=False)
        if kod:
            sonuclar.append({"sira": sira, "durum": "RED", "kod": kod})
        else:
            sonuclar.append({"sira": sira, "durum": "TAMAM"})
    if any(s["durum"] == "RED" for s in sonuclar):
        return _red("PAKET_RED", sonuclar)

    # 5. Paket içi kesişme
    if _paket_ici_kesisme_var_mi(durum, kalemler):
        return _red("PAKET_ICI_KESISME", sonuclar)

    # 6. Toplam ücret (hepsi paket öncesi durumdan hesaplanır)
    ucretler = [ucret.hesapla(durum, k["kaynak"], k["baslangic"], k["bitis"]) for k in kalemler]
    toplam = sum(ucretler)
    if toplam > kullanici.bakiye:
        return _red("BAKIYE_YETERSIZ", sonuclar)

    # Başarılı: numaralar şimdi tüketilir
    paket_id = durum.yeni_paket_no()
    rezervasyonlar = []
    for k, u in zip(kalemler, ucretler):
        rez = talep.rezervasyon_olustur(
            durum, kullanici_id, k["kaynak"], k["baslangic"], k["bitis"],
            paket_id=paket_id, ucret_degeri=u,
        )
        rezervasyonlar.append(rez.id)

    return {
        "durum": "TAMAM",
        "paket_id": paket_id,
        "rezervasyonlar": rezervasyonlar,
        "ucretler": ucretler,
        "toplam": toplam,
        "bakiye": kullanici.bakiye,
    }
