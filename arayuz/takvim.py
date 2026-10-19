"""Kaynak takvimi (doküman Bölüm 7): kaynaklar satır, yatay eksen 08:00-22:00.

Çizilenler: 15 dakikalık ızgara, durum renkleri (renk + desen + etiket), bakım
pencereleri, hazırlık süreleri, simüle saat çizgisi. Aynı kaynakta çakışan kutular
alt satırlara yerleşir. Kutuya tıklayınca detay kartı, boş yere tıklayınca talep
formu o aralıkla dolar. İş kuralı yoktur; veriler okuma.py'den gelir.
"""

from datetime import datetime, timedelta

from PySide6.QtCore import QDate, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (QDateEdit, QFrame, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QToolButton, QToolTip, QVBoxLayout, QWidget)

from arayuz import bicim, stil
from rezervasyon import okuma

EKSEN_BASI_SAAT = 8
EKSEN_SONU_SAAT = 22
EKSEN_DAKIKA = (EKSEN_SONU_SAAT - EKSEN_BASI_SAAT) * 60
ETIKET_GENISLIK = 150
SAG_BOSLUK = 12
BASLIK_YUKSEKLIK = 26
SERIT_YUKSEKLIK = 24
SERIT_ARASI = 3
SATIR_DOLGU = 5


def _serit_ata(rezervasyonlar, hazirlik_bitisi):
    """Aynı kaynaktaki kutuları alt satırlara yerleştirir: [(rezervasyon, serit)].

    Geçerli (hazırlığı olan) rezervasyonlar önce yerleşir, hazırlık süreleriyle
    birlikte; böylece gerçek doluluk ilk satırda kalır. İptal ve gelmeyenler,
    çakışıyorsa alt satırlara düşer. hazirlik_bitisi: {rezervasyon kimliği: hazırlığın
    bittiği an}.
    """
    sirali = sorted(rezervasyonlar, key=lambda r: (
        r.durum not in okuma.HAZIRLIGI_OLAN_DURUMLAR, r.baslangic, int(r.id[1:])))
    seritler = []  # her şeridin dolu olduğu son an
    yerlesim = []
    for r in sirali:
        for i, son in enumerate(seritler):
            if son <= r.baslangic:
                seritler[i] = hazirlik_bitisi.get(r.id, r.bitis)
                yerlesim.append((r, i))
                break
        else:
            seritler.append(hazirlik_bitisi.get(r.id, r.bitis))
            yerlesim.append((r, len(seritler) - 1))
    return yerlesim


class TakvimCizim(QWidget):
    rezervasyon_secildi = Signal(str)
    bos_secildi = Signal(str, object)  # kaynak kimliği, 15 dakikaya yuvarlanmış datetime

    def __init__(self, oturum, parent=None):
        super().__init__(parent)
        self.oturum = oturum
        self._satirlar = []
        self._kutular = []  # (QRectF, rezervasyon kimliği)
        self.setMouseTracking(True)
        self.setMinimumWidth(620)
        self.yenile()

    # --- Veri ---
    def yenile(self):
        self._satirlar = self._satirlari_kur()
        yukseklik = BASLIK_YUKSEKLIK + sum(s["yukseklik"] for s in self._satirlar)
        self.setMinimumHeight(max(yukseklik, 80))
        self.update()

    def _satirlari_kur(self):
        durum, gun = self.oturum.durum, self.oturum.secili_gun
        if durum is None or gun is None:
            return []
        rezervasyonlar = okuma.rezervasyonlar_gun(durum, gun)
        bakimlar = okuma.bakimlar_gun(durum, gun)
        hazirliklar = okuma.hazirlik_araliklari_gun(durum, gun)
        satirlar = []
        for kaynak in okuma.kaynaklar(durum):
            kendi = [r for r in rezervasyonlar if r.kaynak == kaynak.id]
            hazirlik_bitisi = {rid: bit for k, rid, _, bit in hazirliklar if k == kaynak.id}
            yerlesim = _serit_ata(kendi, hazirlik_bitisi)
            serit_no = {r.id: s for r, s in yerlesim}
            serit_sayisi = max([s for _, s in yerlesim], default=0) + 1
            satirlar.append({
                "kaynak": kaynak,
                "yerlesim": yerlesim,
                "bakimlar": [b for b in bakimlar if b.kaynak == kaynak.id],
                "hazirliklar": [(rid, bas, bit, serit_no.get(rid, 0))
                                for k, rid, bas, bit in hazirliklar if k == kaynak.id],
                "yukseklik": 2 * SATIR_DOLGU + serit_sayisi * (SERIT_YUKSEKLIK + SERIT_ARASI),
            })
        return satirlar

    # --- Koordinatlar ---
    def _x(self, an):
        gun = self.oturum.secili_gun
        sifir = datetime(gun.year, gun.month, gun.day, EKSEN_BASI_SAAT)
        dakika = min(max((an - sifir).total_seconds() / 60, 0), EKSEN_DAKIKA)
        alan = max(self.width() - ETIKET_GENISLIK - SAG_BOSLUK, 1)
        return ETIKET_GENISLIK + dakika / EKSEN_DAKIKA * alan

    def _an(self, x):
        """x koordinatı -> 15 dakikaya aşağı yuvarlanmış datetime."""
        gun = self.oturum.secili_gun
        sifir = datetime(gun.year, gun.month, gun.day, EKSEN_BASI_SAAT)
        alan = max(self.width() - ETIKET_GENISLIK - SAG_BOSLUK, 1)
        dakika = (x - ETIKET_GENISLIK) / alan * EKSEN_DAKIKA
        dakika = min(max(dakika, 0), EKSEN_DAKIKA - 15)
        return sifir + timedelta(minutes=int(dakika // 15) * 15)

    def _satir_ustleri(self):
        y = BASLIK_YUKSEKLIK
        for satir in self._satirlar:
            yield satir, y
            y += satir["yukseklik"]

    # --- Çizim ---
    def paintEvent(self, olay):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.fillRect(self.rect(), stil.ZEMIN)
        self._kutular = []
        if not self._satirlar:
            p.setPen(stil.SOLUK_YAZI)
            p.drawText(self.rect(), Qt.AlignCenter,
                       "Takvim için başlangıç dosyası seçin." if self.oturum.durum is None
                       else "Bu başlangıç dosyasında kaynak yok.")
            return

        toplam = BASLIK_YUKSEKLIK + sum(s["yukseklik"] for s in self._satirlar)
        self._zemin_ve_izgara(p, toplam)
        for satir, ust in self._satir_ustleri():
            self._satiri_ciz(p, satir, ust)
        self._saat_imleci(p, toplam)
        self._etiketler(p)

    def _zemin_ve_izgara(self, p, toplam):
        for i, (satir, ust) in enumerate(self._satir_ustleri()):
            if i % 2:
                p.fillRect(QRectF(0, ust, self.width(), satir["yukseklik"]), stil.SATIR_ZEMIN_ALT)
            p.setPen(QPen(stil.CEYREK_CIZGISI, 1))
            p.drawLine(0, int(ust + satir["yukseklik"]), self.width(), int(ust + satir["yukseklik"]))
        gun = self.oturum.secili_gun
        sifir = datetime(gun.year, gun.month, gun.day, EKSEN_BASI_SAAT)
        for ceyrek in range(EKSEN_DAKIKA // 15 + 1):
            x = int(self._x(sifir + timedelta(minutes=ceyrek * 15)))
            saat_cizgisi = ceyrek % 4 == 0
            p.setPen(QPen(stil.SAAT_CIZGISI if saat_cizgisi else stil.CEYREK_CIZGISI, 1))
            baslangic_y = BASLIK_YUKSEKLIK - 6 if saat_cizgisi else BASLIK_YUKSEKLIK
            p.drawLine(x, baslangic_y, x, toplam)

    def _satiri_ciz(self, p, satir, ust):
        yukseklik = satir["yukseklik"]
        for b in satir["bakimlar"]:
            kutu = QRectF(self._x(b.baslangic), ust + 2, self._x(b.bitis) - self._x(b.baslangic),
                          yukseklik - 4)
            self._kutu(p, kutu, stil.BAKIM_DOLGU, stil.BAKIM_CIZGI, stil.BAKIM_DESEN,
                       stil.BAKIM_ETIKET)
        for _, bas, bit, serit in satir["hazirliklar"]:
            y = ust + SATIR_DOLGU + serit * (SERIT_YUKSEKLIK + SERIT_ARASI)
            kutu = QRectF(self._x(bas), y, self._x(bit) - self._x(bas), SERIT_YUKSEKLIK)
            self._kutu(p, kutu, stil.HAZIRLIK_DOLGU, stil.HAZIRLIK_CIZGI, Qt.SolidPattern, "")
        for r, serit in satir["yerlesim"]:
            y = ust + SATIR_DOLGU + serit * (SERIT_YUKSEKLIK + SERIT_ARASI)
            kutu = QRectF(self._x(r.baslangic), y, self._x(r.bitis) - self._x(r.baslangic),
                          SERIT_YUKSEKLIK)
            dolgu, cizgi, desen, etiket = stil.DURUM_STIL[r.durum]
            self._kutu(p, kutu, dolgu, cizgi, desen, f"{r.kullanici} · {etiket}",
                       secili=(r.id == self.oturum.secili_rezervasyon), kisa_metin=r.kullanici)
            self._kutular.append((kutu, r.id))

    def _kutu(self, p, kutu, dolgu, cizgi, desen, metin, secili=False, kisa_metin=None):
        """Tek kutuyu çizer. Desenli durumlar soluk zemin üzerinde çizgi deseniyle ayrışır."""
        if desen == Qt.SolidPattern:
            p.fillRect(kutu, dolgu)
        else:
            p.fillRect(kutu, dolgu.lighter(140))
            p.fillRect(kutu, QBrush(cizgi, desen))
        p.setPen(QPen(stil.YAZI_RENGI if secili else cizgi, 3 if secili else 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(kutu)
        if metin and kutu.width() > 30:
            yazi = QFont(stil.YAZI_AILESI, stil.YAZI_BOYUTU_KUCUK)
            p.setFont(yazi)
            if kisa_metin and QFontMetrics(yazi).horizontalAdvance(metin) > kutu.width() - 8:
                metin = kisa_metin  # dar kutuda yalnızca kullanıcı yazılır
            koyu_zemin = desen == Qt.SolidPattern and dolgu.lightness() < 160
            p.setPen(QColor("#ffffff") if koyu_zemin else stil.YAZI_RENGI)
            kisa = QFontMetrics(yazi).elidedText(metin, Qt.ElideRight, int(kutu.width() - 8))
            if desen != Qt.SolidPattern:  # desenli kutuda yazının arkası okunur kalsın
                p.fillRect(QRectF(kutu.left() + 3, kutu.center().y() - 8,
                                  QFontMetrics(yazi).horizontalAdvance(kisa) + 4, 16),
                           QColor(255, 255, 255, 170))
            p.drawText(QRectF(kutu.left() + 5, kutu.top(), kutu.width() - 8, kutu.height()),
                       Qt.AlignVCenter | Qt.AlignLeft, kisa)

    def _saat_imleci(self, p, toplam):
        simule = self.oturum.durum.saat
        if simule.date() != self.oturum.secili_gun:
            return
        gun = self.oturum.secili_gun
        sifir = datetime(gun.year, gun.month, gun.day, EKSEN_BASI_SAAT)
        if not 0 <= (simule - sifir).total_seconds() / 60 <= EKSEN_DAKIKA:
            return
        x = self._x(simule)
        p.setPen(QPen(stil.SAAT_IMLECI, stil.SAAT_IMLECI_KALINLIK))
        p.drawLine(QPointF(x, 0), QPointF(x, toplam))

    def _etiketler(self, p):
        """Üst saat etiketleri ve sol kaynak adları (kutuların üstüne çizilir)."""
        gun = self.oturum.secili_gun
        sifir = datetime(gun.year, gun.month, gun.day, EKSEN_BASI_SAAT)
        p.setFont(QFont(stil.YAZI_AILESI, stil.YAZI_BOYUTU_KUCUK))
        p.setPen(stil.SOLUK_YAZI)
        for saat in range(EKSEN_SONU_SAAT - EKSEN_BASI_SAAT + 1):
            x = self._x(sifir + timedelta(hours=saat))
            p.drawText(QRectF(x - 20, 2, 40, BASLIK_YUKSEKLIK - 8), Qt.AlignCenter,
                       f"{EKSEN_BASI_SAAT + saat:02d}:00")
        p.fillRect(QRectF(0, BASLIK_YUKSEKLIK, ETIKET_GENISLIK - 4, self.height()), stil.ZEMIN)
        for i, (satir, ust) in enumerate(self._satir_ustleri()):
            if i % 2:
                p.fillRect(QRectF(0, ust, ETIKET_GENISLIK - 4, satir["yukseklik"]),
                           stil.SATIR_ZEMIN_ALT)
            kaynak = satir["kaynak"]
            p.setFont(QFont(stil.YAZI_AILESI, stil.YAZI_BOYUTU))
            p.setPen(stil.YAZI_RENGI)
            p.drawText(QRectF(8, ust + 4, ETIKET_GENISLIK - 16, 20), Qt.AlignLeft | Qt.AlignVCenter,
                       QFontMetrics(p.font()).elidedText(kaynak.ad, Qt.ElideRight,
                                                         ETIKET_GENISLIK - 20))
            p.setFont(QFont(stil.YAZI_AILESI, stil.YAZI_BOYUTU_KUCUK))
            p.setPen(stil.SOLUK_YAZI)
            p.drawText(QRectF(8, ust + 22, ETIKET_GENISLIK - 16, 16), Qt.AlignLeft | Qt.AlignVCenter,
                       f"{kaynak.id} · {kaynak.tur}")

    # --- Fare ---
    def _kutu_altinda(self, nokta):
        for kutu, rid in reversed(self._kutular):
            if kutu.contains(nokta):
                return rid
        return None

    def mouseMoveEvent(self, olay):
        rid = self._kutu_altinda(olay.position())
        if rid:
            r = okuma.rezervasyon(self.oturum.durum, rid)
            kullanici = self.oturum.durum.kullanicilar[r.kullanici]
            QToolTip.showText(
                olay.globalPosition().toPoint(),
                f"{r.id} · {stil.durum_etiketi(r.durum)}\n{kullanici.ad} ({kullanici.id})\n"
                f"{bicim.aralik(r.baslangic, r.bitis)} · {r.ucret} KP", self)
            self.setCursor(Qt.PointingHandCursor)
        else:
            QToolTip.hideText()
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, olay):
        if olay.button() != Qt.LeftButton or not self._satirlar:
            return
        rid = self._kutu_altinda(olay.position())
        if rid:
            self.rezervasyon_secildi.emit(rid)
            return
        if olay.position().x() < ETIKET_GENISLIK:
            return
        for satir, ust in self._satir_ustleri():
            if ust <= olay.position().y() < ust + satir["yukseklik"]:
                self.bos_secildi.emit(satir["kaynak"].id, self._an(olay.position().x()))
                return


class Lejant(QWidget):
    """Renk, desen ve etiket açıklaması (renge ek olarak desen ve yazı da ayırt eder)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        self.setMinimumWidth(620)

    def paintEvent(self, olay):
        p = QPainter(self)
        p.setFont(QFont(stil.YAZI_AILESI, stil.YAZI_BOYUTU_KUCUK))
        ogeler = list(stil.DURUM_STIL.values())
        ogeler.append((stil.BAKIM_DOLGU, stil.BAKIM_CIZGI, stil.BAKIM_DESEN, stil.BAKIM_ETIKET))
        ogeler.append((stil.HAZIRLIK_DOLGU, stil.HAZIRLIK_CIZGI, Qt.SolidPattern, stil.HAZIRLIK_ETIKET))
        x = 8
        for dolgu, cizgi, desen, etiket in ogeler:
            kutu = QRectF(x, 6, 18, 12)
            if desen == Qt.SolidPattern:
                p.fillRect(kutu, dolgu)
            else:
                p.fillRect(kutu, dolgu.lighter(140))
                p.fillRect(kutu, QBrush(cizgi, desen))
            p.setPen(cizgi)
            p.drawRect(kutu)
            p.setPen(stil.YAZI_RENGI)
            genislik = QFontMetrics(p.font()).horizontalAdvance(etiket)
            p.drawText(QRectF(x + 24, 0, genislik + 4, 24), Qt.AlignVCenter | Qt.AlignLeft, etiket)
            x += 24 + genislik + 16
        p.setPen(QPen(stil.SAAT_IMLECI, stil.SAAT_IMLECI_KALINLIK))
        p.drawLine(x, 5, x, 19)
        p.setPen(stil.YAZI_RENGI)
        p.drawText(QRectF(x + 6, 0, 120, 24), Qt.AlignVCenter | Qt.AlignLeft, "Simüle saat")


class Takvim(QWidget):
    """Gün seçici + kaydırılabilir takvim çizimi + açıklama şeridi."""

    def __init__(self, oturum, parent=None):
        super().__init__(parent)
        self.oturum = oturum

        yerlesim = QVBoxLayout(self)
        yerlesim.setContentsMargins(8, 8, 8, 4)
        yerlesim.setSpacing(6)

        ust = QHBoxLayout()
        self.dugme_onceki = QToolButton()
        self.dugme_onceki.setText("◀")
        self.dugme_onceki.setToolTip("Önceki gün")
        self.dugme_sonraki = QToolButton()
        self.dugme_sonraki.setText("▶")
        self.dugme_sonraki.setToolTip("Sonraki gün")
        self.tarih = QDateEdit()
        self.tarih.setCalendarPopup(True)
        self.tarih.setDisplayFormat("dd.MM.yyyy")
        self.gun_adi = QLabel("")
        self.dugme_bugun = QPushButton("Simüle güne git")
        ust.addWidget(self.dugme_onceki)
        ust.addWidget(self.tarih)
        ust.addWidget(self.dugme_sonraki)
        ust.addWidget(self.gun_adi)
        ust.addStretch(1)
        ust.addWidget(self.dugme_bugun)
        yerlesim.addLayout(ust)

        self.cizim = TakvimCizim(oturum)
        alan = QScrollArea()
        alan.setWidgetResizable(True)
        alan.setFrameShape(QFrame.StyledPanel)
        alan.setWidget(self.cizim)
        yerlesim.addWidget(alan, 1)
        yerlesim.addWidget(Lejant())

        self.dugme_onceki.clicked.connect(lambda: self._kaydir(-1))
        self.dugme_sonraki.clicked.connect(lambda: self._kaydir(1))
        self.dugme_bugun.clicked.connect(self._simule_gune_git)
        self.tarih.dateChanged.connect(self._tarih_secildi)
        self.cizim.rezervasyon_secildi.connect(oturum.rezervasyon_sec)
        oturum.veri_degisti.connect(self.yenile)
        oturum.secim_degisti.connect(self.yenile)
        self.yenile()

    def _kaydir(self, gun):
        if self.oturum.secili_gun:
            self.oturum.gun_sec(self.oturum.secili_gun + timedelta(days=gun))

    def _simule_gune_git(self):
        if self.oturum.durum:
            self.oturum.gun_sec(self.oturum.durum.saat.date())

    def _tarih_secildi(self, qdate):
        if self.oturum.durum:
            self.oturum.gun_sec(qdate.toPython())

    def yenile(self):
        var = self.oturum.durum is not None
        for parca in (self.dugme_onceki, self.dugme_sonraki, self.tarih, self.dugme_bugun):
            parca.setEnabled(var)
        if var and self.oturum.secili_gun:
            gun = self.oturum.secili_gun
            self.tarih.blockSignals(True)
            self.tarih.setDate(QDate(gun.year, gun.month, gun.day))
            self.tarih.blockSignals(False)
            self.gun_adi.setText(bicim.HAFTA_GUNLERI[gun.weekday()])
        else:
            self.gun_adi.setText("")
        self.cizim.yenile()
