"""Saat ilerletme ve olay üretimi (K11).

ilerlet, simüle saati ileri alır. Eski saatten sonraki ve yeni saate kadar olan
tüm olaylar zaman sırasıyla işlenir ve raporlanır; tam yeni saatteki olay dahildir.
"""

from datetime import timedelta

from rezervasyon import bekleme, durum_makinesi, zaman
from rezervasyon.modeller import ONAYLI, KULLANIMDA

# K8: başlangıçtan bu kadar sonra giriş yapılmamışsa rezervasyon GELMEDI olur
GELMEDI_SURESI = timedelta(minutes=durum_makinesi.GIRIS_SONRA_DK)


def _rezervasyon_no(rezervasyon):
    """Numaraya göre sıralama için sayısal kısım (r2 önce, r10 sonra)."""
    return int(rezervasyon.id[1:])


def _sonraki_olay_zamani(durum, sonra, yeni, sifirlamalar):
    """(sonra, yeni] aralığındaki en erken olay zamanı; olay yoksa None.

    Olaylar her seferinde güncel durumdan türetilir: bekleme taramasıyla oluşan
    yeni bir rezervasyonun GELMEDI olayı da aynı komutun içinde yakalanır.
    """
    adaylar = list(sifirlamalar)
    for r in durum.rezervasyonlar.values():
        if r.durum == KULLANIMDA:
            adaylar.append(r.bitis)
        elif r.durum == ONAYLI:
            adaylar.append(r.baslangic + GELMEDI_SURESI)
    adaylar = [t for t in adaylar if sonra < t <= yeni]
    return min(adaylar) if adaylar else None


def _an_olaylari(durum, an, sifirlamalar):
    """K11: tek bir andaki olayları belirlenen sırayla işler ve raporlar.

    Sıra: 1. HAFTALIK_SIFIRLAMA, 2. tüm TAMAMLANDI (numara artan),
    3. tüm GELMEDI (numara artan), 4. boşalan her kaynak için bekleme taraması
    (OTOMATIK_ATAMA), gelmeme olaylarının sırasıyla.
    """
    olaylar = []
    an_metni = zaman.bicimle(an)

    if an in sifirlamalar:
        for kullanici in durum.kullanicilar.values():
            kullanici.bakiye = durum.roller[kullanici.rol].haftalik_kota
        olaylar.append({"zaman": an_metni, "tur": "HAFTALIK_SIFIRLAMA"})

    tamamlananlar = [
        r
        for r in durum.rezervasyonlar.values()
        if r.durum == KULLANIMDA and r.bitis == an
    ]
    for r in sorted(tamamlananlar, key=_rezervasyon_no):
        guvenilirlik = durum_makinesi.tamamlandi(durum, r.id)
        olaylar.append(
            {
                "zaman": an_metni,
                "tur": "TAMAMLANDI",
                "rezervasyon": r.id,
                "kullanici": r.kullanici,
                "guvenilirlik": guvenilirlik,
            }
        )

    gelmeyenler = [
        r
        for r in durum.rezervasyonlar.values()
        if r.durum == ONAYLI and r.baslangic + GELMEDI_SURESI == an
    ]
    bosalan_kaynaklar = []
    for r in sorted(gelmeyenler, key=_rezervasyon_no):
        guvenilirlik = durum_makinesi.gelmedi(durum, r.id)
        olaylar.append(
            {
                "zaman": an_metni,
                "tur": "GELMEDI",
                "rezervasyon": r.id,
                "kullanici": r.kullanici,
                "guvenilirlik": guvenilirlik,
            }
        )
        bosalan_kaynaklar.append(r.kaynak)

    for kaynak_id in dict.fromkeys(bosalan_kaynaklar):  # tekrarsız, sıra korunur
        olaylar.extend(bekleme.tara(durum, kaynak_id))

    return olaylar


def ilerlet(durum, yeni):
    """K11: saati yeni değere ilerletir, oluşan olayların listesini döndürür.

    Yeni saat mevcut saatten önceyse SAAT_GERI döner ve durum değişmez.
    """
    eski = durum.saat
    if yeni < eski:
        return {"durum": "RED", "kod": "SAAT_GERI"}

    sifirlamalar = zaman.pazartesi_sifirlamalari(eski, yeni)
    olaylar = []
    sonra = eski
    while True:
        an = _sonraki_olay_zamani(durum, sonra, yeni, sifirlamalar)
        if an is None:
            break
        durum.saat = an  # olay işlenirken "şimdi" olayın kendi zamanıdır
        olaylar.extend(_an_olaylari(durum, an, sifirlamalar))
        sonra = an

    durum.saat = yeni
    bekleme.gecmisleri_sil(durum)
    return {"durum": "TAMAM", "olaylar": olaylar}
