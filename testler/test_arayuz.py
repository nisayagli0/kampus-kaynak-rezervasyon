"""Arayüz testleri (ekransız çalışır). Çalıştırma: python -m unittest testler.test_arayuz -v

Arayüzün tüm komutları Oturum üzerinden modüle gider. Bu yüzden örnek senaryoyu Oturum'dan
oynatmak, "arayüzden 19 komut" denetiminin otomatik karşılığıdır.
"""

import json
import os
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from arayuz import mesajlar  # noqa: E402
from arayuz.ana_pencere import AnaPencere  # noqa: E402
from arayuz.oturum import Oturum  # noqa: E402
from arayuz.saat_denetimi import sonraki_gun_sabahi, sonraki_pazartesi  # noqa: E402
from arayuz.takvim import _serit_ata  # noqa: E402
from arayuz.talep_formu import varsayilan_aralik  # noqa: E402
from rezervasyon.modeller import Rezervasyon  # noqa: E402

_uygulama = QApplication.instance() or QApplication([])
ORNEK_KLASORU = Path(__file__).parent / "ornek"

KUCUK_BASLANGIC = {
    "saat": "2027-03-08T08:00",
    "kaynak_turleri": {
        "ODA": {"hazirlik_dk": 0, "temel_ucret": 4, "enerji_yogun": False, "sertifika": None},
        "YAZICI": {"hazirlik_dk": 20, "temel_ucret": 12, "enerji_yogun": True, "sertifika": None},
    },
    "roller": {"OGRENCI": {"haftalik_kota": 120, "ileri_gun": 7, "azami_sure_dk": 180}},
    "kaynaklar": [
        {"id": "YAZ-1", "ad": "Yazıcı 1", "tur": "YAZICI", "izinli_roller": ["OGRENCI"]},
        {"id": "ODA-1", "ad": "Oda 1", "tur": "ODA", "izinli_roller": ["OGRENCI"]},
    ],
    "bakim_pencereleri": [],
    "kullanicilar": [
        {"id": "u1", "ad": "Ayşe", "rol": "OGRENCI", "sertifikalar": [], "bakiye": 120,
         "guvenilirlik": 80},
        {"id": "u2", "ad": "Mehmet", "rol": "OGRENCI", "sertifikalar": [], "bakiye": 120,
         "guvenilirlik": 80},
    ],
}


def _gecici_dosya(klasor, ad, veri):
    yol = Path(klasor) / ad
    yol.write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
    return str(yol)


def _komut_uygula(oturum, satir):
    """komutlar.jsonl satırını Oturum üzerinden çalıştırır (isleyici ile aynı eşleme)."""
    alanlar = dict(satir)
    ad = alanlar.pop("komut")
    if ad == "sorgu":
        ad = "sorgu_" + alanlar.pop("tur")
    return oturum.komut(ad, **alanlar)


def _farklar(beklenen, cikti):
    """Beklenen satırdaki her alan çıktıda aynı değerle olmalı; fazladan alan hata değil."""
    return [f"{alan}: beklenen {deger!r}, çıktı {cikti.get(alan, 'YOK')!r}"
            for alan, deger in beklenen.items() if cikti.get(alan, object()) != deger]


class OturumTesti(unittest.TestCase):
    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory()
        self.addCleanup(self.klasor.cleanup)
        self.dosya = _gecici_dosya(self.klasor.name, "baslangic.json", KUCUK_BASLANGIC)

    def test_komut_adi_ad_alaniyla_cakismaz(self):
        # kullanici_ekle komutunun `ad` alanı, komut() işlevinin kendi parametresiyle çakışmamalı
        oturum = Oturum()
        oturum.yukle(self.dosya)
        sonuc = oturum.komut("kullanici_ekle", id="u3", ad="Yeni", rol="OGRENCI",
                             sertifikalar=[], bakiye=120, guvenilirlik=80)
        self.assertEqual(sonuc["durum"], "TAMAM")
        self.assertEqual(oturum.secili_kullanici, "u3")

    def test_sonuclar_bolum_5_bicimindedir_ve_gunluge_yazilir(self):
        oturum = Oturum()
        oturum.yukle(self.dosya)
        s1 = oturum.komut("rezervasyon", kullanici="u1", kaynak="YAZ-1",
                          baslangic="2027-03-08T11:00", bitis="2027-03-08T13:00")
        s2 = oturum.komut("rezervasyon", kullanici="u2", kaynak="YAZ-1",
                          baslangic="2027-03-08T12:00", bitis="2027-03-08T13:00")
        self.assertEqual((s1["no"], s1["komut"], s1["durum"], s1["ucret"], s1["bakiye"]),
                         (1, "rezervasyon", "TAMAM", 36, 84))
        self.assertEqual((s2["no"], s2["durum"], s2["kod"]), (2, "RED", "KESISME"))
        self.assertEqual(len(oturum.gunluk), 2)

    def test_sorgu_komut_adi_sorgu_olarak_yazilir(self):
        oturum = Oturum()
        oturum.yukle(self.dosya)
        sonuc = oturum.komut("sorgu_kullanici", id="u1")
        self.assertEqual(sonuc["komut"], "sorgu")

    def test_dosya_yeniden_yuklenince_her_sey_sifirlanir(self):
        oturum = Oturum()
        oturum.yukle(self.dosya)
        oturum.komut("rezervasyon", kullanici="u1", kaynak="YAZ-1",
                     baslangic="2027-03-08T11:00", bitis="2027-03-08T13:00")
        oturum.yukle(self.dosya)
        self.assertEqual(oturum.gunluk, [])
        self.assertEqual(oturum.durum.rezervasyonlar, {})
        self.assertIsNone(oturum.secili_rezervasyon)

    def test_gecersiz_dosyada_eski_durum_korunur(self):
        oturum = Oturum()
        oturum.yukle(self.dosya)
        kotu = Path(self.klasor.name) / "kotu.json"
        kotu.write_text("{bozuk", encoding="utf-8")
        with self.assertRaises(Exception):
            oturum.yukle(str(kotu))
        self.assertIsNotNone(oturum.durum)
        self.assertIn("u1", oturum.durum.kullanicilar)

    def test_saat_ilerleyince_secili_gun_simule_gune_tasinir(self):
        oturum = Oturum()
        oturum.yukle(self.dosya)
        oturum.gun_sec(date(2027, 3, 12))
        oturum.komut("saat", zaman="2027-03-09T08:00")
        self.assertEqual(oturum.secili_gun, date(2027, 3, 9))


class OrnekSenaryoTesti(unittest.TestCase):
    @unittest.skipUnless((ORNEK_KLASORU / "komutlar.jsonl").exists(), "örnek dosyalar yok")
    def test_19_komut_oturum_uzerinden_beklenenle_ayni(self):
        oturum = Oturum()
        oturum.yukle(str(ORNEK_KLASORU / "baslangic.json"))
        komutlar = [json.loads(s) for s in (ORNEK_KLASORU / "komutlar.jsonl").read_text(
            encoding="utf-8").splitlines() if s.strip()]
        beklenenler = [json.loads(s) for s in (ORNEK_KLASORU / "sonuclar.jsonl").read_text(
            encoding="utf-8").splitlines() if s.strip()]
        self.assertEqual(len(komutlar), len(beklenenler))
        for sira, (komut, beklenen) in enumerate(zip(komutlar, beklenenler), 1):
            with self.subTest(komut=sira):
                cikti = _komut_uygula(oturum, komut)
                self.assertEqual(_farklar(beklenen, cikti), [])
        self.assertEqual(len(oturum.gunluk), len(komutlar))


class AnaPencereTesti(unittest.TestCase):
    def setUp(self):
        self.klasor = tempfile.TemporaryDirectory()
        self.addCleanup(self.klasor.cleanup)
        self.dosya = _gecici_dosya(self.klasor.name, "baslangic.json", KUCUK_BASLANGIC)
        self.pencere = AnaPencere()
        self.pencere.resize(1360, 820)
        self.pencere.show()
        _uygulama.processEvents()
        self.addCleanup(self.pencere.close)

    def test_dosya_secilmeden_arayuz_bos_ama_calisir(self):
        self.assertEqual(self.pencere.etiket_saat.text(), "--")
        self.assertFalse(self.pencere.dugme_kullanici.isEnabled())

    def test_dosya_yuklenince_saat_ve_listeler_dolar(self):
        self.pencere.dosya_yukle(self.dosya)
        self.assertIn("08:00", self.pencere.etiket_saat.text())
        self.assertIn("Pazartesi", self.pencere.etiket_saat.text())
        self.assertEqual(self.pencere.talep_formu.kaynak.count(), 2)
        self.assertEqual(self.pencere.talep_formu.kullanici.count(), 2)

    def test_bozuk_dosyada_hata_ust_cubukta_gorunur(self):
        kotu = Path(self.klasor.name) / "kotu.json"
        kotu.write_text("{bozuk", encoding="utf-8")
        self.pencere.dosya_yukle(str(kotu))
        self.assertIn("Yüklenemedi", self.pencere.etiket_dosya.text())

    def test_form_red_sonrasi_bekleme_dugmesi_ve_bekleme_kaydi(self):
        self.pencere.dosya_yukle(self.dosya)
        oturum, form = self.pencere.oturum, self.pencere.talep_formu
        oturum.komut("rezervasyon", kullanici="u1", kaynak="YAZ-1",
                     baslangic="2027-03-08T11:00", bitis="2027-03-08T13:00")
        oturum.kullanici_sec("u2")
        form.kaynak.setCurrentIndex(form._kaynak_kimlikleri.index("YAZ-1"))
        form.bas.setCurrentText("12:00")
        form.bit.setCurrentText("13:00")
        form._tekil_gonder("rezervasyon")
        self.assertIn("KESISME", form.sonuc.text())
        self.assertFalse(form.dugme_bekleme.isHidden())
        form._bekleme_ac()
        self.assertIn("sıranız: 1", form.sonuc.text())
        self.assertEqual(len(oturum.durum.beklemeler), 1)

    def test_gecerli_talep_bekleme_dugmesi_gostermez(self):
        self.pencere.dosya_yukle(self.dosya)
        form = self.pencere.talep_formu
        form._tekil_gonder("rezervasyon")
        self.assertTrue(form.dugme_bekleme.isHidden())
        self.assertIn("Rezervasyon alındı", form.sonuc.text())

    def test_paket_red_kalem_satirlarinda_gorunur(self):
        self.pencere.dosya_yukle(self.dosya)
        form = self.pencere.talep_formu
        form.kalemler[0].bas.setCurrentText("08:00")
        form.kalemler[0].bit.setCurrentText("09:00")
        form.kalemler[1].bas.setCurrentText("22:00")  # çalışma saati dışı
        form.kalemler[1].bit.setCurrentText("22:15")
        form._paket_gonder()
        self.assertIn("PAKET_RED", form.paket_sonuc.text())
        self.assertEqual(form.kalemler[0].sonuc.text(), "Geçti")
        self.assertIn("CALISMA_SAATI_DISI", form.kalemler[1].sonuc.text())

    def test_giris_iptal_sonucu_kartta_gorunur(self):
        self.pencere.dosya_yukle(self.dosya)
        oturum = self.pencere.oturum
        oturum.komut("rezervasyon", kullanici="u1", kaynak="YAZ-1",
                     baslangic="2027-03-08T11:00", bitis="2027-03-08T13:00")
        _uygulama.processEvents()
        karti = self.pencere.detay
        self.assertTrue(karti.eylemler.dugme_iptal.isEnabled())
        karti.eylemler._calistir("giris")  # saat 08:00, giriş penceresi dışı
        self.assertIn("GIRIS_PENCERESI_DISI", karti.eylemler.sonuc.text())
        karti.eylemler._calistir("iptal")
        self.assertIn("İptal edildi", karti.eylemler.sonuc.text())

    def test_saat_denetimi_olaylari_listeler(self):
        self.pencere.dosya_yukle(self.dosya)
        oturum = self.pencere.oturum
        oturum.komut("rezervasyon", kullanici="u1", kaynak="YAZ-1",
                     baslangic="2027-03-08T11:00", bitis="2027-03-08T13:00")
        saat = self.pencere.sag.widget(2)
        saat._git(datetime(2027, 3, 8, 11, 15))
        self.assertEqual(saat.olaylar.count(), 1)
        self.assertIn("Gelmedi", saat.olaylar.item(0).text())
        saat._git(datetime(2027, 3, 8, 9, 0))  # geri
        self.assertIn("SAAT_GERI", saat.mesaj.text())

    def test_ekleme_diyalogu_red_ve_basari(self):
        from arayuz.ekleme_diyaloglari import KaynakEkleDiyalogu, KullaniciEkleDiyalogu
        self.pencere.dosya_yukle(self.dosya)
        oturum = self.pencere.oturum
        diyalog = KullaniciEkleDiyalogu(oturum, self.pencere)
        diyalog.kimlik.setText("u1")
        diyalog._gonder()
        self.assertIn("ID_MEVCUT", diyalog.hata.text())
        diyalog.kimlik.setText("u7")
        diyalog.ad.setText("Yeni")
        diyalog._gonder()
        self.assertIn("u7", oturum.durum.kullanicilar)
        kaynak = KaynakEkleDiyalogu(oturum, self.pencere)
        self.assertEqual(kaynak.kimlik.text(), "ODA-2")  # ilk tür ODA; öneri mevcut adlandırmaya uyar
        kaynak.tur.setCurrentText("YAZICI")
        self.assertEqual(kaynak.kimlik.text(), "YAZ-2")
        kaynak._gonder()
        self.assertIn("YAZ-2", oturum.durum.kaynaklar)

    def test_takvim_cizilir_ve_kutular_kayit_edilir(self):
        self.pencere.dosya_yukle(self.dosya)
        self.pencere.oturum.komut("rezervasyon", kullanici="u1", kaynak="YAZ-1",
                                  baslangic="2027-03-08T11:00", bitis="2027-03-08T13:00")
        _uygulama.processEvents()
        self.pencere.grab()  # paintEvent çalışır
        self.assertEqual([rid for _, rid in self.pencere.takvim.cizim._kutular], ["r1"])


class YardimciIslevTesti(unittest.TestCase):
    def test_varsayilan_aralik(self):
        simule = datetime(2027, 3, 8, 10, 7)
        self.assertEqual(varsayilan_aralik(simule, date(2027, 3, 8)), ("10:15", "11:15"))
        self.assertEqual(varsayilan_aralik(simule, date(2027, 3, 9)), ("08:00", "09:00"))
        self.assertEqual(varsayilan_aralik(datetime(2027, 3, 8, 6, 0), date(2027, 3, 8)),
                         ("08:00", "09:00"))

    def test_hizli_saat_dugmeleri(self):
        carsamba = datetime(2027, 3, 10, 15, 30)
        self.assertEqual(sonraki_gun_sabahi(carsamba), datetime(2027, 3, 11, 8, 0))
        self.assertEqual(sonraki_pazartesi(carsamba), datetime(2027, 3, 15, 8, 0))
        pazartesi = datetime(2027, 3, 8, 8, 0)
        self.assertEqual(sonraki_pazartesi(pazartesi), datetime(2027, 3, 15, 8, 0))

    def test_alt_satir_cakisan_kutular_ust_uste_binmez(self):
        def rez(no, bas, bit, durum):
            return Rezervasyon(f"r{no}", "u1", "YAZ-1", datetime(2027, 3, 8, bas),
                               datetime(2027, 3, 8, bit), 10, durum)
        a, b, c = rez(1, 10, 12, "IPTAL"), rez(2, 11, 13, "ONAYLI"), rez(3, 12, 14, "GELMEDI")
        serit = {r.id: s for r, s in _serit_ata([a, b, c], {})}
        self.assertEqual(serit["r2"], 0)  # geçerli rezervasyon ilk satırda kalır
        self.assertNotEqual(serit["r1"], serit["r2"])  # r1 ile r2 çakışıyor
        self.assertNotEqual(serit["r3"], serit["r2"])  # r3 ile r2 çakışıyor

    def test_olay_metinleri(self):
        olay = {"zaman": "2027-03-08T11:15", "tur": "GELMEDI", "rezervasyon": "r2",
                "kullanici": "u1", "guvenilirlik": 65}
        self.assertEqual(mesajlar.olay_metni(olay),
                         "08.03 11:15  Gelmedi: r2 (u1), güvenilirlik 65.")

    def test_red_metni_bilinmeyen_kodda_cokmez(self):
        self.assertEqual(mesajlar.red_metni({"durum": "RED", "kod": "YENI_KOD"}), "(YENI_KOD)")


if __name__ == "__main__":
    unittest.main()
