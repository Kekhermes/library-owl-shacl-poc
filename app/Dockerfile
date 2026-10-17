FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

# Dépendances système minimales pour compilation et PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY app/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code applicatif et des fichiers sémantiques W3C partagés
COPY rdf /workspace/rdf
COPY app /workspace/app

ENV PYTHONPATH=/workspace \
    RDF_ONTOLOGY_PATH=/workspace/rdf/ontology.ttl \
    RDF_SHAPES_PATH=/workspace/rdf/shapes.ttl

EXPOSE 8000

CMD ["uvicorn", "app.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
