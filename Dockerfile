# Dockerfile
FROM python:3.12-slim

# Logs non-buffered + pas de bytecode
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Déps en premier (cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code ensuite
COPY . .

# Code Engine fournit souvent le port via $PORT
ENV PORT=8000
EXPOSE 8000

# Lance FastAPI (main.py expose "app")
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]