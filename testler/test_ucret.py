"""ucret.py birim testleri. Çalıştırma: python -m unittest testler.test_ucret -v"""

import os
import unittest
from datetime import datetime
from fractions import Fraction

from rezervasyon import ucret, yukleyici
from rezervasyon.modeller import Rezervasyon, ONAYLI, GELMEDI, IPTAL, TAMAMLANDI

ORNEK = os.path.join(os.path.dirname(__file__), "ornek", "baslangic.json")


def t(saat, dakika=0, gun=8):
    return datetime(2027, 3, gun, saat, dakika)


def rez_ekle(d, kaynak, bas, bit, durum=ONAYLI):
    no = d.yeni_rezervasyon_no()
    d.rezervasyonlar[no] = Rezervasyon(no, "u3", kaynak, bas, bit, 0, durum)


class YardimciTesti(unittest.TestCase):
    def test_bant_baslangici(self):
        self.assertEqual(ucret.bant_baslangici(t(8)), t(8))
        self.assertEqual(ucret.bant_baslangici(t(9, 45)), t(8))
        self.assertEqual(ucret.bant_baslangici(t(10)), t(10))
        self.assertEqual(ucret.bant_baslangici(t(21, 45)), t(20))

    def test_bant_carpani_sinirlar(self):
        self.assertEqual(ucret.bant_carpani(Fraction(0)), 1)
        self.assertEqual(ucret.bant_carpani(Fraction(1, 4) - Fraction(1, 240)), 1)
        self.assertEqual(ucret.bant_carpani(Fraction(1, 4)), Fraction(5, 4))
        self.assertEqual(ucret.bant_carpani(Fraction(1, 2)), Fraction(3, 2))
        self.assertEqual(ucret.bant_carpani(Fraction(3, 4)), Fraction(7, 4))
        self.assertEqual(ucret.bant_carpani(Fraction(1)), 2)

    def test_yuvarla(self):
        self.assertEqual(ucret.yuvarla(Fraction(15, 2)), 8)  # 7,5 -> 8
        self.assertEqual(ucret.yuvarla(Fraction(29, 4)), 7)  # 7,25 -> 7
        self.assertEqual(ucret.yuvarla(Fraction(31, 4)), 8)  # 7,75 -> 8


class OrnekSenaryoTesti(unittest.TestCase):
    """Örnek senaryodaki ücretler: 36, 45, 48, 8, 18."""

    def setUp(self):
        self.d = yukleyici.yukle(ORNEK)
        yukleyici.kaynak_ekle(self.d, "YAZ-1", "3B Yazıcı 1", "YAZICI", ["OGRENCI"])

    def test_36_ve_45(self):
        self.assertEqual(ucret.hesapla(self.d, "YAZ-1", t(11), t(13)), 36)
        rez_ekle(self.d, "YAZ-1", t(11), t(13))
        # 10-12 bandında 60 dk dolu / (2 × 120) = 0,25 -> çarpan 1,25
        self.assertEqual(ucret.hesapla(self.d, "YAZ-2", t(10), t(12)), 45)

    def test_48_ve_8(self):
        self.assertEqual(ucret.hesapla(self.d, "CIH-1", t(14), t(16)), 48)
        self.assertEqual(ucret.hesapla(self.d, "ODA-1", t(14), t(16)), 8)

    def test_18_gelmedi_sayilmaz(self):
        rez_ekle(self.d, "YAZ-1", t(11), t(13), GELMEDI)
        rez_ekle(self.d, "YAZ-2", t(10), t(12), GELMEDI)
        self.assertEqual(ucret.hesapla(self.d, "YAZ-1", t(12), t(13)), 18)


class DolulukTesti(unittest.TestCase):
    """İki LAB (kapasite 240 dk/bant), 08-10 bandı, 1 saatlik LAB talebi = 8 × çarpan."""

    def setUp(self):
        self.d = yukleyici.yukle(ORNEK)
        yukleyici.kaynak_ekle(self.d, "LAB-1", "Lab 1", "LAB", ["OGRENCI"])
        yukleyici.kaynak_ekle(self.d, "LAB-2", "Lab 2", "LAB", ["OGRENCI"])

    def fiyat(self):
        return ucret.hesapla(self.d, "LAB-2", t(8), t(9))

    def test_bos(self):
        self.assertEqual(self.fiyat(), 8)

    def test_025_alti(self):
        rez_ekle(self.d, "LAB-1", t(8), t(8, 45))  # 45/240
        self.assertEqual(self.fiyat(), 8)

    def test_tam_025(self):
        rez_ekle(self.d, "LAB-1", t(8), t(9))  # 60/240
        self.assertEqual(self.fiyat(), 10)

    def test_tam_05(self):
        rez_ekle(self.d, "LAB-1", t(8), t(10))  # 120/240
        self.assertEqual(self.fiyat(), 12)

    def test_tam_075(self):
        rez_ekle(self.d, "LAB-1", t(8), t(10))
        rez_ekle(self.d, "LAB-2", t(9), t(10))  # 180/240
        self.assertEqual(self.fiyat(), 14)

    def test_tam_1(self):
        rez_ekle(self.d, "LAB-1", t(8), t(10))
        rez_ekle(self.d, "LAB-2", t(8), t(10))  # 240/240
        self.assertEqual(self.fiyat(), 16)

    def test_bant_disindaki_kisim_sayilmaz(self):
        rez_ekle(self.d, "LAB-1", t(9), t(11))  # 08-10 bandına yalnızca 60 dk düşer
        self.assertEqual(self.fiyat(), 10)

    def test_iptal_ve_tamamlandi_sayilmaz(self):
        rez_ekle(self.d, "LAB-1", t(8), t(10), IPTAL)
        rez_ekle(self.d, "LAB-2", t(8), t(10), TAMAMLANDI)
        self.assertEqual(self.fiyat(), 8)

    def test_baska_gun_sayilmaz(self):
        rez_ekle(self.d, "LAB-1", t(8, gun=9), t(10, gun=9))
        self.assertEqual(self.fiyat(), 8)

    def test_yarim_yukari_yuvarlanir(self):
        # LAB, 45 dk, çarpan 1,25: 3 × 2 × 1,25 = 7,5 -> 8
        rez_ekle(self.d, "LAB-1", t(8), t(9))
        self.assertEqual(ucret.hesapla(self.d, "LAB-2", t(8), t(8, 45)), 8)


class DigerKurallarTesti(unittest.TestCase):
    def setUp(self):
        self.d = yukleyici.yukle(ORNEK)

    def test_iki_banda_yayilan(self):
        # ODA 10-12 bandı 0,5 dolu: 09-10 dilimleri ×1, 10-11 dilimleri ×1,5
        rez_ekle(self.d, "ODA-1", t(10), t(12))
        self.assertEqual(ucret.hesapla(self.d, "ODA-2", t(9), t(11)), 4 + 6)

    def test_enerji_yogun_olmayan_turde_pik_yok(self):
        self.assertEqual(ucret.hesapla(self.d, "ODA-1", t(10), t(12)), 8)

    def test_pik_sinirlari(self):
        # YAZICI dilimi 3 KP; pik dilim 4,5
        self.assertEqual(ucret.hesapla(self.d, "YAZ-2", t(9, 30), t(10, 30)), 6 + 9)
        self.assertEqual(ucret.hesapla(self.d, "YAZ-2", t(15, 30), t(16, 30)), 9 + 6)

    def test_bakim_sayilmaz(self):
        # YAZ-2'nin 08-10 bakımı doluluğa katılmaz
        self.assertEqual(ucret.hesapla(self.d, "YAZ-2", t(8), t(9)), 12)

    def test_kaynak_ekle_sonrasi_doluluk_degisir(self):
        rez_ekle(self.d, "YAZ-2", t(10), t(11))
        # tek yazıcı: 60/120 = 0,5 -> 4 × 3 × 1,5 × 1,5 = 27
        self.assertEqual(ucret.hesapla(self.d, "YAZ-2", t(11), t(12)), 27)
        yukleyici.kaynak_ekle(self.d, "YAZ-1", "3B Yazıcı 1", "YAZICI", ["OGRENCI"])
        # iki yazıcı: 60/240 = 0,25 -> 22,5 -> 23
        self.assertEqual(ucret.hesapla(self.d, "YAZ-2", t(11), t(12)), 23)


if __name__ == "__main__":
    unittest.main()
