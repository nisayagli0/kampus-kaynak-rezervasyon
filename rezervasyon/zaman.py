"""Zaman yardımcıları: metin <-> datetime, 15 dk adımı, dakika farkı,
Pazartesi sıfırlamaları.

Zaman gösterimi YYYY-AA-GGTSS:DD biçimindedir (örn. 2027-03-08T08:00).
Tüm aralıklarda başlangıç dahil, bitiş hariçtir.
"""

from datetime import datetime, timedelta

BICIM = "%Y-%m-%dT%H:%M"


def ayristir(metin):
    """'2027-03-08T08:00' -> datetime. Bozuk biçimde ValueError verir."""
    return datetime.strptime(metin, BICIM)


def bicimle(dt):
    """datetime -> '2027-03-08T08:00'."""
    return dt.strftime(BICIM)


def adima_uygun_mu(dt):
    """K1/K10-2: dakika 0, 15, 30 veya 45 mi (saniye ve alt birimler sıfır)?"""
    return dt.minute % 15 == 0 and dt.second == 0 and dt.microsecond == 0


def dakika_farki(a, b):
    """b - a, dakika olarak. b, a'dan önceyse negatif döner."""
    return int((b - a).total_seconds() // 60)


def pazartesi_sifirlamalari(eski, yeni):
    """K6/K11: eski ile yeni arasındaki Pazartesi 00:00 listesi.

    Aralık (eski, yeni]: eski hariç, yeni dahil. Kronolojik sırada döner.
    """
    gece_yarisi = eski.replace(hour=0, minute=0, second=0, microsecond=0)
    # weekday(): Pazartesi = 0 ... Pazar = 6
    ilk = gece_yarisi + timedelta(days=(7 - eski.weekday()) % 7)
    if ilk <= eski:
        ilk += timedelta(days=7)

    sonuc = []
    t = ilk
    while t <= yeni:
        sonuc.append(t)
        t += timedelta(days=7)
    return sonuc
