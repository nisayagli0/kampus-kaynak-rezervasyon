"""Başlangıç dosyasını (baslangic.json) okuyup Durum nesnesini kurar.

Hiçbir rol, tür veya sayı burada sabit yazılmaz; hepsi dosyadan gelir.
Sözlükler dosyadaki sırayı korur.
"""

import json

from rezervasyon import zaman
from rezervasyon.modeller import (
    BakimPenceresi,
    Durum,
    Kaynak,
    KaynakTuru,
    Kullanici,
    Rol,
)


def yukle(yol):
    """Başlangıç dosyasını okur, Durum döndürür."""
    with open(yol, encoding="utf-8") as f:
        veri = json.load(f)

    durum = Durum(saat=zaman.ayristir(veri["saat"]))

    for ad, t in veri["kaynak_turleri"].items():
        durum.turler[ad] = KaynakTuru(
            ad=ad,
            hazirlik_dk=t["hazirlik_dk"],
            temel_ucret=t["temel_ucret"],
            enerji_yogun=t["enerji_yogun"],
            sertifika=t.get("sertifika"),  # null -> None
        )

    for ad, r in veri["roller"].items():
        durum.roller[ad] = Rol(
            ad=ad,
            haftalik_kota=r["haftalik_kota"],
            ileri_gun=r["ileri_gun"],
            azami_sure_dk=r["azami_sure_dk"],
        )

    for k in veri["kaynaklar"]:
        durum.kaynaklar[k["id"]] = Kaynak(
            id=k["id"],
            ad=k["ad"],
            tur=k["tur"],
            izinli_roller=list(k["izinli_roller"]),
        )

    for b in veri["bakim_pencereleri"]:
        durum.bakimlar.append(
            BakimPenceresi(
                kaynak=b["kaynak"],
                baslangic=zaman.ayristir(b["baslangic"]),
                bitis=zaman.ayristir(b["bitis"]),
            )
        )

    for u in veri["kullanicilar"]:
        durum.kullanicilar[u["id"]] = Kullanici(
            id=u["id"],
            ad=u["ad"],
            rol=u["rol"],
            sertifikalar=list(u["sertifikalar"]),
            bakiye=u["bakiye"],
            guvenilirlik=u["guvenilirlik"],
        )

    return durum


# --- Ekleme komutları (K10 ekleme sırası) ---


def _tam_sayi_mi(deger):
    """True/False da Python'da int sayıldığı için ayrıca dışlanır."""
    return isinstance(deger, int) and not isinstance(deger, bool)


def kullanici_ekle(durum, id, ad, rol, sertifikalar, bakiye, guvenilirlik):
    """Sıra: ID_MEVCUT, TANIMSIZ_DEGER, GECERSIZ_DEGER."""
    if id in durum.kullanicilar:
        return {"durum": "RED", "kod": "ID_MEVCUT"}

    if rol not in durum.roller:
        return {"durum": "RED", "kod": "TANIMSIZ_DEGER"}

    kota = durum.roller[rol].haftalik_kota
    if not _tam_sayi_mi(bakiye) or bakiye < 0 or bakiye > kota:
        return {"durum": "RED", "kod": "GECERSIZ_DEGER"}
    if not _tam_sayi_mi(guvenilirlik) or not 0 <= guvenilirlik <= 100:
        return {"durum": "RED", "kod": "GECERSIZ_DEGER"}

    durum.kullanicilar[id] = Kullanici(
        id=id,
        ad=ad,
        rol=rol,
        sertifikalar=list(sertifikalar),
        bakiye=bakiye,
        guvenilirlik=guvenilirlik,
    )
    return {"durum": "TAMAM"}


def kaynak_ekle(durum, id, ad, tur, izinli_roller):
    """Sıra: ID_MEVCUT, TANIMSIZ_DEGER. GECERSIZ_DEGER burada denetlenmez."""
    if id in durum.kaynaklar:
        return {"durum": "RED", "kod": "ID_MEVCUT"}

    if tur not in durum.turler:
        return {"durum": "RED", "kod": "TANIMSIZ_DEGER"}
    for rol in izinli_roller:
        if rol not in durum.roller:
            return {"durum": "RED", "kod": "TANIMSIZ_DEGER"}

    durum.kaynaklar[id] = Kaynak(
        id=id, ad=ad, tur=tur, izinli_roller=list(izinli_roller)
    )
    return {"durum": "TAMAM"}
