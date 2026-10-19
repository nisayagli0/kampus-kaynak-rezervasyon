"""Hata kodlarının Türkçe açıklamaları ve işlem sonuçlarının ekran metinleri.

Kodlar modülden gelir (doküman K10, K9, K8); burada yalnızca okunur metne çevrilir.
"""

from arayuz import bicim
from rezervasyon import zaman

KOD_ACIKLAMA = {
    "BULUNAMADI": "Kayıt bulunamadı (kullanıcı, kaynak veya rezervasyon yok).",
    "ZAMAN_ADIMI_HATASI": "Saatler 15 dakikanın katı olmalı ve bitiş başlangıçtan sonra olmalı.",
    "GECMIS_ZAMAN": "Başlangıç, simüle saatten önce.",
    "CALISMA_SAATI_DISI": "Talep çalışma saatlerinin dışına çıkıyor.",
    "SURE_SINIRI": "Süre, rolün izin verdiği azami süreyi aşıyor.",
    "ILERI_TARIH_SINIRI": "Başlangıç, rolün ileri tarih sınırından sonra.",
    "ROL_IZNI_YOK": "Bu kaynağı rezerve etme izni rolde yok.",
    "SERTIFIKA_YOK": "Bu kaynak için gereken sertifika kullanıcıda yok.",
    "BAKIM": "Kaynak bu aralıkta bakımda.",
    "KESISME": "Aralık başka bir rezervasyonla çakışıyor.",
    "HAZIRLIK_IHLALI": "Aralık, başka bir rezervasyonun hazırlık süresine denk geliyor.",
    "ARDISIK_KULLANIM": "Aynı kaynakta art arda iki rezervasyon arasında yeterli boşluk yok.",
    "BAKIYE_YETERSIZ": "Bakiye yetersiz.",
    "PAKET_BOYUTU": "Pakette kalem sayısı uygun değil.",
    "GUVENILIRLIK_DUSUK": "Güvenilirlik düşük; paket rezervasyon yapılamaz.",
    "PAKET_RED": "En az bir kalem doğrulamadan geçemedi; hiçbiri alınmadı.",
    "PAKET_ICI_KESISME": "Paketteki kalemler birbiriyle çakışıyor veya hazırlık/art arda kuralını ihlal ediyor.",
    "DURUM_HATASI": "Rezervasyon bu işlem için uygun durumda değil.",
    "GIRIS_PENCERESI_DISI": "Giriş zamanı henüz gelmedi ya da geçti.",
    "BEKLEME_GEREKSIZ": "Talep zaten geçerli; bekleme kaydı gerekmiyor.",
    "SAAT_GERI": "Simüle saat geriye alınamaz.",
    "ID_MEVCUT": "Bu kimlik zaten kullanılıyor.",
    "TANIMSIZ_DEGER": "Seçilen rol veya tür tanımlı değil.",
    "GECERSIZ_DEGER": "Değer geçersiz (örneğin bakiye kotayı aşıyor veya sınır dışı).",
    "BEKLENMEYEN_HATA": "Beklenmeyen bir hata oluştu.",
}

# Bu iki kodda kullanıcıya "Bekleme kaydı aç" önerilir (doküman K9)
BEKLEMEYE_UYGUN_KODLAR = ("KESISME", "HAZIRLIK_IHLALI")


def aciklama(kod):
    return KOD_ACIKLAMA.get(kod, "")


def red_metni(sonuc):
    """RED sonucu -> 'Aralık başka bir rezervasyonla çakışıyor. (KESISME)'."""
    kod = sonuc.get("kod", "?")
    ek = f" {sonuc['mesaj']}" if sonuc.get("mesaj") else ""
    return f"{aciklama(kod)}{ek} ({kod})".strip()


def olay_metni(olay):
    """Saat komutunun bir olayı -> tek satırlık okunur metin."""
    an = bicim.kisa(zaman.ayristir(olay["zaman"]))
    tur = olay["tur"]
    if tur == "HAFTALIK_SIFIRLAMA":
        govde = "Haftalık sıfırlama: bakiyeler rol kotasına eşitlendi."
    elif tur == "TAMAMLANDI":
        govde = (f"Tamamlandı: {olay['rezervasyon']} ({olay['kullanici']}), "
                 f"güvenilirlik {olay['guvenilirlik']}.")
    elif tur == "GELMEDI":
        govde = (f"Gelmedi: {olay['rezervasyon']} ({olay['kullanici']}), "
                 f"güvenilirlik {olay['guvenilirlik']}.")
    elif tur == "OTOMATIK_ATAMA":
        govde = (f"Bekleme listesinden otomatik atama: {olay['kullanici']} → {olay['rezervasyon']}, "
                 f"ücret {olay['ucret']} KP, bakiye {olay['bakiye']} KP.")
    else:
        govde = tur
    return f"{an}  {govde}"


def eylem_ozeti(komut, sonuc):
    """giris / cikis / iptal sonucu -> kartta görünen metin (başarılı veya red)."""
    if sonuc.get("durum") != "TAMAM":
        return red_metni(sonuc)
    if komut == "giris":
        satirlar = ["Giriş yapıldı; rezervasyon kullanımda."]
    elif komut == "cikis":
        satirlar = [f"Çıkış yapıldı; rezervasyon tamamlandı. Güvenilirlik: {sonuc['guvenilirlik']}."]
    else:
        satirlar = [f"İptal edildi. İade: {sonuc['iade']} KP · Bakiye: {sonuc['bakiye']} KP · "
                    f"Güvenilirlik: {sonuc['guvenilirlik']}."]
    satirlar += [olay_metni(o) for o in sonuc.get("olaylar", [])]
    return "\n".join(satirlar)
