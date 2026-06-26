#!/usr/bin/env sh
# Arranque para Railway: corre migraciones y luego uvicorn.
# Si las migraciones fallan, NO tumba el arranque: el servidor sube igual
# para exponer /health y dejar el error visible en los logs.
set -e

echo "==> [start] Ejecutando migraciones (alembic upgrade head)"
if alembic upgrade head; then
  echo "==> [start] Migraciones OK"
else
  echo "!! [start] ERROR en migraciones — revisa DATABASE_URL (Neon)."
  echo "!! [start] El servidor arrancará igual; los endpoints con BD fallarán hasta corregirlo."
fi

echo "==> [start] Iniciando uvicorn en 0.0.0.0:${PORT:-8000}"
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
