#!/bin/sh
# Kullanım: ./calistir.sh baslangic.json komutlar.jsonl > sonuclar.jsonl
# Hangi klasörden çağrılırsa çağrılsın proje klasörü PYTHONPATH'e eklenir.
DIZIN="$(cd "$(dirname "$0")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    PY=python
fi

PYTHONPATH="$DIZIN" exec "$PY" -m komut_satiri.isleyici "$@"
