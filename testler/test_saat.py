"""saat.py testleri (K11). Çalıştırma: python -m unittest testler.test_saat -v"""

import unittest
from datetime import datetime

from rezervasyon import bekleme, durum_makinesi, saat, talep
from rezervasyon.modeller import (
    BeklemeKaydi,
    Durum,
    Kaynak,
    KaynakTuru,
    Kullanici,
    Rol,
    TAMAMLANDI,
    GELMEDI,
)


def an(saat_, dakika=0, gun=8):
    """Mart 2027 (8 Mart Pazartesi), verilen gün/saat/dakika."""
    return datetime(2027, 3, gun, saat_, dakika)


def durum_kur():
    """Saat 08:00 Pazartesi. Tek YAZICI kaynağı, üç kullanıcı (bakiye 120, güvenilirlik 80)."""
    d = Durum(saat=an(8))
    d.turler["YAZICI"] = KaynakTuru("YAZICI", 20, 12, True, None)
    d.roller["OGRENCI"] = Rol("OGRENCI", 120, 7, 180)
    d.kaynaklar["YAZ-1"] = Kaynak("YAZ-1", "3B Yazıcı 1", "YAZICI", ["OGRENCI"])
    for uid in ("u1", "u2", "u3"):
        d.kullanicilar[uid] = Kullanici(uid, uid, "OGRENCI", [], 120, 80)
    return d


def rez(d, kullanici, baslangic, bitis):
    return talep.rezervasyon_olustur(d, kullanici, "YAZ-1", baslangic, bitis)


class SaatTesti(unittest.TestCase):
    def test_geri_gitmek_red_ve_durum_degismez(self):
        d = durum_kur()
        self.assertEqual(saat.ilerlet(d, an(7)), {"durum": "RED", "kod": "SAAT_GERI"})
        self.assertEqual(d.saat, an(8))

    def test_ayni_saat_tamam_ve_olay_yok(self):
        d = durum_kur()
        self.assertEqual(saat.ilerlet(d, an(8)), {"durum": "TAMAM", "olaylar": []})

    def test_gelmedi_tam_on_besinci_dakikada(self):
        d = durum_kur()
        rez(d, "u1", an(11), an(13))
        self.assertEqual(saat.ilerlet(d, an(11, 14))["olaylar"], [])
        sonuc = saat.ilerlet(d, an(11, 15))
        self.assertEqual(
            sonuc["olaylar"],
            [
                {
                    "zaman": "2027-03-08T11:15",
                    "tur": "GELMEDI",
                    "rezervasyon": "r1",
                    "kullanici": "u1",
                    "guvenilirlik": 65,
                }
            ],
        )
        self.assertEqual(d.rezervasyonlar["r1"].durum, GELMEDI)

    def test_tamamlandi_bitis_aninda(self):
        d = durum_kur()
        rez(d, "u1", an(9), an(10))
        d.saat = an(9)
        durum_makinesi.giris(d, "r1")
        sonuc = saat.ilerlet(d, an(10))
        self.assertEqual(
            sonuc["olaylar"],
            [
                {
                    "zaman": "2027-03-08T10:00",
                    "tur": "TAMAMLANDI",
                    "rezervasyon": "r1",
                    "kullanici": "u1",
                    "guvenilirlik": 82,
                }
            ],
        )
        self.assertEqual(d.rezervasyonlar["r1"].durum, TAMAMLANDI)

    def test_gelmedi_sonrasi_bekleme_otomatik_atanir(self):
        d = durum_kur()
        rez(d, "u1", an(11), an(13))
        bekleme.ac(d, "u2", "YAZ-1", an(12), an(13))
        olaylar = saat.ilerlet(d, an(11, 15))["olaylar"]
        self.assertEqual([o["tur"] for o in olaylar], ["GELMEDI", "OTOMATIK_ATAMA"])
        self.assertEqual(olaylar[1]["kullanici"], "u2")
        self.assertEqual(d.beklemeler, {})

    def test_olaylar_zaman_sirasiyla(self):
        d = durum_kur()
        rez(d, "u1", an(9), an(10))  # r1 gelmeyecek: 09:15
        rez(d, "u2", an(11), an(12))  # r2: 11:15
        olaylar = saat.ilerlet(d, an(12))["olaylar"]
        self.assertEqual(
            [(o["zaman"], o["rezervasyon"]) for o in olaylar],
            [("2027-03-08T09:15", "r1"), ("2027-03-08T11:15", "r2")],
        )

    def test_haftalik_sifirlama_pazartesi_gecesi(self):
        d = durum_kur()
        d.saat = an(20, gun=7)  # Pazar
        d.kullanicilar["u1"].bakiye = 10
        olaylar = saat.ilerlet(d, an(8))["olaylar"]
        self.assertEqual(
            olaylar, [{"zaman": "2027-03-08T00:00", "tur": "HAFTALIK_SIFIRLAMA"}]
        )
        self.assertEqual(d.kullanicilar["u1"].bakiye, 120)

    def test_gecmis_bekleme_kayitlari_silinir(self):
        d = durum_kur()
        d.beklemeler["b1"] = BeklemeKaydi("b1", "u2", "YAZ-1", an(9), an(10), an(8))
        saat.ilerlet(d, an(9, 1))
        self.assertEqual(d.beklemeler, {})
        self.assertEqual(d.saat, an(9, 1))


if __name__ == "__main__":
    unittest.main()
