"""Yoğun gün demosu: takvimin kalabalık bir günde okunabilirliğini göstermek için.

Kullanım (proje klasöründen):
    python testler/yogun_gun_demo.py              # pencereyi açar, ekran görüntüsünü siz alırsınız
    python testler/yogun_gun_demo.py cikti.png    # görüntüyü dosyaya kaydedip kapanır

Bu betik iş kuralı içermez. Komutları arayüzün kullandığı Oturum üzerinden verir,
yani ekranda elle yapılan işlemlerle aynı yolu izler. Test paketine dahil değildir.
"""

import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

from PySide6.QtWidgets import QApplication  # noqa: E402

from arayuz.ana_pencere import AnaPencere  # noqa: E402

BASLANGIC = os.path.join(KOK, "testler", "ornek", "baslangic.json")
GUN = "2027-03-08"

# (kaynak, başlangıç, bitiş): kullanıcılar sırayla k1..k6 olarak dağıtılır
PLAN = [
    ("ODA-3", "10:00", "12:00"),
    ("ODA-3", "13:00", "15:00"),
    ("ODA-3", "16:30", "18:00"),
    ("YAZ-3", "08:00", "10:00"),
    ("YAZ-3", "11:00", "12:30"),
    ("YAZ-3", "14:00", "17:00"),
    ("YAZ-4", "09:00", "11:00"),
    ("YAZ-4", "12:30", "14:00"),
    ("YAZ-4", "15:30", "17:30"),
    ("ODA-1", "08:00", "10:00"),
    ("ODA-1", "11:00", "13:00"),
    ("ODA-1", "14:00", "16:00"),
    ("ODA-1", "17:00", "19:00"),
    ("CIH-1", "09:00", "11:00"),
    ("CIH-1", "13:00", "15:30"),
    ("CIH-1", "17:00", "19:00"),
    ("YAZ-5", "10:00", "12:00"),
    ("YAZ-5", "15:00", "16:30"),
    ("YAZ-5", "18:00", "20:00"),
]


def bul(oturum, kaynak, baslangic):
    """Verilen kaynak ve başlangıçtaki rezervasyonun numarasını döndürür."""
    for rez in oturum.durum.rezervasyonlar.values():
        if (
            rez.kaynak == kaynak
            and rez.baslangic.strftime("%Y-%m-%dT%H:%M") == baslangic
        ):
            return rez.id
    return None


def hazirla(pencere):
    oturum = pencere.oturum
    for i in range(1, 7):
        oturum.komut(
            "kullanici_ekle",
            id=f"k{i}",
            ad=f"Kullanıcı {i}",
            rol="ARASTIRMACI",
            sertifikalar=["CIHAZ_EGITIMI"],
            bakiye=300,
            guvenilirlik=90,
        )
    for i in range(3, 6):
        oturum.komut(
            "kaynak_ekle",
            id=f"YAZ-{i}",
            ad=f"3B Yazıcı {i}",
            tur="YAZICI",
            izinli_roller=["OGRENCI", "ARASTIRMACI"],
        )
    oturum.komut(
        "kaynak_ekle",
        id="ODA-3",
        ad="Toplantı Odası 3",
        tur="ODA",
        izinli_roller=["OGRENCI", "ARASTIRMACI"],
    )
    for sira, (kaynak, bas, bit) in enumerate(PLAN):
        sonuc = oturum.komut(
            "rezervasyon",
            kullanici=f"k{sira % 6 + 1}",
            kaynak=kaynak,
            baslangic=f"{GUN}T{bas}",
            bitis=f"{GUN}T{bit}",
        )
        if sonuc["durum"] != "TAMAM":
            print("Reddedildi:", kaynak, bas, bit, sonuc.get("kod"))
    oturum.komut("saat", zaman=f"{GUN}T09:10")
    # İptal edilecekleri numarayla değil kaynak ve başlangıç saatiyle buluruz;
    # bir talep reddedilse bile numaralar kaysa da doğru rezervasyon iptal edilir.
    for kaynak, bas in (("ODA-1", "14:00"), ("CIH-1", "13:00")):
        rez = bul(oturum, kaynak, f"{GUN}T{bas}")
        if rez:
            oturum.komut("iptal", rezervasyon=rez)
    oturum.komut("saat", zaman=f"{GUN}T12:30")
    # iptal edilen aralığa yeni talep: ikisi aynı satırda üst üste gösterilmeli
    oturum.komut(
        "rezervasyon",
        kullanici="k6",
        kaynak="ODA-1",
        baslangic=f"{GUN}T14:00",
        bitis=f"{GUN}T15:00",
    )
    oturum.gun_sec(oturum.durum.saat.date())


def main(argv):
    uygulama = QApplication([])
    pencere = AnaPencere()
    pencere.resize(1360, 820)
    pencere.show()
    uygulama.processEvents()
    pencere.dosya_yukle(BASLANGIC)
    hazirla(pencere)
    uygulama.processEvents()
    if len(argv) > 1:
        pencere.grab().save(argv[1])
        return 0
    return uygulama.exec()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
