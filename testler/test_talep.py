"""talep.py birim testleri. Çalıştırma: python -m unittest testler.test_talep -v"""

import os
import unittest
from datetime import datetime

from rezervasyon import talep, yukleyici

ORNEK = os.path.join(os.path.dirname(__file__), "ornek", "baslangic.json")


def t(saat, dakika=0):
    return datetime(2027, 3, 8, saat, dakika)


class TalepTesti(unittest.TestCase):
    def setUp(self):
        self.d = yukleyici.yukle(ORNEK)
        yukleyici.kullanici_ekle(self.d, "u1", "Ayşe", "OGRENCI", [], 120, 80)
        yukleyici.kaynak_ekle(self.d, "YAZ-1", "3B Yazıcı 1", "YAZICI", ["OGRENCI"])

    def test_basarili_rezervasyon(self):
        sonuc = talep.rezervasyon(self.d, "u1", "YAZ-1", t(11), t(13))
        self.assertEqual(
            sonuc, {"durum": "TAMAM", "rezervasyon_id": "r1", "ucret": 36, "bakiye": 84}
        )
        r = self.d.rezervasyonlar["r1"]
        self.assertEqual((r.kullanici, r.kaynak, r.ucret, r.durum, r.paket),
                         ("u1", "YAZ-1", 36, "ONAYLI", None))

    def test_red_numara_tuketmez_bakiye_degismez(self):
        sonuc = talep.rezervasyon(self.d, "u1", "YAZ-1", t(13, 10), t(14))
        self.assertEqual(sonuc, {"durum": "RED", "kod": "ZAMAN_ADIMI_HATASI"})
        self.assertEqual(self.d.kullanicilar["u1"].bakiye, 120)
        self.assertEqual(self.d.rezervasyonlar, {})
        sonuc = talep.rezervasyon(self.d, "u1", "YAZ-1", t(11), t(12))
        self.assertEqual(sonuc["rezervasyon_id"], "r1")

    def test_bakiye_yetersiz(self):
        self.d.kullanicilar["u1"].bakiye = 10
        sonuc = talep.rezervasyon(self.d, "u1", "YAZ-1", t(11), t(12))
        self.assertEqual(sonuc, {"durum": "RED", "kod": "BAKIYE_YETERSIZ"})

    def test_fiyat_durumu_degistirmez(self):
        sonuc = talep.fiyat(self.d, "u1", "YAZ-1", t(11), t(13))
        self.assertEqual(sonuc, {"durum": "TAMAM", "ucret": 36})
        self.assertEqual(self.d.kullanicilar["u1"].bakiye, 120)
        self.assertEqual(self.d.rezervasyonlar, {})
        self.assertEqual(self.d.sayaclar["r"], 0)

    def test_fiyat_bakiyeye_bakmaz(self):
        self.d.kullanicilar["u1"].bakiye = 0
        self.assertEqual(talep.fiyat(self.d, "u1", "YAZ-1", t(11), t(13))["ucret"], 36)

    def test_fiyat_diger_hatalari_dondurur(self):
        sonuc = talep.fiyat(self.d, "u1", "CIH-1", t(11), t(13))
        self.assertEqual(sonuc, {"durum": "RED", "kod": "ROL_IZNI_YOK"})

    def test_paket_id_kaydedilir(self):
        r = talep.rezervasyon_olustur(self.d, "u1", "YAZ-1", t(11), t(12), paket_id="p1")
        self.assertEqual(r.paket, "p1")
        self.assertEqual(self.d.kullanicilar["u1"].bakiye, 120 - r.ucret)


if __name__ == "__main__":
    unittest.main()
