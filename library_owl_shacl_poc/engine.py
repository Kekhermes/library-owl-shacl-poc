from pathlib import Path
from typing import Any

from pyshacl import shacl_rules, validate
from rdflib import Graph
from rdflib.namespace import OWL, RDF, RDFS

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_raw_graphs() -> tuple[Graph, Graph]:
    """Charge le graphe de données (ontologie + faits) et le graphe de formes SHACL."""
    data_graph = Graph()
    data_graph.parse(str(PROJECT_ROOT / "rdf" / "ontology.ttl"), format="turtle")
    data_graph.parse(str(PROJECT_ROOT / "rdf" / "data.ttl"), format="turtle")

    shapes_graph = Graph()
    shapes_graph.parse(str(PROJECT_ROOT / "rdf" / "shapes.ttl"), format="turtle")

    return data_graph, shapes_graph


def load_ontology_graph() -> Graph:
    """Charge uniquement le graphe du modèle et vocabulaire (T-Box)."""
    ont_graph = Graph()
    ont_graph.parse(str(PROJECT_ROOT / "rdf" / "ontology.ttl"), format="turtle")
    return ont_graph


def validate_tbox_consistency(ontology_graph: Graph | None = None) -> dict[str, Any]:
    """Valide la cohérence logique et la qualité intrinsèque du modèle T-Box.

    Vérifie :
    1. L'absence de classes insatisfiables (conflits d'héritage entre classes mutuellement disjointes).
    2. L'absence de cycles d'héritage illégaux (subClassOf cyclique).
    3. La complétude documentaire (présence de rdfs:label et rdfs:comment).
    """
    g = ontology_graph if ontology_graph is not None else load_ontology_graph()
    classes = set(g.subjects(RDF.type, OWL.Class))
    object_props = set(g.subjects(RDF.type, OWL.ObjectProperty))
    datatype_props = set(g.subjects(RDF.type, OWL.DatatypeProperty))

    def get_superclasses(cls: Any, visited: set | None = None) -> set:
        if visited is None:
            visited = set()
        supers = set()
        for _, _, sup in g.triples((cls, RDFS.subClassOf, None)):
            if sup != cls and sup not in visited:
                visited.add(sup)
                supers.add(sup)
                supers.update(get_superclasses(sup, visited))
        return supers

    errors: list[str] = []
    warnings: list[str] = []

    # 1. Vérification des conflits de disjonction (classes insatisfiables)
    disjoints: set[tuple[Any, Any]] = set()
    for a, _, b in g.triples((None, OWL.disjointWith, None)):
        disjoints.add((a, b))
        disjoints.add((b, a))

    for c in sorted(classes, key=str):
        supers = get_superclasses(c)
        supers.add(c)
        for a, b in disjoints:
            if a in supers and b in supers:
                c_name = str(c).split("#")[-1]
                a_name = str(a).split("#")[-1]
                b_name = str(b).split("#")[-1]
                errors.append(
                    f"Classe insatisfiable: {c_name} hérite de deux classes mutuellement disjointes ({a_name} et {b_name})."
                )
                break

    # 2. Vérification des cycles d'héritage
    for c in sorted(classes, key=str):
        for _, _, sup in g.triples((c, RDFS.subClassOf, None)):
            supers_of_sup = get_superclasses(sup)
            if c in supers_of_sup:
                c_name = str(c).split("#")[-1]
                sup_name = str(sup).split("#")[-1]
                errors.append(f"Cycle d'héritage illégal détecté entre {c_name} et {sup_name}.")

    # 3. Vérification de la complétude documentaire
    for c in sorted(classes, key=str):
        c_name = str(c).split("#")[-1]
        labels = list(g.objects(c, RDFS.label))
        comments = list(g.objects(c, RDFS.comment))
        if not labels:
            warnings.append(f"La classe {c_name} n'a aucun rdfs:label.")
        if not comments:
            warnings.append(f"La classe {c_name} n'a aucun rdfs:comment documentant sa sémantique.")

    return {
        "consistent": len(errors) == 0,
        "classes_count": len(classes),
        "object_properties_count": len(object_props),
        "datatype_properties_count": len(datatype_props),
        "errors": sorted(list(set(errors))),
        "warnings": sorted(list(set(warnings))),
    }


def validate_abox(
    data_graph: Graph | None = None,
    shapes_graph: Graph | None = None,
) -> tuple[bool, Graph, str]:
    """Valide les données concrètes (A-Box) contre les formes SHACL applicatives."""
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


def validate_data_graph(
    data_graph: Graph | None = None,
    shapes_graph: Graph | None = None,
) -> tuple[bool, Graph, str]:
    """Alias rétro-compatible pour la validation de la A-Box."""
    return validate_abox(data_graph, shapes_graph)


def validate_full() -> dict[str, Any]:
    """Exécute la double validation : T-Box (Modèle) et A-Box (Données)."""
    tbox_report = validate_tbox_consistency()
    abox_conforms, _, abox_report_text = validate_abox()

    return {
        "tbox": tbox_report,
        "abox": {
            "conforms": abox_conforms,
            "report_text": abox_report_text,
        },
        "all_valid": tbox_report["consistent"] and abox_conforms,
    }


def build_demo_graph() -> Graph:
    """Charge les faits RDF puis renvoie un graphe enrichi par les règles d'inférence SHACL."""
    data_graph, shapes_graph = load_raw_graphs()
    return shacl_rules(data_graph, shacl_graph=shapes_graph, advanced=True)
