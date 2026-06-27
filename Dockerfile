FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Capa de dependencias primero: Railway la reutiliza mientras requirements.txt
# no cambie, así los deploys de solo-código se saltan el pip install.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh

# Railway inyecta $PORT. start.sh migra y arranca uvicorn (forma exec, señales OK).
CMD ["sh", "start.sh"]
