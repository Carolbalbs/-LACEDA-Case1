FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY tests/ ./tests/

# data/ e output/ entram por volume: as bases não são versionadas
#   docker build -t cidacs-setor .
#   docker run --rm -v "$PWD/data:/app/data" -v "$PWD/output:/app/output" cidacs-setor
ENV PYTHONPATH=/app/src
CMD ["python", "src/main.py"]
