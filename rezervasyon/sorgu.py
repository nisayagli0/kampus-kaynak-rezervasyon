"""Sorgu komutları (Bölüm 5: sorgu kullanici / sorgu kaynak).

Yalnızca okur, durumu değiştirmez ve numara tüketmez.
"""

from datetime import datetime, timedelta

from rezervasyon import zaman
from rezervasyon.modeller import ONAYLI, KULLANIMDA

DOLULUKTA_SAYILAN = (ONAYLI, KULLANIMDA)


def _numara(rezervasyon):
    return int(rezervasyon.id[1:])


def kullanici(durum, kullanici_id):
    """Kullanıcının bakiyesi, güvenilirliği ve tüm rezervasyonları.

    Rezervasyonlar durumu ne olursa olsun listelenir (GELMEDI, IPTAL dahil);
    başlangıca göre, eşitlikte rezervasyon numarasına göre sıralıdır.
    """
    k = durum.kullanicilar.get(kullanici_id)
    if k is None:
        return {"durum": "RED", "kod": "BULUNAMADI"}

    kendi = [r for r in durum.rezervasyonlar.values() if r.kullanici == kullanici_id]
    kendi.sort(key=lambda r: (r.baslangic, _numara(r)))
    return {
        "durum": "TAMAM",
        "bakiye": k.bakiye,
        "guvenilirlik": k.guvenilirlik,
        "rezervasyonlar": [
            {
                "id": r.id,
                "kaynak": r.kaynak,
                "baslangic": zaman.bicimle(r.baslangic),
                "bitis": zaman.bicimle(r.bitis),
                "durum": r.durum,
                "ucret": r.ucret,
            }
            for r in kendi
        ],
    }


def kaynak(durum, kaynak_id, gun):
    """Kaynağın verilen gündeki doluluk listesi (yalnızca ONAYLI, KULLANIMDA ve bakım)."""
    if kaynak_id not in durum.kaynaklar:
        return {"durum": "RED", "kod": "BULUNAMADI"}
    try:
        gun_baslangic = datetime.strptime(gun, "%Y-%m-%d")
    except (TypeError, ValueError):
        return {"durum": "RED", "kod": "GECERSIZ_DEGER"}
    gun_bitis = gun_baslangic + timedelta(days=1)

    satirlar = []  # (başlangıç, sıra anahtarı, satır)
    for r in durum.rezervasyonlar.values():
        if (
            r.kaynak == kaynak_id
            and r.durum in DOLULUKTA_SAYILAN
            and r.baslangic < gun_bitis
            and r.bitis > gun_baslangic
        ):
            satirlar.append(
                (
                    r.baslangic,
                    _numara(r),
                    {
                        "baslangic": zaman.bicimle(r.baslangic),
                        "bitis": zaman.bicimle(r.bitis),
                        "tur": "REZERVASYON",
                        "rezervasyon": r.id,
                    },
                )
            )
    for b in durum.bakimlar:
        if (
            b.kaynak == kaynak_id
            and b.baslangic < gun_bitis
            and b.bitis > gun_baslangic
        ):
            satirlar.append(
                (
                    b.baslangic,
                    0,
                    {
                        "baslangic": zaman.bicimle(b.baslangic),
                        "bitis": zaman.bicimle(b.bitis),
                        "tur": "BAKIM",
                    },
                )
            )

    satirlar.sort(key=lambda s: (s[0], s[1]))
    return {"durum": "TAMAM", "doluluk": [s[2] for s in satirlar]}
