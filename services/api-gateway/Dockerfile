# CloudWatch Pro - API Gateway Dockerfile
FROM python:3.11-slim

# Ustawienie zmiennych środowiskowych
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Instalacja zależności systemowych
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tworzenie użytkownika aplikacji
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Ustawienie katalogu roboczego
WORKDIR /app

# Kopiowanie requirements
COPY requirements.txt .

# Instalacja zależności Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu aplikacji
COPY . .

# Zmiana właściciela plików na appuser
RUN chown -R appuser:appuser /app

# Przełączenie na użytkownika aplikacji
USER appuser

# Eksponowanie portu
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Komenda uruchomienia
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

