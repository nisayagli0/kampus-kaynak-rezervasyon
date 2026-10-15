"""dogrulama.py birim testleri (adım 1-8). Çalıştırma: python -m unittest testler.test_dogrulama -v"""

import os
import unittest
from datetime import datetime

from rezervasyon import yukleyici
from rezervasyon.dogrulama import dogrula
from rezervasyon.modeller import (
    Rezervasyon, ONAYLI, KULLANIMDA, TAMAMLANDI, IPTAL, GELMEDI,
)

ORNEK = os.path.join(os.path.dirname(__file__), "ornek", "baslangic.json")


def t(saat, dakika=0, gun=8):
    return datetime(2027, 3, gun, saat, dakika)


class DogrulamaTesti(unittest.TestCase):
    """Simüle saat 2027-03-08 08:00. u1 OGRENCI (sertifikasız), u3 ARASTIRMACI (CIHAZ_EGITIMI)."""

    def setUp(self):
        self.d = yukleyici.yukle(ORNEK)
        yukleyici.kullanici_ekle(self.d, "u1", "Ayşe", "OGRENCI", [], 120, 80)
        yukleyici.kaynak_ekle(self.d, "LAB-1", "Lab 1", "LAB", ["OGRENCI", "ARASTIRMACI"])

    def kod(self, bas, bit, kullanici="u1", kaynak="ODA-1"):
        return dogrula(self.d, kullanici, kaynak, bas, bit)

    def test_gecerli(self):
        self.assertIsNone(self.kod(t(10), t(11)))

    # 1
    def test_bulunamadi(self):
        self.assertEqual(self.kod(t(10), t(11), kullanici="u9"), "BULUNAMADI")
        self.assertEqual(self.kod(t(10), t(11), kaynak="X-1"), "BULUNAMADI")

    # 2
    def test_zaman_adimi(self):
        self.assertEqual(self.kod(t(13, 10), t(14)), "ZAMAN_ADIMI_HATASI")
        self.assertEqual(self.kod(t(13), t(14, 5)), "ZAMAN_ADIMI_HATASI")
        self.assertEqual(self.kod(t(14), t(13)), "ZAMAN_ADIMI_HATASI")

    def test_bitis_baslangica_esit(self):
        self.assertEqual(self.kod(t(11), t(11)), "ZAMAN_ADIMI_HATASI")  # varsayım 3

    # 3
    def test_gecmis_zaman(self):
        self.d.saat = t(10)
        self.assertEqual(self.kod(t(9, 45), t(11)), "GECMIS_ZAMAN")
        self.assertIsNone(self.kod(t(10), t(11)))  # tam simüle saat geçerli

    # 4
    def test_calisma_saati(self):
        self.assertIsNone(self.kod(t(8), t(9)))
        self.assertIsNone(self.kod(t(21), t(22)))  # bitiş 22:00 dahil değil, geçerli
        self.assertEqual(self.kod(t(21, 30), t(22, 15)), "CALISMA_SAATI_DISI")
        self.d.saat = t(7, gun=8)
        self.assertEqual(self.kod(t(7, 30), t(8, 30)), "CALISMA_SAATI_DISI")

    def test_gun_asimi(self):
        self.assertEqual(self.kod(t(21), t(9, gun=9)), "CALISMA_SAATI_DISI")

    # 5
    def test_sure_siniri(self):
        self.assertEqual(self.kod(t(10), t(10, 15)), "SURE_SINIRI")
        self.assertIsNone(self.kod(t(10), t(10, 30)))  # tam 30 dk
        self.assertIsNone(self.kod(t(10), t(13)))  # OGRENCI azami 180 dk
        self.assertEqual(self.kod(t(10), t(13, 15)), "SURE_SINIRI")

    def test_sure_rolun_azamisine_gore(self):
        self.assertIsNone(self.kod(t(10), t(18), kullanici="u3"))  # 480 dk

    # 6
    def test_ileri_tarih(self):
        # OGRENCI 7 gün: sınır 15 Mart 08:00 (dahil)
        self.assertIsNone(self.kod(t(8, gun=15), t(9, gun=15)))
        self.assertEqual(self.kod(t(8, 15, gun=15), t(9, gun=15)), "ILERI_TARIH_SINIRI")

    def test_ileri_tarih_guvenilirlik_dusuk(self):
        self.d.kullanicilar["u1"].guvenilirlik = 49
        self.assertIsNone(self.kod(t(8, gun=9), t(9, gun=9)))
        self.assertEqual(self.kod(t(8, 15, gun=9), t(9, gun=9)), "ILERI_TARIH_SINIRI")

    def test_guvenilirlik_tam_50_rol_siniri(self):
        self.d.kullanicilar["u1"].guvenilirlik = 50
        self.assertIsNone(self.kod(t(8, gun=15), t(9, gun=15)))

    # 7
    def test_rol_izni(self):
        self.assertEqual(self.kod(t(16, 30), t(17, 30), kaynak="CIH-1"), "ROL_IZNI_YOK")

    # 8
    def test_sertifika(self):
        self.assertEqual(self.kod(t(14), t(15), kaynak="LAB-1"), "SERTIFIKA_YOK")
        self.assertIsNone(self.kod(t(14), t(15), kullanici="u3", kaynak="CIH-1"))

    def test_sertifikasiz_tur(self):
        self.assertIsNone(self.kod(t(11), t(13), kaynak="YAZ-2"))

    # sıra
    def test_sira_adim_once_gecmisten(self):
        self.d.saat = t(12)
        self.assertEqual(self.kod(t(10, 10), t(11)), "ZAMAN_ADIMI_HATASI")

    def test_sira_rol_once_sertifikadan(self):
        # CIH-1 hem rol izni hem sertifika eksik: önce ROL_IZNI_YOK
        self.assertEqual(self.kod(t(14), t(15), kaynak="CIH-1"), "ROL_IZNI_YOK")


class Adim9_13Testi(unittest.TestCase):
    """YAZ-2: YAZICI, hazırlık 20 dk, bakım 08:00-10:00. ODA-1: hazırlık 0."""

    def setUp(self):
        self.d = yukleyici.yukle(ORNEK)
        yukleyici.kullanici_ekle(self.d, "u1", "Ayşe", "OGRENCI", [], 120, 80)
        yukleyici.kullanici_ekle(self.d, "u2", "Mehmet", "OGRENCI", [], 120, 80)

    def rez(self, kaynak, bas, bit, kullanici="u2", durum=ONAYLI):
        no = self.d.yeni_rezervasyon_no()
        self.d.rezervasyonlar[no] = Rezervasyon(no, kullanici, kaynak, bas, bit, 0, durum)

    def kod(self, bas, bit, kullanici="u1", kaynak="YAZ-2", bakiye_kontrolu=True):
        return dogrula(self.d, kullanici, kaynak, bas, bit, bakiye_kontrolu)

    # 9
    def test_bakim(self):
        self.assertEqual(self.kod(t(9, 30), t(10, 30)), "BAKIM")

    def test_bakim_bitisinde_baslayan_gecerli(self):
        self.assertIsNone(self.kod(t(10), t(11)))  # hazırlık uygulanmaz

    def test_bakim_baska_kaynakta_etkisiz(self):
        self.assertIsNone(self.kod(t(9), t(10), kaynak="ODA-1"))

    # 10
    def test_kesisme(self):
        self.rez("YAZ-2", t(14), t(16))
        self.assertEqual(self.kod(t(15), t(17)), "KESISME")
        self.assertEqual(self.kod(t(13), t(14, 15)), "KESISME")

    def test_kullanimda_kesisir(self):
        self.rez("YAZ-2", t(14), t(16), durum=KULLANIMDA)
        self.assertEqual(self.kod(t(15), t(16)), "KESISME")

    def test_gelmedi_ve_iptal_sayilmaz(self):
        self.rez("YAZ-2", t(14), t(16), durum=GELMEDI)
        self.rez("YAZ-2", t(14), t(16), durum=IPTAL)
        self.assertIsNone(self.kod(t(14), t(16)))

    # 11
    def test_hazirlik_sonra(self):
        # K3 örneği: 14:00-16:00, h=20 -> 16:15 red, 16:30 kabul
        self.rez("YAZ-2", t(14), t(16))
        self.assertEqual(self.kod(t(16, 15), t(17)), "HAZIRLIK_IHLALI")
        self.assertIsNone(self.kod(t(16, 30), t(17, 30)))

    def test_hazirlik_once(self):
        # talep bitişi + 20 dk mevcut başlangıcı geçmemeli
        self.rez("YAZ-2", t(14), t(16))
        self.assertEqual(self.kod(t(12, 45), t(13, 45)), "HAZIRLIK_IHLALI")
        self.assertIsNone(self.kod(t(12, 30), t(13, 30)))

    def test_hazirlik_sifir_odada_bitiste_baslar(self):
        self.rez("ODA-1", t(14), t(16))
        self.assertIsNone(self.kod(t(16), t(17), kaynak="ODA-1"))

    def test_tamamlandi_hazirlikta_sayilir_kesismede_sayilmaz(self):
        self.d.saat = t(16)
        self.rez("YAZ-2", t(14), t(16), durum=TAMAMLANDI)
        self.assertEqual(self.kod(t(16), t(17)), "HAZIRLIK_IHLALI")
        # çakışan TAMAMLANDI kayıt KESISME değil, hazırlık kuralıyla yakalanır
        self.rez("ODA-1", t(14), t(16, 30), durum=TAMAMLANDI)
        self.assertEqual(self.kod(t(16), t(17), kaynak="ODA-1"), "HAZIRLIK_IHLALI")

    # 12
    def test_ardisik_sinirlar(self):
        self.rez("ODA-1", t(10), t(11), kullanici="u1")
        self.assertIsNone(self.kod(t(12), t(13), kaynak="ODA-1"))  # tam 60 dk
        self.assertEqual(self.kod(t(11, 45), t(12, 30), kaynak="ODA-1"), "ARDISIK_KULLANIM")
        self.assertEqual(self.kod(t(8, 15), t(9, 15), kaynak="ODA-1"), "ARDISIK_KULLANIM")

    def test_ardisik_tamamlandi_sayilir(self):
        self.d.saat = t(11)
        self.rez("ODA-1", t(10), t(11), kullanici="u1", durum=TAMAMLANDI)
        self.assertEqual(self.kod(t(11, 30), t(12), kaynak="ODA-1"), "ARDISIK_KULLANIM")

    def test_ardisik_baska_kullanici_veya_kaynak(self):
        self.rez("ODA-1", t(10), t(11), kullanici="u2")
        self.assertIsNone(self.kod(t(11), t(12), kaynak="ODA-1"))
        self.rez("ODA-2", t(13), t(14), kullanici="u1")
        self.assertIsNone(self.kod(t(14), t(15), kaynak="ODA-1"))

    def test_ardisik_iptal_sayilmaz(self):
        self.rez("ODA-1", t(10), t(11), kullanici="u1", durum=IPTAL)
        self.assertIsNone(self.kod(t(11), t(12), kaynak="ODA-1"))

    # 13
    def test_bakiye_yetersiz(self):
        self.d.kullanicilar["u1"].bakiye = 11
        self.assertEqual(self.kod(t(8), t(9), kaynak="ODA-1"), None)  # ücret 4
        self.assertEqual(self.kod(t(10), t(11)), "BAKIYE_YETERSIZ")  # ücret 18

    def test_bakiye_tam_esit_gecerli(self):
        self.d.kullanicilar["u1"].bakiye = 18
        self.assertIsNone(self.kod(t(10), t(11)))

    def test_bakiye_kontrolu_kapali(self):
        self.d.kullanicilar["u1"].bakiye = 0
        self.assertIsNone(self.kod(t(10), t(11), bakiye_kontrolu=False))

    # sıra
    def test_sira_bakim_once_kesismeden(self):
        self.rez("YAZ-2", t(9, 30), t(10, 30), durum=ONAYLI)
        self.assertEqual(self.kod(t(9, 30), t(10, 30)), "BAKIM")

    def test_sira_hazirlik_once_ardisiktan(self):
        self.rez("YAZ-2", t(11), t(13), kullanici="u1")
        self.assertEqual(self.kod(t(13, 15), t(14)), "HAZIRLIK_IHLALI")


if __name__ == "__main__":
    unittest.main()
