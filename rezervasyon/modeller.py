"""Veri modeli: rezervasyon durumları, veri sınıfları ve bellek durumu (Durum).

Tüm modüller aynı Durum nesnesi üzerinde çalışır. Hiçbir rol, tür veya sayı
burada sabit yazılmaz; bunlar başlangıç dosyasından gelir.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# Rezervasyon durumları (K8)
ONAYLI = "ONAYLI"
KULLANIMDA = "KULLANIMDA"
TAMAMLANDI = "TAMAMLANDI"
IPTAL = "IPTAL"
GELMEDI = "GELMEDI"


@dataclass
class KaynakTuru:
    """Kaynak türü (ODA, LAB, ...). Başlangıç dosyasındaki 'kaynak_turleri' girdisi."""

    ad: str
    hazirlik_dk: int
    temel_ucret: int
    enerji_yogun: bool
    sertifika: Optional[str] = None  # JSON'daki null -> None


@dataclass
class Rol:
    """Kullanıcı rolü (OGRENCI, ...). Başlangıç dosyasındaki 'roller' girdisi."""

    ad: str
    haftalik_kota: int
    ileri_gun: int
    azami_sure_dk: int


@dataclass
class Kaynak:
    """Rezerve edilebilen oda veya cihaz."""

    id: str
    ad: str
    tur: str
    izinli_roller: list = field(default_factory=list)


@dataclass
class Kullanici:
    """Sistem kullanıcısı. Bakiye KP, güvenilirlik 0-100 arası tam sayı."""

    id: str
    ad: str
    rol: str
    sertifikalar: list = field(default_factory=list)
    bakiye: int = 0
    guvenilirlik: int = 0


@dataclass
class Rezervasyon:
    """Kurallara uyan talebin sonucu (K10)."""

    id: str
    kullanici: str
    kaynak: str
    baslangic: datetime
    bitis: datetime
    ucret: int
    durum: str = ONAYLI
    paket: Optional[str] = None


@dataclass
class BakimPenceresi:
    """Kaynağın kullanıma kapalı olduğu aralık (K2)."""

    kaynak: str
    baslangic: datetime
    bitis: datetime


@dataclass
class BeklemeKaydi:
    """Dolu bir aralık için sıraya girme (K9)."""

    id: str
    kullanici: str
    kaynak: str
    baslangic: datetime
    bitis: datetime
    kayit_saati: datetime


@dataclass
class Durum:
    """Tüm bellek verisi. Modüller bu nesneyi parametre olarak alır."""

    saat: datetime
    turler: dict = field(default_factory=dict)  # ad -> KaynakTuru
    roller: dict = field(default_factory=dict)  # ad -> Rol
    kaynaklar: dict = field(default_factory=dict)  # id -> Kaynak
    kullanicilar: dict = field(default_factory=dict)  # id -> Kullanici
    rezervasyonlar: dict = field(default_factory=dict)  # id -> Rezervasyon
    bakimlar: list = field(default_factory=list)  # BakimPenceresi listesi
    beklemeler: dict = field(default_factory=dict)  # id -> BeklemeKaydi
    sayaclar: dict = field(default_factory=lambda: {"r": 0, "b": 0, "p": 0})

    # Numara yalnızca başarılı işlemden sonra alınmalıdır (reddedilen talep
    # numara tüketmez). Çağıran taraf doğrulamayı geçtikten sonra çağırır.
    def yeni_rezervasyon_no(self):
        self.sayaclar["r"] += 1
        return f"r{self.sayaclar['r']}"

    def yeni_bekleme_no(self):
        self.sayaclar["b"] += 1
        return f"b{self.sayaclar['b']}"

    def yeni_paket_no(self):
        self.sayaclar["p"] += 1
        return f"p{self.sayaclar['p']}"
