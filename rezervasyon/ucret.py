"""Ücret hesabı (K5).

ücret = yuvarla( Σ dilim  temel_ucret × 0,25 × bant_çarpanı × pik_çarpanı )

Kesirli değerlerde yuvarlama hatası olmaması için Fraction kullanılır.
Zamanlar datetime'dır; doluluk talep anındaki Durum'a göre hesaplanır.
"""

import math
from datetime import timedelta
from fractions import Fraction

from rezervasyon import zaman
from rezervasyon.modeller import ONAYLI, KULLANIMDA

DILIM = timedelta(minutes=15)
BANT_DK = 120  # her bant iki saat
BANT = timedelta(minutes=BANT_DK)


def bant_baslangici(t):
    """t'nin düştüğü iki saatlik bandın başlangıcı (08-10, 10-12, ..., 20-22)."""
    saat = 8 + (t.hour - 8) // 2 * 2
    return t.replace(hour=saat, minute=0)


def doluluk(durum, tur, bant_bas):
    """O bantta, o türdeki ONAYLI/KULLANIMDA rezervasyonların doluluk oranı."""
    bant_bit = bant_bas + BANT
    kaynak_sayisi = sum(1 for k in durum.kaynaklar.values() if k.tur == tur)

    dolu_dk = 0
    for r in durum.rezervasyonlar.values():
        if r.durum not in (ONAYLI, KULLANIMDA):
            continue
        if durum.kaynaklar[r.kaynak].tur != tur:
            continue
        # rezervasyonun bant içinde kalan kısmı
        bas = max(r.baslangic, bant_bas)
        bit = min(r.bitis, bant_bit)
        if bas < bit:
            dolu_dk += zaman.dakika_farki(bas, bit)

    return Fraction(dolu_dk, kaynak_sayisi * BANT_DK)


def bant_carpani(oran):
    """1 + 0,25 × ⌊4 × doluluk⌋"""
    return 1 + Fraction(1, 4) * math.floor(4 * oran)


def yuvarla(deger):
    """En yakın tam sayı; kesirli kısım tam 0,5 ise yukarı."""
    return math.floor(deger + Fraction(1, 2))


def hesapla(durum, kaynak_id, baslangic, bitis):
    """Talebin ücreti (int). Talebin kendisi ve bakım doluluğa katılmaz."""
    kaynak = durum.kaynaklar[kaynak_id]
    tur = durum.turler[kaynak.tur]

    toplam = Fraction(0)
    t = baslangic
    while t < bitis:
        oran = doluluk(durum, kaynak.tur, bant_baslangici(t))
        pik = Fraction(3, 2) if tur.enerji_yogun and 10 <= t.hour < 16 else 1
        toplam += tur.temel_ucret * Fraction(1, 4) * bant_carpani(oran) * pik
        t += DILIM

    return yuvarla(toplam)
