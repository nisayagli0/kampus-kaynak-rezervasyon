"""sorgu.py testleri. Çalıştırma: python -m unittest testler.test_sorgu -v"""

import unittest
from datetime import datetime

from rezervasyon import durum_makinesi, sorgu, talep
from rezervasyon.modeller import (
    BakimPenceresi,
    Durum,
    Kaynak,
    KaynakTuru,
    Kullanici,
    Rol,
)


def an(saat, dakika=0, gun=8):
    return datetime(2027, 3, gun, saat, dakika)


def durum_kur():
    d = Durum(saat=an(8))
    d.turler["YAZICI"] = KaynakTuru("YAZICI", 20, 12, True, None)
    d.roller["OGRENCI"] = Rol("OGRENCI", 120, 7, 180)
    for kid in ("YAZ-1", "YAZ-2"):
        d.kaynaklar[kid] = Kaynak(kid, kid, "YAZICI", ["OGRENCI"])
    for uid in ("u1", "u2"):
        d.kullanicilar[uid] = Kullanici(uid, uid, "OGRENCI", [], 120, 80)
    return d


class KullaniciSorgusu(unittest.TestCase):
    def test_bilinmeyen_kullanici(self):
        self.assertEqual(
            sorgu.kullanici(durum_kur(), "x"), {"durum": "RED", "kod": "BULUNAMADI"}
        )

    def test_tum_durumlar_baslangica_ve_numaraya_gore(self):
        d = durum_kur()
        talep.rezervasyon_olustur(d, "u1", "YAZ-1", an(12), an(13))  # r1
        talep.rezervasyon_olustur(d, "u1", "YAZ-2", an(10), an(11))  # r2
        talep.rezervasyon_olustur(
            d, "u1", "YAZ-1", an(10), an(11)
        )  # r3, r2 ile aynı başlangıç
        talep.rezervasyon_olustur(d, "u2", "YAZ-1", an(15), an(16))  # başkasının
        durum_makinesi.iptal(d, "r1")  # iptal edilen de listelenir
        s = sorgu.kullanici(d, "u1")
        self.assertEqual([r["id"] for r in s["rezervasyonlar"]], ["r2", "r3", "r1"])
        self.assertEqual(s["rezervasyonlar"][2]["durum"], "IPTAL")
        self.assertEqual(s["bakiye"], d.kullanicilar["u1"].bakiye)


class KaynakSorgusu(unittest.TestCase):
    def test_bilinmeyen_kaynak(self):
        self.assertEqual(
            sorgu.kaynak(durum_kur(), "x", "2027-03-08")["kod"], "BULUNAMADI"
        )

    def test_yalniz_onayli_kullanimda_ve_bakim_sirali(self):
        d = durum_kur()
        d.bakimlar.append(BakimPenceresi("YAZ-1", an(8), an(10)))
        talep.rezervasyon_olustur(d, "u1", "YAZ-1", an(14), an(15))  # r1
        talep.rezervasyon_olustur(d, "u2", "YAZ-1", an(11), an(12))  # r2
        talep.rezervasyon_olustur(
            d, "u1", "YAZ-1", an(18), an(19)
        )  # r3, iptal edilecek
        talep.rezervasyon_olustur(d, "u2", "YAZ-2", an(11), an(12))  # başka kaynak
        durum_makinesi.iptal(d, "r3")
        s = sorgu.kaynak(d, "YAZ-1", "2027-03-08")
        self.assertEqual(
            s["doluluk"],
            [
                {
                    "baslangic": "2027-03-08T08:00",
                    "bitis": "2027-03-08T10:00",
                    "tur": "BAKIM",
                },
                {
                    "baslangic": "2027-03-08T11:00",
                    "bitis": "2027-03-08T12:00",
                    "tur": "REZERVASYON",
                    "rezervasyon": "r2",
                },
                {
                    "baslangic": "2027-03-08T14:00",
                    "bitis": "2027-03-08T15:00",
                    "tur": "REZERVASYON",
                    "rezervasyon": "r1",
                },
            ],
        )

    def test_baska_gun_bos(self):
        d = durum_kur()
        talep.rezervasyon_olustur(d, "u1", "YAZ-1", an(14), an(15))
        self.assertEqual(
            sorgu.kaynak(d, "YAZ-1", "2027-03-09"), {"durum": "TAMAM", "doluluk": []}
        )

    def test_gecersiz_gun(self):
        self.assertEqual(
            sorgu.kaynak(durum_kur(), "YAZ-1", "bugün")["kod"], "GECERSIZ_DEGER"
        )


if __name__ == "__main__":
    unittest.main()
