"""durum_makinesi.py testleri. Çalıştırma: python -m unittest testler.test_durum_makinesi -v"""

import unittest
from datetime import datetime

from rezervasyon import durum_makinesi
from rezervasyon.modeller import (
    Durum,
    Rezervasyon,
    ONAYLI,
    KULLANIMDA,
    TAMAMLANDI,
    IPTAL,
    GELMEDI,
)

BASLANGIC = datetime(2027, 3, 8, 10, 0)


def durum_kur(saat, rez_durum=ONAYLI):
    d = Durum(saat=saat)
    d.rezervasyonlar["r1"] = Rezervasyon(
        "r1", "u1", "YAZ-1", BASLANGIC, datetime(2027, 3, 8, 12, 0), 36, rez_durum
    )
    return d


class GirisTesti(unittest.TestCase):
    def test_pencere_alt_siniri_dahil(self):
        d = durum_kur(datetime(2027, 3, 8, 9, 50))  # başlangıçtan tam 10 dk önce
        self.assertEqual(
            durum_makinesi.giris(d, "r1"),
            {"durum": "TAMAM", "yeni_durum": "KULLANIMDA"},
        )
        self.assertEqual(d.rezervasyonlar["r1"].durum, KULLANIMDA)

    def test_pencere_ust_siniri_dahil(self):
        d = durum_kur(datetime(2027, 3, 8, 10, 15))  # başlangıçtan tam 15 dk sonra
        self.assertEqual(durum_makinesi.giris(d, "r1")["durum"], "TAMAM")

    def test_pencereden_bir_dakika_once(self):
        d = durum_kur(datetime(2027, 3, 8, 9, 49))
        self.assertEqual(
            durum_makinesi.giris(d, "r1"),
            {"durum": "RED", "kod": "GIRIS_PENCERESI_DISI"},
        )
        self.assertEqual(d.rezervasyonlar["r1"].durum, ONAYLI)  # durum değişmedi

    def test_pencereden_bir_dakika_sonra(self):
        d = durum_kur(datetime(2027, 3, 8, 10, 16))
        self.assertEqual(durum_makinesi.giris(d, "r1")["kod"], "GIRIS_PENCERESI_DISI")

    def test_onayli_olmayan_durum_hatasi(self):
        # Saat pencere içinde olsa da durum hatası döner
        for rez_durum in [KULLANIMDA, TAMAMLANDI, IPTAL, GELMEDI]:
            with self.subTest(rez_durum=rez_durum):
                d = durum_kur(datetime(2027, 3, 8, 10, 0), rez_durum)
                self.assertEqual(
                    durum_makinesi.giris(d, "r1"),
                    {"durum": "RED", "kod": "DURUM_HATASI"},
                )

    def test_durum_hatasi_pencere_hatasindan_once(self):
        d = durum_kur(datetime(2027, 3, 8, 9, 0), GELMEDI)  # pencere dışı ve GELMEDI
        self.assertEqual(durum_makinesi.giris(d, "r1")["kod"], "DURUM_HATASI")

    def test_olmayan_rezervasyon(self):
        d = durum_kur(datetime(2027, 3, 8, 10, 0))
        self.assertEqual(
            durum_makinesi.giris(d, "r99"), {"durum": "RED", "kod": "BULUNAMADI"}
        )

    def test_ikinci_giris_durum_hatasi(self):
        d = durum_kur(datetime(2027, 3, 8, 10, 0))
        durum_makinesi.giris(d, "r1")
        self.assertEqual(durum_makinesi.giris(d, "r1")["kod"], "DURUM_HATASI")


if __name__ == "__main__":
    unittest.main()
