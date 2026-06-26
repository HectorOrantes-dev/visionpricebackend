FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh

# Railway inyecta $PORT. start.sh migra y arranca uvicorn (forma exec, señales OK).
CMD ["sh", "start.sh"]
