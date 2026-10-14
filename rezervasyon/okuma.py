"""Okuma işlevleri: arayüzün Durum nesnesinden okuduğu değerler.

Bu işlevler durumu değiştirmez. Hiçbir rol, tür, sertifika veya sayı kodda
sabit değildir; hepsi başlangıç dosyasından kurulan Durum'dan gelir.
"""


def simule_saat(durum):
    """Simüle saat (datetime)."""
    return durum.saat


def roller(durum):
    """Başlangıç dosyasındaki rol adları, dosyadaki sırayla."""
    return list(durum.roller)


def turler(durum):
    """Başlangıç dosyasındaki kaynak türü adları, dosyadaki sırayla."""
    return list(durum.turler)


def sertifikalar(durum):
    """Türlerin gerektirdiği ve kullanıcıların sahip olduğu sertifikaların birleşimi."""
    bulunanlar = set()
    for tur in durum.turler.values():
        if tur.sertifika:  # None (JSON'daki null) atlanır
            bulunanlar.add(tur.sertifika)
    for kullanici in durum.kullanicilar.values():
        bulunanlar.update(kullanici.sertifikalar)
    return sorted(bulunanlar)


def kullanicilar(durum):
    """Kullanıcı listesi (ekleme sırasıyla)."""
    return list(durum.kullanicilar.values())


def kaynaklar(durum):
    """Kaynak listesi (ekleme sırasıyla)."""
    return list(durum.kaynaklar.values())
