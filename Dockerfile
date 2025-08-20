FROM python:3.11-slim

WORKDIR /app

# dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia il codice (deve esistere la cartella app/ accanto al Dockerfile)
COPY app ./app

# avvio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]