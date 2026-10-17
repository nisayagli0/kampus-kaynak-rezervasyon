"""yukleyici.py birim testleri. Çalıştırma: python -m unittest testler.test_yukleyici -v"""

import os
import unittest
from datetime import datetime

from rezervasyon import yukleyici

ORNEK = os.path.join(os.path.dirname(__file__), "ornek", "baslangic.json")


class YukleTesti(unittest.TestCase):
    def setUp(self):
        self.d = yukleyici.yukle(ORNEK)

    def test_saat(self):
        self.assertEqual(self.d.saat, datetime(2027, 3, 8, 8, 0))

    def test_turler_ve_null_sertifika(self):
        self.assertEqual(list(self.d.turler), ["ODA", "LAB", "YAZICI", "CIHAZ"])
        self.assertIsNone(self.d.turler["ODA"].sertifika)
        self.assertEqual(self.d.turler["LAB"].sertifika, "LAB_GUVENLIK")
        self.assertTrue(self.d.turler["YAZICI"].enerji_yogun)
        self.assertEqual(self.d.turler["CIHAZ"].hazirlik_dk, 15)

    def test_roller(self):
        self.assertEqual(list(self.d.roller), ["OGRENCI", "ARASTIRMACI", "TEKNISYEN"])
        self.assertEqual(self.d.roller["OGRENCI"].haftalik_kota, 120)

    def test_kaynaklar_dosya_sirasinda(self):
        self.assertEqual(list(self.d.kaynaklar), ["YAZ-2", "CIH-1", "ODA-1", "ODA-2"])
        self.assertEqual(self.d.kaynaklar["CIH-1"].izinli_roller, ["ARASTIRMACI", "TEKNISYEN"])

    def test_bakim(self):
        b = self.d.bakimlar[0]
        self.assertEqual(b.kaynak, "YAZ-2")
        self.assertEqual(b.bitis, datetime(2027, 3, 8, 10, 0))

    def test_kullanicilar_ve_bos_kayitlar(self):
        u3 = self.d.kullanicilar["u3"]
        self.assertEqual((u3.bakiye, u3.guvenilirlik), (300, 80))
        self.assertEqual(self.d.rezervasyonlar, {})
        self.assertEqual(self.d.beklemeler, {})


TAMAM = {"durum": "TAMAM"}


def red(kod):
    return {"durum": "RED", "kod": kod}


class KullaniciEkleTesti(unittest.TestCase):
    def setUp(self):
        self.d = yukleyici.yukle(ORNEK)

    def ekle(self, **degisen):
        alanlar = {"id": "u1", "ad": "Ayşe Kaya", "rol": "OGRENCI",
                   "sertifikalar": [], "bakiye": 120, "guvenilirlik": 80}
        alanlar.update(degisen)
        return yukleyici.kullanici_ekle(self.d, **alanlar)

    def test_basarili_ekleme(self):
        self.assertEqual(self.ekle(), TAMAM)
        self.assertEqual(self.d.kullanicilar["u1"].bakiye, 120)
        self.assertEqual(list(self.d.kullanicilar), ["u3", "u1"])

    def test_id_mevcut(self):
        self.assertEqual(self.ekle(id="u3"), red("ID_MEVCUT"))

    def test_tanimsiz_rol(self):
        self.assertEqual(self.ekle(rol="MISAFIR"), red("TANIMSIZ_DEGER"))

    def test_sira_id_once(self):
        # id de rol de hatalı: önce ID_MEVCUT
        self.assertEqual(self.ekle(id="u3", rol="MISAFIR", bakiye=-1), red("ID_MEVCUT"))

    def test_sira_rol_bakiyeden_once(self):
        self.assertEqual(self.ekle(rol="MISAFIR", bakiye=-1), red("TANIMSIZ_DEGER"))

    def test_bakiye_sinirlari(self):
        self.assertEqual(self.ekle(id="a", bakiye=0), TAMAM)
        self.assertEqual(self.ekle(id="b", bakiye=120), TAMAM)  # kotaya eşit
        self.assertEqual(self.ekle(id="c", bakiye=-1), red("GECERSIZ_DEGER"))
        self.assertEqual(self.ekle(id="d", bakiye=121), red("GECERSIZ_DEGER"))

    def test_bakiye_rolun_kotasina_gore(self):
        # ARASTIRMACI kotası 300: 300 geçerli
        self.assertEqual(self.ekle(rol="ARASTIRMACI", bakiye=300), TAMAM)

    def test_guvenilirlik_gecersiz(self):
        for deger in [80.5, "80", 101, -1, True, None]:
            with self.subTest(deger=deger):
                self.assertEqual(self.ekle(guvenilirlik=deger), red("GECERSIZ_DEGER"))
        self.assertNotIn("u1", self.d.kullanicilar)

    def test_guvenilirlik_sinirlari(self):
        self.assertEqual(self.ekle(id="a", guvenilirlik=0), TAMAM)
        self.assertEqual(self.ekle(id="b", guvenilirlik=100), TAMAM)


class KaynakEkleTesti(unittest.TestCase):
    def setUp(self):
        self.d = yukleyici.yukle(ORNEK)

    def test_basarili_ekleme_tur_sayisi_artar(self):
        sonuc = yukleyici.kaynak_ekle(self.d, "YAZ-1", "3B Yazıcı 1", "YAZICI", ["OGRENCI"])
        self.assertEqual(sonuc, TAMAM)
        yazicilar = [k for k in self.d.kaynaklar.values() if k.tur == "YAZICI"]
        self.assertEqual(len(yazicilar), 2)

    def test_id_mevcut(self):
        sonuc = yukleyici.kaynak_ekle(self.d, "ODA-1", "x", "ODA", ["OGRENCI"])
        self.assertEqual(sonuc, red("ID_MEVCUT"))

    def test_tanimsiz_tur(self):
        sonuc = yukleyici.kaynak_ekle(self.d, "X-1", "x", "DRONE", ["OGRENCI"])
        self.assertEqual(sonuc, red("TANIMSIZ_DEGER"))

    def test_tanimsiz_izinli_rol(self):
        sonuc = yukleyici.kaynak_ekle(self.d, "X-1", "x", "ODA", ["OGRENCI", "MISAFIR"])
        self.assertEqual(sonuc, red("TANIMSIZ_DEGER"))
        self.assertNotIn("X-1", self.d.kaynaklar)


if __name__ == "__main__":
    unittest.main()
