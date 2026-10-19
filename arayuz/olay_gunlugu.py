"""Olay günlüğü (doküman Bölüm 7): oturumdaki tüm işlemler sırayla.

Satıra tıklayınca komutun JSON karşılığı ve modülün döndürdüğü JSON (Bölüm 5 biçimi) görünür.
"""

import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QFont
from PySide6.QtWidgets import (QAbstractItemView, QHeaderView, QPlainTextEdit, QSplitter,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from arayuz import bicim, mesajlar, stil


def _ozet(sonuc):
    if sonuc.get("durum") != "TAMAM":
        return mesajlar.red_metni(sonuc)
    return "TAMAM"


class OlayGunlugu(QWidget):
    def __init__(self, oturum, parent=None):
        super().__init__(parent)
        self.oturum = oturum
        yerlesim = QVBoxLayout(self)
        yerlesim.setContentsMargins(0, 0, 0, 0)
        bolucu = QSplitter(Qt.Horizontal)

        self.tablo = QTableWidget(0, 4)
        self.tablo.setHorizontalHeaderLabels(["Sıra", "Simüle saat", "Komut", "Sonuç"])
        self.tablo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tablo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablo.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tablo.verticalHeader().hide()
        baslik = self.tablo.horizontalHeader()
        baslik.setSectionResizeMode(QHeaderView.ResizeToContents)
        baslik.setSectionResizeMode(3, QHeaderView.Stretch)
        self.json_alani = QPlainTextEdit()
        self.json_alani.setReadOnly(True)
        self.json_alani.setFont(QFont("Consolas", 9))
        self.json_alani.setPlaceholderText("Bir satıra tıklayın: komut ve modülün döndürdüğü JSON burada görünür.")
        bolucu.addWidget(self.tablo)
        bolucu.addWidget(self.json_alani)
        bolucu.setStretchFactor(0, 3)
        bolucu.setStretchFactor(1, 2)
        yerlesim.addWidget(bolucu)

        self.tablo.itemSelectionChanged.connect(self._satir_secildi)
        oturum.veri_degisti.connect(self.yenile)
        self.yenile()

    def yenile(self):
        kayitlar = self.oturum.gunluk
        self.tablo.blockSignals(True)
        self.tablo.setRowCount(len(kayitlar))
        for i, k in enumerate(kayitlar):
            renk = stil.BASARI_YAZI if k["sonuc"]["durum"] == "TAMAM" else stil.HATA_YAZI
            for j, deger in enumerate([str(k["no"]), bicim.kisa(k["saat"]), k["komut"],
                                       _ozet(k["sonuc"])]):
                oge = QTableWidgetItem(deger)
                if j == 3:
                    oge.setForeground(QBrush(renk))
                self.tablo.setItem(i, j, oge)
        self.tablo.blockSignals(False)
        if kayitlar:
            self.tablo.selectRow(len(kayitlar) - 1)  # son işlem seçilir ve görünür
            self.tablo.scrollToBottom()
            self._satir_secildi()
        else:
            self.json_alani.clear()

    def _satir_secildi(self):
        satirlar = self.tablo.selectionModel().selectedRows()
        if not satirlar:
            return
        k = self.oturum.gunluk[satirlar[0].row()]
        komut = json.dumps({"komut": k["komut"], **k["girdi"]}, ensure_ascii=False, indent=2)
        sonuc = json.dumps(k["sonuc"], ensure_ascii=False, indent=2)
        self.json_alani.setPlainText(f"Komut:\n{komut}\n\nSonuç:\n{sonuc}")
