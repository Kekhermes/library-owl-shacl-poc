import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]  # Racine du projet

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://library_user:library_pass@localhost:5433/library_db",
)

RDF_ONTOLOGY_PATH = os.getenv(
    "RDF_ONTOLOGY_PATH",
    str(BASE_DIR / "rdf" / "ontology.ttl"),
)

RDF_SHAPES_PATH = os.getenv(
    "RDF_SHAPES_PATH",
    str(BASE_DIR / "rdf" / "shapes.ttl"),
)
