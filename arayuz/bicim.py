"""Tarih ve saat gösterim yardımcıları (yalnızca ekranda görünen metin)."""

HAFTA_GUNLERI = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def saat_metni(dt):
    """datetime -> '08.03.2027 Pazartesi 08:00'."""
    return f"{dt.strftime('%d.%m.%Y')} {HAFTA_GUNLERI[dt.weekday()]} {dt.strftime('%H:%M')}"


def kisa(dt):
    """datetime -> '08.03 12:00'."""
    return dt.strftime("%d.%m %H:%M")


def aralik(baslangic, bitis):
    """İki datetime -> '08.03 12:00–13:00' (farklı günse iki tarih de yazılır)."""
    if baslangic.date() == bitis.date():
        return f"{kisa(baslangic)}–{bitis.strftime('%H:%M')}"
    return f"{kisa(baslangic)}–{kisa(bitis)}"
