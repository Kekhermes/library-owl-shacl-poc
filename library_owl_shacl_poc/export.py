from pathlib import Path

from rdflib import Graph


def save_graph(graph: Graph, destination: str | Path) -> Path:
    """Enregistre un graphe RDF au format Turtle et renvoie le chemin créé."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(path), format="turtle")
    return path
