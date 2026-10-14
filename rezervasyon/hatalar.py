"""Hata kodları ve Türkçe açıklamaları.

Arayüz, bir talep reddedilince bu sözlükten kodun açıklamasını gösterir.
Kod adları ödev dokümanındaki (K1-K11) adlarla birebir aynıdır.
"""

HATA_ACIKLAMALARI = {
    # K10 doğrulama sırası (1-13)
    "BULUNAMADI": "Kullanıcı, kaynak veya rezervasyon bulunamadı.",
    "ZAMAN_ADIMI_HATASI": "Saatler 15 dakikalık adımlara oturmuyor veya bitiş başlangıçtan önce.",
    "GECMIS_ZAMAN": "Başlangıç, simüle saatten önce olamaz.",
    "CALISMA_SAATI_DISI": "Rezervasyon aynı gün içinde 08:00-22:00 arasında kalmalıdır.",
    "SURE_SINIRI": "Süre en az 30 dakika, en fazla rolün azami süresi kadar olabilir.",
    "ILERI_TARIH_SINIRI": "Başlangıç, rolün izin verdiği ileri tarih sınırını aşıyor.",
    "ROL_IZNI_YOK": "Kullanıcının rolü bu kaynağı rezerve etme iznine sahip değil.",
    "SERTIFIKA_YOK": "Bu kaynak için gereken sertifika kullanıcıda yok.",
    "BAKIM": "Talep edilen aralık bir bakım penceresiyle kesişiyor.",
    "KESISME": "Talep edilen aralık başka bir rezervasyonla kesişiyor.",
    "HAZIRLIK_IHLALI": "Kaynağın iki kullanım arasındaki hazırlık süresi ihlal ediliyor.",
    "ARDISIK_KULLANIM": "Aynı kaynakta art arda iki rezervasyon arasında en az 60 dakika olmalı.",
    "BAKIYE_YETERSIZ": "Kaynak Puan bakiyesi ücreti karşılamıyor.",
    # Paket (K7)
    "PAKET_BOYUTU": "Pakette en az 2, en fazla 4 kalem olmalı.",
    "GUVENILIRLIK_DUSUK": "Güvenilirlik puanı 50'nin altında olduğu için paket rezervasyon yapılamaz.",
    "PAKET_RED": "Paketteki en az bir kalem doğrulamadan geçemedi.",
    "PAKET_ICI_KESISME": "Paketteki aynı kaynağa ait kalemler birbiriyle çakışıyor veya hazırlık/art arda kullanım kuralını ihlal ediyor.",
    # Durum makinesi (K8)
    "DURUM_HATASI": "Rezervasyon bu işlem için uygun durumda değil.",
    "GIRIS_PENCERESI_DISI": "Giriş yalnızca başlangıçtan 10 dakika önce ile 15 dakika sonra arasında yapılabilir.",
    # Bekleme listesi (K9)
    "BEKLEME_GEREKSIZ": "Talep zaten geçerli, bekleme kaydı açmaya gerek yok.",
    # Saat (K11)
    "SAAT_GERI": "Yeni saat, mevcut simüle saatten önce olamaz.",
    # Kullanıcı ve kaynak ekleme
    "ID_MEVCUT": "Bu kimlikle bir kayıt zaten var.",
    "TANIMSIZ_DEGER": "Rol, tür veya izinli rollerden biri başlangıç dosyasında tanımlı değil.",
    "GECERSIZ_DEGER": "Bakiye veya güvenilirlik değeri geçersiz.",
}


def aciklama(kod):
    """Hata kodunun Türkçe açıklamasını döndürür (bilinmeyen kod için kodun kendisi)."""
    return HATA_ACIKLAMALARI.get(kod, kod)