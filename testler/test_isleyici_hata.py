import json
import os
import subprocess
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORNEK = os.path.join(KOK, "testler", "ornek", "baslangic.json")


def calistir(satirlar):
    """Komut satırı işleyicisini gerçek süreç olarak çalıştırır."""
    with tempfile.TemporaryDirectory() as klasor:
        yol = os.path.join(klasor, "komutlar.jsonl")
        with open(yol, "w", encoding="utf-8") as f:
            f.write("\n".join(satirlar) + "\n")
        islem = subprocess.run(
            [sys.executable, "-m", "komut_satiri.isleyici", ORNEK, yol],
            cwd=KOK,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    return islem, [json.loads(s) for s in islem.stdout.splitlines()]


class HataliKomutTesti(unittest.TestCase):
    def test_bozuk_json_satiri_red_olarak_yazilir(self):
        islem, sonuclar = calistir(
            [
                '{"komut":"saat","zaman":"2027-03-08T09:00"}',
                "{bozuk",
                '{"komut":"saat","zaman":"2027-03-08T10:00"}',
            ]
        )
        self.assertEqual(len(sonuclar), 3)
        self.assertEqual([s["no"] for s in sonuclar], [1, 2, 3])
        self.assertEqual(sonuclar[1]["durum"], "RED")
        self.assertEqual(sonuclar[1]["kod"], "BEKLENMEYEN_HATA")
        self.assertEqual(sonuclar[2]["durum"], "TAMAM")
        self.assertIn("2. komut işlenemedi", islem.stderr)

    def test_bilinmeyen_komut_satiri_red_olarak_yazilir(self):
        _, sonuclar = calistir(['{"komut":"yok_boyle_komut"}'])
        self.assertEqual(len(sonuclar), 1)
        self.assertEqual(sonuclar[0]["komut"], "yok_boyle_komut")
        self.assertEqual(sonuclar[0]["durum"], "RED")

    def test_eksik_alan_satiri_red_olarak_yazilir(self):
        _, sonuclar = calistir(['{"komut":"saat"}'])
        self.assertEqual(len(sonuclar), 1)
        self.assertEqual(sonuclar[0]["durum"], "RED")


if __name__ == "__main__":
    unittest.main()
