"""okuma.py birim testleri. Çalıştırma: python -m unittest testler.test_okuma -v"""

import unittest
from datetime import datetime

from rezervasyon import okuma
from rezervasyon.modeller import Durum, KaynakTuru, Rol, Kaynak, Kullanici


def ornek_durum():
    d = Durum(saat=datetime(2027, 3, 8, 8, 0))
    d.turler = {
        "ODA": KaynakTuru("ODA", 0, 4, False, None),
        "LAB": KaynakTuru("LAB", 10, 8, False, "LAB_GUVENLIK"),
    }
    d.roller = {
        "OGRENCI": Rol("OGRENCI", 120, 7, 180),
        "TEKNISYEN": Rol("TEKNISYEN", 600, 30, 840),
    }
    d.kaynaklar = {"ODA-1": Kaynak("ODA-1", "Oda 1", "ODA", ["OGRENCI"])}
    d.kullanicilar = {
        "u1": Kullanici("u1", "Ayşe", "OGRENCI", ["CIHAZ_EGITIMI"], 120, 80)
    }
    return d


class OkumaTesti(unittest.TestCase):
    def test_simule_saat(self):
        self.assertEqual(okuma.simule_saat(ornek_durum()), datetime(2027, 3, 8, 8, 0))

    def test_roller_ve_turler_dosya_sirasinda(self):
        d = ornek_durum()
        self.assertEqual(okuma.roller(d), ["OGRENCI", "TEKNISYEN"])
        self.assertEqual(okuma.turler(d), ["ODA", "LAB"])

    def test_sertifikalar_birlesim_ve_null_atlanir(self):
        # ODA'nın sertifikası None: listeye girmez. LAB_GUVENLIK türden, CIHAZ_EGITIMI kullanıcıdan.
        self.assertEqual(
            okuma.sertifikalar(ornek_durum()), ["CIHAZ_EGITIMI", "LAB_GUVENLIK"]
        )

    def test_kullanicilar_ve_kaynaklar(self):
        d = ornek_durum()
        self.assertEqual([k.id for k in okuma.kullanicilar(d)], ["u1"])
        self.assertEqual([k.id for k in okuma.kaynaklar(d)], ["ODA-1"])


if __name__ == "__main__":
    unittest.main()
