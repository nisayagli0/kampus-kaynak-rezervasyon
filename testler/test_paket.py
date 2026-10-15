"""paket.py birim testleri. Çalıştırma: python -m unittest testler.test_paket -v"""

import os
import unittest
from datetime import datetime

from rezervasyon import paket, yukleyici
from rezervasyon.modeller import Rezervasyon

ORNEK = os.path.join(os.path.dirname(__file__), "ornek", "baslangic.json")


def t(saat, dakika=0):
    return datetime(2027, 3, 8, saat, dakika)


def kalem(kaynak, bas, bit):
    return {"kaynak": kaynak, "baslangic": bas, "bitis": bit}


class PaketTesti(unittest.TestCase):
    """u3: ARASTIRMACI, CIHAZ_EGITIMI, bakiye 300, güvenilirlik 80."""

    def setUp(self):
        self.d = yukleyici.yukle(ORNEK)
        self.iki = [kalem("CIH-1", t(14), t(16)), kalem("ODA-1", t(14), t(16))]

    def test_ornek_senaryo_12(self):
        sonuc = paket.paket(self.d, "u3", self.iki)
        self.assertEqual(sonuc, {
            "durum": "TAMAM", "paket_id": "p1", "rezervasyonlar": ["r1", "r2"],
            "ucretler": [48, 8], "toplam": 56, "bakiye": 244,
        })
        self.assertEqual(self.d.rezervasyonlar["r2"].paket, "p1")
        self.assertEqual(self.d.rezervasyonlar["r2"].ucret, 8)

    def test_bulunamadi(self):
        sonuc = paket.paket(self.d, "u9", self.iki)
        self.assertEqual((sonuc["kod"], sonuc["kalemler"]), ("BULUNAMADI", []))

    def test_boyut_sinirlari(self):
        odalar = [kalem("ODA-1", t(8 + 2 * i), t(9 + 2 * i)) for i in range(5)]
        for adet, beklenen in [(1, "RED"), (2, "TAMAM"), (4, "TAMAM"), (5, "RED")]:
            with self.subTest(adet=adet):
                d = yukleyici.yukle(ORNEK)
                sonuc = paket.paket(d, "u3", odalar[:adet])
                self.assertEqual(sonuc["durum"], beklenen)
                if beklenen == "RED":
                    self.assertEqual((sonuc["kod"], sonuc["kalemler"]), ("PAKET_BOYUTU", []))

    def test_guvenilirlik(self):
        self.d.kullanicilar["u3"].guvenilirlik = 49
        sonuc = paket.paket(self.d, "u3", self.iki)
        self.assertEqual((sonuc["kod"], sonuc["kalemler"]), ("GUVENILIRLIK_DUSUK", []))
        self.d.kullanicilar["u3"].guvenilirlik = 50
        self.assertEqual(paket.paket(self.d, "u3", self.iki)["durum"], "TAMAM")

    def test_paket_red_tum_kalemler_listelenir(self):
        kalemler = [kalem("ODA-1", t(14), t(16)), kalem("YAZ-2", t(14), t(15)),
                    kalem("ODA-2", t(14), t(14, 10))]
        sonuc = paket.paket(self.d, "u3", kalemler)
        self.assertEqual(sonuc, {"durum": "RED", "kod": "PAKET_RED", "kalemler": [
            {"sira": 0, "durum": "TAMAM"},
            {"sira": 1, "durum": "RED", "kod": "ROL_IZNI_YOK"},
            {"sira": 2, "durum": "RED", "kod": "ZAMAN_ADIMI_HATASI"},
        ]})
        self.assertEqual(self.d.rezervasyonlar, {})
        self.assertEqual(self.d.sayaclar, {"r": 0, "b": 0, "p": 0})

    def test_kalem_dogrulamasi_bakiyeye_bakmaz(self):
        self.d.kullanicilar["u3"].bakiye = 0
        sonuc = paket.paket(self.d, "u3", self.iki)
        self.assertEqual(sonuc["kod"], "BAKIYE_YETERSIZ")
        self.assertEqual(sonuc["kalemler"],
                         [{"sira": 0, "durum": "TAMAM"}, {"sira": 1, "durum": "TAMAM"}])

    def test_bakiye_yetersiz_ve_tam_esit(self):
        self.d.kullanicilar["u3"].bakiye = 55
        self.assertEqual(paket.paket(self.d, "u3", self.iki)["kod"], "BAKIYE_YETERSIZ")
        self.assertEqual(self.d.kullanicilar["u3"].bakiye, 55)
        self.d.kullanicilar["u3"].bakiye = 56
        self.assertEqual(paket.paket(self.d, "u3", self.iki)["bakiye"], 0)

    def ici_kesisme(self, a, b):
        sonuc = paket.paket(self.d, "u3", [a, b])
        return sonuc["durum"], sonuc.get("kod"), sonuc.get("kalemler")

    def test_paket_ici_kesisme(self):
        tamam = [{"sira": 0, "durum": "TAMAM"}, {"sira": 1, "durum": "TAMAM"}]
        self.assertEqual(self.ici_kesisme(kalem("ODA-1", t(10), t(12)), kalem("ODA-1", t(11), t(13))),
                         ("RED", "PAKET_ICI_KESISME", tamam))

    def test_paket_ici_hazirlik(self):
        # CIHAZ hazırlık 15 dk; ardışık 60 dk zaten daha geniş, ikisi de aynı kodu verir
        durum, kod, _ = self.ici_kesisme(kalem("CIH-1", t(10), t(11)), kalem("CIH-1", t(11), t(12)))
        self.assertEqual(kod, "PAKET_ICI_KESISME")

    def test_paket_ici_ardisik(self):
        durum, kod, _ = self.ici_kesisme(kalem("ODA-1", t(10), t(11)), kalem("ODA-1", t(11, 45), t(12, 30)))
        self.assertEqual(kod, "PAKET_ICI_KESISME")
        # tam 60 dk boşluk geçerli
        durum, kod, _ = self.ici_kesisme(kalem("ODA-1", t(10), t(11)), kalem("ODA-1", t(12), t(13)))
        self.assertEqual(durum, "TAMAM")

    def test_farkli_kaynaklar_kesisebilir(self):
        durum, _, _ = self.ici_kesisme(kalem("ODA-1", t(10), t(11)), kalem("ODA-2", t(10), t(11)))
        self.assertEqual(durum, "TAMAM")

    def test_kalemler_birbirinin_dolulugunu_etkilemez(self):
        # İki ODA kalemi aynı bantta: ikisi de boş banda göre 8 KP.
        # Biri diğerine katılsaydı ikinci kalem 120/240 = 0,5 -> 12 KP olurdu.
        sonuc = paket.paket(self.d, "u3", [kalem("ODA-1", t(8), t(10)), kalem("ODA-2", t(8), t(10))])
        self.assertEqual(sonuc["ucretler"], [8, 8])
        self.assertEqual([self.d.rezervasyonlar[r].ucret for r in sonuc["rezervasyonlar"]], [8, 8])

    def test_mevcut_rezervasyon_dolulugu_sayilir(self):
        self.d.rezervasyonlar["r1"] = Rezervasyon("r1", "u3", "ODA-2", t(8), t(10), 8)
        self.d.sayaclar["r"] = 1
        sonuc = paket.paket(self.d, "u3", [kalem("ODA-1", t(8), t(10)), kalem("ODA-1", t(12), t(13))])
        self.assertEqual(sonuc["ucretler"], [12, 4])
        self.assertEqual(sonuc["rezervasyonlar"], ["r2", "r3"])


if __name__ == "__main__":
    unittest.main()
