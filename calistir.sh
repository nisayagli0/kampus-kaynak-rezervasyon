#!/bin/sh
# Kullanım: ./calistir.sh baslangic.json komutlar.jsonl > sonuclar.jsonl
# Hangi klasörden çağrılırsa çağrılsın proje klasörü PYTHONPATH'e eklenir.
DIZIN="$(cd "$(dirname "$0")" && pwd)"

# Çalışan ve sürümü 3.11 veya üzeri olan ilk Python'u seç.
# (Windows'ta "python3" bazen Microsoft Store kısayoludur; var görünür ama çalışmaz.)
PY=""
for ADAY in python3 python py; do
    if "$ADAY" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >/dev/null 2>&1; then
        PY="$ADAY"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "Python 3.11 veya üzeri bulunamadı." >&2
    exit 1
fi

PYTHONPATH="$DIZIN" exec "$PY" -m komut_satiri.isleyici "$@"