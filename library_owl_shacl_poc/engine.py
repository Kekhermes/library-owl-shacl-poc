from pathlib import Path

from pyshacl import shacl_rules, validate
from rdflib import Graph

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_raw_graphs() -> tuple[Graph, Graph]:
    """Charge le graphe de données (ontologie + faits) et le graphe de formes SHACL."""
    data_graph = Graph()
    data_graph.parse(str(PROJECT_ROOT / "rdf" / "ontology.ttl"), format="turtle")
    data_graph.parse(str(PROJECT_ROOT / "rdf" / "data.ttl"), format="turtle")

    shapes_graph = Graph()
    shapes_graph.parse(str(PROJECT_ROOT / "rdf" / "shapes.ttl"), format="turtle")

    return data_graph, shapes_graph


def validate_data_graph(
    data_graph: Graph | None = None,
    shapes_graph: Graph | None = None,
) -> tuple[bool, Graph, str]:
    """Valide les données contre les formes SHACL Core et renvoie le rapport de conformité."""
    if data_graph is None or shapes_graph is None:
        dg, sg = load_raw_graphs()
        data_graph = data_graph or dg
        shapes_graph = shapes_graph or sg

    conforms, report_graph, report_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        advanced=True,
    )
    return conforms, report_graph, report_text


def build_demo_graph() -> Graph:
    """Charge les faits RDF puis renvoie un graphe enrichi par les règles d'inférence SHACL."""
    data_graph, shapes_graph = load_raw_graphs()
    return shacl_rules(data_graph, shacl_graph=shapes_graph, advanced=True)
