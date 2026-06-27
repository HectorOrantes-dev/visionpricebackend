# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Capa de dependencias: se cachea mientras requirements.txt no cambie.
# La caché de pip (BuildKit) persiste las descargas entre builds -> más rápido.
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY . .
RUN chmod +x start.sh

# Railway inyecta $PORT. start.sh migra y arranca uvicorn (forma exec, señales OK).
CMD ["sh", "start.sh"]
