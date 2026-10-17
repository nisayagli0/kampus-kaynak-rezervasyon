"""bekleme.py testleri (K9). Çalıştırma: python -m unittest testler.test_bekleme -v"""

import unittest
from datetime import datetime

from rezervasyon import bekleme, durum_makinesi, talep
from rezervasyon.modeller import (
    BeklemeKaydi,
    Durum,
    Kaynak,
    KaynakTuru,
    Kullanici,
    Rol,
    ONAYLI,
    KULLANIMDA,
    IPTAL,
)


def an(saat, dakika=0):
    """8 Mart 2027 günü, verilen saat ve dakika."""
    return datetime(2027, 3, 8, saat, dakika)


def durum_kur():
    """Saat 08:00. Tek YAZICI kaynağı (YAZ-1), dört kullanıcı (bakiye 120, güvenilirlik 80)."""
    d = Durum(saat=an(8))
    d.turler["YAZICI"] = KaynakTuru("YAZICI", 20, 12, True, None)
    d.roller["OGRENCI"] = Rol("OGRENCI", 120, 7, 180)
    d.kaynaklar["YAZ-1"] = Kaynak("YAZ-1", "3B Yazıcı 1", "YAZICI", ["OGRENCI"])
    for uid in ("u1", "u2", "u3", "u4"):
        d.kullanicilar[uid] = Kullanici(uid, uid, "OGRENCI", [], 120, 80)
    return d


def rezervasyon_yap(d, kullanici, baslangic, bitis):
    """Doğrulamasız rezervasyon (numara ve bakiye düşümü gerçek akıştaki gibi)."""
    return talep.rezervasyon_olustur(d, kullanici, "YAZ-1", baslangic, bitis)


def kayit_ekle(d, no, kullanici, baslangic, bitis, kayit_saati):
    d.beklemeler[no] = BeklemeKaydi(
        no, kullanici, "YAZ-1", baslangic, bitis, kayit_saati
    )


class AcTesti(unittest.TestCase):
    def test_kesisme_nedeniyle_kayit_acilir(self):
        d = durum_kur()
        rezervasyon_yap(d, "u1", an(11), an(13))
        sonuc = bekleme.ac(d, "u2", "YAZ-1", an(12), an(13))
        self.assertEqual(sonuc, {"durum": "TAMAM", "bekleme_id": "b1", "sira": 1})
        kayit = d.beklemeler["b1"]
        self.assertEqual((kayit.kullanici, kayit.kayit_saati), ("u2", an(8)))

    def test_hazirlik_ihlali_nedeniyle_kayit_acilir(self):
        d = durum_kur()
        rezervasyon_yap(d, "u1", an(11), an(13))  # hazırlık 13:20'de biter
        sonuc = bekleme.ac(d, "u2", "YAZ-1", an(13, 15), an(14))
        self.assertEqual(sonuc, {"durum": "TAMAM", "bekleme_id": "b1", "sira": 1})

    def test_gecerli_talepte_bekleme_gereksiz_ve_numara_tuketilmez(self):
        d = durum_kur()
        self.assertEqual(
            bekleme.ac(d, "u1", "YAZ-1", an(11), an(13)),
            {"durum": "RED", "kod": "BEKLEME_GEREKSIZ"},
        )
        self.assertEqual(d.beklemeler, {})
        rezervasyon_yap(d, "u4", an(11), an(13))
        self.assertEqual(
            bekleme.ac(d, "u2", "YAZ-1", an(12), an(13))["bekleme_id"], "b1"
        )

    def test_baska_hata_kodu_aynen_doner(self):
        d = durum_kur()
        self.assertEqual(
            bekleme.ac(d, "u1", "YAZ-1", an(11, 10), an(13))["kod"],
            "ZAMAN_ADIMI_HATASI",
        )
        self.assertEqual(
            bekleme.ac(d, "u99", "YAZ-1", an(11), an(13))["kod"], "BULUNAMADI"
        )
        self.assertEqual(d.beklemeler, {})

    def test_yalniz_bakiye_yetmeyen_talepte_bekleme_gereksiz(self):
        d = durum_kur()
        d.kullanicilar["u2"].bakiye = 0  # aralık boş, tek sorun bakiye
        self.assertEqual(
            bekleme.ac(d, "u2", "YAZ-1", an(11), an(13))["kod"], "BEKLEME_GEREKSIZ"
        )

    def test_kayit_acilirken_bakiye_kontrol_edilmez(self):
        d = durum_kur()
        rezervasyon_yap(d, "u1", an(11), an(13))
        d.kullanicilar["u2"].bakiye = 0
        self.assertEqual(bekleme.ac(d, "u2", "YAZ-1", an(12), an(13))["durum"], "TAMAM")

    def test_ardisik_kullanim_kayit_acmaz(self):
        d = durum_kur()
        rezervasyon_yap(d, "u1", an(11), an(12))
        # 12:30 başlangıç: kesişme ve hazırlık yok, ama aynı kullanıcıda 60 dk boşluk yok
        sonuc = bekleme.ac(d, "u1", "YAZ-1", an(12, 30), an(13, 30))
        self.assertEqual(sonuc, {"durum": "RED", "kod": "ARDISIK_KULLANIM"})
        self.assertEqual(d.beklemeler, {})

    def test_sira_tarama_sirasindaki_yerdir(self):
        d = durum_kur()
        d.kullanicilar["u3"].guvenilirlik = 90
        rezervasyon_yap(d, "u4", an(11), an(13))
        self.assertEqual(bekleme.ac(d, "u2", "YAZ-1", an(12), an(13))["sira"], 1)  # b1
        self.assertEqual(
            bekleme.ac(d, "u3", "YAZ-1", an(12), an(13))["sira"], 1
        )  # b2, 90 önde
        self.assertEqual(
            bekleme.ac(d, "u1", "YAZ-1", an(12), an(13))["sira"], 3
        )  # b3, b1'den sonra


class TaraTesti(unittest.TestCase):
    def test_bos_liste(self):
        self.assertEqual(bekleme.tara(durum_kur(), "YAZ-1"), [])

    def test_yer_bosalinca_kayit_rezervasyona_donusur(self):
        d = durum_kur()
        rezervasyon_yap(d, "u1", an(11), an(13))  # r1, ücret 36
        bekleme.ac(d, "u2", "YAZ-1", an(12), an(13))  # b1
        d.rezervasyonlar["r1"].durum = IPTAL
        d.saat = an(11, 15)

        olaylar = bekleme.tara(d, "YAZ-1")

        self.assertEqual(
            olaylar,
            [
                {
                    "zaman": "2027-03-08T11:15",
                    "tur": "OTOMATIK_ATAMA",
                    "bekleme": "b1",
                    "rezervasyon": "r2",
                    "kullanici": "u2",
                    "ucret": 18,
                    "bakiye": 102,
                }
            ],
        )
        self.assertNotIn("b1", d.beklemeler)
        self.assertEqual(d.rezervasyonlar["r2"].durum, ONAYLI)

    def test_gecemeyen_kayit_listede_kalir_ve_tarama_devam_eder(self):
        d = durum_kur()
        rezervasyon_yap(d, "u1", an(11), an(13))  # r1, yerinde kalacak
        rezervasyon_yap(d, "u4", an(15), an(16))  # r2, iptal edilecek
        bekleme.ac(d, "u2", "YAZ-1", an(12), an(13))  # b1: r1 yüzünden bekler
        bekleme.ac(d, "u3", "YAZ-1", an(15, 15), an(16))  # b2: r2 yüzünden bekler
        d.rezervasyonlar["r2"].durum = IPTAL
        d.saat = an(11, 15)

        olaylar = bekleme.tara(d, "YAZ-1")

        self.assertEqual(
            [(o["bekleme"], o["kullanici"]) for o in olaylar], [("b2", "u3")]
        )
        self.assertEqual(list(d.beklemeler), ["b1"])

    def test_guvenilirligi_yuksek_kayit_once_gelir(self):
        d = durum_kur()
        d.kullanicilar["u3"].guvenilirlik = 90
        rezervasyon_yap(d, "u4", an(11), an(13))
        bekleme.ac(d, "u2", "YAZ-1", an(12), an(13))  # b1, güvenilirlik 80
        bekleme.ac(d, "u3", "YAZ-1", an(12), an(13))  # b2, güvenilirlik 90
        d.rezervasyonlar["r1"].durum = IPTAL

        olaylar = bekleme.tara(d, "YAZ-1")

        self.assertEqual([o["bekleme"] for o in olaylar], ["b2"])  # b1 artık kesişiyor
        self.assertEqual(list(d.beklemeler), ["b1"])

    def test_esit_guvenilirlikte_numara_sayisal_siralanir(self):
        d = durum_kur()
        kayit_ekle(
            d, "b10", "u2", an(12), an(13), an(8)
        )  # önce eklendi ama numarası büyük
        kayit_ekle(d, "b2", "u3", an(12), an(13), an(8))
        olaylar = bekleme.tara(d, "YAZ-1")
        self.assertEqual([o["bekleme"] for o in olaylar], ["b2"])

    def test_esit_guvenilirlikte_once_kaydolan_gelir(self):
        d = durum_kur()
        kayit_ekle(d, "b1", "u2", an(12), an(13), an(7, 30))
        kayit_ekle(d, "b2", "u3", an(12), an(13), an(7, 0))  # daha erken kaydolmuş
        olaylar = bekleme.tara(d, "YAZ-1")
        self.assertEqual([o["bekleme"] for o in olaylar], ["b2"])

    def test_bakiyesi_yetmeyen_kayit_listede_kalir(self):
        d = durum_kur()
        d.kullanicilar["u2"].bakiye = 5  # ücret 18
        kayit_ekle(d, "b1", "u2", an(12), an(13), an(8))
        self.assertEqual(bekleme.tara(d, "YAZ-1"), [])
        self.assertIn("b1", d.beklemeler)

    def test_baska_kaynagin_kayitlari_taranmaz(self):
        d = durum_kur()
        d.kaynaklar["YAZ-2"] = Kaynak("YAZ-2", "3B Yazıcı 2", "YAZICI", ["OGRENCI"])
        d.beklemeler["b1"] = BeklemeKaydi("b1", "u2", "YAZ-2", an(12), an(13), an(8))
        self.assertEqual(bekleme.tara(d, "YAZ-1"), [])
        self.assertIn("b1", d.beklemeler)


class GecmisleriSilTesti(unittest.TestCase):
    def test_baslangici_saatten_once_olan_silinir(self):
        d = durum_kur()
        kayit_ekle(d, "b1", "u2", an(12), an(13), an(8))
        d.saat = an(12)  # başlangıç tam şimdi: silinmez
        bekleme.gecmisleri_sil(d)
        self.assertIn("b1", d.beklemeler)
        d.saat = an(12, 15)
        bekleme.gecmisleri_sil(d)
        self.assertNotIn("b1", d.beklemeler)


class IptalVeCikisTesti(unittest.TestCase):
    """durum_makinesi, boşalan yer için bekleme.tara'yı çağırır; olaylar sonuca girer."""

    def test_iptal_sonucunda_otomatik_atama_olayi(self):
        d = durum_kur()
        rezervasyon_yap(d, "u1", an(11), an(13))  # r1, ücret 36, u1 bakiye 84
        bekleme.ac(d, "u2", "YAZ-1", an(12), an(13))  # b1

        sonuc = durum_makinesi.iptal(d, "r1")  # başlangıca 3 saat var: %50 iade

        self.assertEqual(sonuc["iade"], 18)
        self.assertEqual(sonuc["bakiye"], 102)
        self.assertEqual(
            sonuc["olaylar"],
            [
                {
                    "zaman": "2027-03-08T08:00",
                    "tur": "OTOMATIK_ATAMA",
                    "bekleme": "b1",
                    "rezervasyon": "r2",
                    "kullanici": "u2",
                    "ucret": 18,
                    "bakiye": 102,
                }
            ],
        )

    def test_cikis_sonucunda_otomatik_atama_olayi(self):
        d = durum_kur()
        rezervasyon_yap(d, "u1", an(11), an(13))
        d.rezervasyonlar["r1"].durum = KULLANIMDA
        bekleme.ac(d, "u2", "YAZ-1", an(12), an(13))  # b1
        d.saat = an(11, 30)

        sonuc = durum_makinesi.cikis(d, "r1")

        self.assertEqual(sonuc["yeni_durum"], "TAMAMLANDI")
        self.assertEqual(
            sonuc["olaylar"],
            [
                {
                    "zaman": "2027-03-08T11:30",
                    "tur": "OTOMATIK_ATAMA",
                    "bekleme": "b1",
                    "rezervasyon": "r2",
                    "kullanici": "u2",
                    "ucret": 18,
                    "bakiye": 102,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
