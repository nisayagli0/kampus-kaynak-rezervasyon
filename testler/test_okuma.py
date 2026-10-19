"""okuma.py birim testleri. Çalıştırma: python -m unittest testler.test_okuma -v"""

import unittest
from datetime import date, datetime

from rezervasyon import durum_makinesi, okuma, talep
from rezervasyon.modeller import (
    BakimPenceresi,
    BeklemeKaydi,
    Durum,
    Kaynak,
    KaynakTuru,
    Kullanici,
    Rol,
)


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


# --- Takvim ve paneller için eklenen okuma işlevlerinin testleri ---


def gun_an(saat, dakika=0, gun=8):
    return datetime(2027, 3, gun, saat, dakika)


def gun_durum_kur():
    d = Durum(saat=gun_an(8))
    d.turler["YAZICI"] = KaynakTuru("YAZICI", 20, 12, True, None)
    d.turler["ODA"] = KaynakTuru("ODA", 0, 4, False, None)
    d.roller["OGRENCI"] = Rol("OGRENCI", 120, 7, 180)
    d.kaynaklar["YAZ-1"] = Kaynak("YAZ-1", "Yazıcı 1", "YAZICI", ["OGRENCI"])
    d.kaynaklar["ODA-1"] = Kaynak("ODA-1", "Oda 1", "ODA", ["OGRENCI"])
    for uid in ("u1", "u2"):
        d.kullanicilar[uid] = Kullanici(uid, uid, "OGRENCI", ["X"], 120, 80)
    return d


class GunSorgulari(unittest.TestCase):
    def test_rezervasyonlar_gun_tum_durumlar_ve_sirali(self):
        d = gun_durum_kur()
        talep.rezervasyon_olustur(d, "u1", "YAZ-1", gun_an(12), gun_an(13))  # r1
        talep.rezervasyon_olustur(d, "u2", "ODA-1", gun_an(10), gun_an(11))  # r2
        talep.rezervasyon_olustur(d, "u1", "YAZ-1", gun_an(10), gun_an(11))  # r3
        talep.rezervasyon_olustur(
            d, "u1", "ODA-1", gun_an(9, gun=9), gun_an(10, gun=9)
        )  # r4, başka gün
        durum_makinesi.iptal(d, "r1")
        ids = [r.id for r in okuma.rezervasyonlar_gun(d, date(2027, 3, 8))]
        self.assertEqual(
            ids, ["r2", "r3", "r1"]
        )  # iptal edilen de var; 10:00 eşitliğinde r2 önce
        self.assertEqual(
            [r.id for r in okuma.rezervasyonlar_gun(d, date(2027, 3, 9))], ["r4"]
        )

    def test_bakimlar_gun(self):
        d = gun_durum_kur()
        d.bakimlar.append(BakimPenceresi("YAZ-1", gun_an(8), gun_an(10)))
        d.bakimlar.append(BakimPenceresi("ODA-1", gun_an(8, gun=9), gun_an(10, gun=9)))
        self.assertEqual(
            [b.kaynak for b in okuma.bakimlar_gun(d, date(2027, 3, 8))], ["YAZ-1"]
        )

    def test_hazirlik_araliklari_turden_okunur_ve_yalniz_gecerli_durumlar(self):
        d = gun_durum_kur()
        talep.rezervasyon_olustur(
            d, "u1", "YAZ-1", gun_an(10), gun_an(11)
        )  # r1: hazırlık 11:00-11:20
        talep.rezervasyon_olustur(
            d, "u2", "ODA-1", gun_an(10), gun_an(11)
        )  # r2: hazırlık süresi 0
        talep.rezervasyon_olustur(
            d, "u1", "YAZ-1", gun_an(14), gun_an(15)
        )  # r3, iptal edilecek
        durum_makinesi.iptal(d, "r3")
        self.assertEqual(
            okuma.hazirlik_araliklari_gun(d, date(2027, 3, 8)),
            [("YAZ-1", "r1", gun_an(11), gun_an(11, 20))],
        )

    def test_hazirlik_yalniz_kendi_gununde_gorunur(self):
        d = gun_durum_kur()
        talep.rezervasyon_olustur(
            d, "u1", "YAZ-1", gun_an(21), gun_an(22)
        )  # hazırlık 22:00-22:20
        self.assertEqual(len(okuma.hazirlik_araliklari_gun(d, date(2027, 3, 8))), 1)
        self.assertEqual(okuma.hazirlik_araliklari_gun(d, date(2027, 3, 9)), [])


class KullaniciOkumalari(unittest.TestCase):
    def test_bekleme_kayitlari_numaraya_gore_ve_filtreli(self):
        d = gun_durum_kur()
        for no, kul in (("b10", "u1"), ("b2", "u2"), ("b3", "u1")):
            d.beklemeler[no] = BeklemeKaydi(
                no, kul, "YAZ-1", gun_an(12), gun_an(13), gun_an(8)
            )
        self.assertEqual(
            [k.id for k in okuma.bekleme_kayitlari(d)], ["b2", "b3", "b10"]
        )
        self.assertEqual(
            [k.id for k in okuma.bekleme_kayitlari(d, "u1")], ["b3", "b10"]
        )

    def test_kullanici_ozeti(self):
        d = gun_durum_kur()
        ozet = okuma.kullanici_ozeti(d, "u1")
        self.assertEqual(
            (ozet["bakiye"], ozet["guvenilirlik"], ozet["haftalik_kota"]),
            (120, 80, 120),
        )
        self.assertIsNone(okuma.kullanici_ozeti(d, "yok"))

    def test_kullanici_rezervasyonlari_sirali(self):
        d = gun_durum_kur()
        talep.rezervasyon_olustur(d, "u1", "YAZ-1", gun_an(14), gun_an(15))
        talep.rezervasyon_olustur(d, "u1", "ODA-1", gun_an(9), gun_an(10))
        talep.rezervasyon_olustur(d, "u2", "ODA-1", gun_an(11), gun_an(12))
        self.assertEqual(
            [r.id for r in okuma.kullanici_rezervasyonlari(d, "u1")], ["r2", "r1"]
        )


if __name__ == "__main__":
    unittest.main()
