"""durum_makinesi.py testleri. Çalıştırma: python -m unittest testler.test_durum_makinesi -v"""

import unittest
from datetime import datetime

from rezervasyon import durum_makinesi
from rezervasyon.modeller import (
    Durum,
    Kullanici,
    Rezervasyon,
    Rol,
    ONAYLI,
    KULLANIMDA,
    TAMAMLANDI,
    IPTAL,
    GELMEDI,
)

BASLANGIC = datetime(2027, 3, 8, 10, 0)
BITIS = datetime(2027, 3, 8, 12, 0)


def durum_kur(saat, rez_durum=ONAYLI, ucret=36, bakiye=84, guvenilirlik=80):
    d = Durum(saat=saat)
    d.roller["OGRENCI"] = Rol("OGRENCI", 120, 7, 180)  # haftalık kota 120
    d.kullanicilar["u1"] = Kullanici("u1", "Ayşe", "OGRENCI", [], bakiye, guvenilirlik)
    d.rezervasyonlar["r1"] = Rezervasyon(
        "r1", "u1", "YAZ-1", BASLANGIC, BITIS, ucret, rez_durum
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


class IadeEtTesti(unittest.TestCase):
    def test_kota_icinde_tamami_eklenir(self):
        d = durum_kur(BASLANGIC, bakiye=84)
        self.assertEqual(durum_makinesi.iade_et(d, "u1", 10), 10)
        self.assertEqual(d.kullanicilar["u1"].bakiye, 94)

    def test_kota_asan_kisim_eklenmez(self):
        d = durum_kur(BASLANGIC, bakiye=119)  # kota 120
        self.assertEqual(durum_makinesi.iade_et(d, "u1", 4), 1)
        self.assertEqual(d.kullanicilar["u1"].bakiye, 120)

    def test_bakiye_kotadaysa_hicbir_sey_eklenmez(self):
        d = durum_kur(BASLANGIC, bakiye=120)
        self.assertEqual(durum_makinesi.iade_et(d, "u1", 5), 0)
        self.assertEqual(d.kullanicilar["u1"].bakiye, 120)


class IptalTesti(unittest.TestCase):
    def iptal_et(self, saat, **kwargs):
        d = durum_kur(saat, **kwargs)
        return d, durum_makinesi.iptal(d, "r1")

    def test_tam_24_saat_tam_iade(self):
        d, sonuc = self.iptal_et(datetime(2027, 3, 7, 10, 0))  # başlangıca tam 24 saat
        self.assertEqual(
            sonuc,
            {
                "durum": "TAMAM",
                "iade": 36,
                "bakiye": 120,
                "guvenilirlik": 80,
                "olaylar": [],
            },
        )
        self.assertEqual(d.rezervasyonlar["r1"].durum, IPTAL)

    def test_24_saatten_15_dk_az_yarim_iade(self):
        d, sonuc = self.iptal_et(datetime(2027, 3, 7, 10, 15))
        self.assertEqual(
            (sonuc["iade"], sonuc["bakiye"], sonuc["guvenilirlik"]), (18, 102, 80)
        )

    def test_tam_2_saat_yarim_iade_guvenilirlik_degismez(self):
        d, sonuc = self.iptal_et(datetime(2027, 3, 8, 8, 0))  # başlangıca tam 2 saat
        self.assertEqual(
            (sonuc["iade"], sonuc["bakiye"], sonuc["guvenilirlik"]), (18, 102, 80)
        )

    def test_2_saatten_15_dk_az_iade_yok_guvenilirlik_eksi_5(self):
        d, sonuc = self.iptal_et(datetime(2027, 3, 8, 8, 15))
        self.assertEqual(
            (sonuc["iade"], sonuc["bakiye"], sonuc["guvenilirlik"]), (0, 84, 75)
        )

    def test_baslangic_gecmisse_iade_yok(self):
        d, sonuc = self.iptal_et(datetime(2027, 3, 8, 10, 30))
        self.assertEqual((sonuc["iade"], sonuc["guvenilirlik"]), (0, 75))

    def test_yarim_iade_asagi_yuvarlanir(self):
        d, sonuc = self.iptal_et(datetime(2027, 3, 8, 8, 0), ucret=45, bakiye=50)
        self.assertEqual((sonuc["iade"], sonuc["bakiye"]), (22, 72))  # 45 / 2 = 22,5

    def test_kota_tasmasinda_iade_gercekte_eklenen_kadar(self):
        d, sonuc = self.iptal_et(datetime(2027, 3, 6, 10, 0), ucret=4, bakiye=119)
        self.assertEqual((sonuc["iade"], sonuc["bakiye"]), (1, 120))

    def test_guvenilirlik_sifirin_altina_inmez(self):
        d, sonuc = self.iptal_et(datetime(2027, 3, 8, 8, 15), guvenilirlik=3)
        self.assertEqual(sonuc["guvenilirlik"], 0)

    def test_onayli_olmayanda_durum_hatasi(self):
        for rez_durum in [KULLANIMDA, TAMAMLANDI, IPTAL, GELMEDI]:
            with self.subTest(rez_durum=rez_durum):
                d, sonuc = self.iptal_et(
                    datetime(2027, 3, 7, 10, 0), rez_durum=rez_durum
                )
                self.assertEqual(sonuc, {"durum": "RED", "kod": "DURUM_HATASI"})
                self.assertEqual(d.kullanicilar["u1"].bakiye, 84)  # bakiye değişmedi

    def test_olmayan_rezervasyon(self):
        d = durum_kur(BASLANGIC)
        self.assertEqual(
            durum_makinesi.iptal(d, "r99"), {"durum": "RED", "kod": "BULUNAMADI"}
        )


class CikisTesti(unittest.TestCase):
    def test_erken_cikis(self):
        d = durum_kur(datetime(2027, 3, 8, 11, 0), KULLANIMDA)
        sonuc = durum_makinesi.cikis(d, "r1")
        self.assertEqual(
            sonuc,
            {
                "durum": "TAMAM",
                "yeni_durum": "TAMAMLANDI",
                "guvenilirlik": 80,
                "olaylar": [],
            },
        )
        rez = d.rezervasyonlar["r1"]
        self.assertEqual(rez.durum, TAMAMLANDI)
        self.assertEqual(rez.bitis, datetime(2027, 3, 8, 11, 0))  # bitiş çıkış saati
        self.assertEqual(d.kullanicilar["u1"].bakiye, 84)  # iade yok

    def test_kullanimda_olmayanda_durum_hatasi(self):
        for rez_durum in [ONAYLI, TAMAMLANDI, IPTAL, GELMEDI]:
            with self.subTest(rez_durum=rez_durum):
                d = durum_kur(datetime(2027, 3, 8, 11, 0), rez_durum)
                self.assertEqual(
                    durum_makinesi.cikis(d, "r1"),
                    {"durum": "RED", "kod": "DURUM_HATASI"},
                )

    def test_olmayan_rezervasyon(self):
        d = durum_kur(BASLANGIC)
        self.assertEqual(durum_makinesi.cikis(d, "r99")["kod"], "BULUNAMADI")


class GelmediTesti(unittest.TestCase):
    def test_gecis_guvenilirlik_eksi_15_iade_yok(self):
        d = durum_kur(datetime(2027, 3, 8, 10, 15))
        self.assertEqual(durum_makinesi.gelmedi(d, "r1"), 65)
        self.assertEqual(d.rezervasyonlar["r1"].durum, GELMEDI)
        self.assertEqual(d.kullanicilar["u1"].bakiye, 84)

    def test_guvenilirlik_sifirin_altina_inmez(self):
        d = durum_kur(datetime(2027, 3, 8, 10, 15), guvenilirlik=10)
        self.assertEqual(durum_makinesi.gelmedi(d, "r1"), 0)


class TamamlandiTesti(unittest.TestCase):
    def test_gecis_guvenilirlik_arti_2(self):
        d = durum_kur(BITIS, KULLANIMDA)
        self.assertEqual(durum_makinesi.tamamlandi(d, "r1"), 82)
        rez = d.rezervasyonlar["r1"]
        self.assertEqual(rez.durum, TAMAMLANDI)
        self.assertEqual(rez.bitis, BITIS)  # bitiş değişmez

    def test_guvenilirlik_100u_asmaz(self):
        d = durum_kur(BITIS, KULLANIMDA, guvenilirlik=99)
        self.assertEqual(durum_makinesi.tamamlandi(d, "r1"), 100)


if __name__ == "__main__":
    unittest.main()
