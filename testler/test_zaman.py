"""zaman.py birim testleri. Çalıştırma: python -m unittest testler.test_zaman -v"""

import unittest
from datetime import datetime

from rezervasyon import zaman


class AyristirBicimleTesti(unittest.TestCase):
    def test_ayristir_degerler(self):
        self.assertEqual(zaman.ayristir("2027-03-08T08:00"), datetime(2027, 3, 8, 8, 0))

    def test_gidis_donus(self):
        self.assertEqual(
            zaman.bicimle(zaman.ayristir("2027-03-08T11:15")), "2027-03-08T11:15"
        )

    def test_bozuk_metin_hata_verir(self):
        for metin in [
            "2027-03-08 08:00",
            "abc",
            "2027-13-01T08:00",
            "2027-03-08T08:00:00",
        ]:
            with self.assertRaises(ValueError):
                zaman.ayristir(metin)


class AdimTesti(unittest.TestCase):
    def test_gecerli_dakikalar(self):
        for dakika in [0, 15, 30, 45]:
            self.assertTrue(zaman.adima_uygun_mu(datetime(2027, 3, 8, 13, dakika)))

    def test_gecersiz_dakikalar(self):
        for dakika in [1, 10, 20, 59]:
            self.assertFalse(zaman.adima_uygun_mu(datetime(2027, 3, 8, 13, dakika)))

    def test_saniye_varsa_uygun_degil(self):
        self.assertFalse(zaman.adima_uygun_mu(datetime(2027, 3, 8, 13, 15, 1)))


class DakikaFarkiTesti(unittest.TestCase):
    def test_pozitif_fark(self):
        a = datetime(2027, 3, 8, 11, 0)
        b = datetime(2027, 3, 8, 13, 15)
        self.assertEqual(zaman.dakika_farki(a, b), 135)

    def test_negatif_fark(self):
        a = datetime(2027, 3, 8, 13, 0)
        b = datetime(2027, 3, 8, 11, 0)
        self.assertEqual(zaman.dakika_farki(a, b), -120)

    def test_gun_asan_fark(self):
        a = datetime(2027, 3, 8, 8, 0)
        b = datetime(2027, 3, 9, 8, 0)
        self.assertEqual(zaman.dakika_farki(a, b), 1440)


class PazartesiTesti(unittest.TestCase):
    # 8 Mart 2027 Pazartesi, 15 ve 22 Mart de Pazartesi.
    def test_tek_pazartesi(self):
        eski = datetime(2027, 3, 8, 8, 0)
        yeni = datetime(2027, 3, 15, 8, 0)
        self.assertEqual(
            zaman.pazartesi_sifirlamalari(eski, yeni), [datetime(2027, 3, 15, 0, 0)]
        )

    def test_eski_hariç(self):
        eski = datetime(2027, 3, 8, 0, 0)  # tam Pazartesi 00:00
        yeni = datetime(2027, 3, 10, 0, 0)
        self.assertEqual(zaman.pazartesi_sifirlamalari(eski, yeni), [])

    def test_yeni_dahil(self):
        eski = datetime(2027, 3, 14, 23, 45)
        yeni = datetime(2027, 3, 15, 0, 0)  # tam Pazartesi 00:00
        self.assertEqual(
            zaman.pazartesi_sifirlamalari(eski, yeni), [datetime(2027, 3, 15, 0, 0)]
        )

    def test_coklu_pazartesi(self):
        eski = datetime(2027, 3, 7, 12, 0)  # Pazar
        yeni = datetime(2027, 3, 23, 0, 0)
        beklenen = [datetime(2027, 3, 8), datetime(2027, 3, 15), datetime(2027, 3, 22)]
        self.assertEqual(zaman.pazartesi_sifirlamalari(eski, yeni), beklenen)

    def test_ayni_hafta_icinde_yok(self):
        eski = datetime(2027, 3, 9, 8, 0)
        yeni = datetime(2027, 3, 14, 22, 0)
        self.assertEqual(zaman.pazartesi_sifirlamalari(eski, yeni), [])

    def test_esit_saat_bos(self):
        t = datetime(2027, 3, 8, 8, 0)
        self.assertEqual(zaman.pazartesi_sifirlamalari(t, t), [])


if __name__ == "__main__":
    unittest.main()
